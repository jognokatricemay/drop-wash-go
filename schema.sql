PRAGMA foreign_keys = ON;

-- 1. Table: shops
CREATE TABLE IF NOT EXISTS shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact_number TEXT,
    owner_name TEXT,
    offers_dropoff INTEGER NOT NULL DEFAULT 1 CHECK (offers_dropoff IN (0, 1)),
    offers_pickup INTEGER NOT NULL DEFAULT 0 CHECK (offers_pickup IN (0, 1)),
    offers_delivery INTEGER NOT NULL DEFAULT 0 CHECK (offers_delivery IN (0, 1)),
    delivery_fee REAL NOT NULL DEFAULT 0.00,
    accepts_cash INTEGER NOT NULL DEFAULT 1 CHECK (accepts_cash IN (0, 1)),
    accepts_gcash INTEGER NOT NULL DEFAULT 0 CHECK (accepts_gcash IN (0, 1)),
    gcash_number TEXT,
    gcash_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shops_name ON shops(name);
CREATE INDEX IF NOT EXISTS idx_shops_is_active ON shops(is_active);

-- 2. Table: services
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rate REAL NOT NULL CHECK (rate >= 0),
    unit TEXT NOT NULL DEFAULT 'kg',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_services_shop_id ON services(shop_id);
CREATE INDEX IF NOT EXISTS idx_services_is_active ON services(is_active);

-- 3. Table: users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'staff', 'admin')),
    full_name TEXT NOT NULL,
    mobile TEXT,
    email TEXT,
    username TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    address TEXT,
    shop_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 4. Table: bookings
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT,
    customer_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    service_name TEXT NOT NULL,
    rate REAL NOT NULL DEFAULT 0.00,
    unit TEXT NOT NULL DEFAULT 'kg',
    handling TEXT NOT NULL DEFAULT 'drop-off' CHECK (handling IN ('drop-off', 'pickup-delivery', 'pickup', 'delivery')),
    delivery_fee REAL NOT NULL DEFAULT 0.00,
    est_weight REAL,
    actual_weight REAL,
    requested_date TEXT NOT NULL,
    requested_time TEXT,
    confirmed_schedule TEXT,
    delivery_schedule TEXT,
    address TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Accepted', 'Processing', 'Ready for Delivery', 'Completed', 'Rejected', 'Cancelled')),
    reject_reason TEXT,
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK (payment_status IN ('Unpaid', 'Paid', 'Refunded')),
    payment_method TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bookings_order_code ON bookings(order_code);
CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id);
CREATE INDEX IF NOT EXISTS idx_bookings_shop_id ON bookings(shop_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_requested_date ON bookings(requested_date);

-- 5. Table: notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    booking_id INTEGER,
    kind TEXT NOT NULL DEFAULT 'info' CHECK (kind IN ('success', 'info', 'error', 'warning')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_booking_id ON notifications(booking_id);
