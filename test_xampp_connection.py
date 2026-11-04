"""
XAMPP MySQL / MariaDB Connection Diagnostic Tool
Checks port 3306 reachability, credentials, server version, and database status.
"""

import os
import sys
import socket
from dotenv import load_dotenv

load_dotenv()

def test_xampp():
    print("=" * 70)
    print("          XAMPP MYSQL / MARIADB CONNECTION DIAGNOSTIC")
    print("=" * 70)

    from database_mysql import get_mysql_config

    cfg = get_mysql_config()
    host = cfg["host"]
    port = cfg["port"]
    user = cfg["user"]
    db = cfg["database"]

    print(f"[*] Target Server : {host}:{port}")
    print(f"[*] Target User   : {user}")
    print(f"[*] Target DB     : {db}")

    # Step 1: Check port reachability
    print(f"\n[1/3] Checking if MySQL service is listening on {host}:{port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect((host, port))
        sock.close()
        print(f"  [+] Port {port} is OPEN and reachable!")
    except Exception:
        print(f"  [-] FAILED: Could not connect to {host}:{port}.")
        print("\n  ============================= HOW TO FIX =============================")
        print("  1. Open the XAMPP Control Panel application on your computer.")
        print("  2. Look for 'MySQL' in the Module list.")
        print("  3. Click the 'Start' button next to MySQL.")
        print("  4. Once the MySQL background turns green and shows a Port (e.g. 3306),")
        print("     run this command again:")
        print("     .\\pyrun.bat test_xampp_connection.py")
        print("  ======================================================================")
        return False

    # Step 2: Test authentication
    print(f"\n[2/3] Authenticating as user '{user}'...")
    import pymysql
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=cfg["password"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except Exception as e:
        print(f"  [-] FAILED: Authentication error: {e}")
        print("\n  Fix: Verify your MySQL credentials in .env.")
        print("  Default XAMPP credentials are user: 'root' with NO password (blank).")
        return False

    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS ver, DATABASE() AS cur_db;")
        row = cur.fetchone()
        server_ver = row["ver"]
        print(f"  [+] Connected successfully! Server Version: {server_ver}")

        # Step 3: Check database & tables
        print(f"\n[3/3] Checking database '{db}'...")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute(f"USE `{db}`;")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name IN ('shops', 'users', 'services', 'bookings', 'notifications');
        """, (db,))
        tables = [r["table_name"] or r["TABLE_NAME"] for r in cur.fetchall()]

    conn.close()

    print(f"  [+] Database '{db}' is ready. Tables found: {len(tables)}/5 ({', '.join(tables) if tables else 'None yet'})")

    print("\n" + "=" * 70)
    print("       ALL CHECKS PASSED! XAMPP MYSQL IS FULLY OPERATIONAL.")
    print("=" * 70)
    print("\nHelpful XAMPP Links & Commands:")
    print("  * Open phpMyAdmin in browser: http://localhost/phpmyadmin")
    print("  * Initialize & Seed Database: .\\pyrun.bat seed.py --init")
    print("  * Inspect Database Rows     : .\\pyrun.bat inspect_db.py")
    return True

if __name__ == "__main__":
    test_xampp()
