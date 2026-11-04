"""
PostgreSQL Database Management Module (using psycopg 3)
Supports high-throughput, indefinite data growth on PostgreSQL (Supabase, Neon, AWS RDS, Docker, local).
"""

import os
import sys
import random
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DEFAULT_PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/booking_db"
)
SCHEMA_PG_PATH = "schema_postgres.sql"


def get_pg_connection(conn_str: str = DEFAULT_PG_URL) -> psycopg.Connection:
    """Creates a new PostgreSQL connection with dictionary row factory."""
    # Convert 'postgres://' to 'postgresql://' if coming from cloud providers like Heroku/Render
    if conn_str.startswith("postgres://"):
        conn_str = "postgresql://" + conn_str[len("postgres://"):]
    conn = psycopg.connect(conn_str, row_factory=dict_row)
    return conn


def init_pg_schema(conn_str: str = DEFAULT_PG_URL, schema_path: str = SCHEMA_PG_PATH) -> None:
    """Initializes tables, indexes, and trigger functions in PostgreSQL from schema_postgres.sql."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"PostgreSQL schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_pg_connection(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    print("[*] PostgreSQL schema initialized successfully!")


def clear_pg_tables(conn_str: str = DEFAULT_PG_URL) -> None:
    """
    Instantly wipes all 5 tables in PostgreSQL and resets identity counters back to 1
    using TRUNCATE ... RESTART IDENTITY CASCADE.
    """
    with get_pg_connection(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'TRUNCATE TABLE notifications, bookings, services, users, shops RESTART IDENTITY CASCADE;'
            )
        conn.commit()
    print("[+] All PostgreSQL tables cleared and primary key identity counters reset to 1!")


def get_pg_table_counts(conn_str: str = DEFAULT_PG_URL) -> dict:
    """Returns row counts across all 5 tables in PostgreSQL."""
    tables = ['shops', 'users', 'services', 'bookings', 'notifications']
    counts = {}
    with get_pg_connection(conn_str) as conn:
        with conn.cursor() as cur:
            for tbl in tables:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                counts[tbl] = cur.fetchone()["count"]
    return counts


def seed_pg_initial_data(conn_str: str = DEFAULT_PG_URL) -> None:
    """Seeds baseline realistic data into PostgreSQL."""
    print("[*] Seeding baseline starter records into PostgreSQL...")
    from seed import INITIAL_SHOPS, INITIAL_USERS, INITIAL_SERVICES, INITIAL_BOOKINGS, INITIAL_NOTIFICATIONS

    with get_pg_connection(conn_str) as conn:
        with conn.cursor() as cur:
            # 1. Shops (convert 1/0 to True/False for PostgreSQL boolean)
            pg_shops = [
                (s[0], s[1], s[2], s[3], s[4], s[5], s[6], bool(s[7])) for s in INITIAL_SHOPS
            ]
            cur.executemany(
                """
                INSERT INTO "Shops" (name, description, address, phone, email, opening_time, closing_time, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                pg_shops,
            )

            # 2. Users
            cur.executemany(
                """
                INSERT INTO "Users" (full_name, email, phone, role)
                VALUES (%s, %s, %s, %s);
                """,
                INITIAL_USERS,
            )

            # 3. Services
            pg_services = [
                (srv[0], srv[1], srv[2], srv[3], srv[4], bool(srv[5])) for srv in INITIAL_SERVICES
            ]
            cur.executemany(
                """
                INSERT INTO "Services" (shop_id, name, description, duration_minutes, price, is_active)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                pg_services,
            )

            # 4. Bookings
            cur.executemany(
                """
                INSERT INTO "Bookings" (user_id, shop_id, service_id, booking_time, status, total_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                INITIAL_BOOKINGS,
            )

            # 5. Notification
            pg_notifs = [
                (n[0], n[1], n[2], n[3], n[4], bool(n[5])) for n in INITIAL_NOTIFICATIONS
            ]
            cur.executemany(
                """
                INSERT INTO "Notification" (user_id, booking_id, title, message, type, is_read)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                pg_notifs,
            )
        conn.commit()
    print("[+] Baseline seeding for PostgreSQL complete!")


def seed_pg_indefinitely(total_to_add: int = 5000, chunk_size: int = 1000, conn_str: str = DEFAULT_PG_URL) -> None:
    """
    Generates and streams arbitrary amounts of relational records into PostgreSQL.
    Scales indefinitely to millions of rows with constant RAM footprint.
    """
    from seed import FIRST_NAMES, LAST_NAMES, SHOP_NOUNS, SHOP_ADJECTIVES, SERVICE_CATALOG, BOOKING_STATUSES, NOTIFICATION_TYPES

    print(f"[*] Ingesting {total_to_add:,} records per table into PostgreSQL in batches of {chunk_size:,}...")

    with get_pg_connection(conn_str) as conn:
        with conn.cursor() as cur:
            # Query existing IDs
            cur.execute('SELECT id FROM "Shops";')
            existing_shop_ids = [r["id"] for r in cur.fetchall()]

            cur.execute('SELECT id FROM "Users";')
            existing_user_ids = [r["id"] for r in cur.fetchall()]

            cur.execute('SELECT id, shop_id, price FROM "Services";')
            all_services = [(r["id"], r["shop_id"], float(r["price"])) for r in cur.fetchall()]

            remaining = total_to_add
            batch_num = 1
            total_added = 0

            while remaining > 0:
                current_chunk = min(remaining, chunk_size)
                start_time = datetime.now()
                salt = int(start_time.timestamp() * 1000)

                # 1. Shops
                new_shops = []
                for i in range(current_chunk):
                    adj = random.choice(SHOP_ADJECTIVES)
                    noun = random.choice(SHOP_NOUNS)
                    name = f"{adj} {noun} #{salt + i}"
                    desc = f"Professional {adj.lower()} services."
                    addr = f"{random.randint(100, 9999)} {random.choice(LAST_NAMES)} Street, Metro City"
                    phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                    email = f"info_{salt}_{i}@shop{random.randint(1000, 9999)}.com"
                    new_shops.append((name, desc, addr, phone, email, "09:00", "18:00", True))

                cur.executemany(
                    """
                    INSERT INTO "Shops" (name, description, address, phone, email, opening_time, closing_time, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    new_shops,
                )

                cur.execute('SELECT id FROM "Shops";')
                all_shop_ids = [r["id"] for r in cur.fetchall()]

                # 2. Users
                new_users = []
                for i in range(current_chunk):
                    first = random.choice(FIRST_NAMES)
                    last = random.choice(LAST_NAMES)
                    full_name = f"{first} {last}"
                    email = f"{first.lower()}.{last.lower()}_{salt}_{i}@example.com"
                    phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                    role = random.choice(["customer", "customer", "customer", "staff", "shop_owner"])
                    new_users.append((full_name, email, phone, role))

                cur.executemany(
                    """
                    INSERT INTO "Users" (full_name, email, phone, role)
                    VALUES (%s, %s, %s, %s);
                    """,
                    new_users,
                )

                cur.execute('SELECT id FROM "Users";')
                all_user_ids = [r["id"] for r in cur.fetchall()]

                # 3. Services
                new_services = []
                for i in range(current_chunk):
                    shop_id = random.choice(all_shop_ids)
                    srv_name, duration, price = random.choice(SERVICE_CATALOG)
                    srv_title = f"{srv_name} (Tier {random.randint(1, 5)})"
                    desc = f"Certified {srv_name.lower()}."
                    new_services.append((shop_id, srv_title, desc, duration, price, True))

                cur.executemany(
                    """
                    INSERT INTO "Services" (shop_id, name, description, duration_minutes, price, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    new_services,
                )

                cur.execute('SELECT id, shop_id, price FROM "Services";')
                all_services = [(r["id"], r["shop_id"], float(r["price"])) for r in cur.fetchall()]

                # 4. Bookings
                new_bookings = []
                for i in range(current_chunk):
                    srv_id, srv_shop_id, srv_price = random.choice(all_services)
                    usr_id = random.choice(all_user_ids)
                    b_time = (datetime.now() + timedelta(days=random.randint(-60, 60), hours=random.randint(8, 18))).strftime("%Y-%m-%d %H:%M:%S")
                    status = random.choice(BOOKING_STATUSES)
                    notes = f"Auto-generated PG booking #{i + 1}"
                    new_bookings.append((usr_id, srv_shop_id, srv_id, b_time, status, srv_price, notes))

                cur.executemany(
                    """
                    INSERT INTO "Bookings" (user_id, shop_id, service_id, booking_time, status, total_price, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    new_bookings,
                )

                # 5. Notifications
                cur.execute('SELECT id, user_id FROM "Bookings" ORDER BY id DESC LIMIT %s;', (current_chunk,))
                recent_bookings = [(r["id"], r["user_id"]) for r in cur.fetchall()]

                new_notifs = []
                for i in range(current_chunk):
                    b_id, u_id = random.choice(recent_bookings)
                    n_type = random.choice(NOTIFICATION_TYPES)
                    title = f"PG Alert: {n_type.replace('_', ' ').title()}"
                    msg = f"Notification update for booking #{b_id}."
                    new_notifs.append((u_id, b_id, title, msg, n_type, random.choice([True, False])))

                cur.executemany(
                    """
                    INSERT INTO "Notification" (user_id, booking_id, title, message, type, is_read)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    new_notifs,
                )

                conn.commit()

                duration = (datetime.now() - start_time).total_seconds()
                total_added += current_chunk
                remaining -= current_chunk
                print(f"  [+] Batch {batch_num}: Inserted {current_chunk:,} records across all 5 tables in {duration:.2f}s | Total: {total_added:,}/{total_to_add:,}")
                batch_num += 1

    print(f"[+] PostgreSQL ingestion complete! Added {total_added:,} records to each table.")


if __name__ == "__main__":
    conn_url = os.environ.get("DATABASE_URL")
    if not conn_url:
        print("[-] Notice: No DATABASE_URL environment variable provided.")
        print("    Example: set DATABASE_URL=postgresql://user:password@localhost:5432/booking_db")
        print("    Or pass connection URL to test against Supabase, Neon, or local Postgres.")
        sys.exit(0)

    if "--init" in sys.argv:
        init_pg_schema(conn_url)
        seed_pg_initial_data(conn_url)

    if "--clear" in sys.argv:
        clear_pg_tables(conn_url)

    if "--add" in sys.argv:
        idx = sys.argv.index("--add")
        count = int(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 1000
        seed_pg_indefinitely(total_to_add=count, chunk_size=min(count, 1000), conn_str=conn_url)

    counts = get_pg_table_counts(conn_url)
    print("\nCURRENT POSTGRESQL ROW COUNTS:")
    for tbl, count in counts.items():
        print(f"  {tbl:<15}: {count:>8,} rows")
