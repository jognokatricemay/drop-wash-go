from werkzeug.security import check_password_hash, generate_password_hash
"""Shop staff side.  Every route only sees bookings of the logged-in staff's shop (NFR-03, NFR-04).
Owners:  Member 5 — dashboard, booking requests, accept / reject, Order ID
         Member 6 — orders, confirm weight, update status, mark as paid, shop info, profile
"""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import execute, query
from .helpers import BOOKING_SQL, booking_price, login_required, notify, peso

bp = Blueprint("staff", __name__, url_prefix="/shop")

STATUSES = [
    ("Accepted", ""),
    ("Processing", "Washing and drying"),
    ("Ready for Pickup", "For drop-off and pickup-only orders"),
    ("Ready for Delivery", "Rider will bring it to the customer"),
    ("Completed", "Laundry received by the customer"),
]


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
    counts = {r["status"]: r["n"] for r in query(
        "SELECT status, COUNT(*) AS n FROM bookings WHERE shop_id=%s GROUP BY status", [sid])}
    active = query(BOOKING_SQL + """ WHERE b.shop_id=%s AND b.order_code IS NOT NULL
                   AND b.status NOT IN ('Completed','Rejected') ORDER BY b.updated_at DESC LIMIT 6""", [sid])
    return render_template("staff/dashboard.html", counts=counts, active_orders=active)


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
    if request.method == "POST" and b["status"] == "Pending":
        schedule = request.form.get("confirmed_schedule", "").strip() or b["requested_time"]
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
            # FR-05: the Order ID is created only when the booking is accepted
            code = f"DWG-{b['id']:05d}"
            execute("UPDATE bookings SET status='Accepted', order_code=%s, confirmed_schedule=%s WHERE id=%s",
                    [code, schedule, b["id"]])
            what = "Drop-off" if b["handling"] == "drop-off" else "Pickup"
            notify(b["customer_id"], b["id"], "success", "Booking accepted",
                   f"#{code} · {what} confirmed {b['requested_date']:%b} {b['requested_date'].day}, {schedule}")
            return redirect(url_for("staff.booking_accepted", booking_id=b["id"]))
    return render_template("staff/booking_details.html", b=b, price=booking_price(b), errors=errors)


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
    
    # Kukuha ng error kung galing sa submit weight form
    weight_error = request.args.get('weight_error')
    
    return render_template("staff/order_details.html", b=b, price=booking_price(b), weight_error=weight_error)


@bp.route("/orders/<int:booking_id>/weight", methods=["POST"])
@login_required("staff")
def confirm_weight(booking_id):
    """The Confirm weight pop-up on the order details page posts here."""
    b = shop_booking(booking_id)
    try:
        weight = Decimal(request.form.get("actual_weight", ""))
        # Binago to block 0 or negative
        if weight <= 0 or weight > 100:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        # I-redirect pabalik na may red text error
        return redirect(url_for("staff.order_details", booking_id=b["id"], weight_error="Enter a valid whole weight (1 or more)."))
        
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
    if request.method == "POST":
        status = request.form.get("status")
        if status not in [s for s, _ in STATUSES]:
            flash("Choose a status.")
        else:
            schedule = request.form.get("delivery_schedule", "").strip() or None
            execute("UPDATE bookings SET status=%s, delivery_schedule=COALESCE(%s, delivery_schedule) WHERE id=%s",
                    [status, schedule, b["id"]])
            if status != b["status"]:
                kind = "delivery" if status.startswith("Ready") else "info"
                body = f"#{b['order_code']}" + (f" · {schedule}" if schedule else "")
                notify(b["customer_id"], b["id"], kind, status if status != "Processing" else "Your laundry is being processed", body)
            flash(f"#{b['order_code']} is now {status}.")
            return redirect(url_for("staff.order_details", booking_id=b["id"]))
    return render_template("staff/update_status.html", b=b, price=booking_price(b), statuses=STATUSES)


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

        # TASK: Remove service
        if "delete_service_id" in f:
            count = query("SELECT COUNT(*) as c FROM services WHERE shop_id=%s", [shop["id"]], one=True)["c"]
            if count <= 1:
                flash("Cannot remove. Your shop must have at least one service.")
            else:
                try:
                    execute("DELETE FROM services WHERE id=%s AND shop_id=%s", [f["delete_service_id"], shop["id"]])
                    flash("Service removed.")
                except Exception:
                    flash("Cannot remove a service that is currently used in bookings.")
            return redirect(url_for("staff.shop_info"))

        # TASK: Add service
        elif "add_new_service" in f:
            new_name = f.get("new_service_name", "").strip()
            new_rate = f.get("new_service_rate", "").strip()
            new_unit = f.get("new_service_unit", "kg").strip()
            
            if not new_name:
                flash("Service name cannot be empty.")
            elif not new_rate:
                flash("Service rate cannot be empty.")
            else:
                try:
                    rate_val = Decimal(new_rate.replace("₱", "").replace(",", ""))
                    if rate_val <= 0:
                        flash("Service rate must be greater than 0.")
                    else:
                        existing = query("SELECT id FROM services WHERE shop_id=%s AND LOWER(name)=LOWER(%s)", [shop["id"], new_name])
                        if existing:
                            flash(f"A service named '{new_name}' already exists.")
                        else:
                            execute("INSERT INTO services (shop_id, name, rate, unit) VALUES (%s, %s, %s, %s)",
                                    [shop["id"], new_name, rate_val, new_unit])
                            flash(f"Service '{new_name}' added successfully.")
                except InvalidOperation:
                    flash("Invalid rate format.")
            return redirect(url_for("staff.shop_info"))

        # KUNG "SAVE CHANGES" (Main form update)
        else:
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
            
            flash("Shop changes saved. They apply to new bookings only.")
            nxt = f.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("staff.shop_info"))
    
    services = query("SELECT * FROM services WHERE shop_id=%s ORDER BY id", [shop["id"]])
    return render_template("staff/shop_info.html", shop=shop, services=services)


@bp.route("/profile", methods=["GET", "POST"])
@login_required("staff")
def profile():
    errors = {}
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        user = query("SELECT * FROM users WHERE id=%s", [g.user["id"]], one=True)
        pw_col = "password_hash" if "password_hash" in user else "password"
        stored_pw = user[pw_col]

        is_valid = check_password_hash(stored_pw, current_pw) if stored_pw.startswith(("scrypt:", "pbkdf2:")) else (stored_pw == current_pw)

        if not is_valid:
            errors["current_password"] = "Incorrect current password."
        elif len(new_pw) < 6:
            errors["new_password"] = "New password must be at least 6 characters."
        elif new_pw != confirm_pw:
            errors["confirm_password"] = "New passwords do not match."
        else:
            new_hash = generate_password_hash(new_pw)
            execute(f"UPDATE users SET {pw_col}=%s WHERE id=%s", [new_hash, g.user["id"]])
            flash("Password updated successfully.")
            return redirect(url_for("staff.profile"))

    return render_template("staff/profile.html", errors=errors)