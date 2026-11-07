"""Shop staff side.  Every route only sees bookings of the logged-in staff's shop (NFR-03, NFR-04).
Owners:  Member 5 — dashboard, booking requests, accept / reject, Order ID
         Member 6 — orders, confirm weight, update status, mark as paid, shop info, profile
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query
from .helpers import BOOKING_SQL, booking_price, login_required, notify, peso, schedule_label, time_input_value, time_label, today_ph

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


def status_flow(b):
    """The steps of one order, in order. An order moves one step at a time and never goes back."""
    ready = "Ready for Delivery" if b["handling"] == "pickup-delivery" else "Ready for Pickup"
    return ["Accepted", "Processing", ready, "Completed"]


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
    today = today_ph().isoformat()
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
    unpaid_done = query(BOOKING_SQL + """ WHERE b.shop_id=%s AND b.status='Completed' AND b.payment_status<>'Paid'
                       ORDER BY b.updated_at DESC LIMIT 6""", [sid])
    return render_template("staff/dashboard.html", counts=counts, active_orders=active,
                           today_pickup_count=today_pickup_count, unpaid_done=unpaid_done)


@bp.route("/pickups/today")
@login_required("staff")
def today_pickups():
    today = today_ph().isoformat()
    rows = query(BOOKING_SQL + """ WHERE b.shop_id=%s AND b.requested_date=%s
                      AND b.handling IN ('pickup','pickup-delivery') AND b.status IN %s
                      ORDER BY b.requested_time, b.id""",
                 [g.shop["id"], today, TODAY_PICKUP_STATUSES])
    return render_template("staff/today_pickups.html", rows=rows, today=today_ph())


@bp.route("/requests")
@login_required("staff")
def requests():
    tab = request.args.get("tab", "Pending")
    where = {"Pending": "b.status='Pending'", "Rejected": "b.status='Rejected'", "Cancelled": "b.status='Cancelled'"}.get(
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
        elif request.form.get("action") == "accept":
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
    elif tab == "unpaid":  # done, but the money is not collected yet
        where += " AND b.status = 'Completed' AND b.payment_status <> 'Paid'"
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
    
    weight_error = request.args.get("weight_error")
    weight_val = request.args.get("weight_val")
    return render_template("staff/order_details.html", b=b, price=booking_price(b), weight_error=weight_error, weight_val=weight_val)


@bp.route("/orders/<int:booking_id>/weight", methods=["POST"])
@login_required("staff")
def confirm_weight(booking_id):
    """The Confirm weight pop-up on the order details page posts here."""
    b = shop_booking(booking_id)
    if b["status"] == "Completed":
        flash("This order is completed. The weight can't be changed anymore.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
    # the weight is confirmed once, while Accepted; after that it can only be corrected until the order is completed
    if b["status"] not in status_flow(b) or (b["status"] != "Accepted" and b["actual_weight"] is None):
        flash("The weight can only be confirmed while the order is Accepted.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
    raw_weight = request.form.get("actual_weight", "").strip()
    if not raw_weight:
        return redirect(url_for("staff.order_details", booking_id=b["id"], weight_error="Actual weight cannot be empty.", weight_val=""))
    try:
        weight = Decimal(raw_weight)
        if weight <= 0 or weight > 100:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return redirect(url_for("staff.order_details", booking_id=b["id"], weight_error="Enter a valid weight (more than 0 and up to 100).", weight_val=raw_weight))
        
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
    flow = status_flow(b)
    if b["status"] not in flow:
        return redirect(url_for("staff.booking_details", booking_id=b["id"]))
    if b["status"] == "Completed":
        flash("This order is completed. Its status can't be changed anymore.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
    if b["status"] == "Accepted":  # the laundry has to be weighed first; saving the weight starts Processing
        flash("Confirm the weight first. The order moves to Processing after that.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
    # only the current status and the next one can be chosen
    allowed = flow[flow.index(b["status"]):][:2]
    choices = [(name, sub) for name, sub in STATUSES if name in allowed]

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
        if status not in allowed:
            errors["status"] = "Choose the current status or the next step. An order can't skip a step or go back."
        schedule = None
        # the customer must know when the laundry will be delivered, so Ready for Delivery needs a schedule
        needs_schedule = status == "Ready for Delivery"
        if needs_schedule or form_date or form_time:
            try:
                scheduled_date = datetime.strptime(form_date, "%Y-%m-%d").date()
                if scheduled_date < today_ph():
                    errors["delivery_date"] = "Choose today or a later date."
            except ValueError:
                errors["delivery_date"] = "Choose a delivery date." if needs_schedule else "Choose a date."
            if not form_time or form_time != time_input_value(form_time):
                errors["delivery_time"] = "Choose a delivery time." if needs_schedule else "Choose a time."
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
            if status == "Completed" and b["payment_status"] != "Paid":
                flash("Reminder: this order is not marked as paid yet. Collect the payment, then use Mark as paid.")
            return redirect(url_for("staff.order_details", booking_id=b["id"]))
    return render_template("staff/update_status.html", b=b, price=booking_price(b), statuses=choices,
                           errors=errors, selected_status=selected_status, form_date=form_date, form_time=form_time,
                           existing_schedule=existing_schedule)


@bp.route("/orders/<int:booking_id>/paid", methods=["GET", "POST"])
@login_required("staff")
def mark_paid(booking_id):
    b = shop_booking(booking_id)
        # A payment can only be recorded after the shop accepted the order and weighed the laundry (the final price is known)
    if not b["order_code"] or b["actual_weight"] is None:
        flash("Confirm the weight first. An order can only be marked as paid after it is accepted and weighed.")
        return redirect(url_for("staff.order_details", booking_id=b["id"]))
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


# ---------- Notifications (new requests, cancellations) ----------

@bp.route("/notifications")
@login_required("staff")
def notifications():
    rows = query("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC, id DESC LIMIT 50", [g.user["id"]])
    return render_template("staff/notifications.html", items=rows, now=datetime.now())


@bp.route("/notifications/read-all", methods=["POST"])
@login_required("staff")
def read_all():
    execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", [g.user["id"]])
    return redirect(url_for("staff.notifications"))


@bp.route("/notifications/<int:nid>")
@login_required("staff")
def open_notification(nid):
    n = query("SELECT * FROM notifications WHERE id=%s AND user_id=%s", [nid, g.user["id"]], one=True)
    if not n:
        abort(404)
    execute("UPDATE notifications SET is_read=1 WHERE id=%s", [nid])
    if not n["booking_id"]:
        return redirect(url_for("staff.notifications"))
    # a request opens its request page; an accepted order opens its order page (order_details sorts that out)
    return redirect(url_for("staff.order_details", booking_id=n["booking_id"]))


# ---------- Member 6: shop info and profile ----------

def _parse_opening_hours(hours_str):
    if not hours_str:
        return "08:00", "18:00"
    parts = re.split(r'\s*(?:–|-|to)\s*', hours_str.strip(), flags=re.IGNORECASE)
    if len(parts) == 2:
        res = []
        for p in parts:
            p_clean = p.strip().upper()
            for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
                try:
                    res.append(datetime.strptime(p_clean, fmt).strftime("%H:%M"))
                    break
                except ValueError:
                    pass
        if len(res) == 2:
            return res[0], res[1]
    return "08:00", "18:00"


def _format_12hr(time_24):
    try:
        dt = datetime.strptime(time_24.strip(), "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return time_24


@bp.route("/shop-info", methods=["GET", "POST"])
@login_required("staff")
def shop_info():
    shop = g.shop
    services = query("SELECT * FROM services WHERE shop_id=%s ORDER BY id", [shop["id"]])
    
    status_msg = session.pop("shop_status_msg", None)
    add_service_error = session.pop("add_service_error", None)
    add_service_data = session.pop("add_service_data", {"name": "", "rate": "", "unit": "kg"})
    shop_errors = {}
    form_data = None
    hours_from, hours_to = _parse_opening_hours(shop.get("opening_hours", ""))

    if request.method == "POST":
        f = request.form

        if "delete_service_id" in f:
            count = query("SELECT COUNT(*) as c FROM services WHERE shop_id=%s", [shop["id"]], one=True)["c"]
            if count <= 1:
                session["shop_status_msg"] = "Cannot remove. Your shop must have at least one service."
            else:
                try:
                    execute("DELETE FROM services WHERE id=%s AND shop_id=%s", [f["delete_service_id"], shop["id"]])
                    session["shop_status_msg"] = "Service removed."
                except Exception:
                    session["shop_status_msg"] = "Cannot remove a service that is currently used in bookings."
            return redirect(url_for("staff.shop_info"))

        elif "add_new_service" in f:
            new_name = f.get("new_service_name", "").strip()
            new_rate = f.get("new_service_rate", "").strip()
            new_unit = f.get("new_service_unit", "kg").strip()
            
            err = None
            if not new_name:
                err = "Service name cannot be empty."
            elif not new_rate:
                err = "Service rate cannot be empty."
            else:
                try:
                    rate_val = Decimal(new_rate.replace("₱", "").replace(",", ""))
                    if rate_val <= 0:
                        err = "Service rate must be greater than 0."
                    else:
                        existing = query("SELECT id FROM services WHERE shop_id=%s AND LOWER(name)=LOWER(%s)", [shop["id"], new_name])
                        if existing:
                            err = f"A service named '{new_name}' already exists."
                        else:
                            execute("INSERT INTO services (shop_id, name, rate, unit) VALUES (%s, %s, %s, %s)",
                                    [shop["id"], new_name, rate_val, new_unit])
                            session["shop_status_msg"] = f"Service '{new_name}' added."
                except InvalidOperation:
                    err = "Invalid rate format."
            
            if err:
                session["add_service_error"] = err
                session["add_service_data"] = {"name": new_name, "rate": new_rate, "unit": new_unit}
            return redirect(url_for("staff.shop_info"))

        else:
            name = f.get("name", "").strip()
            raw_contact = f.get("contact_number", "").strip()
            contact_digits = re.sub(r"[\s\-]", "", raw_contact)
            address = f.get("address", "").strip()
            h_from = f.get("hours_from", "").strip()
            h_to = f.get("hours_to", "").strip()
            
            offers_dropoff = "offers_dropoff" in f
            offers_pickup = "offers_pickup" in f
            offers_delivery = "offers_delivery" in f
            accepts_cash = "accepts_cash" in f
            accepts_gcash = "accepts_gcash" in f
            raw_gcash_number = f.get("gcash_number", "").strip()
            gcash_digits = re.sub(r"[\s\-]", "", raw_gcash_number)
            gcash_name = f.get("gcash_name", "").strip()

            if not name:
                shop_errors["name"] = "Shop name cannot be empty."
            if not contact_digits:
                shop_errors["contact_number"] = "Contact number cannot be empty."
            elif not re.match(r"^09\d{9}$", contact_digits):
                shop_errors["contact_number"] = 'Contact number must start with "09" and contain 11 numbers.'
            if not address:
                shop_errors["address"] = "Address cannot be empty."
            if not h_from or not h_to:
                shop_errors["opening_hours"] = "Please select both opening and closing hours."
            elif h_from >= h_to:
                shop_errors["opening_hours"] = "Closing time must be later than opening time."
            
            if not (offers_dropoff or offers_pickup or offers_delivery):
                shop_errors["offers"] = "You must offer at least one service (Drop-off, Pickup, or Delivery)."
            if not (accepts_cash or accepts_gcash):
                shop_errors["payments"] = "You must accept at least one payment method (Cash or GCash)."
            if accepts_gcash:
                if not gcash_digits:
                    shop_errors["gcash_number"] = "GCash number cannot be empty."
                elif not re.match(r"^09\d{9}$", gcash_digits):
                    shop_errors["gcash_number"] = 'GCash number must start with "09" and contain 11 numbers.'
                if not gcash_name:
                    shop_errors["gcash_name"] = "Account name cannot be empty."

            if shop_errors:
                hours_from, hours_to = h_from, h_to
                form_data = {
                    "name": name, "contact_number": raw_contact, "address": address,
                    "opening_hours": f.get("opening_hours", ""),
                    "offers_dropoff": offers_dropoff, "offers_pickup": offers_pickup, "offers_delivery": offers_delivery,
                    "delivery_fee": f.get("delivery_fee", "0"),
                    "accepts_cash": accepts_cash, "accepts_gcash": accepts_gcash,
                    "gcash_number": raw_gcash_number, "gcash_name": gcash_name
                }
                return render_template("staff/shop_info.html", shop=shop, services=services,
                                       shop_errors=shop_errors, form_data=form_data,
                                       hours_from=hours_from, hours_to=hours_to,
                                       add_service_error=None, add_service_data=add_service_data,
                                       status_msg=None)

            opening_hours_formatted = f"{_format_12hr(h_from)} – {_format_12hr(h_to)}"
            try:
                fee = Decimal((f.get("delivery_fee") or "0").replace("₱", "").replace(",", ""))
                if fee < 0:
                    fee = Decimal("0")
            except InvalidOperation:
                fee = shop["delivery_fee"]
                
            execute("""UPDATE shops SET name=%s, contact_number=%s, address=%s, opening_hours=%s,
                       offers_dropoff=%s, offers_pickup=%s, offers_delivery=%s, delivery_fee=%s,
                       accepts_cash=%s, accepts_gcash=%s, gcash_number=%s, gcash_name=%s WHERE id=%s""",
                    [name, contact_digits, address, opening_hours_formatted,
                     offers_dropoff, offers_pickup, offers_delivery, fee,
                     accepts_cash, accepts_gcash, gcash_digits or None,
                     gcash_name or None, shop["id"]])
                     
            for svc in services:
                rate = f.get(f"rate_{svc['id']}")
                if rate:
                    try:
                        r_val = Decimal(rate)
                        if r_val > 0:
                            execute("UPDATE services SET rate=%s WHERE id=%s", [r_val, svc["id"]])
                    except InvalidOperation:
                        pass
            
            session["shop_status_msg"] = "Shop changes saved. They apply to new bookings only."
            nxt = f.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("staff.shop_info"))
    
    return render_template("staff/shop_info.html", shop=shop, services=services,
                           shop_errors=shop_errors, form_data=form_data,
                           hours_from=hours_from, hours_to=hours_to,
                           add_service_error=add_service_error, add_service_data=add_service_data,
                           status_msg=status_msg)


@bp.route("/profile", methods=["GET", "POST"])
@login_required("staff")
def profile():
    errors = {}
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        user = query("SELECT password_hash FROM users WHERE id=%s", [g.user["id"]], one=True)
        is_valid = check_password_hash(user["password_hash"], current_pw)

        if not is_valid:
            errors["current_password"] = "Incorrect current password."
        elif len(new_pw) < 8:
            errors["new_password"] = "Use at least 8 characters."
        elif new_pw != confirm_pw:
            errors["confirm_password"] = "New passwords do not match."
        else:
            new_hash = generate_password_hash(new_pw)
            execute("UPDATE users SET password_hash=%s WHERE id=%s", [new_hash, g.user["id"]])
            flash("Password updated successfully.")
            return redirect(url_for("staff.profile"))

    return render_template("staff/profile.html", errors=errors)