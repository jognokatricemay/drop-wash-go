"""
Unified Database Adapter (XAMPP MySQL / PostgreSQL / SQLite)
Automatically detects the environment:
- If DATABASE_URL starts with mysql:// or mariadb:// (or MYSQL_HOST is set) -> Routes to XAMPP MySQL
- If DATABASE_URL starts with postgresql:// -> Routes to PostgreSQL
- Otherwise -> Defaults to local SQLite
"""

import os
import sqlite3
from typing import Any, List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
IS_PLACEHOLDER = bool("YOUR_AIVEN_HOST" in DATABASE_URL or ":PORT" in DATABASE_URL or "YOUR_PASSWORD" in DATABASE_URL)

# Determine active engine
IS_MYSQL = bool(
    (DATABASE_URL.startswith("mysql://") or DATABASE_URL.startswith("mariadb://") or os.environ.get("MYSQL_HOST"))
    and not IS_PLACEHOLDER
)
IS_POSTGRES = bool(
    (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"))
    and not IS_PLACEHOLDER
    and not IS_MYSQL
)


def get_engine_name() -> str:
    """Returns 'XAMPP MySQL', 'PostgreSQL', or 'SQLite' based on active configuration."""
    if IS_MYSQL:
        return "XAMPP MySQL"
    elif IS_POSTGRES:
        return "PostgreSQL"
    else:
        return "SQLite"


def init_database() -> None:
    """Initializes tables and seeds base records for the active database engine."""
    if IS_MYSQL:
        import database_mysql
        database_mysql.init_mysql_schema()
        from seed import seed_figma_data
        seed_figma_data()
    elif IS_POSTGRES:
        import database_pg
        database_pg.init_pg_schema(DATABASE_URL)
        from seed import seed_figma_data
        seed_figma_data()
    else:
        import database
        database.init_db()
        from seed import seed_figma_data
        seed_figma_data()


def clear_database() -> None:
    """Wipes all data and resets autoincrement ID counters back to 1."""
    if IS_MYSQL:
        import database_mysql
        database_mysql.clear_mysql_tables()
    elif IS_POSTGRES:
        import database_pg
        database_pg.clear_pg_tables(DATABASE_URL)
    else:
        import database
        database.clear_db()


def add_records_indefinitely(count: int = 1000) -> None:
    """Adds arbitrary volumes of records into whichever database engine is active."""
    from seed import seed_indefinitely
    seed_indefinitely(total_to_add=count)


def get_counts() -> Dict[str, int]:
    """Retrieves live counts across all 5 tables from the active database."""
    if IS_MYSQL:
        import database_mysql
        return database_mysql.get_mysql_table_counts()
    elif IS_POSTGRES:
        import database_pg
        return database_pg.get_pg_table_counts(DATABASE_URL)
    else:
        import database
        return database.get_table_counts()


if __name__ == "__main__":
    print(f"[*] Active Database Engine: {get_engine_name()}")
    try:
        counts = get_counts()
        print("=" * 45)
        print("CURRENT LIVE TABLE COUNTS:")
        print("=" * 45)
        for table, count in counts.items():
            print(f"  {table:<15}: {count:>8,} records")
        print("=" * 45)
    except Exception as e:
        print(f"[-] {e}")
