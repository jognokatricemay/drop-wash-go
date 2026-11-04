"""
Database Integrity & Scale Verification Suite
Tests the LAUNDRY BOOKING schema across all three supported engines:
  - XAMPP MySQL / MariaDB
  - PostgreSQL (Aiven)
  - SQLite (local fallback)

Tests:
  1. Foreign-key enforcement   – booking with non-existent customer_id must be rejected
  2. CHECK / ENUM constraints  – invalid status, negative service rate
  3. Orphan detection          – bookings whose customer no longer exists
  4. Index utilisation         – EXPLAIN confirms indexes are used on key queries
  5. Constraint summary        – lists FKs / checks reported by the engine
"""

import sys
import sqlite3

sys.stdout.reconfigure(encoding="utf-8")

# ── Engine detection ─────────────────────────────────────────────────────────
from db import IS_MYSQL, IS_POSTGRES, get_engine_name

PASS = "[+] PASS"
FAIL = "[-] FAIL"
INFO = "[*]     "
SEP  = "─" * 60


# ══════════════════════════════════════════════════════════════════════════════
# MySQL helpers
# ══════════════════════════════════════════════════════════════════════════════

def _mysql_conn():
    """Return an open PyMySQL connection (raises ConnectionError if XAMPP is down)."""
    try:
        import database_mysql
        return database_mysql.get_mysql_connection()
    except Exception as exc:
        raise ConnectionError(
            "Could not connect to XAMPP MySQL.\n"
            "  → Open XAMPP Control Panel and click Start next to MySQL."
        ) from exc


def _mysql_run(conn, sql, params=(), fetch=False):
    import pymysql.cursors
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        return cur.rowcount


def run_mysql():
    conn = _mysql_conn()
    conn.autocommit = False
    errors = 0

    try:
        print(f"\n{SEP}")
        print("TEST 1 — Foreign-key enforcement (invalid customer_id)")
        print(SEP)
        # Use a customer_id that certainly does not exist
        bad_sql = """
            INSERT INTO bookings
              (customer_id, shop_id, service_name, rate, unit, handling,
               delivery_fee, requested_date, status, payment_status)
            VALUES (99999, 1, 'Test', 35, 'kg', 'drop-off',
                    0, CURDATE(), 'Pending', 'Unpaid')
        """
        try:
            _mysql_run(conn, bad_sql)
            conn.rollback()
            print(f"{FAIL}: FK not enforced — orphan booking was accepted!")
            errors += 1
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: FK rejected non-existent customer_id — {e}")

        print(f"\n{SEP}")
        print("TEST 2 — ENUM constraint on users.role")
        print(SEP)
        # MySQL ENUM rejects unknown values by default (strict mode)
        try:
            _mysql_run(conn,
                "INSERT INTO users (role, full_name, password_hash) "
                "VALUES ('hacker', 'Bad Actor', 'x')")
            conn.rollback()
            print(f"{FAIL}: ENUM not enforced — invalid role was accepted!")
            errors += 1
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: ENUM rejected invalid role — {e}")

        print(f"\n{SEP}")
        print("TEST 3 — Negative service rate (application-level guard)")
        print(SEP)
        # MySQL < 8.0.16 silently ignores CHECK constraints; warn the user.
        try:
            _mysql_run(conn,
                "INSERT INTO services (shop_id, name, rate, unit) "
                "VALUES (1, '__neg_test__', -99, 'kg')")
            conn.rollback()
            # Clean the test row in case it committed somehow
            _mysql_run(conn,
                "DELETE FROM services WHERE name = '__neg_test__'")
            conn.commit()
            print(
                f"  ⚠  MySQL accepted a negative rate — this is expected on "
                "MariaDB / MySQL < 8.0.16 which ignores CHECK constraints.\n"
                f"  ℹ  Enforce rate >= 0 in your Python layer (seed.py / CRUD)."
            )
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: CHECK rejected negative rate — {e}")

        print(f"\n{SEP}")
        print("TEST 4 — Orphan detection (bookings with no matching customer)")
        print(SEP)
        rows = _mysql_run(conn, """
            SELECT b.id, b.order_code, b.customer_id
            FROM   bookings b
            LEFT JOIN users u ON u.id = b.customer_id
            WHERE  u.id IS NULL
        """, fetch=True)
        if rows:
            print(f"{FAIL}: {len(rows)} orphaned booking(s) found:")
            for r in rows:
                print(f"      booking id={r['id']}  code={r['order_code']}  "
                      f"customer_id={r['customer_id']}")
            errors += 1
        else:
            print(f"{PASS}: No orphaned bookings.")

        print(f"\n{SEP}")
        print("TEST 5 — Index utilisation (EXPLAIN on key queries)")
        print(SEP)

        def explain_mysql(label, sql, params=()):
            rows = _mysql_run(conn, "EXPLAIN " + sql, params, fetch=True)
            for r in rows:
                key      = r.get("key") or "NONE (full scan!)"
                possible = r.get("possible_keys") or "-"
                tbl      = r.get("table") or "?"
                print(f"  {label}")
                print(f"      table={tbl}  key_used={key}  "
                      f"possible_keys={possible}")
                if key == "NONE (full scan!)":
                    print(f"      ⚠  No index used — consider adding one.")

        explain_mysql("bookings by customer_id + requested_date",
            "SELECT * FROM bookings "
            "WHERE customer_id = %s AND requested_date >= '2026-01-01' "
            "ORDER BY requested_date DESC", (1,))

        explain_mysql("bookings by status",
            "SELECT * FROM bookings WHERE status = %s", ("Pending",))

        explain_mysql("notifications by user_id + is_read",
            "SELECT * FROM notifications WHERE user_id = %s AND is_read = 0",
            (1,))

        explain_mysql("bookings by order_code",
            "SELECT * FROM bookings WHERE order_code = %s", ("DWG-00483",))

        print(f"\n{SEP}")
        print("TEST 6 — Constraint summary (INFORMATION_SCHEMA)")
        print(SEP)
        fks = _mysql_run(conn, """
            SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME
            FROM   INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE  TABLE_SCHEMA = DATABASE()
              AND  REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME, CONSTRAINT_NAME
        """, fetch=True)
        if fks:
            print("  Foreign keys declared:")
            for fk in fks:
                print(f"    {fk['TABLE_NAME']}.{fk['CONSTRAINT_NAME']} "
                      f"→ {fk['REFERENCED_TABLE_NAME']}")
        else:
            print("  ⚠  No foreign keys found — was InnoDB used?")

    finally:
        conn.close()

    return errors


# ══════════════════════════════════════════════════════════════════════════════
# PostgreSQL helpers
# ══════════════════════════════════════════════════════════════════════════════

def _pg_conn():
    try:
        import os
        import psycopg
        from dotenv import load_dotenv
        load_dotenv()
        url = os.environ.get("DATABASE_URL", "")
        return psycopg.connect(url, connect_timeout=10)
    except Exception as exc:
        raise ConnectionError(
            "Could not connect to PostgreSQL.\n"
            "  → Check DATABASE_URL in .env and your network connection."
        ) from exc


def run_postgres():
    conn = _pg_conn()
    conn.autocommit = False
    cur = conn.cursor()
    errors = 0

    try:
        print(f"\n{SEP}")
        print("TEST 1 — Foreign-key enforcement (invalid customer_id)")
        print(SEP)
        try:
            cur.execute("""
                INSERT INTO bookings
                  (customer_id, shop_id, service_name, rate, unit, handling,
                   delivery_fee, requested_date, status, payment_status)
                VALUES (99999, 1, 'Test', 35, 'kg', 'drop-off',
                        0, CURRENT_DATE, 'Pending', 'Unpaid')
            """)
            conn.rollback()
            print(f"{FAIL}: FK not enforced — orphan booking was accepted!")
            errors += 1
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: FK rejected non-existent customer_id — {e}")

        print(f"\n{SEP}")
        print("TEST 2 — CHECK constraint on bookings.status")
        print(SEP)
        try:
            cur.execute("""
                INSERT INTO bookings
                  (customer_id, shop_id, service_name, rate, unit, handling,
                   delivery_fee, requested_date, status, payment_status)
                VALUES (1, 1, 'Test', 35, 'kg', 'drop-off',
                        0, CURRENT_DATE, 'invalid_status', 'Unpaid')
            """)
            conn.rollback()
            print(f"{FAIL}: CHECK not enforced — invalid status was accepted!")
            errors += 1
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: CHECK rejected invalid status — {e}")

        print(f"\n{SEP}")
        print("TEST 3 — CHECK constraint: negative service rate")
        print(SEP)
        try:
            cur.execute("""
                INSERT INTO services (shop_id, name, rate, unit)
                VALUES (1, '__neg_test__', -99, 'kg')
            """)
            conn.rollback()
            print(f"{FAIL}: CHECK not enforced — negative rate was accepted!")
            errors += 1
        except Exception as e:
            conn.rollback()
            print(f"{PASS}: CHECK rejected negative rate — {e}")

        print(f"\n{SEP}")
        print("TEST 4 — Orphan detection")
        print(SEP)
        cur.execute("""
            SELECT b.id, b.order_code, b.customer_id
            FROM   bookings b
            LEFT JOIN users u ON u.id = b.customer_id
            WHERE  u.id IS NULL
        """)
        rows = cur.fetchall()
        if rows:
            print(f"{FAIL}: {len(rows)} orphaned booking(s) found:")
            for r in rows:
                print(f"      booking id={r[0]}  code={r[1]}  customer_id={r[2]}")
            errors += 1
        else:
            print(f"{PASS}: No orphaned bookings.")

        print(f"\n{SEP}")
        print("TEST 5 — Index utilisation (EXPLAIN)")
        print(SEP)

        def explain_pg(label, sql, params=()):
            cur.execute("EXPLAIN " + sql, params)
            plan = "\n".join(r[0] for r in cur.fetchall())
            uses_index = "Index" in plan
            tag = PASS if uses_index else "  ⚠ "
            print(f"  {tag} {label}")
            for line in plan.splitlines()[:4]:
                print(f"       {line}")

        explain_pg("bookings by customer_id + requested_date",
            "SELECT * FROM bookings "
            "WHERE customer_id = %s AND requested_date >= '2026-01-01' "
            "ORDER BY requested_date DESC", (1,))

        explain_pg("notifications unread by user_id",
            "SELECT * FROM notifications WHERE user_id = %s AND is_read = false",
            (1,))

        print(f"\n{SEP}")
        print("TEST 6 — Constraint summary (pg_constraint)")
        print(SEP)
        cur.execute("""
            SELECT conrelid::regclass AS tbl,
                   conname            AS name,
                   contype            AS kind
            FROM   pg_constraint
            WHERE  connamespace = 'public'::regnamespace
            ORDER  BY tbl, kind
        """)
        rows = cur.fetchall()
        kind_map = {"f": "FOREIGN KEY", "p": "PRIMARY KEY",
                    "u": "UNIQUE", "c": "CHECK"}
        print("  Constraints declared:")
        for tbl, name, kind in rows:
            print(f"    {tbl:<20} {kind_map.get(kind, kind):<14} {name}")

    finally:
        cur.close()
        conn.close()

    return errors


# ══════════════════════════════════════════════════════════════════════════════
# SQLite helpers
# ══════════════════════════════════════════════════════════════════════════════

def _sqlite_conn():
    try:
        from database import get_connection, DEFAULT_DB_PATH
        conn = get_connection(DEFAULT_DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as exc:
        raise ConnectionError(f"Could not open SQLite database: {exc}") from exc


def run_sqlite():
    conn = _sqlite_conn()
    errors = 0

    try:
        print(f"\n{SEP}")
        print("TEST 1 — Foreign-key enforcement (invalid customer_id)")
        print(SEP)
        try:
            conn.execute("""
                INSERT INTO bookings
                  (customer_id, shop_id, service_name, rate, unit, handling,
                   delivery_fee, requested_date, status, payment_status)
                VALUES (99999, 1, 'Test', 35, 'kg', 'drop-off',
                        0, date('now'), 'Pending', 'Unpaid')
            """)
            conn.rollback()
            print(f"{FAIL}: FK not enforced — did you run PRAGMA foreign_keys = ON?")
            errors += 1
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"{PASS}: FK rejected non-existent customer_id — {e}")

        print(f"\n{SEP}")
        print("TEST 2 — CHECK constraint on bookings.status")
        print(SEP)
        try:
            conn.execute("""
                INSERT INTO bookings
                  (customer_id, shop_id, service_name, rate, unit, handling,
                   delivery_fee, requested_date, status, payment_status)
                VALUES (1, 1, 'Test', 35, 'kg', 'drop-off',
                        0, date('now'), 'invalid_status', 'Unpaid')
            """)
            conn.rollback()
            print(f"{FAIL}: CHECK not enforced — invalid status was accepted!")
            errors += 1
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"{PASS}: CHECK rejected invalid status — {e}")

        print(f"\n{SEP}")
        print("TEST 3 — CHECK constraint: negative service rate")
        print(SEP)
        try:
            conn.execute("""
                INSERT INTO services (shop_id, name, rate, unit)
                VALUES (1, '__neg_test__', -99, 'kg')
            """)
            conn.rollback()
            print(f"{FAIL}: CHECK not enforced — negative rate was accepted!")
            errors += 1
        except sqlite3.IntegrityError as e:
            conn.rollback()
            print(f"{PASS}: CHECK rejected negative rate — {e}")

        print(f"\n{SEP}")
        print("TEST 4 — Orphan detection via PRAGMA foreign_key_check")
        print(SEP)
        orphans = conn.execute("PRAGMA foreign_key_check(bookings)").fetchall()
        if orphans:
            print(f"{FAIL}: {len(orphans)} orphaned row(s) in bookings:")
            for o in orphans:
                print(f"      {dict(o)}")
            errors += 1
        else:
            print(f"{PASS}: No orphaned bookings (PRAGMA foreign_key_check).")

        # Also check notifications
        orphans_n = conn.execute("PRAGMA foreign_key_check(notifications)").fetchall()
        if orphans_n:
            print(f"{FAIL}: {len(orphans_n)} orphaned row(s) in notifications:")
            for o in orphans_n:
                print(f"      {dict(o)}")
            errors += 1
        else:
            print(f"{PASS}: No orphaned notifications.")

        print(f"\n{SEP}")
        print("TEST 5 — Index utilisation (EXPLAIN QUERY PLAN)")
        print(SEP)

        def explain_sqlite(label, sql, params=()):
            rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
            # sqlite3.Row.__str__ returns object address — access the 'detail' column
            details = [r["detail"] for r in rows]
            # "SEARCH ... USING INDEX" = good; plain "SCAN" = full table scan
            uses_index = any("SEARCH" in d and "USING" in d for d in details)
            tag = PASS if uses_index else "  ⚠ "
            print(f"  {tag} {label}")
            for d in details:
                print(f"       {d}")

        explain_sqlite(
            "bookings by customer_id + requested_date",
            "SELECT * FROM bookings "
            "WHERE customer_id = ? AND requested_date >= '2026-01-01' "
            "ORDER BY requested_date DESC", (1,))

        explain_sqlite(
            "bookings by status",
            "SELECT * FROM bookings WHERE status = ?", ("Pending",))

        explain_sqlite(
            "notifications unread by user_id",
            "SELECT * FROM notifications WHERE user_id = ? AND is_read = 0",
            (1,))

        explain_sqlite(
            "bookings by order_code",
            "SELECT * FROM bookings WHERE order_code = ?", ("DWG-00483",))

        print(f"\n{SEP}")
        print("TEST 6 — Constraint summary (sqlite_master)")
        print(SEP)
        tables = ["shops", "services", "users", "bookings", "notifications"]
        for t in tables:
            ddl = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)
            ).fetchone()
            if ddl:
                # Pull FK and CHECK lines from the DDL
                lines = [ln.strip() for ln in ddl[0].splitlines()
                         if "FOREIGN KEY" in ln or "CHECK" in ln or "REFERENCES" in ln]
                if lines:
                    print(f"  {t}:")
                    for ln in lines:
                        print(f"      {ln}")
                else:
                    print(f"  {t}: (no FK / CHECK declarations found)")

    finally:
        conn.close()

    return errors


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    engine = get_engine_name()
    print("=" * 60)
    print(f"  LAUNDRY DB — INTEGRITY & SCALE VERIFICATION")
    print(f"  Engine : {engine}")
    print("=" * 60)

    try:
        if IS_MYSQL:
            total_errors = run_mysql()
        elif IS_POSTGRES:
            total_errors = run_postgres()
        else:
            total_errors = run_sqlite()
    except ConnectionError as ce:
        print(f"\n  ✗  Connection failed:\n  {ce}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    if total_errors == 0:
        print("  ✓  All integrity tests passed.")
    else:
        print(f"  ✗  {total_errors} test(s) FAILED — review output above.")
    print("=" * 60)
    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
