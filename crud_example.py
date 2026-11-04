"""
CRUD & Relational Query Demonstrations for Laundry System
Supports XAMPP MySQL, PostgreSQL, and SQLite.
Demonstrates adding a new shop, customer, service, and booking with order codes.
"""

import sys
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from db import IS_MYSQL, IS_POSTGRES, get_engine_name, DATABASE_URL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_conn():
    if IS_MYSQL:
        from database_mysql import get_mysql_connection
        return get_mysql_connection(include_database=True)
    elif IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        from database import get_connection
        return get_connection()


def add_laundry_order():
    conn = get_conn()
    cur = conn.cursor()

    try:
        # 1. Fetch Juan Dela Cruz (user #1) and Mama Fe Laundry (shop #1)
        cur.execute("SELECT id, full_name, address FROM users WHERE id = 1;")
        user = cur.fetchone()

        cur.execute("SELECT id, name, delivery_fee FROM shops WHERE id = 1;")
        shop = cur.fetchone()

        cur.execute("SELECT id, name, rate, unit FROM services WHERE shop_id = 1 LIMIT 1;")
        service = cur.fetchone()

        cur.execute("SELECT COALESCE(MAX(id), 487) AS max_id FROM bookings;")
        max_id_row = cur.fetchone()
        if IS_MYSQL:
            next_id = max_id_row["max_id"] + 1
        elif IS_POSTGRES:
            next_id = (max_id_row[0] if isinstance(max_id_row, tuple) else max_id_row["coalesce"]) + 1
        else:
            next_id = max_id_row[0] + 1

        order_code = f"DWG-{next_id:05d}"

        # 2. Insert new booking
        req_date = date.today().isoformat()
        placeholder = "%s" if (IS_MYSQL or IS_POSTGRES) else "?"
        cur.execute(
            f"""
            INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
                                   delivery_fee, est_weight, requested_date, requested_time, confirmed_schedule,
                                   address, notes, status, payment_status)
            VALUES ({','.join([placeholder]*17)})
            """,
            (
                next_id, order_code, user["id"], shop["id"], service["name"], service["rate"], service["unit"],
                "pickup-delivery", shop["delivery_fee"], 5.0, req_date, "1-3 PM", "1-3 PM",
                user["address"], "Express wash needed", "Accepted", "Unpaid"
            ),
        )

        # 3. Insert notification
        cur.execute(
            f"""
            INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read)
            VALUES ({','.join([placeholder]*6)})
            """,
            (
                user["id"], next_id, "success", "New Order Confirmed",
                f"#{order_code} · Scheduled for pickup today, 1-3 PM", 0 if (IS_MYSQL or not IS_POSTGRES) else False
            ),
        )

        if IS_MYSQL:
            cur.execute(f"ALTER TABLE bookings AUTO_INCREMENT = {next_id + 1};")
        elif IS_POSTGRES:
            cur.execute(f"SELECT setval(pg_get_serial_sequence('bookings', 'id'), {next_id});")

        conn.commit()

        print(f"[+] Successfully created Booking #{order_code} for {user['full_name']} at {shop['name']}!")
        print(f"    Service: {service['name']} (₱{float(service['rate']):.2f}/{service['unit']})")
        print(f"    Handling: pickup-delivery | Delivery Fee: ₱{float(shop['delivery_fee']):.2f}")

    finally:
        conn.close()


if __name__ == "__main__":
    print(f"[*] Running CRUD Demo on {get_engine_name()}...")
    try:
        add_laundry_order()
    except ConnectionError as e:
        print(f"\n[-] CONNECTION ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] ERROR: {e}\n")
        sys.exit(1)
