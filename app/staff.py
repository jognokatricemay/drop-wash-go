"""Shop staff side.  Every route only sees bookings of the logged-in staff's shop (NFR-03, NFR-04).
Owners:  Member 5 — dashboard, booking requests, accept / reject, Order ID
         Member 6 — orders, confirm weight, update status, mark as paid, shop info, profile
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import execute, query
from .helpers import BOOKING_SQL, booking_price, login_required, notify, peso, schedule_label, time_input_value, time_label

bp = Blueprint("staff", __name__, url_prefix="/shop")

SHOP_ORDER_PREFIXES = {"clean & fresh": "CNF"}

STATUSES = [
    ("Accepted", ""),
    ("Processing", "Washing and drying"),
    ("Ready for Pickup", "For drop-off and pickup-only orders"),
    ("Ready for Delivery", "Rider will bring it to the customer"),
    ("Completed", "Laundry received by the customer"),
]

TODAY_PICKUP_STATUSES = ("Pending", "Accepted", "Processing")


def order_code(shop_name, booking_id):
    normalized_name = " ".join(shop_name.casefold().split())
    prefix = SHOP_ORDER_PREFIXES.get(normalized_name)
    if prefix is None:
        words = ["".join(char for char in word if char.isalnum()) for word in shop_name.split()]
        prefix = "".join(word[0] for word in words if word).upper()
    return f"{prefix}-{booking_id:05d}"


def shop_booking(booking_id):
    b = query(BOOKING_SQL + " WHERE b.id=%s AND b.shop_id=%s", [booking_id, g.shop["id"]], one=True)
    if not b:
        abort(404)
    return b


# ---------- Member 5: dashboard and booking requests ----------

@bp.route("/dashboard")
@login_required("staff")
def dashboard():
    sid = g.shop["id"]
    today = date.today().isoformat()
    counts = {r["status"]: r["n"] for r in query(
        "SELECT status, COUNT(*) AS n FROM bookings WHERE shop_id=%s GROUP BY status", [sid])}
    active = query(BOOKING_SQL + """ WHERE b.shop_id=%s AND b.order_code IS NOT NULL
                   AND b.status NOT IN ('Completed','Rejected') ORDER BY b.updated_at DESC LIMIT 6""", [sid])
    today_pickup_count = query(
        """SELECT COUNT(*) AS n FROM bookings
           WHERE shop_id=%s AND requested_date=%s AND handling IN ('pickup','pickup-delivery')
           AND status IN %s""",
        [sid, today, TODAY_PICKUP_STATUSES], one=True,
    )["n"]
    return render_template("staff/dashboard.html", counts=counts, active_orders=active,
                           today_pickup_count=today_pickup_count)


@bp.route("/pickups/today")
@login_required("staff")
def today_pickups():
    today = date.today().isoformat()
    rows = query(BOOKING_SQL + """ WHERE b.shop_id=%s AND b.requested_date=%s
                      AND b.handling IN ('pickup','pickup-delivery') AND b.status IN %s
                      ORDER BY b.requested_time, b.id""",
                 [g.shop["id"], today, TODAY_PICKUP_STATUSES])
    return render_template("staff/today_pickups.html", rows=rows, today=date.today())


@bp.route("/requests")
@login_required("staff")
def requests():
    tab = request.args.get("tab", "Pending")
    where = {"Pending": "b.status='Pending'", "Rejected": "b.status='Rejected'"}.get(
        tab, "b.order_code IS NOT NULL")
    rows = query(BOOKING_SQL + f" WHERE b.shop_id=%s AND {where} ORDER BY b.requested_date, b.id DESC LIMIT 50",
                 [g.shop["id"]])
    n_pending = query("SELECT COUNT(*) AS n FROM bookings WHERE shop_id=%s AND status='Pending'",
                      [g.shop["id"]], one=True)["n"]
    return render_template("staff/requests.html", rows=rows, tab=tab, n_pending=n_pending)


@bp.route("/requests/<int:booking_id>", methods=["GET", "POST"])
@login_required("staff")
def booking_details(booking_id):
    b = shop_booking(booking_id)
    errors = {}
    confirmed_time = request.form.get("confirmed_schedule", "").strip() if request.method == "POST" else b["requested_time"]
    if request.method == "POST" and b["status"] == "Pending":
        if request.form.get("action") == "reject":
            reason = request.form.get("reason", "").strip()
            if not reason:
                errors["reason"] = "Give the customer a reason."
            else:
                execute("UPDATE bookings SET status='Rejected', reject_reason=%s WHERE id=%s", [reason, b["id"]])
                notify(b["customer_id"], b["id"], "error", "Booking not accepted", f"{b['shop_name']} · {reason}")
                flash(f"Booking from {b['customer_name']} was rejected.")
                return redirect(url_for("staff.requests"))
        else:
            if not time_input_value(confirmed_time) or confirmed_time != time_input_value(confirmed_time):
                errors["confirmed_schedule"] = "Choose a time."
            else:
                # FR-05: the Order ID is created only when the booking is accepted
                code = order_code(b["shop_name"], b["id"])
                execute("UPDATE bookings SET status='Accepted', order_code=%s, confirmed_schedule=%s WHERE id=%s",
                        [code, confirmed_time, b["id"]])
                what = "Drop-off" if b["handling"] == "drop-off" else "Pickup"
                notify(b["customer_id"], b["id"], "success", "Booking accepted",
                       f"#{code} · {what} confirmed {b['requested_date']:%b} {b['requested_date'].day}, {time_label(confirmed_time)}")
                return redirect(url_for("staff.booking_accepted", booking_id=b["id"]))
    return render_template("staff/booking_details.html", b=b, price=booking_price(b), errors=errors,
                           confirmed_time=confirmed_time)


@bp.route("/requests/<int:booking_id>/accepted")
@login_required("staff")
def booking_accepted(booking_id):
    return render_template("staff/booking_accepted.html", b=shop_booking(booking_id))


# ---------- Member 6: orders ----------

@bp.route("/orders")
@login_required("staff")
def orders():
    tab = request.args.get("tab", "all")
    q = request.args.get("q", "").strip()
    where = "b.shop_id=%s AND b.order_code IS NOT NULL"
    args = [g.shop["id"]]
    if tab == "active":
        where += " AND b.status <> 'Completed'"
    elif tab == "completed":
        where += " AND b.status = 'Completed'"
    if q:
        where += " AND (b.order_code LIKE %s OR u.full_name LIKE %s)"
        args += [f"%{q.lstrip('#')}%", f"%{q}%"]
    rows = query(BOOKING_SQL + f" WHERE {where} ORDER BY b.updated_at DESC LIMIT 100", args)
    return render_template("staff/orders.html", rows=rows, tab=tab, q=q)


@bp.route("/orders/<int:booking_id>")
@login_required("staff")
def order_details(booking_id):
    b = shop_booking(booking_id)
    if not b["order_code"]:
        return redirect(url_for("staff.booking_details", booking_id=b["id"]))
    return render_template("staff/order_details.html", b=b, price=booking_price(b))


@bp.route("/orders/<int:booking_id>/weight", methods=["POST"])
@login_required("staff")
def confirm_weight(booking_id):
    """The Confirm weight pop-up on the order details page posts here."""
    b = shop_booking(booking_id)
    try:
        weight = Decimal(request.form.get("actual_weight", ""))
        if weight <= 0 or weight > 100:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        flash("Enter a valid weight.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
    new_status = "Processing" if b["status"] == "Accepted" else b["status"]
    execute("UPDATE bookings SET actual_weight=%s, status=%s WHERE id=%s", [weight, new_status, b["id"]])
    b.update(actual_weight=weight)
    total = booking_price(b)["total"]
    notify(b["customer_id"], b["id"], "info", "Your laundry is being processed",
           f"#{b['order_code']} · Final total {peso(total, 2)} ({weight.normalize():f} {b['unit']})")
    flash(f"Weight saved: {weight.normalize():f} {b['unit']}. New total {peso(total, 2)}.")
    return redirect(url_for("staff.order_details", booking_id=b["id"]))


@bp.route("/orders/<int:booking_id>/status", methods=["GET", "POST"])
@login_required("staff")
def update_status(booking_id):
    b = shop_booking(booking_id)
    errors = {}
    selected_status = request.form.get("status", b["status"]) if request.method == "POST" else b["status"]
    form_date = request.form.get("delivery_date", "").strip() if request.method == "POST" else ""
    form_time = request.form.get("delivery_time", "").strip() if request.method == "POST" else ""
    existing_schedule = b["delivery_schedule"] or ""
    if request.method == "GET" and existing_schedule:
        try:
            scheduled = datetime.strptime(existing_schedule, "%Y-%m-%dT%H:%M")
            form_date = scheduled.date().isoformat()
            form_time = scheduled.strftime("%H:%M")
        except ValueError:
            pass

    if request.method == "POST":
        status = request.form.get("status")
        if status not in [s for s, _ in STATUSES]:
            errors["status"] = "Choose a status."
            flash("Choose a status.")
        schedule = None
        if form_date or form_time:
            try:
                scheduled_date = datetime.strptime(form_date, "%Y-%m-%d").date()
                if scheduled_date < date.today():
                    errors["delivery_date"] = "Choose today or a later date."
            except ValueError:
                errors["delivery_date"] = "Choose a date."
            if not form_time or form_time != time_input_value(form_time):
                errors["delivery_time"] = "Choose a time."
            if not errors:
                schedule = f"{form_date}T{form_time}"
        if not errors:
            execute("UPDATE bookings SET status=%s, delivery_schedule=COALESCE(%s, delivery_schedule) WHERE id=%s",
                    [status, schedule, b["id"]])
            if status != b["status"]:
                kind = "delivery" if status.startswith("Ready") else "info"
                body = f"#{b['order_code']}" + (f" · {schedule_label(schedule)}" if schedule else "")
                notify(b["customer_id"], b["id"], kind, status if status != "Processing" else "Your laundry is being processed", body)
            flash(f"#{b['order_code']} is now {status}.")
            return redirect(url_for("staff.order_details", booking_id=b["id"]))
    return render_template("staff/update_status.html", b=b, price=booking_price(b), statuses=STATUSES,
                           errors=errors, selected_status=selected_status, form_date=form_date, form_time=form_time,
                           existing_schedule=existing_schedule)


@bp.route("/orders/<int:booking_id>/paid", methods=["GET", "POST"])
@login_required("staff")
def mark_paid(booking_id):
    b = shop_booking(booking_id)
    price = booking_price(b)
    errors = {}
    if request.method == "POST":
        method = request.form.get("method")
        if method == "gcash":
            ref = request.form.get("gcash_reference", "").strip()
            if not ref:
                errors["gcash_reference"] = "Enter the GCash reference number."
            else:
                execute("UPDATE bookings SET payment_status='Paid', payment_method='gcash', gcash_reference=%s WHERE id=%s",
                        [ref, b["id"]])
        else:
            try:
                received = Decimal(request.form.get("amount_received", "").replace("₱", "").replace(",", ""))
                if received < price["total"]:
                    errors["amount_received"] = f"Amount is less than {peso(price['total'], 2)}."
            except InvalidOperation:
                errors["amount_received"] = "Enter the amount received."
            if not errors:
                execute("UPDATE bookings SET payment_status='Paid', payment_method='cash', amount_received=%s WHERE id=%s",
                        [received, b["id"]])
        if not errors:
            flash(f"#{b['order_code']} is marked as paid.")
            return redirect(url_for("staff.order_details", booking_id=b["id"]))
    return render_template("staff/mark_paid.html", b=b, price=price, errors=errors, form=request.form)


# ---------- Member 6: shop info and profile ----------

@bp.route("/shop-info", methods=["GET", "POST"])
@login_required("staff")
def shop_info():
    shop = g.shop
    if request.method == "POST":
        f = request.form
        try:
            fee = Decimal((f.get("delivery_fee") or "0").replace("₱", "").replace(",", ""))
        except InvalidOperation:
            fee = shop["delivery_fee"]
        execute("""UPDATE shops SET name=%s, contact_number=%s, address=%s, opening_hours=%s,
                   offers_dropoff=%s, offers_pickup=%s, offers_delivery=%s, delivery_fee=%s,
                   accepts_cash=%s, accepts_gcash=%s, gcash_number=%s, gcash_name=%s WHERE id=%s""",
                [f.get("name", shop["name"]).strip() or shop["name"], f.get("contact_number", "").strip(),
                 f.get("address", "").strip(), f.get("opening_hours", "").strip(),
                 "offers_dropoff" in f, "offers_pickup" in f, "offers_delivery" in f, fee,
                 "accepts_cash" in f, "accepts_gcash" in f, f.get("gcash_number", "").strip() or None,
                 f.get("gcash_name", "").strip() or None, shop["id"]])
        for svc in query("SELECT id FROM services WHERE shop_id=%s", [shop["id"]]):
            rate = f.get(f"rate_{svc['id']}")
            if rate:
                try:
                    execute("UPDATE services SET rate=%s WHERE id=%s", [Decimal(rate), svc["id"]])
                except InvalidOperation:
                    pass
        # TODO (Member 6): "+ Add service" form (name, rate, unit) -> INSERT INTO services
        flash("Changes saved. They apply to new bookings only.")
        nxt = f.get("next", "")
        return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("staff.shop_info"))
    services = query("SELECT * FROM services WHERE shop_id=%s ORDER BY id", [shop["id"]])
    return render_template("staff/shop_info.html", shop=shop, services=services)


@bp.route("/profile")
@login_required("staff")
def profile():
    # TODO (Member 6): change password page
    return render_template("staff/profile.html")
