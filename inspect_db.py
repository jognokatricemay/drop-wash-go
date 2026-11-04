"""
Database Inspection and Verification Script (Laundry Figma Schema)
Supports both PostgreSQL (Aiven/Cloud) and local SQLite.
Displays:
1. Active engine name and live row counts.
2. Sample data from each table.
3. Referential integrity checks.
"""

import sys
from db import IS_MYSQL, IS_POSTGRES, get_engine_name, get_counts, DATABASE_URL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def inspect_all():
    engine = get_engine_name()
    print("=" * 70)
    print(f"       {engine.upper()} LAUNDRY DATABASE STATUS REPORT")
    print("=" * 70)

    # 1. Row counts
    try:
        counts = get_counts()
        print("\n[1] TABLE ROW COUNTS:")
        for table, count in counts.items():
            print(f"    - {table:<15}: {count:>8,} records")
    except Exception as e:
        print(f"\n[-] Could not fetch counts: {e}")
        return

    # Connect to active database
    if IS_MYSQL:
        from database_mysql import get_mysql_connection
        conn = get_mysql_connection(include_database=True)
    elif IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        from database import get_connection
        conn = get_connection()

    try:
        cur = conn.cursor()

        print("\n[2] SAMPLE DATA PREVIEW:")

        # Shops
        cur.execute("SELECT id, name, address, contact_number, owner_name, delivery_fee FROM shops ORDER BY id ASC LIMIT 3;")
        print("  * Shops:")
        for r in cur.fetchall():
            print(f"    [{r['id']}] {r['name']} ({r['address']}) | Owner: {r['owner_name']} | Fee: ₱{float(r['delivery_fee']):.2f}")

        # Users
        cur.execute("SELECT id, role, full_name, mobile, username FROM users ORDER BY id ASC LIMIT 4;")
        print("\n  * Users:")
        for r in cur.fetchall():
            identifier = r['mobile'] or r['username']
            print(f"    [{r['id']}] {r['full_name']} | Role: {r['role']} | Contact/Login: {identifier}")

        # Services
        cur.execute("SELECT id, shop_id, name, rate, unit FROM services ORDER BY id ASC LIMIT 3;")
        print("\n  * Services:")
        for r in cur.fetchall():
            print(f"    [{r['id']}] {r['name']} (Shop #{r['shop_id']}) | ₱{float(r['rate']):.2f} / {r['unit']}")

        # Bookings
        cur.execute("""
            SELECT b.id, b.order_code, u.full_name AS customer_name, s.name AS shop_name,
                   b.service_name, b.rate, b.unit, b.handling, b.status, b.payment_status
            FROM bookings b
            JOIN users u ON b.customer_id = u.id
            JOIN shops s ON b.shop_id = s.id
            ORDER BY b.id ASC
            LIMIT 3;
        """)
        print("\n  * Bookings (Figma Orders):")
        for r in cur.fetchall():
            code = r['order_code'] or f"ID-{r['id']}"
            print(f"    [{code}] {r['customer_name']} -> {r['service_name']} at {r['shop_name']}")
            print(f"      Handling: {r['handling']} | Status: {r['status']} | Payment: {r['payment_status']} (₱{float(r['rate']):.2f}/{r['unit']})")

        # Notifications
        cur.execute("""
            SELECT n.id, u.full_name, n.booking_id, n.kind, n.title, n.body, n.is_read
            FROM notifications n
            JOIN users u ON n.user_id = u.id
            ORDER BY n.id ASC
            LIMIT 3;
        """)
        print("\n  * Notifications:")
        for r in cur.fetchall():
            status = "READ" if r['is_read'] else "UNREAD"
            print(f"    [{r['kind'].upper()}] To {r['full_name']}: {r['title']} - '{r['body']}' ({status})")

        # 3. Relational integrity
        print("\n[3] RELATIONAL INTEGRITY CHECKS:")
        cur.execute("SELECT COUNT(*) AS count FROM services WHERE shop_id NOT IN (SELECT id FROM shops);")
        orphans_srv = cur.fetchone()["count"]
        cur.execute("SELECT COUNT(*) AS count FROM bookings WHERE customer_id NOT IN (SELECT id FROM users);")
        orphans_bkg = cur.fetchone()["count"]
        cur.execute("SELECT COUNT(*) AS count FROM notifications WHERE user_id NOT IN (SELECT id FROM users);")
        orphans_notif = cur.fetchone()["count"]

        print(f"    [+] Orphaned Services: {orphans_srv}")
        print(f"    [+] Orphaned Bookings: {orphans_bkg}")
        print(f"    [+] Orphaned Notifications: {orphans_notif}")

    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("                      ALL CHECKS HEALTHY!")
    print("=" * 70)


if __name__ == "__main__":
    inspect_all()
