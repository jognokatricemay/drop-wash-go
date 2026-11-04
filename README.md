# Laundry Booking System (XAMPP / MySQL / MariaDB)

A database system configured for **XAMPP** (Apache + MySQL / MariaDB + phpMyAdmin) matching the Figma Laundry design:
- **`shops`**: Mama Fe Laundry, Clean & Fresh, Wash Hub
- **`users`**: Juan Dela Cruz, Maria Santos, Fe Reyes, Ana Cruz, Ben Lim
- **`services`**: Wash & Fold (₱35/kg), Wash Dry & Fold (₱50/kg), Comforter (₱150/piece)
- **`bookings`**: Order codes `#DWG-00478` through `#DWG-00487`, sequential ID increments from `488`
- **`notifications`**: Order acceptance, processing, and rejection alerts

---

## 📁 Key Files

| File | Description |
| :--- | :--- |
| [`schema_mysql.sql`](schema_mysql.sql) | Native MySQL/MariaDB DDL with `AUTO_INCREMENT`, `TINYINT`, `DECIMAL`, and indexes. |
| [`database_mysql.py`](database_mysql.py) | XAMPP MySQL connector using `pymysql` (auto-creates `laundry_db` if missing). |
| [`seed.py`](seed.py) | Figma seed dataset + indefinite order generator (`ALTER TABLE bookings AUTO_INCREMENT = 488`). |
| [`test_xampp_connection.py`](test_xampp_connection.py) | Diagnostic tool verifying port 3306, credentials, and phpMyAdmin readiness. |
| [`inspect_db.py`](inspect_db.py) | Displays live row counts, sample orders with ₱ symbols, and referential integrity checks. |
| [`clear_db.py`](clear_db.py) | Truncates all tables and resets `AUTO_INCREMENT` back to 1. |
| [`crud_example.py`](crud_example.py) | Inserts a new laundry booking with order code generation (e.g. `#DWG-00488`). |
| [`.env`](.env) | XAMPP connection settings (`localhost:3306`, user `root`, blank password). |

---

## 🚀 Quick Start with XAMPP

### 1. Start MySQL in XAMPP
1. Open the **XAMPP Control Panel**.
2. Click the **Start** button next to **MySQL** (and optionally **Apache** for phpMyAdmin).
3. The module background will turn green and display Port `3306`.

### 2. Test Connection
```powershell
.\pyrun.bat test_xampp_connection.py
```

### 3. Initialize & Seed Database
Automatically creates the `laundry_db` database, tables, and seeds all Figma demo data:
```powershell
.\pyrun.bat seed.py --init
```

### 4. View Tables in phpMyAdmin
Open your browser and navigate to:
[http://localhost/phpmyadmin](http://localhost/phpmyadmin)
Click on `laundry_db` on the left sidebar to view the tables visually.

### 5. Ingest Indefinite Orders
Stream unlimited realistic laundry bookings into XAMPP MySQL:
```powershell
# Add 1,000 orders
.\pyrun.bat seed.py --add 1000

# Inspect live counts
.\pyrun.bat inspect_db.py
```
