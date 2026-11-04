"""
Database Management Module
Provides connection management, schema initialization, and transactional operations
for Shops, Users, Services, Bookings, and Notification tables.

Designed for high-throughput, indefinite data growth using SQLite with WAL mode.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

DEFAULT_DB_PATH = "booking_system.db"
DEFAULT_SCHEMA_PATH = "schema.sql"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Creates and returns an optimized SQLite connection.
    Configured for high write performance, data integrity, and indefinite data growth.
    """
    conn = sqlite3.connect(db_path, timeout=30.0)
    # Return rows as sqlite3.Row for dict-like and index-based access
    conn.row_factory = sqlite3.Row

    # Performance & Integrity Pragmas:
    # 1. Enforce relational constraints across foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    # 2. Write-Ahead Logging (WAL) for high concurrency and indefinite writes without lock contention
    conn.execute("PRAGMA journal_mode = WAL;")
    # 3. Synchronous = NORMAL balances data safety with exceptional insert speed
    conn.execute("PRAGMA synchronous = NORMAL;")
    # 4. Cache size (negative number means kilobytes: 64MB cache in RAM)
    conn.execute("PRAGMA cache_size = -65536;")

    return conn


@contextmanager
def get_db(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for safe database connections and transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DEFAULT_DB_PATH, schema_path: str = DEFAULT_SCHEMA_PATH) -> None:
    """
    Initializes the database by executing schema.sql.
    Idempotent: will not drop existing data if tables already exist.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db(db_path) as conn:
        conn.executescript(schema_sql)
    print(f"[*] Database initialized successfully at '{db_path}' using '{schema_path}'.")


def get_table_counts(db_path: str = DEFAULT_DB_PATH) -> dict:
    """Returns row counts for all 5 core tables."""
    tables = ["shops", "users", "services", "bookings", "notifications"]
    counts = {}
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            counts[tbl] = cursor.fetchone()[0]
    return counts


def clear_db(db_path: str = DEFAULT_DB_PATH, reset_autoincrement: bool = True) -> None:
    """
    Clears all records from shops, users, services, bookings, and notifications tables.
    Preserves schema and indexes, resets autoincrement counters, and vacuums database.
    """
    if not os.path.exists(db_path):
        print(f"[-] Database file '{db_path}' does not exist.")
        return

    with get_db(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        tables = ["notifications", "bookings", "services", "users", "shops"]
        for tbl in tables:
            conn.execute(f"DELETE FROM {tbl};")

        if reset_autoincrement:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name IN ('shops', 'users', 'services', 'bookings', 'notifications');"
            )
        conn.execute("PRAGMA foreign_keys = ON;")

    # Reclaim disk space
    raw_conn = get_connection(db_path)
    raw_conn.execute("VACUUM;")
    raw_conn.close()
    print(f"[+] Successfully cleared all data from '{db_path}'. Tables are empty and ID sequences reset to 1.")


