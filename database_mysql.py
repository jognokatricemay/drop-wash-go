"""
XAMPP MySQL / MariaDB Database Manager
Provides connection handling, database creation, schema initialization,
and table operations for XAMPP (Apache + MySQL/MariaDB).
"""

import os
import sys
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

load_dotenv()

SCHEMA_MYSQL_PATH = "schema_mysql.sql"


def get_mysql_config() -> dict:
    """Extracts connection parameters from environment or defaults to standard XAMPP settings."""
    url = os.environ.get("DATABASE_URL")
    
    # Defaults for standard XAMPP installation
    host = os.environ.get("MYSQL_HOST", "localhost")
    port = int(os.environ.get("MYSQL_PORT", 3306))
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    database = os.environ.get("MYSQL_DATABASE", "laundry_db")

    if url and (url.startswith("mysql://") or url.startswith("mariadb://")):
        parsed = urlparse(url)
        host = parsed.hostname or host
        port = parsed.port or port
        user = parsed.username or user
        password = unquote(parsed.password or "")
        path = parsed.path.lstrip("/")
        if path:
            database = path

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }


def get_mysql_connection(include_database: bool = True) -> pymysql.Connection:
    """
    Connects to XAMPP MySQL.
    If include_database is False, connects to the server root (useful for creating the database).
    """
    cfg = get_mysql_config()
    connect_params = {
        "host": cfg["host"],
        "port": cfg["port"],
        "user": cfg["user"],
        "password": cfg["password"],
        "charset": cfg["charset"],
        "cursorclass": cfg["cursorclass"],
        "autocommit": cfg["autocommit"],
    }
    if include_database:
        connect_params["database"] = cfg["database"]

    try:
        conn = pymysql.connect(**connect_params)
        return conn
    except pymysql.err.OperationalError as e:
        err_code, err_msg = e.args
        if err_code == 1049 and include_database:
            # Database does not exist yet; create it automatically!
            ensure_database_exists()
            return pymysql.connect(**connect_params)
        elif err_code == 2003:
            raise ConnectionError(
                f"Could not connect to MySQL at {cfg['host']}:{cfg['port']}.\n"
                "  --> Is XAMPP running? Please open XAMPP Control Panel and click 'Start' next to MySQL."
            ) from e
        raise


def ensure_database_exists():
    """Creates the target database in XAMPP MySQL if it does not exist yet."""
    cfg = get_mysql_config()
    db_name = cfg["database"]
    root_conn = get_mysql_connection(include_database=False)
    try:
        with root_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        root_conn.commit()
        print(f"[*] Database '{db_name}' ensured on XAMPP MySQL server.")
    finally:
        root_conn.close()


def init_mysql_schema(schema_path: str = SCHEMA_MYSQL_PATH) -> None:
    """Executes schema_mysql.sql on XAMPP MySQL to create tables and indexes."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    ensure_database_exists()

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    conn = get_mysql_connection(include_database=True)
    try:
        with conn.cursor() as cur:
            # Execute statement by statement
            statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
            for stmt in statements:
                cur.execute(stmt)
        conn.commit()
        print("[*] XAMPP MySQL schema initialized successfully!")
    finally:
        conn.close()


def clear_mysql_tables() -> None:
    """Clears all records from tables and resets AUTO_INCREMENT counters back to 1."""
    conn = get_mysql_connection(include_database=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            tables = ["notifications", "bookings", "services", "users", "shops"]
            for tbl in tables:
                cur.execute(f"TRUNCATE TABLE `{tbl}`;")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("[+] All XAMPP MySQL tables truncated and AUTO_INCREMENT counters reset to 1!")
    finally:
        conn.close()


def get_mysql_table_counts() -> dict:
    """Returns row counts across all 5 tables in XAMPP MySQL."""
    tables = ["shops", "users", "services", "bookings", "notifications"]
    counts = {}
    conn = get_mysql_connection(include_database=True)
    try:
        with conn.cursor() as cur:
            for tbl in tables:
                cur.execute(f"SELECT COUNT(*) AS count FROM `{tbl}`;")
                counts[tbl] = cur.fetchone()["count"]
        return counts
    finally:
        conn.close()


if __name__ == "__main__":
    if "--init" in sys.argv:
        init_mysql_schema()

    if "--clear" in sys.argv:
        clear_mysql_tables()

    try:
        counts = get_mysql_table_counts()
        print("\nCURRENT XAMPP MYSQL ROW COUNTS:")
        for t, c in counts.items():
            print(f"  {t:<15}: {c:>8,} rows")
    except Exception as e:
        print(f"[-] {e}")
