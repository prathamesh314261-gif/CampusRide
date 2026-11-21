-- 
-- CampusRide — MySQL Schema (100% DBMS-Driven Architecture)
-- Tables: Student, Vehicle, Coupon, Rental, Payment,
--         Review, Maintenance, Insurance, Dispute, AuditLog
-- 

DROP DATABASE IF EXISTS campusride;
CREATE DATABASE campusride CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campusride;

-- TABLE 1: STUDENT
CREATE TABLE Student (
    student_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    phone         VARCHAR(15) NOT NULL,
    department    VARCHAR(50) NOT NULL,
    hostel        VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('student', 'owner', 'admin') DEFAULT 'student',
    roll_number   VARCHAR(50),
    bio           TEXT,
    trust_score   DECIMAL(3,1) DEFAULT 5.0,
    is_verified   BOOLEAN DEFAULT TRUE,
    account_status ENUM('Active', 'Suspended', 'Locked') DEFAULT 'Active',
    failed_attempts INT DEFAULT 0,
    locked_until  DATETIME DEFAULT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
);

-- TABLE 2: VEHICLE
CREATE TABLE Vehicle (
    vehicle_id         INT AUTO_INCREMENT PRIMARY KEY,
    owner_id           INT NOT NULL,
    vehicle_type       VARCHAR(30) NOT NULL,
    brand              VARCHAR(50) NOT NULL,
    model              VARCHAR(50) NOT NULL,
    seating_capacity   INT NOT NULL DEFAULT 2,
    fuel_type          ENUM('Petrol', 'Diesel', 'Electric') NOT NULL,
    hourly_rate        DECIMAL(10,2) NOT NULL CHECK (hourly_rate > 0),
    availability_status ENUM('Available', 'Rented', 'Maintenance') DEFAULT 'Available',
    license_plate      VARCHAR(20) UNIQUE NOT NULL,
    location           VARCHAR(100) DEFAULT 'Campus Main Gate',
    description        TEXT,
    avg_rating         DECIMAL(3,1) DEFAULT 0.0,
    total_reviews      INT DEFAULT 0,
    is_approved        BOOLEAN DEFAULT TRUE,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    INDEX idx_vehicle_owner  (owner_id),
    INDEX idx_vehicle_status (availability_status)
);

-- TABLE 3: COUPON
CREATE TABLE Coupon (
    coupon_id           INT AUTO_INCREMENT PRIMARY KEY,
    code                VARCHAR(20) UNIQUE NOT NULL,
    discount_percentage DECIMAL(5,2) NOT NULL CHECK (discount_percentage BETWEEN 1 AND 100),
    valid_from          DATE NOT NULL,
    valid_to            DATE NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE 4: RENTAL
CREATE TABLE Rental (
    rental_id       INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    vehicle_id      INT NOT NULL,
    start_time      DATETIME NOT NULL,
    end_time        DATETIME NOT NULL,
    pickup_location VARCHAR(100) NOT NULL,
    return_location VARCHAR(100) NOT NULL,
    total_hours     DECIMAL(10,2) NOT NULL,
    subtotal        DECIMAL(10,2) NOT NULL,
    discount        DECIMAL(10,2) DEFAULT 0.00,
    final_amount    DECIMAL(10,2) NOT NULL,
    coupon_id       INT DEFAULT NULL,
    status          ENUM('Confirmed','Active','Completed','Cancelled') DEFAULT 'Confirmed',
    cancel_reason   TEXT,
    pickup_code     VARCHAR(10),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE RESTRICT,
    FOREIGN KEY (coupon_id) REFERENCES Coupon(coupon_id) ON DELETE SET NULL,
    INDEX idx_rental_student (student_id),
    INDEX idx_rental_vehicle (vehicle_id),
    INDEX idx_rental_status  (status)
);

-- TABLE 5: PAYMENT
CREATE TABLE Payment (
    payment_id      INT AUTO_INCREMENT PRIMARY KEY,
    rental_id       INT UNIQUE NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    payment_method  ENUM('UPI', 'Card', 'Cash') NOT NULL,
    payment_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status  ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Pending',
    transaction_id  VARCHAR(50) UNIQUE NOT NULL,
    refund_amount   DECIMAL(10,2) DEFAULT 0.00,
    refund_date     DATETIME DEFAULT NULL,
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id) ON DELETE CASCADE,
    INDEX idx_payment_rental (rental_id)
);

-- TABLE 6: REVIEW
CREATE TABLE Review (
    review_id   INT AUTO_INCREMENT PRIMARY KEY,
    rental_id   INT NOT NULL,
    reviewer_id INT NOT NULL,
    vehicle_id  INT NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rental_id)   REFERENCES Rental(rental_id)  ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id)  REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE
);

-- TABLE 7: MAINTENANCE
CREATE TABLE Maintenance (
    maintenance_id   INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id       INT NOT NULL,
    maintenance_type VARCHAR(50) NOT NULL,
    description      TEXT,
    cost             DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    maintenance_date DATE NOT NULL,
    status           ENUM('Scheduled', 'Done') DEFAULT 'Scheduled',
    reported_by      INT DEFAULT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id)   REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by)  REFERENCES Student(student_id) ON DELETE SET NULL,
    INDEX idx_maintenance_vehicle (vehicle_id)
);

-- TABLE 8: INSURANCE
CREATE TABLE Insurance (
    insurance_id    INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id      INT NOT NULL,
    provider        VARCHAR(100) NOT NULL,
    policy_number   VARCHAR(50) UNIQUE NOT NULL,
    coverage_amount DECIMAL(12,2) NOT NULL,
    valid_from      DATE NOT NULL,
    valid_to        DATE NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id) ON DELETE CASCADE,
    INDEX idx_insurance_vehicle (vehicle_id)
);

-- TABLE 9: DISPUTE
CREATE TABLE Dispute (
    dispute_id  INT AUTO_INCREMENT PRIMARY KEY,
    rental_id   INT NOT NULL,
    raised_by   INT NOT NULL,
    issue_type  VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status      ENUM('Open', 'InReview', 'Resolved') DEFAULT 'Open',
    resolution  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME DEFAULT NULL,
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id) ON DELETE CASCADE,
    FOREIGN KEY (raised_by) REFERENCES Student(student_id) ON DELETE CASCADE
);

-- TABLE 10: AUDIT LOG
CREATE TABLE AuditLog (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT DEFAULT NULL,
    action     VARCHAR(50) NOT NULL,
    details    TEXT,
    ip_address VARCHAR(45) DEFAULT '127.0.0.1',
    timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE SET NULL,
    INDEX idx_auditlog_student (student_id),
    INDEX idx_auditlog_action  (action),
    INDEX idx_auditlog_ts      (timestamp)
);

SELECT 'Schema created: 10 tables with constraints and indexes!' AS result;
