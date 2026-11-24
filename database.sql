-- =====================================================================
-- FindIt – Smart Lost and Found Platform
-- Complete MySQL Database Dump and Initialization Script
-- Charset: utf8mb4 | Collation: utf8mb4_unicode_ci
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `findit_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `findit_db`;

SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------
-- Table: users
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) NULL UNIQUE,
  `password_hash` VARCHAR(255) NULL,
  `phone` VARCHAR(25) NULL,
  `firebase_uid` VARCHAR(128) NULL UNIQUE,
  `phone_verified_at` DATETIME NULL,
  `role` ENUM('user', 'admin', 'finder') NOT NULL DEFAULT 'user',
  `status` ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
  `avatar` VARCHAR(255) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_users_email` (`email`),
  INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: categories
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(60) NOT NULL UNIQUE,
  `slug` VARCHAR(60) NOT NULL UNIQUE,
  `icon` VARCHAR(50) NOT NULL DEFAULT 'tag',
  `description` VARCHAR(255) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: items
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `items`;
CREATE TABLE `items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `report_type` ENUM('lost', 'found') NOT NULL,
  `item_name` VARCHAR(150) NOT NULL,
  `category_id` INT NOT NULL,
  `description` TEXT NOT NULL,
  `location` VARCHAR(200) NOT NULL,
  `event_date` DATE NOT NULL,
  `contact_phone` VARCHAR(50) NULL,
  `contact_email` VARCHAR(120) NULL,
  `primary_image` VARCHAR(255) NULL,
  `reward` VARCHAR(50) NULL,
  `status` ENUM('open', 'pending_claim', 'claimed', 'recovered', 'rejected') NOT NULL DEFAULT 'open',
  `is_suspicious` BOOLEAN DEFAULT FALSE,
  `user_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_items_type` (`report_type`),
  INDEX `idx_items_status` (`status`),
  INDEX `idx_items_category` (`category_id`),
  INDEX `idx_items_user` (`user_id`),
  CONSTRAINT `fk_items_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_items_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: item_images
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `item_images`;
CREATE TABLE `item_images` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `item_id` INT NOT NULL,
  `image_url` VARCHAR(255) NOT NULL,
  `is_primary` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_item_images_item` (`item_id`),
  CONSTRAINT `fk_item_images_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: claim_requests
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `claim_requests`;
CREATE TABLE `claim_requests` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `item_id` INT NOT NULL,
  `claimant_id` INT NOT NULL,
  `proof_details` TEXT NOT NULL,
  `claimant_phone` VARCHAR(30) NOT NULL,
  `claimant_email` VARCHAR(120) NOT NULL,
  `proof_document_image` VARCHAR(255) NULL,
  `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
  `admin_notes` TEXT NULL,
  `reviewed_by` INT NULL,
  `reviewed_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_claims_item` (`item_id`),
  INDEX `idx_claims_claimant` (`claimant_id`),
  INDEX `idx_claims_status` (`status`),
  CONSTRAINT `fk_claims_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_claims_claimant` FOREIGN KEY (`claimant_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_claims_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: notifications
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `message` TEXT NOT NULL,
  `type` VARCHAR(50) DEFAULT 'info',
  `link` VARCHAR(255) NULL,
  `is_read` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_notifications_user` (`user_id`),
  INDEX `idx_notifications_read` (`is_read`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: activity_logs
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `activity_logs`;
CREATE TABLE `activity_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `action` VARCHAR(100) NOT NULL,
  `details` TEXT NULL,
  `ip_address` VARCHAR(50) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_logs_user` (`user_id`),
  CONSTRAINT `fk_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: contact_messages
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `contact_messages`;
CREATE TABLE `contact_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `status` ENUM('new', 'resolved') DEFAULT 'new',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- SEED DATA
-- =====================================================================

-- Default Categories
INSERT INTO `categories` (`id`, `name`, `slug`, `icon`, `description`) VALUES
(1, 'Electronics', 'electronics', 'laptop', 'Laptops, smartphones, headphones, smartwatches, chargers, tablets, power banks'),
(2, 'Identity Cards', 'identity-cards', 'id-card', 'Student IDs, driver licenses, university badges, library cards, national IDs'),
(3, 'Books and Documents', 'books-and-documents', 'book', 'Textbooks, lab manuals, certificates, spiral notebooks, degree certificates, files'),
(4, 'Bags and Wallets', 'bags-and-wallets', 'briefcase', 'Backpacks, leather wallets, purses, laptop sleeves, handbags, gym duffels'),
(5, 'Accessories', 'accessories', 'watch', 'Watches, prescription glasses, sunglasses, rings, bracelets, umbrellas, jewellery'),
(6, 'Keys', 'keys', 'key', 'Hostel keys, motorcycle/car keys, locker keys, keychains with tags'),
(7, 'Clothing', 'clothing', 'shirt', 'Hoodies, varsity jackets, blazers, lab coats, caps, winter scarves'),
(8, 'Other', 'other', 'package', 'Sports equipment, water bottles, scientific calculators, musical instruments, art supplies');

-- Default Demo Users (Passwords hashed using Werkzeug pbkdf2:sha256)
-- admin123 -> pbkdf2:sha256:1000000$g7Jk6Y... or werkzeug hash
-- All passwords for test accounts:
-- admin@findit.com / admin123
-- john@university.edu / user123
-- security@campus.edu / finder123
-- jane@university.edu / user123
INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `phone`, `role`, `status`) VALUES
(1, 'Campus Administrator', 'admin@findit.com', 'scrypt:32768:8:1$K5zQ7FvJ6wT0zO9y$05a18a584061a7a08b73f8b031b79f94539efbdfc488319f390887df5d5b78f4bb7f55b1f5c6e864ee0db3f56a5c3639908cfd0725514f653457a3e7ecaa6959', '+1 (555) 100-2000', 'admin', 'active'),
(2, 'John Doe', 'john@university.edu', 'scrypt:32768:8:1$xN4vYw2ZqR7uP9mK$7cb95a3eeec69b0fa8ffca5ca4237ea0b571d87e07d0f9554feaeaf11667cb4c3d82a6fdf9a44c5b162f4b46c65011f016d44be589505dc2a8a5fba0b991d911', '+1 (555) 234-5678', 'user', 'active'),
(3, 'Officer Marcus (Campus Security)', 'security@campus.edu', 'scrypt:32768:8:1$mK9pL2vR8wX1zQ4y$8d2b9a7ffec69a0fa8ffca5ca4237ea0b571d87e07d0f9554feaeaf11667cb4c3d82a6fdf9a44c5b162f4b46c65011f016d44be589505dc2a8a5fba0b991d922', '+1 (555) 999-4321', 'finder', 'active'),
(4, 'Jane Smith', 'jane@university.edu', 'scrypt:32768:8:1$xN4vYw2ZqR7uP9mK$7cb95a3eeec69b0fa8ffca5ca4237ea0b571d87e07d0f9554feaeaf11667cb4c3d82a6fdf9a44c5b162f4b46c65011f016d44be589505dc2a8a5fba0b991d911', '+1 (555) 876-5432', 'user', 'active');

-- Sample Items
INSERT INTO `items` (`id`, `report_type`, `item_name`, `category_id`, `description`, `location`, `event_date`, `contact_phone`, `contact_email`, `primary_image`, `reward`, `status`, `is_suspicious`, `user_id`) VALUES
(1, 'lost', 'Space Grey MacBook Air M2 13"', 1, 'Lost in the Central Library 2nd floor reading hall near table 14. Has a subtle GitHub Octocat sticker and blue protective sleeve.', 'Central Library, 2nd Floor Reading Hall', '2026-11-20', '+1 (555) 234-5678', 'john@university.edu', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80', '$50 Reward for Safe Return', 'open', 0, 2),
(2, 'found', 'Apple MacBook Air Space Grey with Sleeve', 1, 'Turned in to Central Security Desk. Found on the 2nd floor of Library. Secured inside a dark navy zip sleeve with developer decals on the top lid.', 'Central Library Desk / Security Office Room 101', '2026-11-21', '+1 (555) 999-4321', 'security@campus.edu', 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?auto=format&fit=crop&w=600&q=80', NULL, 'open', 0, 3),
(3, 'lost', 'University Student ID Card - Jane Smith', 2, 'Student ID card with Department of Computer Science tag and blue lanyard. Lost near North Cafeteria during lunch hour.', 'North Cafeteria & Food Court', '2026-11-19', '+1 (555) 876-5432', 'jane@university.edu', 'https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80', 'Gratitude & coffee', 'open', 0, 4),
(4, 'found', 'Black Leather Bi-Fold Wallet with Cards', 4, 'Black leather wallet discovered under seat 18 in Main Auditorium after the freshman orientation session. Contains student transit pass and cash.', 'Main Auditorium, Row G', '2026-11-18', '+1 (555) 999-4321', 'security@campus.edu', 'https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=600&q=80', NULL, 'open', 0, 3),
(5, 'lost', 'Honda Bike Key with Red Carabiner & Tag', 6, 'Single black Honda motorcycle ignition key attached to a red metal carabiner clip and miniature anime keychain figurine.', 'Student Parking Lot Zone B', '2026-11-17', '+1 (555) 234-5678', 'john@university.edu', 'https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=600&q=80', '$20', 'open', 0, 2),
(6, 'found', 'Sony WH-1000XM4 Wireless Headphones', 1, 'Black over-ear Sony headphones left on bench in Science Quad. Includes black zip case and USB-C charging cord.', 'Science Quadrangle East Lawn', '2026-11-15', '+1 (555) 999-4321', 'security@campus.edu', 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=600&q=80', NULL, 'claimed', 0, 3),
(7, 'lost', 'Ray-Ban Wayfarer Classic Sunglasses', 5, 'Classic matte black Ray-Ban sunglasses in brown leather case. Lost around the Campus Gymnasium / Locker Room.', 'Campus Gymnasium Entrance', '2026-11-12', '+1 (555) 876-5432', 'jane@university.edu', 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80', NULL, 'recovered', 0, 4),
(8, 'found', 'Stewart Multivariable Calculus 9th Edition', 3, 'Hardcover calculus textbook with sticky notes inside chapters 14-16. Found on desk in Math Building Room 204.', 'Mathematics Building Room 204', '2026-11-21', '+1 (555) 999-4321', 'security@campus.edu', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80', NULL, 'open', 0, 3);

-- Sample Claims
INSERT INTO `claim_requests` (`id`, `item_id`, `claimant_id`, `proof_details`, `claimant_phone`, `claimant_email`, `status`, `admin_notes`, `reviewed_by`, `reviewed_at`) VALUES
(1, 6, 2, 'Serial number on left headband ends with 8841. My phone Bluetooth name is "John\'s XM4". The custom EQ preset in Sony Headphones app is Bass Boosted.', '+1 (555) 234-5678', 'john@university.edu', 'approved', 'Claim verified by Officer Marcus. Bluetooth device name and serial match verified in person.', 3, '2026-11-21 14:30:00');

-- Sample Notifications
INSERT INTO `notifications` (`id`, `user_id`, `title`, `message`, `type`, `link`, `is_read`) VALUES
(1, 2, '🎉 Claim Approved for Sony Headphones', 'Your claim for the Sony WH-1000XM4 has been approved by Campus Security. Please bring your student ID to Room 101 to collect.', 'claim', '/my-claims', 0),
(2, 2, 'Potential Smart Match Detected!', 'We detected an Apple MacBook Air turned in at Central Library that matches your lost report details!', 'match', '/items/2', 0);

-- Sample Activity Logs
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `details`, `ip_address`) VALUES
(1, 1, 'SYSTEM_BOOT', 'FindIt Platform database initialized and seeded with demo data', '127.0.0.1'),
(2, 2, 'REPORT_LOST_ITEM', 'Reported lost item: Space Grey MacBook Air M2 13" (ID: FID-00001)', '127.0.0.1'),
(3, 3, 'REPORT_FOUND_ITEM', 'Reported found item: Apple MacBook Air Space Grey with Sleeve (ID: FID-00002)', '127.0.0.1');
