-- Drop, Wash, Go database
-- Run with:  flask --app app init-db   (this DROPS and recreates every table)

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS shops;
SET FOREIGN_KEY_CHECKS = 1;

-- A participating laundry shop (FR-01, FR-11)
CREATE TABLE shops (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  name             VARCHAR(100) NOT NULL,
  address          VARCHAR(200) NOT NULL,
  contact_number   VARCHAR(30)  NOT NULL,
  owner_name       VARCHAR(100) NOT NULL,
  opening_hours    VARCHAR(60)  NOT NULL DEFAULT '8:00 AM - 8:00 PM',
  offers_dropoff   BOOLEAN NOT NULL DEFAULT TRUE,
  offers_pickup    BOOLEAN NOT NULL DEFAULT FALSE,
  offers_delivery  BOOLEAN NOT NULL DEFAULT FALSE,
  delivery_fee     DECIMAL(8,2) NOT NULL DEFAULT 0,
  accepts_cash     BOOLEAN NOT NULL DEFAULT TRUE,
  accepts_gcash    BOOLEAN NOT NULL DEFAULT FALSE,
  gcash_number     VARCHAR(30),
  gcash_name       VARCHAR(100),
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers log in with mobile number; staff log in with username (one account per shop)
CREATE TABLE users (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  role           ENUM('customer','staff') NOT NULL,
  full_name      VARCHAR(100) NOT NULL,
  mobile         VARCHAR(30),
  email          VARCHAR(120),
  username       VARCHAR(60),
  password_hash  VARCHAR(255) NOT NULL,
  address        VARCHAR(200),
  shop_id        INT NULL,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_mobile (mobile),
  UNIQUE KEY uq_username (username),
  FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

-- Services and rates of a shop (FR-02)
CREATE TABLE services (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  shop_id  INT NOT NULL,
  name     VARCHAR(80) NOT NULL,
  rate     DECIMAL(8,2) NOT NULL,
  unit     ENUM('kg','piece') NOT NULL DEFAULT 'kg',
  FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

-- A booking request. It becomes an order (gets order_code) when the shop accepts it (FR-03..FR-12).
-- rate / unit / delivery_fee are copied from the shop when booking, so later price changes
-- only apply to new bookings.
CREATE TABLE bookings (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  order_code          VARCHAR(20) NULL,
  customer_id         INT NOT NULL,
  shop_id             INT NOT NULL,
  service_name        VARCHAR(80) NOT NULL,
  rate                DECIMAL(8,2) NOT NULL,
  unit                ENUM('kg','piece') NOT NULL DEFAULT 'kg',
  handling            ENUM('drop-off','pickup','pickup-delivery') NOT NULL,
  delivery_fee        DECIMAL(8,2) NOT NULL DEFAULT 0,
  est_weight          DECIMAL(6,2) NOT NULL,
  actual_weight       DECIMAL(6,2) NULL,
  requested_date      DATE NOT NULL,
  requested_time      VARCHAR(30) NOT NULL,
  confirmed_schedule  VARCHAR(60) NULL,
  delivery_schedule   VARCHAR(60) NULL,
  address             VARCHAR(200) NULL,
  notes               VARCHAR(255) NULL,
  status              ENUM('Pending','Accepted','Processing','Ready for Pickup','Ready for Delivery','Completed','Rejected', 'Cancelled')
                      NOT NULL DEFAULT 'Pending',
  reject_reason       VARCHAR(200) NULL,
  payment_status      ENUM('Unpaid','Paid') NOT NULL DEFAULT 'Unpaid',
  payment_method      ENUM('cash','gcash') NULL,
  amount_received     DECIMAL(8,2) NULL,
  gcash_reference     VARCHAR(60) NULL,
  created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_order_code (order_code),
  FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
);

-- In-app notifications for customers (FR-13)
CREATE TABLE notifications (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT NOT NULL,
  booking_id  INT NULL,
  kind        ENUM('success','info','delivery','error') NOT NULL DEFAULT 'info',
  title       VARCHAR(120) NOT NULL,
  body        VARCHAR(255) NOT NULL,
  is_read     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);
