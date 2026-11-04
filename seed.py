"""
Seed Script for Laundry Booking System (Figma Design)
Features:
1. Exact Figma seed data (Mama Fe Laundry, Clean & Fresh, Wash Hub, Juan Dela Cruz, order codes DWG-00483).
2. Demo user accounts with password 'password123' hashed using werkzeug.security.
3. Proper sequence synchronization for PostgreSQL and SQLite (booking IDs 488+).
4. High-performance indefinite data generator for adding unlimited laundry orders.
"""

import sys
import os
import random
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

PASSWORD = "password123"

# -----------------------------------------------------------------------------
# Figma Baseline Seed Data
# -----------------------------------------------------------------------------

def get_figma_seed_data():
    pw = generate_password_hash(PASSWORD)
    today = date.today()
    d = lambda days: (today + timedelta(days=days)).isoformat()

    shops = [
        # name, address, contact, owner, dropoff, pickup, delivery, fee, cash, gcash, gcash no, gcash name
        ("Mama Fe Laundry", "Mabini St., Balete", "0917 123 4567", "Fe Reyes", 1, 1, 1, 50.0, 1, 1, "0917 123 4567", "Fe Reyes"),
        ("Clean & Fresh", "Poblacion, Balete", "0918 555 0101", "Ana Cruz", 1, 1, 0, 0.0, 1, 1, "0918 555 0101", "Ana Cruz"),
        ("Wash Hub", "Brgy. San Juan, Balete", "0919 777 0202", "Ben Lim", 1, 0, 0, 0.0, 1, 0, None, None),
    ]

    services = []
    for shop_id in (1, 2, 3):
        services += [
            (shop_id, "Wash & Fold", 35.0, "kg"),
            (shop_id, "Wash, Dry & Fold", 50.0, "kg"),
            (shop_id, "Comforter / Bedsheet", 150.0, "piece"),
        ]

    users = [
        (1, "customer", "Juan Dela Cruz", "09171234567", "juan@gmail.com", None, pw, "123 Mabini St., Balete", None),
        (2, "customer", "Maria Santos", "09181112222", "maria@gmail.com", None, pw, "45 Rizal St., Balete", None),
        (3, "customer", "Pedro Reyes", "09183334444", None, None, pw, "Poblacion, Balete", None),
        (4, "customer", "Carlo Mendoza", "09185556666", None, None, pw, "Brgy. San Juan, Balete", None),
        (10, "staff", "Fe Reyes", None, None, "fe.reyes", pw, None, 1),
        (11, "staff", "Ana Cruz", None, None, "cf.staff", pw, None, 2),
        (12, "staff", "Ben Lim", None, None, "washhub", pw, None, 3),
    ]

    bookings = [
        (478, "DWG-00478", 4, 1, "Wash & Fold", 35.0, "kg", "drop-off", 0.0, 6.0, 6.0, d(-6), "9-11 AM", "9-11 AM", None, None, None, "Completed", None, "Paid", "cash"),
        (480, "DWG-00480", 3, 1, "Wash & Fold", 35.0, "kg", "drop-off", 0.0, 7.0, 7.0, d(-1), "8-10 AM", "8-10 AM", None, None, None, "Processing", None, "Unpaid", None),
        (481, "DWG-00481", 1, 2, "Wash & Fold", 35.0, "kg", "drop-off", 0.0, 7.0, 7.0, d(-1), "1-3 PM", "1-3 PM", None, None, None, "Processing", None, "Unpaid", None),
        (482, "DWG-00482", 2, 1, "Wash & Fold", 35.0, "kg", "pickup-delivery", 50.0, 3.0, 3.5, d(-2), "1-3 PM", "1-3 PM", "3-6 PM", "45 Rizal St., Balete", None, "Ready for Delivery", None, "Unpaid", None),
        (483, "DWG-00483", 1, 1, "Wash & Fold", 35.0, "kg", "pickup-delivery", 50.0, 3.0, None, d(0), "9-11 AM", "9-11 AM", None, "123 Mabini St., Balete", "Separate whites, no fabric softener", "Accepted", None, "Unpaid", None),
        (484, None, 1, 3, "Wash & Fold", 35.0, "kg", "drop-off", 0.0, 3.0, None, d(-3), "9-11 AM", None, None, None, None, "Rejected", "Fully booked on that day.", "Unpaid", None),
        (485, None, 1, 2, "Wash & Fold", 35.0, "kg", "drop-off", 0.0, 3.0, None, d(1), "9-11 AM", None, None, None, None, "Pending", None, "Unpaid", None),
        (486, None, 2, 1, "Wash & Fold", 35.0, "kg", "pickup-delivery", 50.0, 3.0, None, d(1), "1-3 PM", None, None, "45 Rizal St., Balete", None, "Pending", None, "Unpaid", None),
        (487, None, 3, 1, "Wash, Dry & Fold", 50.0, "kg", "drop-off", 0.0, 7.0, None, d(2), "8-10 AM", None, None, None, "Hang dry the polo shirts", "Pending", None, "Unpaid", None),
    ]

    notifications = [
        (1, 483, "success", "Booking accepted", "#DWG-00483 · Pickup confirmed, 9-11 AM", 1),
        (1, 481, "info", "Your laundry is being processed", "#DWG-00481 · Final total ₱245.00 (7 kg)", 1),
        (1, 484, "error", "Booking not accepted", "Wash Hub · Fully booked on that day.", 0),
    ]

    return shops, services, users, bookings, notifications


def seed_figma_data():
    """Seeds the exact Figma design dataset with cross-engine sequence compatibility."""
    from db import IS_MYSQL, IS_POSTGRES, DATABASE_URL

    shops, services, users, bookings, notifications = get_figma_seed_data()

    if IS_MYSQL:
        from database_mysql import get_mysql_connection
        conn = get_mysql_connection(include_database=True)
        try:
            with conn.cursor() as cur:
                # 1. Shops
                cur.executemany(
                    """
                    INSERT INTO shops (name, address, contact_number, owner_name, offers_dropoff, offers_pickup,
                                       offers_delivery, delivery_fee, accepts_cash, accepts_gcash, gcash_number, gcash_name)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    shops,
                )

                # 2. Services
                cur.executemany(
                    "INSERT INTO services (shop_id, name, rate, unit) VALUES (%s,%s,%s,%s)",
                    services,
                )

                # 3. Users (explicit IDs)
                cur.executemany(
                    """
                    INSERT INTO users (id, role, full_name, mobile, email, username, password_hash, address, shop_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    users,
                )

                # 4. Bookings (explicit IDs)
                cur.executemany(
                    """
                    INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
                                           delivery_fee, est_weight, actual_weight, requested_date, requested_time,
                                           confirmed_schedule, delivery_schedule, address, notes, status, reject_reason,
                                           payment_status, payment_method)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    bookings,
                )

                # 5. Native MySQL syntax for next booking ID
                cur.execute("ALTER TABLE bookings AUTO_INCREMENT = 488;")
                cur.execute("ALTER TABLE users AUTO_INCREMENT = 13;")
                cur.execute("ALTER TABLE shops AUTO_INCREMENT = 4;")

                # 6. Notifications
                cur.executemany(
                    "INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES (%s,%s,%s,%s,%s,%s)",
                    notifications,
                )
            conn.commit()
        finally:
            conn.close()

    elif IS_POSTGRES:
        import psycopg
        clean_url = DATABASE_URL
        if clean_url.startswith("postgres://"):
            clean_url = "postgresql://" + clean_url[len("postgres://"):]

        with psycopg.connect(clean_url) as conn:
            with conn.cursor() as cur:
                # 1. Shops (convert 1/0 to booleans for PG)
                pg_shops = [
                    (s[0], s[1], s[2], s[3], bool(s[4]), bool(s[5]), bool(s[6]), s[7], bool(s[8]), bool(s[9]), s[10], s[11])
                    for s in shops
                ]
                cur.executemany(
                    """
                    INSERT INTO shops (name, address, contact_number, owner_name, offers_dropoff, offers_pickup,
                                       offers_delivery, delivery_fee, accepts_cash, accepts_gcash, gcash_number, gcash_name)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    pg_shops,
                )

                # 2. Services
                cur.executemany(
                    "INSERT INTO services (shop_id, name, rate, unit) VALUES (%s,%s,%s,%s)",
                    services,
                )

                # 3. Users (explicit IDs)
                cur.executemany(
                    """
                    INSERT INTO users (id, role, full_name, mobile, email, username, password_hash, address, shop_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    users,
                )

                # 4. Bookings (explicit IDs)
                cur.executemany(
                    """
                    INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
                                           delivery_fee, est_weight, actual_weight, requested_date, requested_time,
                                           confirmed_schedule, delivery_schedule, address, notes, status, reject_reason,
                                           payment_status, payment_method)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    bookings,
                )

                # 5. Notifications
                pg_notifs = [(n[0], n[1], n[2], n[3], n[4], bool(n[5])) for n in notifications]
                cur.executemany(
                    "INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES (%s,%s,%s,%s,%s,%s)",
                    pg_notifs,
                )

                # FIX FOR MYSQL 'AUTO_INCREMENT = 488' SYNTAX IN POSTGRESQL:
                # In PostgreSQL, sync the identity sequence so new bookings start at ID 488!
                cur.execute("SELECT setval(pg_get_serial_sequence('bookings', 'id'), 487);")
                cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), 12);")
                cur.execute("SELECT setval(pg_get_serial_sequence('shops', 'id'), 3);")

            conn.commit()
    else:
        from database import get_db
        with get_db() as conn:
            cur = conn.cursor()

            cur.executemany(
                """
                INSERT INTO shops (name, address, contact_number, owner_name, offers_dropoff, offers_pickup,
                                   offers_delivery, delivery_fee, accepts_cash, accepts_gcash, gcash_number, gcash_name)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                shops,
            )

            cur.executemany(
                "INSERT INTO services (shop_id, name, rate, unit) VALUES (?,?,?,?)",
                services,
            )

            cur.executemany(
                """
                INSERT INTO users (id, role, full_name, mobile, email, username, password_hash, address, shop_id)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                users,
            )

            cur.executemany(
                """
                INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
                                       delivery_fee, est_weight, actual_weight, requested_date, requested_time,
                                       confirmed_schedule, delivery_schedule, address, notes, status, reject_reason,
                                       payment_status, payment_method)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                bookings,
            )

            cur.executemany(
                "INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES (?,?,?,?,?,?)",
                notifications,
            )

            # SQLite sequence sync
            cur.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('bookings', 487), ('users', 12), ('shops', 3);")

    print("[+] Successfully seeded Figma demo data (Mama Fe Laundry, Juan Dela Cruz, #DWG-00483)!")


# -----------------------------------------------------------------------------
# Indefinite Data Generator (Laundry Domain)
# -----------------------------------------------------------------------------

PH_FIRST_NAMES = ["Juan", "Maria", "Pedro", "Carlo", "Jose", "Angelica", "Mark", "Maricel", "Francis", "Diane", "Paolo", "Kristine"]
PH_LAST_NAMES = ["Dela Cruz", "Santos", "Reyes", "Mendoza", "Bautista", "Garcia", "Lim", "Ramos", "Aquino", "Villanueva"]
BARANGAYS = ["Poblacion", "Brgy. San Juan", "Mabini St.", "Rizal St.", "Brgy. Malabanan", "Brgy. San Sebastian", "Burgos St."]
LAUNDRY_SERVICES = [
    ("Wash & Fold", 35.0, "kg"),
    ("Wash, Dry & Fold", 50.0, "kg"),
    ("Comforter / Bedsheet", 150.0, "piece"),
    ("Dry Clean", 120.0, "piece"),
    ("Press Only", 25.0, "piece"),
]
HANDLING_OPTIONS = ["drop-off", "pickup-delivery"]
STATUSES = ["Pending", "Accepted", "Processing", "Ready for Delivery", "Completed"]
PAY_METHODS = ["cash", "gcash"]


def seed_indefinitely(total_to_add: int = 1000, chunk_size: int = 500):
    """Adds unlimited realistic laundry bookings indefinitely."""
    from db import IS_MYSQL, IS_POSTGRES, DATABASE_URL

    print(f"[*] Ingesting {total_to_add:,} additional laundry bookings indefinitely...")
    pw = generate_password_hash(PASSWORD)
    today = date.today()

    if IS_MYSQL:
        from database_mysql import get_mysql_connection
        conn = get_mysql_connection(include_database=True)
    elif IS_POSTGRES:
        import psycopg
        clean_url = DATABASE_URL
        if clean_url.startswith("postgres://"):
            clean_url = "postgresql://" + clean_url[len("postgres://"):]
        conn = psycopg.connect(clean_url)
    else:
        from database import get_connection
        conn = get_connection()

    try:
        cur = conn.cursor()
        remaining = total_to_add
        batch_num = 1
        total_added = 0

        while remaining > 0:
            current_chunk = min(remaining, chunk_size)

            # Fetch active customers and shops
            if IS_MYSQL:
                cur.execute("SELECT id FROM users WHERE role = 'customer';")
                customer_ids = [r["id"] for r in cur.fetchall()]
                cur.execute("SELECT id FROM shops;")
                shop_ids = [r["id"] for r in cur.fetchall()]
                cur.execute("SELECT COALESCE(MAX(id), 487) AS max_id FROM bookings;")
                max_id = cur.fetchone()["max_id"]
            elif IS_POSTGRES:
                cur.execute("SELECT id FROM users WHERE role = 'customer';")
                customer_ids = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT id FROM shops;")
                shop_ids = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT COALESCE(MAX(id), 487) FROM bookings;")
                max_id = cur.fetchone()[0]
            else:
                cur.execute("SELECT id FROM users WHERE role = 'customer';")
                customer_ids = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT id FROM shops;")
                shop_ids = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT COALESCE(MAX(id), 487) FROM bookings;")
                max_id = cur.fetchone()[0]

            new_bookings = []
            new_notifs = []
            for i in range(current_chunk):
                b_id = max_id + i + 1
                code = f"DWG-{b_id:05d}"
                cust_id = random.choice(customer_ids)
                s_id = random.choice(shop_ids)
                s_name, rate, unit = random.choice(LAUNDRY_SERVICES)
                handling = random.choice(HANDLING_OPTIONS)
                fee = 50.0 if handling == "pickup-delivery" else 0.0
                est = round(random.uniform(3.0, 9.0), 1)
                actual = est if random.choice([True, False]) else None
                req_date = (today + timedelta(days=random.randint(-10, 10))).isoformat()
                req_time = random.choice(["8-10 AM", "9-11 AM", "1-3 PM", "3-5 PM"])
                status = random.choice(STATUSES)
                addr = f"{random.randint(10, 999)} {random.choice(BARANGAYS)}, Balete"
                pay_status = "Paid" if status == "Completed" else random.choice(["Unpaid", "Paid"])
                pay_method = random.choice(PAY_METHODS) if pay_status == "Paid" else None

                new_bookings.append((
                    b_id, code, cust_id, s_id, s_name, rate, unit, handling, fee, est, actual,
                    req_date, req_time, req_time, None, addr, "Handle with care", status, None, pay_status, pay_method
                ))

                new_notifs.append((
                    cust_id, b_id, "info" if status == "Processing" else "success",
                    f"Booking {status}", f"#{code} · Status: {status}", 0 if (IS_MYSQL or not IS_POSTGRES) else False
                ))

            placeholder = "%s" if (IS_MYSQL or IS_POSTGRES) else "?"
            cur.executemany(
                f"""
                INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
                                       delivery_fee, est_weight, actual_weight, requested_date, requested_time,
                                       confirmed_schedule, delivery_schedule, address, notes, status, reject_reason,
                                       payment_status, payment_method)
                VALUES ({','.join([placeholder]*21)})
                """,
                new_bookings,
            )

            cur.executemany(
                f"INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES ({','.join([placeholder]*6)})",
                new_notifs,
            )

            if IS_MYSQL:
                cur.execute(f"ALTER TABLE bookings AUTO_INCREMENT = {max_id + current_chunk + 1};")
            elif IS_POSTGRES:
                cur.execute(f"SELECT setval(pg_get_serial_sequence('bookings', 'id'), {max_id + current_chunk});")

            conn.commit()
            total_added += current_chunk
            remaining -= current_chunk
            print(f"  [+] Batch {batch_num}: Inserted {current_chunk:,} laundry bookings | Progress: {total_added:,}/{total_to_add:,}")
            batch_num += 1

    finally:
        conn.close()

    print(f"[+] Successfully added {total_added:,} bookings!")


if __name__ == "__main__":
    from db import IS_MYSQL, IS_POSTGRES, get_engine_name, get_counts, init_database

    engine = get_engine_name()
    print(f"[*] Target Database Engine: {engine}")

    try:
        if "--init" in sys.argv:
            # Re-initialize schema to match Figma design
            if IS_MYSQL:
                import database_mysql
                database_mysql.init_mysql_schema()
                database_mysql.clear_mysql_tables()
            elif IS_POSTGRES:
                import database_pg
                database_pg.init_pg_schema()
                database_pg.clear_pg_tables()
            else:
                import database
                database.init_db()
                database.clear_db()

            seed_figma_data()

        if "--add" in sys.argv:
            idx = sys.argv.index("--add")
            count = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 1000
            seed_indefinitely(total_to_add=count)

        print("\n" + "=" * 50)
        print(f"CURRENT {engine.upper()} ROW COUNTS:")
        print("=" * 50)
        counts = get_counts()
        for table_name, count in counts.items():
            print(f"  {table_name:<15}: {count:>10,} rows")
        print("=" * 50)

    except ConnectionError as e:
        print(f"\n[-] CONNECTION ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
