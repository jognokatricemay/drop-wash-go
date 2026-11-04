"""
crud.py — Full Create / Read / Update / Delete for the Laundry Booking System
Supports XAMPP MySQL, PostgreSQL, and SQLite transparently via db.py.

SECTIONS
  A. Connection helpers
  B. Shops       — add, get, list, update, deactivate
  C. Services    — add, get, list, update, deactivate
  D. Users       — add customer, add staff, get, find by mobile / username
  E. Bookings    — create, get, list (by customer / shop / status),
                   accept, reject, update weight, complete, cancel
  F. Notifications — add, list, mark read, mark all read
  G. Quick-demo  — run as a script to see everything in action
"""

import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from werkzeug.security import generate_password_hash
from db import IS_MYSQL, IS_POSTGRES, DATABASE_URL, get_engine_name

# ─────────────────────────────────────────────────────────────────────────────
# A. Connection helpers
# ─────────────────────────────────────────────────────────────────────────────

PH = "%s" if (IS_MYSQL or IS_POSTGRES) else "?"   # SQL placeholder


def _connect():
    """Return an open connection with dict-style row access on all engines."""
    if IS_MYSQL:
        from database_mysql import get_mysql_connection
        return get_mysql_connection(include_database=True)
    elif IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        import sqlite3
        from database import get_connection, DEFAULT_DB_PATH
        conn = get_connection(DEFAULT_DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn


from contextlib import contextmanager

@contextmanager
def _cursor(conn):
    """
    Unified cursor context manager.
    MySQL (PyMySQL) and PostgreSQL (psycopg3) support 'with conn.cursor()',
    but sqlite3.Cursor does NOT — so we wrap it ourselves.
    """
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()


def _row(row):
    """Normalise a DB row to a plain dict (works for PyMySQL, psycopg3, sqlite3.Row)."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def _rows(rows):
    return [_row(r) for r in rows] if rows else []


def _next_booking_id(cur) -> int:
    """Return the next booking id (MAX + 1, minimum 488)."""
    cur.execute("SELECT COALESCE(MAX(id), 487) AS m FROM bookings")
    row = _row(cur.fetchone())
    # psycopg3 lower-cases the alias
    val = row.get("m") or row.get("coalesce") or 487
    return int(val) + 1


def _make_order_code(booking_id: int) -> str:
    return f"DWG-{booking_id:05d}"


def _bump_autoincrement(conn, cur, next_id: int):
    """Advance the auto-increment / sequence after a manual id insert."""
    if IS_MYSQL:
        cur.execute(f"ALTER TABLE bookings AUTO_INCREMENT = {next_id + 1}")
    elif IS_POSTGRES:
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('bookings','id'), {next_id})"
        )
    # SQLite: AUTOINCREMENT tracks MAX(id) automatically — nothing needed


# ─────────────────────────────────────────────────────────────────────────────
# B. Shops
# ─────────────────────────────────────────────────────────────────────────────

def add_shop(
    name: str,
    address: str,
    contact_number: str = None,
    owner_name: str = None,
    offers_dropoff: bool = True,
    offers_pickup: bool = False,
    offers_delivery: bool = False,
    delivery_fee: float = 0.0,
    accepts_cash: bool = True,
    accepts_gcash: bool = False,
    gcash_number: str = None,
    gcash_name: str = None,
) -> int:
    """Insert a new shop. Returns the new shop id."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"""INSERT INTO shops
                    (name, address, contact_number, owner_name,
                     offers_dropoff, offers_pickup, offers_delivery, delivery_fee,
                     accepts_cash, accepts_gcash, gcash_number, gcash_name)
                VALUES ({','.join([PH]*12)})""",
                (name, address, contact_number, owner_name,
                 int(offers_dropoff), int(offers_pickup), int(offers_delivery), delivery_fee,
                 int(accepts_cash), int(accepts_gcash), gcash_number, gcash_name),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def get_shop(shop_id: int) -> dict:
    """Fetch a single shop by id. Returns None if not found."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(f"SELECT * FROM shops WHERE id = {PH}", (shop_id,))
            return _row(cur.fetchone())
    finally:
        conn.close()


def list_shops(active_only: bool = True) -> list:
    """Return all shops, optionally filtered to active ones only."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            if active_only:
                cur.execute("SELECT * FROM shops WHERE is_active = 1 ORDER BY name")
            else:
                cur.execute("SELECT * FROM shops ORDER BY name")
            return _rows(cur.fetchall())
    finally:
        conn.close()


def update_shop(shop_id: int, **fields) -> bool:
    """
    Update any columns on a shop row.
    Example: update_shop(1, delivery_fee=75.0, accepts_gcash=True)
    Returns True if a row was actually changed.
    """
    allowed = {
        "name", "address", "contact_number", "owner_name",
        "offers_dropoff", "offers_pickup", "offers_delivery", "delivery_fee",
        "accepts_cash", "accepts_gcash", "gcash_number", "gcash_name",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{col} = {PH}" for col in updates)
    values = list(updates.values()) + [shop_id]
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE shops SET {set_clause} WHERE id = {PH}", values
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def deactivate_shop(shop_id: int) -> bool:
    """Soft-delete: sets is_active = 0. Returns True if the row existed."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE shops SET is_active = 0 WHERE id = {PH}", (shop_id,)
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# C. Services
# ─────────────────────────────────────────────────────────────────────────────

def add_service(shop_id: int, name: str, rate: float, unit: str = "kg") -> int:
    """Add a service to a shop. Returns the new service id."""
    if rate < 0:
        raise ValueError("rate must be >= 0")
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"INSERT INTO services (shop_id, name, rate, unit) VALUES ({','.join([PH]*4)})",
                (shop_id, name, rate, unit),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def get_service(service_id: int) -> dict:
    """Fetch a single service by id."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(f"SELECT * FROM services WHERE id = {PH}", (service_id,))
            return _row(cur.fetchone())
    finally:
        conn.close()


def list_services(shop_id: int, active_only: bool = True) -> list:
    """Return all services for a given shop."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            if active_only:
                cur.execute(
                    f"SELECT * FROM services WHERE shop_id = {PH} AND is_active = 1 ORDER BY name",
                    (shop_id,),
                )
            else:
                cur.execute(
                    f"SELECT * FROM services WHERE shop_id = {PH} ORDER BY name",
                    (shop_id,),
                )
            return _rows(cur.fetchall())
    finally:
        conn.close()


def update_service(service_id: int, **fields) -> bool:
    """
    Update name, rate, or unit on a service.
    Example: update_service(2, rate=45.0)
    """
    allowed = {"name", "rate", "unit"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "rate" in updates and updates["rate"] < 0:
        raise ValueError("rate must be >= 0")
    if not updates:
        return False
    set_clause = ", ".join(f"{col} = {PH}" for col in updates)
    values = list(updates.values()) + [service_id]
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE services SET {set_clause} WHERE id = {PH}", values
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def deactivate_service(service_id: int) -> bool:
    """Soft-delete a service (is_active = 0)."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE services SET is_active = 0 WHERE id = {PH}", (service_id,)
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# D. Users
# ─────────────────────────────────────────────────────────────────────────────

def add_customer(
    full_name: str,
    mobile: str,
    password: str,
    address: str = None,
    email: str = None,
) -> int:
    """Register a new customer. Returns the new user id."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"""INSERT INTO users (role, full_name, mobile, email, password_hash, address)
                    VALUES ({','.join([PH]*6)})""",
                ("customer", full_name, mobile, email,
                 generate_password_hash(password), address),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def add_staff(
    full_name: str,
    username: str,
    password: str,
    shop_id: int,
) -> int:
    """Register a new staff member linked to a shop. Returns the new user id."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"""INSERT INTO users (role, full_name, username, password_hash, shop_id)
                    VALUES ({','.join([PH]*5)})""",
                ("staff", full_name, username,
                 generate_password_hash(password), shop_id),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def get_user(user_id: int) -> dict:
    """Fetch a user by id (password_hash excluded from output)."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT id, role, full_name, mobile, email, username, address, shop_id, created_at "
                f"FROM users WHERE id = {PH}",
                (user_id,),
            )
            return _row(cur.fetchone())
    finally:
        conn.close()


def get_user_by_mobile(mobile: str) -> dict:
    """Find a customer by mobile number."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT id, role, full_name, mobile, email, address, shop_id "
                f"FROM users WHERE mobile = {PH}",
                (mobile,),
            )
            return _row(cur.fetchone())
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict:
    """Find a staff member by username."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT id, role, full_name, username, shop_id "
                f"FROM users WHERE username = {PH}",
                (username,),
            )
            return _row(cur.fetchone())
    finally:
        conn.close()


def update_user(user_id: int, **fields) -> bool:
    """
    Update profile fields for a user.
    Example: update_user(1, address='New St., Balete', email='new@email.com')
    Pass password='new_password' to update the hash automatically.
    """
    allowed = {"full_name", "mobile", "email", "address", "username"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    # Handle password separately
    if "password" in fields:
        updates["password_hash"] = generate_password_hash(fields["password"])
    if not updates:
        return False
    set_clause = ", ".join(f"{col} = {PH}" for col in updates)
    values = list(updates.values()) + [user_id]
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE users SET {set_clause} WHERE id = {PH}", values
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# E. Bookings
# ─────────────────────────────────────────────────────────────────────────────

def create_booking(
    customer_id: int,
    shop_id: int,
    service_name: str,
    rate: float,
    unit: str,
    handling: str,
    delivery_fee: float,
    est_weight: float,
    requested_date: str,       # "YYYY-MM-DD"
    requested_time: str,       # e.g. "9-11 AM"
    address: str = None,       # required for pickup-delivery
    notes: str = None,
) -> dict:
    """
    Create a new booking and its 'Pending' notification.
    Returns a dict with the new booking id and order_code.
    """
    if handling not in ("drop-off", "pickup-delivery", "pickup", "delivery"):
        raise ValueError(f"Invalid handling: {handling!r}")

    conn = _connect()
    try:
        with _cursor(conn) as cur:
            new_id = _next_booking_id(cur)
            order_code = _make_order_code(new_id)

            cur.execute(
                f"""INSERT INTO bookings
                    (id, order_code, customer_id, shop_id, service_name, rate, unit,
                     handling, delivery_fee, est_weight, requested_date, requested_time,
                     address, notes, status, payment_status)
                VALUES ({','.join([PH]*16)})""",
                (new_id, order_code, customer_id, shop_id, service_name, rate, unit,
                 handling, delivery_fee, est_weight, requested_date, requested_time,
                 address, notes, "Pending", "Unpaid"),
            )

            # Notify the customer
            cur.execute(
                f"""INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
                    VALUES ({','.join([PH]*6)})""",
                (customer_id, new_id, "info",
                 "Booking submitted",
                 f"#{order_code} · Waiting for shop confirmation", 0),
            )

            _bump_autoincrement(conn, cur, new_id)

        conn.commit()
        return {"id": new_id, "order_code": order_code}
    finally:
        conn.close()


def get_booking(booking_id: int) -> dict:
    """Fetch a single booking by id."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(f"SELECT * FROM bookings WHERE id = {PH}", (booking_id,))
            return _row(cur.fetchone())
    finally:
        conn.close()


def get_booking_by_code(order_code: str) -> dict:
    """Fetch a booking by its DWG-XXXXX order code."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT * FROM bookings WHERE order_code = {PH}", (order_code,)
            )
            return _row(cur.fetchone())
    finally:
        conn.close()


def list_bookings_by_customer(customer_id: int, status: str = None) -> list:
    """
    All bookings for a customer, newest first.
    Pass status='Pending' (etc.) to filter by status.
    """
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            if status:
                cur.execute(
                    f"SELECT * FROM bookings WHERE customer_id = {PH} AND status = {PH} "
                    f"ORDER BY requested_date DESC, id DESC",
                    (customer_id, status),
                )
            else:
                cur.execute(
                    f"SELECT * FROM bookings WHERE customer_id = {PH} "
                    f"ORDER BY requested_date DESC, id DESC",
                    (customer_id,),
                )
            return _rows(cur.fetchall())
    finally:
        conn.close()


def list_bookings_by_shop(shop_id: int, status: str = None) -> list:
    """
    All bookings for a shop, newest first.
    Pass status='Pending' to filter — useful for a staff dashboard.
    """
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            if status:
                cur.execute(
                    f"SELECT * FROM bookings WHERE shop_id = {PH} AND status = {PH} "
                    f"ORDER BY requested_date ASC, id ASC",
                    (shop_id, status),
                )
            else:
                cur.execute(
                    f"SELECT * FROM bookings WHERE shop_id = {PH} "
                    f"ORDER BY requested_date ASC, id ASC",
                    (shop_id,),
                )
            return _rows(cur.fetchall())
    finally:
        conn.close()


def accept_booking(
    booking_id: int,
    confirmed_schedule: str,
    delivery_schedule: str = None,
) -> bool:
    """
    Staff accepts a pending booking.
    confirmed_schedule: e.g. "9-11 AM"
    delivery_schedule:  e.g. "3-6 PM" (only for pickup-delivery)
    Also sends an acceptance notification to the customer.
    Returns True if the booking was updated.
    """
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT customer_id, order_code, handling FROM bookings WHERE id = {PH}",
                (booking_id,),
            )
            row = _row(cur.fetchone())
            if not row:
                return False

            cur.execute(
                f"""UPDATE bookings
                    SET status = {PH}, confirmed_schedule = {PH}, delivery_schedule = {PH}
                    WHERE id = {PH}""",
                ("Accepted", confirmed_schedule, delivery_schedule, booking_id),
            )

            cur.execute(
                f"""INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
                    VALUES ({','.join([PH]*6)})""",
                (row["customer_id"], booking_id, "success",
                 "Booking accepted",
                 f"#{row['order_code']} · Pickup confirmed, {confirmed_schedule}", 0),
            )

        conn.commit()
        return True
    finally:
        conn.close()


def reject_booking(booking_id: int, reason: str) -> bool:
    """
    Staff rejects a pending booking with a reason.
    Sends a rejection notification to the customer.
    """
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT customer_id, order_code, shop_id FROM bookings WHERE id = {PH}",
                (booking_id,),
            )
            row = _row(cur.fetchone())
            if not row:
                return False

            # Fetch shop name for the notification body
            cur.execute(f"SELECT name FROM shops WHERE id = {PH}", (row["shop_id"],))
            shop = _row(cur.fetchone())
            shop_name = shop["name"] if shop else "Shop"

            cur.execute(
                f"UPDATE bookings SET status = {PH}, reject_reason = {PH} WHERE id = {PH}",
                ("Rejected", reason, booking_id),
            )

            cur.execute(
                f"""INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
                    VALUES ({','.join([PH]*6)})""",
                (row["customer_id"], booking_id, "error",
                 "Booking not accepted",
                 f"{shop_name} · {reason}", 0),
            )

        conn.commit()
        return True
    finally:
        conn.close()


def update_actual_weight(booking_id: int, actual_weight: float) -> bool:
    """
    Record the actual weight after the laundry is weighed.
    Moves the booking to 'Processing' status automatically.
    Also notifies the customer with the final total cost.
    """
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"SELECT customer_id, order_code, rate, delivery_fee FROM bookings WHERE id = {PH}",
                (booking_id,),
            )
            row = _row(cur.fetchone())
            if not row:
                return False

            total = float(row["rate"]) * actual_weight + float(row["delivery_fee"])

            cur.execute(
                f"UPDATE bookings SET actual_weight = {PH}, status = {PH} WHERE id = {PH}",
                (actual_weight, "Processing", booking_id),
            )

            cur.execute(
                f"""INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
                    VALUES ({','.join([PH]*6)})""",
                (row["customer_id"], booking_id, "info",
                 "Your laundry is being processed",
                 f"#{row['order_code']} · Final total ₱{total:.2f} ({actual_weight} kg)", 0),
            )

        conn.commit()
        return True
    finally:
        conn.close()


def mark_ready_for_delivery(booking_id: int) -> bool:
    """Mark an order as ready for delivery / pickup."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE bookings SET status = {PH} WHERE id = {PH}",
                ("Ready for Delivery", booking_id),
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def complete_booking(booking_id: int) -> bool:
    """Mark a booking as Completed."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE bookings SET status = {PH} WHERE id = {PH}",
                ("Completed", booking_id),
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def cancel_booking(booking_id: int) -> bool:
    """Customer cancels their own booking. Only works on Pending bookings."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE bookings SET status = {PH} "
                f"WHERE id = {PH} AND status = {PH}",
                ("Cancelled", booking_id, "Pending"),
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def mark_payment_paid(booking_id: int, method: str) -> bool:
    """
    Record a payment.
    method: 'cash' or 'gcash'
    """
    if method not in ("cash", "gcash"):
        raise ValueError("method must be 'cash' or 'gcash'")
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE bookings SET payment_status = {PH}, payment_method = {PH} WHERE id = {PH}",
                ("Paid", method, booking_id),
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# F. Notifications
# ─────────────────────────────────────────────────────────────────────────────

def add_notification(
    user_id: int,
    booking_id: int,
    kind: str,
    title: str,
    body: str,
) -> int:
    """Manually push a notification. Returns the new notification id."""
    if kind not in ("success", "info", "error", "warning"):
        raise ValueError(f"Invalid kind: {kind!r}")
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"""INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
                    VALUES ({','.join([PH]*6)})""",
                (user_id, booking_id, kind, title, body, 0),
            )
            new_id = cur.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()


def list_notifications(user_id: int, unread_only: bool = False) -> list:
    """Return notifications for a user, newest first."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            if unread_only:
                cur.execute(
                    f"SELECT * FROM notifications WHERE user_id = {PH} AND is_read = 0 "
                    f"ORDER BY created_at DESC",
                    (user_id,),
                )
            else:
                cur.execute(
                    f"SELECT * FROM notifications WHERE user_id = {PH} "
                    f"ORDER BY created_at DESC",
                    (user_id,),
                )
            return _rows(cur.fetchall())
    finally:
        conn.close()


def mark_notification_read(notification_id: int) -> bool:
    """Mark a single notification as read."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE notifications SET is_read = 1 WHERE id = {PH}",
                (notification_id,),
            )
            changed = cur.rowcount > 0
        conn.commit()
        return changed
    finally:
        conn.close()


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    conn = _connect()
    try:
        with _cursor(conn) as cur:
            cur.execute(
                f"UPDATE notifications SET is_read = 1 WHERE user_id = {PH} AND is_read = 0",
                (user_id,),
            )
            count = cur.rowcount
        conn.commit()
        return count
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# G. Quick demo (python crud.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback

    SEP = "─" * 55

    def show(label, value):
        print(f"  {label}: {value}")

    print("=" * 55)
    print(f"  CRUD DEMO — {get_engine_name()}")
    print("=" * 55)

    try:
        # ── 1. Add a new shop ───────────────────────────────────
        print(f"\n{SEP}\n[CREATE] Add a new shop\n{SEP}")
        shop_id = add_shop(
            name="Sparkle Wash",
            address="Brgy. Bagong Silang, Balete",
            contact_number="0920 111 2233",
            owner_name="Liza Gomez",
            offers_dropoff=True,
            offers_pickup=True,
            offers_delivery=True,
            delivery_fee=60.0,
            accepts_cash=True,
            accepts_gcash=True,
            gcash_number="0920 111 2233",
            gcash_name="Liza Gomez",
        )
        show("New shop id", shop_id)

        # ── 2. Add a service to that shop ───────────────────────
        print(f"\n{SEP}\n[CREATE] Add a service\n{SEP}")
        svc_id = add_service(shop_id, "Wash & Fold", rate=38.0, unit="kg")
        show("New service id", svc_id)

        # ── 3. Register a new customer ──────────────────────────
        print(f"\n{SEP}\n[CREATE] Register a customer\n{SEP}")
        cust_id = add_customer(
            full_name="Rina Valdez",
            mobile="09209998877",
            password="secret123",
            address="45 Maharlika St., Balete",
            email="rina@example.com",
        )
        show("New customer id", cust_id)

        # ── 4. Create a booking ─────────────────────────────────
        print(f"\n{SEP}\n[CREATE] Create a booking\n{SEP}")
        result = create_booking(
            customer_id=cust_id,
            shop_id=shop_id,
            service_name="Wash & Fold",
            rate=38.0,
            unit="kg",
            handling="pickup-delivery",
            delivery_fee=60.0,
            est_weight=4.0,
            requested_date=date.today().isoformat(),
            requested_time="10 AM - 12 PM",
            address="45 Maharlika St., Balete",
            notes="Please use unscented detergent.",
        )
        booking_id  = result["id"]
        order_code  = result["order_code"]
        show("New booking", f"#{order_code}  (id={booking_id})")

        # ── 5. Read back ────────────────────────────────────────
        print(f"\n{SEP}\n[READ] Fetch the booking\n{SEP}")
        b = get_booking(booking_id)
        show("Status",        b["status"])
        show("Customer id",   b["customer_id"])
        show("Service",       f"{b['service_name']}  ₱{float(b['rate']):.2f}/{b['unit']}")
        show("Handling",      b["handling"])

        print(f"\n{SEP}\n[READ] Customer's bookings\n{SEP}")
        all_b = list_bookings_by_customer(cust_id)
        show("Total bookings for Rina", len(all_b))

        print(f"\n{SEP}\n[READ] Unread notifications for Rina\n{SEP}")
        notifs = list_notifications(cust_id, unread_only=True)
        for n in notifs:
            show("  🔔", f"[{n['kind']}] {n['title']} — {n['body']}")

        # ── 6. Update ───────────────────────────────────────────
        print(f"\n{SEP}\n[UPDATE] Staff accepts the booking\n{SEP}")
        accepted = accept_booking(booking_id, confirmed_schedule="10 AM - 12 PM",
                                  delivery_schedule="4-6 PM")
        show("Accepted", accepted)
        show("New status", get_booking(booking_id)["status"])

        print(f"\n{SEP}\n[UPDATE] Record actual weight (3.5 kg)\n{SEP}")
        update_actual_weight(booking_id, 3.5)
        b = get_booking(booking_id)
        show("Status now",       b["status"])
        show("Actual weight",    b["actual_weight"])

        print(f"\n{SEP}\n[UPDATE] Mark payment as paid (gcash)\n{SEP}")
        mark_payment_paid(booking_id, "gcash")
        b = get_booking(booking_id)
        show("Payment status",  b["payment_status"])
        show("Payment method",  b["payment_method"])

        print(f"\n{SEP}\n[UPDATE] Mark all Rina's notifications as read\n{SEP}")
        n_updated = mark_all_notifications_read(cust_id)
        show("Notifications marked read", n_updated)

        # ── 7. Update shop details ──────────────────────────────
        print(f"\n{SEP}\n[UPDATE] Update shop delivery fee\n{SEP}")
        update_shop(shop_id, delivery_fee=70.0)
        show("New delivery fee", get_shop(shop_id)["delivery_fee"])

        # ── 8. Complete the booking ─────────────────────────────
        print(f"\n{SEP}\n[UPDATE] Complete the booking\n{SEP}")
        complete_booking(booking_id)
        show("Final status", get_booking(booking_id)["status"])

        # ── 9. Deactivate / soft-delete ─────────────────────────
        print(f"\n{SEP}\n[DELETE] Deactivate the demo service\n{SEP}")
        deactivate_service(svc_id)
        show("is_active after deactivate", get_service(svc_id)["is_active"])

        print(f"\n{SEP}\n[DELETE] Deactivate the demo shop\n{SEP}")
        deactivate_shop(shop_id)
        show("is_active after deactivate", get_shop(shop_id)["is_active"])

        print(f"\n{'=' * 55}")
        print("  ✓  All CRUD operations completed successfully.")
        print("=" * 55)

    except ConnectionError as ce:
        print(f"\n[-] CONNECTION ERROR: {ce}\n")
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
