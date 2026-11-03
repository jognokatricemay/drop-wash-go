"""Customer side.
Owners:  Member 3 — shops, shop details, booking, review, request sent
         Member 4 — home, my orders, order details, notifications, profile
"""
from datetime import date, datetime, timedelta, time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for

from .db import execute, query
from .helpers import BOOKING_SQL, HANDLING, TIME_SLOTS, booking_price, login_required, now_ph, today_ph

bp = Blueprint("customer", __name__)

ACTIVE = ("Pending", "Accepted", "Processing", "Ready for Pickup", "Ready for Delivery")


def get_shop(shop_id):
    shop = query("SELECT * FROM shops WHERE id=%s", [shop_id], one=True)
    if not shop:
        abort(404)
    shop["services"] = query("SELECT * FROM services WHERE shop_id=%s ORDER BY id", [shop_id])
    return shop


def own_booking(booking_id):
    b = query(BOOKING_SQL + " WHERE b.id=%s AND b.customer_id=%s", [booking_id, g.user["id"]], one=True)
    if not b:
        abort(404)
    return b


# ---------- Member 4: home ----------

@bp.route("/home")
@login_required("customer")
def home():
    uid = g.user["id"]
    active = query(BOOKING_SQL + """ WHERE b.customer_id=%s AND b.order_code IS NOT NULL
                   AND b.status IN ('Accepted','Processing','Ready for Pickup','Ready for Delivery')
                   ORDER BY b.updated_at DESC LIMIT 1""", [uid], one=True)
    recent = query(BOOKING_SQL + " WHERE b.customer_id=%s ORDER BY b.created_at DESC, b.id DESC LIMIT 5", [uid])
    n_active = query("SELECT COUNT(*) AS n FROM bookings WHERE customer_id=%s AND status IN %s", [uid, ACTIVE], one=True)["n"]
    return render_template("customer/home.html", active_order=active, recent=recent, n_active=n_active)


# ---------- Member 3: shops and booking ----------

@bp.route("/shops")
def shops():
    # Every shop is listed; the search box and filter chips work in the browser (see app.js)
    rows = query("""SELECT s.*, MIN(CASE WHEN v.unit='kg' THEN v.rate END) AS from_rate
                    FROM shops s LEFT JOIN services v ON v.shop_id = s.id
                    GROUP BY s.id ORDER BY s.name""")
    return render_template("customer/shops.html", shops=rows)


@bp.route("/shops/<int:shop_id>")
def shop_details(shop_id):
    shop = get_shop(shop_id)
    if not shop:
        abort(404)
    return render_template("customer/shop_details.html", shop=get_shop(shop_id))

def offered_for(shop):
    return [h for h, ok in (("drop-off", shop["offers_dropoff"]), ("pickup", shop["offers_pickup"]),
                            ("pickup-delivery", shop["offers_pickup"] and shop["offers_delivery"])) if ok]
def parse_hours(text):
    """Ginagawang (opens, closes) na time ang '8:00 AM - 8:00 PM'. Ibinabalik ang None kung hindi mabasa."""
    try:
        left, right = text.replace("–", "-").split("-")
        fmt = "%I:%M %p"
        return (datetime.strptime(left.strip().upper(), fmt).time(),
                datetime.strptime(right.strip().upper(), fmt).time())
    except (ValueError, AttributeError):
        return None


def slot_error(shop, when, slot):
    start, end = TIME_SLOTS[slot]
    hours = parse_hours(shop["opening_hours"])
    if hours:   
        opens, closes = hours
        if start < opens or end > closes:
            return (f"This shop is open from {opens:%I:%M %p} until {closes:%I:%M %p}. "
                    "Please choose a time within these hours.")
    if when == today_ph() and start <= now_ph().time():
        return "This time slot has already passed. Please choose a later time or another date."
    return None


def validate_booking(shop, form, offered):
    errors, weight, when = {}, None, None
    service = next((s for s in shop["services"] if str(s["id"]) == form.get("service_id")), None)
    if not service:
        errors["service_id"] = "Please choose a service."

    handling = form.get("handling")
    if handling not in offered:
        errors["handling"] = "This shop doesn't offer the selected option."

    try:
        weight = Decimal(form.get("est_weight", "").strip())
        if not weight.is_finite() or weight <= 0:
            errors["est_weight"] = "Weight must be greater than 0 kg."
        elif weight > 100:
            errors["est_weight"] = "We can only accept up to 100 kg per booking."
    except (InvalidOperation, ValueError):
        errors["est_weight"] = "Enter the estimated weight as a number (e.g., 3.5)."

    try:
        when = datetime.strptime(form.get("requested_date", ""), "%Y-%m-%d").date()
        if when < today_ph():
            errors["requested_date"] = "Past dates are not allowed. Choose today or a later date."
    except ValueError:
        errors["requested_date"] = "Please choose a date."

    slot = form.get("requested_time")
    if slot not in TIME_SLOTS:
        errors["requested_time"] = "Please choose a time."
    elif when and "requested_date" not in errors:
        msg = slot_error(shop, when, slot)
        if msg:
            errors["requested_time"] = msg

    if handling in ("pickup", "pickup-delivery") and not form.get("address", "").strip():
        errors["address"] = "Enter the address where we should pick up your laundry."

    return errors, service, weight

@bp.route("/shops/<int:shop_id>/book", methods=["GET", "POST"])
@login_required("customer")
def book(shop_id):
    shop = get_shop(shop_id)
    if not shop:
        abort(404)
    offered = offered_for(shop)
    errors = {}
    # Start from the saved draft when coming back from Review ("Edit booking")
    draft = session.get("draft") if session.get("draft", {}).get("shop_id") == shop_id else {}
    form = request.form if request.method == "POST" else {
        "service_id": str(draft.get("service_id", shop["services"][0]["id"] if shop["services"] else "")),
        "handling": draft.get("handling", offered[-1] if offered else "drop-off"),
        "est_weight": draft.get("est_weight", ""),
        "requested_date": draft.get("requested_date", ""),
        "requested_time": draft.get("requested_time", "9-11 AM"),
        "address": draft.get("address", g.user["address"] or ""),
        "notes": draft.get("notes", ""),
    }

    if request.method == "POST":
        errors, service, weight = validate_booking(shop, form, offered)
        if not errors:
            handling = form.get("handling")
            session["draft"] = {
                "shop_id": shop_id, "service_id": service["id"], "handling": handling,
                "est_weight": str(weight), "requested_date": form["requested_date"],
                "requested_time": form["requested_time"],
                "address": form.get("address", "").strip() if handling != "drop-off" else "",
                "notes": form.get("notes", "").strip()[:255],
            }
            return redirect(url_for("customer.review"))
    return render_template("customer/book.html", shop=shop, offered=offered, errors=errors, form=form,
                           time_slots=TIME_SLOTS, handling_labels=HANDLING,
                           today=today_ph().isoformat())


def draft_booking():
    """The booking being reviewed, shaped like a row from the bookings table."""
    d = session.get("draft")
    if not d:
        return None, None
    shop = get_shop(d["shop_id"])
    if not shop:                      
        session.pop("draft", None)    
        return None, None             
    service = next((s for s in shop["services"] if s["id"] == d["service_id"]), None)
    if not service:
        return None, None
    b = {"service_name": service["name"], "rate": service["rate"], "unit": service["unit"],
         "handling": d["handling"], "delivery_fee": shop["delivery_fee"] if d["handling"] == "pickup-delivery" else 0,
         "est_weight": Decimal(d["est_weight"]), "actual_weight": None,
         "requested_date": datetime.strptime(d["requested_date"], "%Y-%m-%d").date(),
         "requested_time": d["requested_time"], "address": d["address"], "notes": d["notes"]}
    return shop, b


@bp.route("/book/review", methods=["GET", "POST"])
@login_required("customer")
def review():
    shop, b = draft_booking()
    if not shop:
        return redirect(url_for("customer.shops"))
    if request.method == "POST":
        form_data = {k: str(v) for k, v in session["draft"].items()}
        errors, _, _ = validate_booking(shop, form_data, offered_for(shop))
        if errors:
            flash("May kailangang ayusin sa booking mo. Paki-edit at subukan ulit.", "error")
            return redirect(url_for("customer.book", shop_id=shop["id"]))
        new_id = execute(
            """INSERT INTO bookings (customer_id, shop_id, service_name, rate, unit, handling, delivery_fee,
               est_weight, requested_date, requested_time, address, notes)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [g.user["id"], shop["id"], b["service_name"], b["rate"], b["unit"], b["handling"], b["delivery_fee"],
             b["est_weight"], b["requested_date"], b["requested_time"], b["address"] or None, b["notes"] or None])
        session.pop("draft", None)
        return redirect(url_for("customer.request_sent", booking_id=new_id))
    return render_template("customer/review.html", shop=shop, b=b, price=booking_price(b))


@bp.route("/book/sent/<int:booking_id>")
@login_required("customer")
def request_sent(booking_id):
    return render_template("customer/request_sent.html", b=own_booking(booking_id))


# ---------- Member 4: orders, notifications, profile ----------

@bp.route("/orders")
@login_required("customer")
def my_orders():
    tab = request.args.get("tab", "active")
    if tab == "past":
        rows = query(BOOKING_SQL + " WHERE b.customer_id=%s AND b.status IN ('Completed','Rejected') ORDER BY b.updated_at DESC",
                     [g.user["id"]])
    else:
        rows = query(BOOKING_SQL + " WHERE b.customer_id=%s AND b.status IN %s ORDER BY b.created_at DESC",
                     [g.user["id"], ACTIVE])
    return render_template("customer/my_orders.html", orders=rows, tab=tab)


@bp.route("/orders/<int:booking_id>")
@login_required("customer")
def order_details(booking_id):
    b = own_booking(booking_id)
    if b["status"] == "Rejected":
        others = query("""SELECT * FROM shops WHERE id<>%s AND offers_dropoff=1 ORDER BY name LIMIT 3""", [b["shop_id"]])
        return render_template("customer/booking_rejected.html", b=b, others=others)
    ready = "Ready for Delivery" if b["handling"] == "pickup-delivery" else "Ready for Pickup"
    steps = ["Pending", "Accepted", "Processing", ready, "Completed"]
    current = steps.index(b["status"]) if b["status"] in steps else 0
    return render_template("customer/order_details.html", b=b, price=booking_price(b), steps=steps, current=current)


@bp.route("/notifications")
@login_required("customer")
def notifications():
    rows = query("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC, id DESC LIMIT 50", [g.user["id"]])
    return render_template("customer/notifications.html", items=rows, now=datetime.now())


@bp.route("/notifications/read-all", methods=["POST"])
@login_required("customer")
def read_all():
    execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", [g.user["id"]])
    return redirect(url_for("customer.notifications"))


@bp.route("/notifications/<int:nid>")
@login_required("customer")
def open_notification(nid):
    n = query("SELECT * FROM notifications WHERE id=%s AND user_id=%s", [nid, g.user["id"]], one=True)
    if not n:
        abort(404)
    execute("UPDATE notifications SET is_read=1 WHERE id=%s", [nid])
    return redirect(url_for("customer.order_details", booking_id=n["booking_id"]) if n["booking_id"]
                    else url_for("customer.notifications"))


@bp.route("/profile")
@login_required("customer")
def profile():
    # TODO (Member 4): add pages to edit personal information and saved address
    return render_template("customer/profile.html")
