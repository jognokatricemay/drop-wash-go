"""Shared helpers: who is logged in, role checks, prices and template filters."""
import re
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from .db import execute, query

HANDLING = {"drop-off": "Drop-off", "pickup": "Pickup", "pickup-delivery": "Pickup & Delivery"}

PILL = {"Pending": "pending", "Accepted": "accepted", "Processing": "processing",
        "Ready for Pickup": "ready", "Ready for Delivery": "ready", "Completed": "completed",
        "Rejected": "rejected","Cancelled":"cancelled", "Unpaid": "unpaid", "Paid": "paid"}

# A booking with its shop and customer details. Add WHERE / ORDER BY after it.
BOOKING_SQL = """
SELECT b.*, s.name AS shop_name, s.address AS shop_address, s.gcash_number, s.gcash_name,
       s.accepts_cash, s.accepts_gcash, u.full_name AS customer_name, u.mobile AS customer_mobile
FROM bookings b
JOIN shops s ON s.id = b.shop_id
JOIN users u ON u.id = b.customer_id
"""


def payment_methods(shop):
    methods = [m for m, ok in (("Cash", shop["accepts_cash"]), ("GCash", shop["accepts_gcash"])) if ok]
    return " · ".join(methods) or "Ask the shop"


# ---------- Login ----------

def load_user():
    """Runs before every request: puts the logged-in user (or None) in g.user."""
    uid = session.get("user_id")
    g.user = query("SELECT * FROM users WHERE id=%s", [uid], one=True) if uid else None
    g.shop = None
    if g.user and g.user["role"] == "staff":
        g.shop = query("SELECT * FROM shops WHERE id=%s", [g.user["shop_id"]], one=True)


def login_required(role):
    """@login_required("customer") or @login_required("staff") on a route (NFR-03)."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None or g.user["role"] != role:
                if role == "staff":
                    return redirect(url_for("auth.staff_login"))
                return redirect(url_for("auth.login", next=request.full_path))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ---------- Prices ----------

def booking_price(b):
    """Laundry price, delivery fee and total. Uses the actual weight once the shop weighs it."""
    weight = b["actual_weight"] if b["actual_weight"] is not None else b["est_weight"]
    laundry = Decimal(b["rate"]) * Decimal(weight)
    fee = Decimal(b["delivery_fee"]) if b["handling"] == "pickup-delivery" else Decimal(0)
    return {"weight": weight, "laundry": laundry, "fee": fee, "total": laundry + fee,
            "estimated": b["actual_weight"] is None}


def order_label(b):
    return "#" + b["order_code"] if b["order_code"] else "Booking request"


def notify(user_id, booking_id, kind, title, body):
    execute("INSERT INTO notifications (user_id, booking_id, kind, title, body) VALUES (%s,%s,%s,%s,%s)",
            [user_id, booking_id, kind, title, body])


# ---------- Template filters ----------

def peso(value, decimals=None):
    value = Decimal(value or 0)
    if decimals is None:
        decimals = 0 if value == value.to_integral() else 2
    return f"₱{value:,.{decimals}f}"


def kg(value):
    value = Decimal(value or 0)
    return f"{value.normalize():f}"


def short_date(d):
    return f"{d:%b} {d.day}" if d else ""


def time_input_value(value):
    """Return a value supported by an HTML time input, including legacy time ranges."""
    value = str(value or "").strip()
    if re.fullmatch(r"\d{2}:\d{2}", value):
        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            return ""

    match = re.fullmatch(
        r"(\d{1,2})(?::(\d{2}))?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM)",
        value,
        re.IGNORECASE,
    )
    if not match:
        return ""
    start_hour = int(match.group(1))
    start_minute = int(match.group(2) or 0)
    end_hour = int(match.group(3))
    end_minute = int(match.group(4) or 0)
    meridiem = match.group(5).upper()
    if not 1 <= start_hour <= 12 or not 1 <= end_hour <= 12 or start_minute > 59 or end_minute > 59:
        return ""

    start_hour %= 12
    end_hour %= 12
    if meridiem == "PM":
        start_hour += 12
        end_hour += 12
    if start_hour > end_hour:
        start_hour += -12 if meridiem == "PM" else 12
    return f"{start_hour:02d}:{start_minute:02d}"


def time_label(value):
    """Format stored HH:MM values for display while preserving legacy range labels."""
    value = str(value or "").strip()
    if not re.fullmatch(r"\d{2}:\d{2}", value):
        return value
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError:
        return value
    hour = parsed.hour % 12 or 12
    meridiem = "AM" if parsed.hour < 12 else "PM"
    return f"{hour}:{parsed.minute:02d} {meridiem}"


def schedule_label(value):
    """Format new ISO delivery schedules while leaving older free-text schedules readable."""
    value = str(value or "").strip()
    try:
        scheduled = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return value
    return f"{short_date(scheduled.date())} · {time_label(scheduled.strftime('%H:%M'))}"


def init_app(app):
    app.before_request(load_user)
    app.jinja_env.filters.update(peso=peso, kg=kg, short_date=short_date,
                                 time_label=time_label, time_input=time_input_value,
                                 schedule_label=schedule_label,
                                 pill=lambda s: PILL.get(s, "completed"),
                                 handling=lambda h: HANDLING.get(h, h))
    app.jinja_env.globals.update(order_label=order_label, booking_price=booking_price,
                                 payment_methods=payment_methods,
                                 now_label=lambda: f"{date.today():%A, %B} {date.today().day}")

    @app.context_processor
    def unread_count():
        if g.get("user") and g.user["role"] == "customer":
            row = query("SELECT COUNT(*) AS n FROM notifications WHERE user_id=%s AND is_read=0",
                        [g.user["id"]], one=True)
            return {"unread": row["n"]}
        return {"unread": 0}

    @app.errorhandler(404)
    def not_found(_e):
        flash("That page doesn't exist.")
        return redirect(url_for("auth.welcome"))
