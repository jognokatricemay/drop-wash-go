CREATE DATABASE IF NOT EXISTS `laundry_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `laundry_db`;

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. Table: shops
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `shops` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `address` TEXT NOT NULL,
    `contact_number` VARCHAR(50) NULL,
    `owner_name` VARCHAR(255) NULL,
    `offers_dropoff` TINYINT(1) NOT NULL DEFAULT 1,
    `offers_pickup` TINYINT(1) NOT NULL DEFAULT 0,
    `offers_delivery` TINYINT(1) NOT NULL DEFAULT 0,
    `delivery_fee` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `accepts_cash` TINYINT(1) NOT NULL DEFAULT 1,
    `accepts_gcash` TINYINT(1) NOT NULL DEFAULT 0,
    `gcash_number` VARCHAR(50) NULL,
    `gcash_name` VARCHAR(255) NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_shops_name` (`name`),
    INDEX `idx_shops_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Table: services
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `services` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `shop_id` INT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `rate` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `unit` VARCHAR(50) NOT NULL DEFAULT 'kg',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_services_shop` FOREIGN KEY (`shop_id`) REFERENCES `shops` (`id`) ON DELETE CASCADE,
    INDEX `idx_services_shop_id` (`shop_id`),
    INDEX `idx_services_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Table: users
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `role` ENUM('customer', 'staff', 'admin') NOT NULL DEFAULT 'customer',
    `full_name` VARCHAR(255) NOT NULL,
    `mobile` VARCHAR(50) NULL,
    `email` VARCHAR(255) NULL,
    `username` VARCHAR(100) NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `address` TEXT NULL,
    `shop_id` INT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_users_shop` FOREIGN KEY (`shop_id`) REFERENCES `shops` (`id`) ON DELETE SET NULL,
    INDEX `idx_users_mobile` (`mobile`),
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Table: bookings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bookings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_code` VARCHAR(50) NULL,
    `customer_id` INT NOT NULL,
    `shop_id` INT NOT NULL,
    `service_name` VARCHAR(255) NOT NULL,
    `rate` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `unit` VARCHAR(50) NOT NULL DEFAULT 'kg',
    `handling` VARCHAR(50) NOT NULL DEFAULT 'drop-off',
    `delivery_fee` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `est_weight` DECIMAL(10, 2) NULL,
    `actual_weight` DECIMAL(10, 2) NULL,
    `requested_date` DATE NOT NULL,
    `requested_time` VARCHAR(50) NULL,
    `confirmed_schedule` VARCHAR(50) NULL,
    `delivery_schedule` VARCHAR(50) NULL,
    `address` TEXT NULL,
    `notes` TEXT NULL,
    `status` VARCHAR(50) NOT NULL DEFAULT 'Pending',
    `reject_reason` TEXT NULL,
    `payment_status` VARCHAR(30) NOT NULL DEFAULT 'Unpaid',
    `payment_method` VARCHAR(50) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_bookings_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bookings_shop` FOREIGN KEY (`shop_id`) REFERENCES `shops` (`id`) ON DELETE CASCADE,
    INDEX `idx_bookings_order_code` (`order_code`),
    INDEX `idx_bookings_customer_id` (`customer_id`),
    INDEX `idx_bookings_shop_id` (`shop_id`),
    INDEX `idx_bookings_status` (`status`),
    INDEX `idx_bookings_requested_date` (`requested_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. Table: notifications
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `booking_id` INT NULL,
    `kind` VARCHAR(40) NOT NULL DEFAULT 'info',
    `title` VARCHAR(255) NOT NULL,
    `body` TEXT NOT NULL,
    `is_read` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_notifications_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE SET NULL,
    INDEX `idx_notifications_user_unread` (`user_id`, `is_read`),
    INDEX `idx_notifications_booking_id` (`booking_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
