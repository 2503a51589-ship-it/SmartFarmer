-- ==========================================================
-- SIH26032: Smart Farmer Procurement & Queue System Database
-- Target Database: MySQL 8.0+
-- ==========================================================

CREATE DATABASE IF NOT EXISTS smart_farmer_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_farmer_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('farmer', 'operator', 'admin') NOT NULL DEFAULT 'farmer',
    email VARCHAR(120),
    phone VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_role (role),
    INDEX idx_user_username (username)
) ENGINE=InnoDB;

-- 2. Procurement Centers Table
CREATE TABLE IF NOT EXISTS procurement_centers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    center_name VARCHAR(150) NOT NULL,
    center_code VARCHAR(30) NOT NULL UNIQUE,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Gujarat',
    address TEXT NOT NULL,
    contact_phone VARCHAR(20),
    total_counters INT NOT NULL DEFAULT 3,
    avg_processing_time_mins INT NOT NULL DEFAULT 15,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_center_district (district)
) ENGINE=InnoDB;

-- 3. Farmers Table
CREATE TABLE IF NOT EXISTS farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    farmer_uid VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    village VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Gujarat',
    land_size_acres DECIMAL(6,2) DEFAULT 0.00,
    bank_account_no VARCHAR(50),
    ifsc_code VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_farmer_district (district)
) ENGINE=InnoDB;

-- 4. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Agriculture & Food Procurement Dept',
    designation VARCHAR(100) DEFAULT 'District Procurement Officer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Operators Table
CREATE TABLE IF NOT EXISTS operators (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    center_id INT NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    badge_id VARCHAR(50) NOT NULL UNIQUE,
    assigned_counter INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 6. Crops Table
CREATE TABLE IF NOT EXISTS crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL DEFAULT 'Cereal',
    msp_per_quintal DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL DEFAULT 'Quintal',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 7. Slots Table
CREATE TABLE IF NOT EXISTS slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    center_id INT NOT NULL,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    max_capacity INT NOT NULL DEFAULT 20,
    booked_count INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE CASCADE,
    UNIQUE KEY uq_center_date_time (center_id, slot_date, start_time, end_time),
    INDEX idx_slot_date (slot_date)
) ENGINE=InnoDB;

-- 8. Bookings Table
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_ref VARCHAR(50) NOT NULL UNIQUE,
    farmer_id INT NOT NULL,
    center_id INT NOT NULL,
    slot_id INT NOT NULL,
    crop_id INT NOT NULL,
    crop_quantity DECIMAL(8,2) NOT NULL,
    harvest_date DATE NOT NULL,
    token_number VARCHAR(30) NOT NULL,
    queue_number INT NOT NULL DEFAULT 1,
    status ENUM('Booked', 'Arrived', 'Weighing', 'Quality Checking', 'Accepted', 'Rejected', 'Procurement Completed', 'Cancelled') NOT NULL DEFAULT 'Booked',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE RESTRICT,
    FOREIGN KEY (slot_id) REFERENCES slots(id) ON DELETE RESTRICT,
    FOREIGN KEY (crop_id) REFERENCES crops(id) ON DELETE RESTRICT,
    INDEX idx_booking_token (token_number),
    INDEX idx_booking_status (status)
) ENGINE=InnoDB;

-- 9. Queue Table
CREATE TABLE IF NOT EXISTS queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    center_id INT NOT NULL,
    booking_id INT NOT NULL UNIQUE,
    queue_date DATE NOT NULL,
    token_number VARCHAR(30) NOT NULL,
    position INT NOT NULL,
    status ENUM('Waiting', 'Calling', 'In-Process', 'Completed', 'Skipped', 'Cancelled') NOT NULL DEFAULT 'Waiting',
    counter_assigned INT DEFAULT 1,
    arrival_time DATETIME NULL,
    called_time DATETIME NULL,
    completed_time DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    INDEX idx_queue_center_date (center_id, queue_date, status)
) ENGINE=InnoDB;

-- 10. Procurement Records Table
CREATE TABLE IF NOT EXISTS procurement_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    operator_id INT NOT NULL,
    center_id INT NOT NULL,
    actual_quantity DECIMAL(8,2) NOT NULL,
    moisture_content DECIMAL(4,2) DEFAULT 12.00,
    quality_grade ENUM('Grade A', 'Grade B', 'Grade C', 'Sub-standard') NOT NULL DEFAULT 'Grade A',
    deduction_percentage DECIMAL(5,2) DEFAULT 0.00,
    final_accepted_quantity DECIMAL(8,2) NOT NULL,
    rejection_reason TEXT NULL,
    remarks TEXT,
    status ENUM('Accepted', 'Rejected', 'Verified') NOT NULL DEFAULT 'Verified',
    verified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES operators(id) ON DELETE RESTRICT,
    FOREIGN KEY (center_id) REFERENCES procurement_centers(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 11. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    procurement_id INT NOT NULL UNIQUE,
    booking_id INT NOT NULL UNIQUE,
    farmer_id INT NOT NULL,
    msp_rate DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    payment_status ENUM('Pending', 'Processing', 'Credited', 'Failed') NOT NULL DEFAULT 'Pending',
    transaction_ref VARCHAR(100) NULL UNIQUE,
    payment_date DATETIME NULL,
    bank_status VARCHAR(100) DEFAULT 'Payment Initiated under Govt DBT Scheme',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (procurement_id) REFERENCES procurement_records(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    INDEX idx_payment_status (payment_status)
) ENGINE=InnoDB;
