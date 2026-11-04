"""
Clear Database Script
Wipes all records from shops, users, services, bookings, and notifications.
Resets primary key AUTO_INCREMENT sequences back to 1.
Automatically targets XAMPP MySQL, PostgreSQL, or SQLite based on configuration.
"""

import sys
from db import get_engine_name, clear_database, init_database, get_counts

if __name__ == "__main__":
    reseed = "--reseed" in sys.argv
    engine = get_engine_name()

    print(f"[*] Clearing {engine} database...")
    try:
        clear_database()

        if reseed:
            print(f"\n[*] Re-seeding baseline data into {engine}...")
            init_database()

        print("\n" + "=" * 50)
        print(f"UPDATED {engine.upper()} ROW COUNTS:")
        print("=" * 50)
        counts = get_counts()
        for table, count in counts.items():
            print(f"  {table:<15}: {count:>8,} rows")
        print("=" * 50)

    except ConnectionError as e:
        print(f"\n[-] CONNECTION ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] ERROR: {e}\n")
        sys.exit(1)
