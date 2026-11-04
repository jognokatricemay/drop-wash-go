"""
Comprehensive Aiven / PostgreSQL Connection Diagnostic & Troubleshooting Tool
Performs step-by-step isolated checks:
1. Environment & URL syntax validation (detects unescaped special characters)
2. DNS resolution (verifies host exists)
3. TCP Socket connection (verifies port is open and reachable through firewalls)
4. SSL Handshake & Authentication (verifies credentials and sslmode)
"""

import os
import sys
import socket
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

load_dotenv()


def diagnose():
    print("=" * 70)
    print("       AIVEN / POSTGRESQL STEP-BY-STEP DIAGNOSTIC TOOL")
    print("=" * 70)

    conn_url = os.environ.get("DATABASE_URL")

    # -------------------------------------------------------------------------
    # CHECK 1: Environment Variable Check
    # -------------------------------------------------------------------------
    print("\n[Check 1/4] Checking 'DATABASE_URL' in .env or environment...")
    if not conn_url:
        print("  [-] FAILED: 'DATABASE_URL' is not set.")
        print("      Fix: Create a '.env' file in this folder and add:")
        print('      DATABASE_URL="postgres://avnadmin:PASSWORD@HOST:PORT/defaultdb?sslmode=require"')
        return False

    # Check for unedited placeholder templates
    if "YOUR_AIVEN_HOST" in conn_url or ":PORT" in conn_url or "YOUR_PASSWORD" in conn_url:
        print("  [-] FAILED: Your .env file contains placeholder text ('YOUR_AIVEN_HOST', 'PORT', or 'YOUR_PASSWORD').")
        print("      Fix:")
        print("      1. Open the '.env' file in VS Code.")
        print("      2. Replace the placeholder values with your real Aiven Service URI from console.aiven.io.")
        return False

    print("  [+] PASSED: 'DATABASE_URL' found.")

    # -------------------------------------------------------------------------
    # CHECK 2: URL Parsing & Special Characters Check
    # -------------------------------------------------------------------------
    print("\n[Check 2/4] Parsing connection string components...")
    clean_url = conn_url.strip()
    if clean_url.startswith("postgres://"):
        clean_url = "postgresql://" + clean_url[len("postgres://"):]

    try:
        parsed = urlparse(clean_url)
        username = parsed.username
        password = parsed.password
        hostname = parsed.hostname
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") or "defaultdb"
        query = parsed.query
    except Exception as e:
        print(f"  [-] FAILED: Could not parse connection URL ({e})")
        return False

    if not hostname or not username:
        print("  [-] FAILED: URL is missing hostname or username.")
        return False

    # Check for unencoded special characters in password
    raw_user_info = clean_url.split("@")[0].split("//")[-1] if "@" in clean_url else ""
    if raw_user_info.count(":") > 1:
        print("  [!] WARNING: Your password appears to contain unencoded special characters (like ':' or '@').")
        print("      Fix: If your password has '@', replace it with '%40'. If ':', replace with '%3A'.")

    print(f"  [+] PASSED: Host: {hostname} | Port: {port} | User: {username} | DB: {dbname}")

    # Check SSL mode
    if "sslmode=require" not in query and "sslmode=verify-full" not in query:
        print("  [!] WARNING: Aiven requires SSL, but '?sslmode=require' was not found in the URL query.")
        print("      Fix: Append '?sslmode=require' to your connection string.")

    # -------------------------------------------------------------------------
    # CHECK 3: DNS Resolution & Network Reachability (Firewall check)
    # -------------------------------------------------------------------------
    print(f"\n[Check 3/4] Testing DNS resolution and TCP reachability to {hostname}:{port}...")
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"  [+] DNS Resolved: {hostname} -> {ip_address}")
    except socket.gaierror as e:
        print(f"  [-] FAILED: Could not resolve hostname '{hostname}'.")
        print("      Fix:")
        print("      1. Verify you didn't leave placeholder text like 'pg-your-project.aivencloud.com'.")
        print("      2. Ensure your Aiven service is RUNNING in the Aiven Console (not deleted or rebuilding).")
        return False

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((ip_address, port))
        sock.close()
        print(f"  [+] Network reachable: TCP connection established to port {port}.")
    except socket.timeout:
        print(f"  [-] FAILED: Connection timed out attempting to reach port {port}.")
        print("      Fix:")
        print("      1. Aiven IP Filter: Go to Aiven Console -> Service Settings -> IP Filter.")
        print("         Ensure your current public IP is allowed (or temporarily set to '0.0.0.0/0' to test).")
        print("      2. Corporate/School Firewall: Some networks block high ports (e.g. 10000-30000).")
        print("         Try connecting from a standard home Wi-Fi or mobile hotspot.")
        return False
    except ConnectionRefusedError:
        print(f"  [-] FAILED: Connection refused by host on port {port}.")
        print("      Fix: Verify the port number. Aiven assigns dynamic ports (e.g., 23456) instead of 5432.")
        return False
    except Exception as e:
        print(f"  [-] FAILED: Network error: {e}")
        return False

    # -------------------------------------------------------------------------
    # CHECK 4: PostgreSQL Handshake & Authentication
    # -------------------------------------------------------------------------
    print("\n[Check 4/4] Performing PostgreSQL SSL handshake and credential authentication...")
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(clean_url, connect_timeout=10, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                pg_ver = cur.fetchone()["version"]

                cur.execute("SELECT current_database(), current_user;")
                row = cur.fetchone()
                db_name, user_name = row["current_database"], row["current_user"]

        print("  [+] PASSED: Authentication successful!")
        print(f"      - Connected as: {user_name}")
        print(f"      - Database    : {db_name}")
        print(f"      - Server      : {pg_ver.split(',')[0]}")

        print("\n" + "=" * 70)
        print("       ALL CHECKS PASSED! AIVEN POSTGRESQL IS READY TO USE.")
        print("=" * 70)
        print("\nNext command to run:")
        print("  .\\pyrun.bat seed.py --init")
        return True

    except Exception as e:
        err = str(e)
        print(f"  [-] FAILED: Database authentication failed.")
        print(f"      Error details: {err}")
        print("\n      Fix:")
        if "password authentication failed" in err.lower():
            print("      - Password incorrect: In Aiven Console, click 'Show password' or reset it.")
            print("      - Ensure special characters in password are URL-encoded if using a connection string.")
        elif "no pg_hba.conf entry" in err.lower() or "ssl" in err.lower():
            print("      - SSL is required: Ensure '?sslmode=require' is at the end of DATABASE_URL.")
        return False


if __name__ == "__main__":
    diagnose()
