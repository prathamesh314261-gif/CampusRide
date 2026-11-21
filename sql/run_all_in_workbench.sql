-- ============================================================
-- SOURCE: schema.sql
-- ============================================================
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


-- ============================================================
-- SOURCE: views.sql
-- ============================================================
-- CampusRide - MySQL Views (Fixed)
USE campusride;

-- VIEW 1: Available Vehicles with Owner Details
CREATE OR REPLACE VIEW vw_available_vehicles AS
SELECT
    v.vehicle_id, v.vehicle_type, v.brand, v.model,
    v.seating_capacity, v.fuel_type, v.hourly_rate,
    v.license_plate, v.location, v.description,
    v.availability_status, v.avg_rating, v.total_reviews,
    s.student_id AS owner_id,
    s.full_name AS owner_name,
    s.phone AS owner_phone
FROM Vehicle v
JOIN Student s ON v.owner_id = s.student_id
WHERE v.availability_status = 'Available';


-- VIEW 2: Rental History (includes student_id + vehicle_id for API filtering)
CREATE OR REPLACE VIEW vw_rental_history AS
SELECT
    r.rental_id,
    r.student_id,
    r.vehicle_id,
    s.full_name AS student_name,
    s.phone AS student_phone,
    v.vehicle_type,
    CONCAT(v.brand, ' ', v.model) AS vehicle_name,
    v.brand,
    v.model,
    v.license_plate,
    r.start_time,
    r.end_time,
    r.total_hours,
    r.subtotal,
    r.discount,
    r.final_amount,
    r.status,
    r.cancel_reason,
    r.pickup_code,
    r.created_at,
    c.code AS coupon_code
FROM Rental r
JOIN Student s ON r.student_id = s.student_id
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
LEFT JOIN Coupon c ON r.coupon_id = c.coupon_id;


-- VIEW 3: Payment History with Status
CREATE OR REPLACE VIEW vw_payment_history AS
SELECT
    p.payment_id, p.transaction_id, p.amount,
    p.payment_method, p.payment_status, p.payment_date,
    r.rental_id, r.student_id,
    s.full_name AS student_name,
    CONCAT(v.brand, ' ', v.model) AS vehicle_name,
    v.vehicle_type,
    v.license_plate
FROM Payment p
JOIN Rental r ON p.rental_id = r.rental_id
JOIN Student s ON r.student_id = s.student_id
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id;



-- VIEW 4: Owner Earnings
CREATE OR REPLACE VIEW vw_owner_earnings AS
SELECT
    s.student_id AS owner_id,
    s.full_name AS owner_name,
    COUNT(r.rental_id) AS total_rentals,
    COALESCE(SUM(r.final_amount), 0) AS total_earnings,
    COALESCE(AVG(r.final_amount), 0) AS avg_earning
FROM Student s
LEFT JOIN Vehicle v ON s.student_id = v.owner_id
LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id
WHERE r.status = 'Completed' OR r.status IS NULL
GROUP BY s.student_id, s.full_name;


-- VIEW 5: Active Maintenance
CREATE OR REPLACE VIEW vw_active_maintenance AS
SELECT
    m.maintenance_id, v.license_plate, v.brand, v.model,
    m.maintenance_type, m.description, m.cost,
    m.maintenance_date, m.status
FROM Maintenance m
JOIN Vehicle v ON m.vehicle_id = v.vehicle_id
WHERE m.status = 'Scheduled';


-- VIEW 6: Insurance Status (Valid vs Expired)
CREATE OR REPLACE VIEW vw_insurance_status AS
SELECT
    i.insurance_id, v.license_plate, v.brand, v.model,
    i.provider, i.policy_number, i.coverage_amount,
    i.valid_from, i.valid_to,
    CASE WHEN i.valid_to >= CURDATE() THEN 'Active' ELSE 'Expired' END AS insurance_status,
    DATEDIFF(i.valid_to, CURDATE()) AS days_remaining
FROM Insurance i
JOIN Vehicle v ON i.vehicle_id = v.vehicle_id;


SELECT 'All 6 Views Created Successfully!' AS result;


-- ============================================================
-- SOURCE: procedures.sql
-- ============================================================
-- 
-- CampusRide — MySQL Stored Procedures & Functions
-- 7 Functions + 10 Stored Procedures (100% DBMS Logic)
-- 

USE campusride;
SET GLOBAL log_bin_trust_function_creators = 1;

-- 
-- FUNCTION 1: Calculate total hours between two timestamps
-- 
DROP FUNCTION IF EXISTS fn_total_hours;
DELIMITER //
CREATE FUNCTION fn_total_hours(p_start DATETIME, p_end DATETIME)
RETURNS DECIMAL(10,2) DETERMINISTIC NO SQL
BEGIN
    RETURN TIMESTAMPDIFF(MINUTE, p_start, p_end) / 60.0;
END //
DELIMITER ;

-- 
-- FUNCTION 2: Calculate rental cost (hours * hourly_rate)
-- 
DROP FUNCTION IF EXISTS fn_calculate_rental_cost;
DELIMITER //
CREATE FUNCTION fn_calculate_rental_cost(p_vehicle_id INT, p_hours DECIMAL(10,2))
RETURNS DECIMAL(10,2) DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_rate DECIMAL(10,2) DEFAULT 0;
    SELECT hourly_rate INTO v_rate FROM Vehicle WHERE vehicle_id = p_vehicle_id;
    RETURN ROUND(v_rate * p_hours, 2);
END //
DELIMITER ;

-- 
-- FUNCTION 3: Calculate discount amount from coupon
-- 
DROP FUNCTION IF EXISTS fn_calculate_discount;
DELIMITER //
CREATE FUNCTION fn_calculate_discount(p_subtotal DECIMAL(10,2), p_coupon_code VARCHAR(20))
RETURNS DECIMAL(10,2) DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_discount_pct DECIMAL(5,2) DEFAULT 0;
    IF p_coupon_code IS NOT NULL AND p_coupon_code != '' THEN
        SELECT discount_percentage INTO v_discount_pct
        FROM Coupon
        WHERE code = p_coupon_code
          AND is_active = TRUE
          AND valid_from <= CURDATE()
          AND valid_to >= CURDATE()
        LIMIT 1;
    END IF;
    RETURN ROUND(p_subtotal * v_discount_pct / 100, 2);
END //
DELIMITER ;

-- 
-- FUNCTION 4: Hash password using SHA2-256
-- 
DROP FUNCTION IF EXISTS fn_hash_password;
DELIMITER //
CREATE FUNCTION fn_hash_password(p_password VARCHAR(255))
RETURNS VARCHAR(255) DETERMINISTIC NO SQL
BEGIN
    -- Salt prefix 'vitcampus' must match how passwords are stored in sample_data.sql
    RETURN SHA2(CONCAT('vitcampus', p_password), 256);
END //
DELIMITER ;

-- 
-- FUNCTION 5: Check vehicle availability
-- 
DROP FUNCTION IF EXISTS fn_is_vehicle_available;
DELIMITER //
CREATE FUNCTION fn_is_vehicle_available(p_vehicle_id INT)
RETURNS BOOLEAN DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_status VARCHAR(30);
    SELECT availability_status INTO v_status FROM Vehicle WHERE vehicle_id = p_vehicle_id;
    RETURN v_status = 'Available';
END //
DELIMITER ;

-- 
-- FUNCTION 6: Generate unique transaction ID
-- 
DROP FUNCTION IF EXISTS fn_generate_txn_id;
DELIMITER //
CREATE FUNCTION fn_generate_txn_id()
RETURNS VARCHAR(50) NOT DETERMINISTIC NO SQL
BEGIN
    RETURN CONCAT('TXN', UNIX_TIMESTAMP(), LPAD(FLOOR(RAND()*99999), 5, '0'));
END //
DELIMITER ;

-- 
-- FUNCTION 7: Get total rental count for a student
-- 
DROP FUNCTION IF EXISTS fn_get_rental_count;
DELIMITER //
CREATE FUNCTION fn_get_rental_count(p_student_id INT)
RETURNS INT DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE v_count INT DEFAULT 0;
    SELECT COUNT(*) INTO v_count FROM Rental
    WHERE student_id = p_student_id AND status = 'Completed';
    RETURN v_count;
END //
DELIMITER ;


-- 
-- PROCEDURE 1: REGISTER Student
-- 
DROP PROCEDURE IF EXISTS sp_register;
DELIMITER //
CREATE PROCEDURE sp_register(
    IN  p_name       VARCHAR(100),
    IN  p_email      VARCHAR(100),
    IN  p_phone      VARCHAR(15),
    IN  p_dept       VARCHAR(50),
    IN  p_hostel     VARCHAR(50),
    IN  p_password   VARCHAR(255),
    IN  p_roll       VARCHAR(50),
    OUT p_status     VARCHAR(20)
)
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; SET p_status = 'ERROR'; END;

    SELECT COUNT(*) INTO v_exists FROM Student WHERE email = p_email;
    IF v_exists > 0 THEN
        SET p_status = 'DUPLICATE_EMAIL';
    ELSE
        START TRANSACTION;
        INSERT INTO Student (full_name, email, phone, department, hostel, password_hash, roll_number)
        VALUES (p_name, p_email, p_phone, p_dept, p_hostel, fn_hash_password(p_password), p_roll);
        COMMIT;
        SET p_status = 'OK';
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 2: LOGIN with brute-force protection
-- 
DROP PROCEDURE IF EXISTS sp_login;
DELIMITER //
CREATE PROCEDURE sp_login(
    IN  p_email    VARCHAR(100),
    IN  p_password VARCHAR(255),
    OUT p_status   VARCHAR(20)
)
BEGIN
    DECLARE v_id         INT;
    DECLARE v_hash       VARCHAR(255);
    DECLARE v_acct       VARCHAR(20);
    DECLARE v_locked     DATETIME;
    DECLARE v_attempts   INT;

    SELECT student_id, password_hash, account_status, locked_until, failed_attempts
    INTO v_id, v_hash, v_acct, v_locked, v_attempts
    FROM Student WHERE email = p_email LIMIT 1;

    IF v_id IS NULL THEN
        SET p_status = 'NOT_FOUND';
    ELSEIF v_acct = 'Suspended' THEN
        SET p_status = 'SUSPENDED';
    ELSEIF v_acct = 'Locked' AND v_locked > NOW() THEN
        SET p_status = 'LOCKED';
    ELSEIF v_hash != fn_hash_password(p_password) THEN
        -- Increment failed attempts
        UPDATE Student SET failed_attempts = failed_attempts + 1 WHERE student_id = v_id;
        IF v_attempts + 1 >= 5 THEN
            UPDATE Student SET account_status = 'Locked', locked_until = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE student_id = v_id;
        END IF;
        SET p_status = 'BAD_PASSWORD';
    ELSE
        -- Reset on success
        UPDATE Student SET failed_attempts = 0, locked_until = NULL,
                           account_status = IF(account_status='Locked','Active',account_status)
        WHERE student_id = v_id;
        INSERT INTO AuditLog (student_id, action, details) VALUES (v_id, 'LOGIN', CONCAT('Login: ', p_email));
        SET p_status = 'OK';
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 3: CREATE RENTAL (Booking with coupon + transaction)
-- 
DROP PROCEDURE IF EXISTS sp_create_rental;
DELIMITER //
CREATE PROCEDURE sp_create_rental(
    IN  p_student_id     INT,
    IN  p_vehicle_id     INT,
    IN  p_start_time     DATETIME,
    IN  p_end_time       DATETIME,
    IN  p_pickup_location VARCHAR(100),
    IN  p_return_location VARCHAR(100),
    IN  p_coupon_code    VARCHAR(20),
    OUT p_status         VARCHAR(20)
)
BEGIN
    DECLARE v_hours      DECIMAL(10,2);
    DECLARE v_subtotal   DECIMAL(10,2);
    DECLARE v_discount   DECIMAL(10,2);
    DECLARE v_final      DECIMAL(10,2);
    DECLARE v_coupon_id  INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; SET p_status = 'ERROR'; END;

    IF NOT fn_is_vehicle_available(p_vehicle_id) THEN
        SET p_status = 'NOT_AVAILABLE';
    ELSE
        START TRANSACTION;
        SET v_hours    = fn_total_hours(p_start_time, p_end_time);
        SET v_subtotal = fn_calculate_rental_cost(p_vehicle_id, v_hours);
        SET v_discount = fn_calculate_discount(v_subtotal, p_coupon_code);
        SET v_final    = v_subtotal - v_discount;

        IF p_coupon_code IS NOT NULL AND p_coupon_code != '' THEN
            SELECT coupon_id INTO v_coupon_id FROM Coupon WHERE code = p_coupon_code LIMIT 1;
        END IF;

        INSERT INTO Rental (student_id, vehicle_id, start_time, end_time,
                            pickup_location, return_location, total_hours,
                            subtotal, discount, final_amount, coupon_id, status)
        VALUES (p_student_id, p_vehicle_id, p_start_time, p_end_time,
                p_pickup_location, p_return_location, v_hours,
                v_subtotal, v_discount, v_final, v_coupon_id, 'Confirmed');
        COMMIT;
        SET p_status = 'OK';
        SELECT * FROM Rental WHERE rental_id = LAST_INSERT_ID();
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 4: COMPLETE RENTAL
-- 
DROP PROCEDURE IF EXISTS sp_complete_rental;
DELIMITER //
CREATE PROCEDURE sp_complete_rental(
    IN  p_rental_id INT,
    OUT p_status    VARCHAR(20)
)
BEGIN
    DECLARE v_current_status VARCHAR(30);
    SELECT status INTO v_current_status FROM Rental WHERE rental_id = p_rental_id;
    IF v_current_status IN ('Completed', 'Cancelled') THEN
        SET p_status = 'ALREADY_DONE';
    ELSE
        UPDATE Rental SET status = 'Completed' WHERE rental_id = p_rental_id;
        SET p_status = 'OK';
        SELECT * FROM Rental WHERE rental_id = p_rental_id;
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 5: CANCEL RENTAL
-- 
DROP PROCEDURE IF EXISTS sp_cancel_rental;
DELIMITER //
CREATE PROCEDURE sp_cancel_rental(
    IN  p_rental_id  INT,
    IN  p_student_id INT,
    IN  p_reason     TEXT,
    OUT p_status     VARCHAR(20)
)
BEGIN
    DECLARE v_owner INT;
    SELECT student_id INTO v_owner FROM Rental WHERE rental_id = p_rental_id;
    IF v_owner != p_student_id THEN
        SET p_status = 'FORBIDDEN';
    ELSE
        UPDATE Rental SET status = 'Cancelled', cancel_reason = p_reason
        WHERE rental_id = p_rental_id;
        SET p_status = 'OK';
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 6: PROCESS PAYMENT
-- 
DROP PROCEDURE IF EXISTS sp_process_payment;
DELIMITER //
CREATE PROCEDURE sp_process_payment(
    IN  p_rental_id      INT,
    IN  p_payment_method ENUM('UPI', 'Card', 'Cash'),
    OUT p_txn_id         VARCHAR(50),
    OUT p_status         VARCHAR(20)
)
BEGIN
    DECLARE v_amount  DECIMAL(10,2);
    DECLARE v_already INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; SET p_status = 'ERROR'; END;

    SELECT COUNT(*) INTO v_already FROM Payment WHERE rental_id = p_rental_id;
    IF v_already > 0 THEN
        SET p_status = 'ALREADY_PAID';
    ELSE
        SELECT final_amount INTO v_amount FROM Rental WHERE rental_id = p_rental_id;
        SET p_txn_id = fn_generate_txn_id();
        START TRANSACTION;
        INSERT INTO Payment (rental_id, amount, payment_method, payment_status, transaction_id)
        VALUES (p_rental_id, v_amount, p_payment_method, 'Completed', p_txn_id);
        UPDATE Rental SET status = 'Active' WHERE rental_id = p_rental_id AND status = 'Confirmed';
        COMMIT;
        SET p_status = 'OK';
        SELECT * FROM Payment WHERE rental_id = p_rental_id;
    END IF;
END //
DELIMITER ;

-- 
-- PROCEDURE 7: ADD VEHICLE
-- 
DROP PROCEDURE IF EXISTS sp_add_vehicle;
DELIMITER //
CREATE PROCEDURE sp_add_vehicle(
    IN  p_owner_id    INT,
    IN  p_type        VARCHAR(30),
    IN  p_brand       VARCHAR(50),
    IN  p_model       VARCHAR(50),
    IN  p_seats       INT,
    IN  p_fuel        ENUM('Petrol', 'Diesel', 'Electric'),
    IN  p_rate        DECIMAL(10,2),
    IN  p_plate       VARCHAR(20),
    IN  p_location    VARCHAR(100),
    IN  p_description TEXT,
    OUT p_status      VARCHAR(20)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN SET p_status = 'ERROR_DUPLICATE_PLATE'; END;
    INSERT INTO Vehicle (owner_id, vehicle_type, brand, model, seating_capacity,
                         fuel_type, hourly_rate, availability_status, license_plate, location, description)
    VALUES (p_owner_id, p_type, p_brand, p_model, p_seats,
            p_fuel, p_rate, 'Available', p_plate, p_location, p_description);
    SET p_status = 'OK';
    SELECT * FROM Vehicle WHERE vehicle_id = LAST_INSERT_ID();
END //
DELIMITER ;

-- 
-- PROCEDURE 8: SCHEDULE MAINTENANCE
-- 
DROP PROCEDURE IF EXISTS sp_add_maintenance;
DELIMITER //
CREATE PROCEDURE sp_add_maintenance(
    IN  p_vehicle_id INT,
    IN  p_type       VARCHAR(50),
    IN  p_desc       TEXT,
    IN  p_cost       DECIMAL(10,2),
    IN  p_date       DATE,
    OUT p_status     VARCHAR(20)
)
BEGIN
    INSERT INTO Maintenance (vehicle_id, maintenance_type, description, cost, maintenance_date, status)
    VALUES (p_vehicle_id, p_type, p_desc, p_cost, p_date, 'Scheduled');
    SET p_status = 'OK';
    SELECT * FROM Maintenance WHERE maintenance_id = LAST_INSERT_ID();
END //
DELIMITER ;

-- 
-- PROCEDURE 9: VEHICLE UTILIZATION REPORT (Admin)
-- 
DROP PROCEDURE IF EXISTS sp_vehicle_utilization_report;
DELIMITER //
CREATE PROCEDURE sp_vehicle_utilization_report()
BEGIN
    SELECT
        v.vehicle_id, v.license_plate,
        CONCAT(v.brand, ' ', v.model)    AS vehicle,
        v.vehicle_type, v.availability_status,
        COUNT(r.rental_id)               AS total_rentals,
        COALESCE(SUM(r.total_hours), 0)  AS total_hours_rented,
        COALESCE(SUM(r.final_amount), 0) AS total_earnings,
        v.avg_rating
    FROM Vehicle v
    LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id AND r.status = 'Completed'
    GROUP BY v.vehicle_id
    ORDER BY total_earnings DESC;
END //
DELIMITER ;

-- 
-- PROCEDURE 10: STUDENT SPENDING REPORT
-- 
DROP PROCEDURE IF EXISTS sp_student_spending_report;
DELIMITER //
CREATE PROCEDURE sp_student_spending_report(IN p_student_id INT)
BEGIN
    SELECT
        s.full_name, s.email, s.department, s.trust_score,
        fn_get_rental_count(s.student_id)  AS total_rentals,
        COALESCE(SUM(r.total_hours), 0)    AS total_hours,
        COALESCE(SUM(r.final_amount), 0)   AS total_spent,
        COALESCE(AVG(r.final_amount), 0)   AS avg_rental_cost
    FROM Student s
    LEFT JOIN Rental r ON s.student_id = r.student_id AND r.status = 'Completed'
    WHERE s.student_id = p_student_id
    GROUP BY s.student_id;
END //
DELIMITER ;

SELECT 'All 7 Functions + 10 Stored Procedures created successfully!' AS result;


-- ============================================================
-- SOURCE: triggers.sql
-- ============================================================
-- 
-- CampusRide - MySQL Triggers
-- All business state transitions handled by the DATABASE ENGINE
-- No Python logic needed for these operations
-- 

USE campusride;

-- 
-- TRIGGER 1: When a Rental is INSERTED → Mark Vehicle as 'Rented'
-- 
DROP TRIGGER IF EXISTS trg_after_rental_insert;
DELIMITER //
CREATE TRIGGER trg_after_rental_insert
AFTER INSERT ON Rental
FOR EACH ROW
BEGIN
    -- Automatically mark the vehicle as Rented
    UPDATE Vehicle
    SET availability_status = 'Rented'
    WHERE vehicle_id = NEW.vehicle_id;

    -- Log this in AuditLog
    INSERT INTO AuditLog (student_id, action, details)
    VALUES (NEW.student_id, 'RENTAL_CREATED',
            CONCAT('Rental #', NEW.rental_id, ' created for vehicle #', NEW.vehicle_id,
                   ' | Amount: ₹', NEW.final_amount));
END //
DELIMITER ;


-- 
-- TRIGGER 2: When a Rental STATUS changes to 'Completed' or 'Cancelled'
--            → Mark Vehicle back to 'Available'
-- 
DROP TRIGGER IF EXISTS trg_after_rental_update;
DELIMITER //
CREATE TRIGGER trg_after_rental_update
AFTER UPDATE ON Rental
FOR EACH ROW
BEGIN
    -- If rental is completed or cancelled, free up the vehicle
    IF NEW.status IN ('Completed', 'Cancelled') AND OLD.status NOT IN ('Completed', 'Cancelled') THEN
        UPDATE Vehicle
        SET availability_status = 'Available'
        WHERE vehicle_id = NEW.vehicle_id;

        -- Log the status change
        INSERT INTO AuditLog (student_id, action, details)
        VALUES (NEW.student_id,
                CONCAT('RENTAL_', NEW.status),
                CONCAT('Rental #', NEW.rental_id, ' marked as ', NEW.status,
                       ' | Vehicle #', NEW.vehicle_id, ' now Available'));
    END IF;
END //
DELIMITER ;


-- 
-- TRIGGER 3: When a Payment is INSERTED → Log it
-- 
DROP TRIGGER IF EXISTS trg_after_payment_insert;
DELIMITER //
CREATE TRIGGER trg_after_payment_insert
AFTER INSERT ON Payment
FOR EACH ROW
BEGIN
    -- Log payment event in AuditLog
    INSERT INTO AuditLog (action, details)
    VALUES ('PAYMENT_COMPLETED',
            CONCAT('Payment #', NEW.payment_id, ' | Rental #', NEW.rental_id,
                   ' | TxnID: ', NEW.transaction_id,
                   ' | Amount: ₹', NEW.amount,
                   ' | Method: ', NEW.payment_method));
END //
DELIMITER ;


-- 
-- TRIGGER 4: When a new Student REGISTERS → Log the event
-- 
DROP TRIGGER IF EXISTS trg_after_student_insert;
DELIMITER //
CREATE TRIGGER trg_after_student_insert
AFTER INSERT ON Student
FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (student_id, action, details)
    VALUES (NEW.student_id, 'REGISTER',
            CONCAT('New user registered: ', NEW.email, ' | Role: ', NEW.role));
END //
DELIMITER ;


-- 
-- TRIGGER 5: When Maintenance is INSERTED → Set Vehicle to 'Maintenance'
-- 
DROP TRIGGER IF EXISTS trg_after_maintenance_insert;
DELIMITER //
CREATE TRIGGER trg_after_maintenance_insert
AFTER INSERT ON Maintenance
FOR EACH ROW
BEGIN
    IF NEW.status = 'Scheduled' THEN
        UPDATE Vehicle
        SET availability_status = 'Maintenance'
        WHERE vehicle_id = NEW.vehicle_id;

        INSERT INTO AuditLog (action, details)
        VALUES ('MAINTENANCE_SCHEDULED',
                CONCAT('Vehicle #', NEW.vehicle_id, ' scheduled for: ',
                       NEW.maintenance_type, ' on ', NEW.maintenance_date));
    END IF;
END //
DELIMITER ;


-- 
-- TRIGGER 6: When Maintenance STATUS = 'Done' → Free the Vehicle
-- 
DROP TRIGGER IF EXISTS trg_after_maintenance_done;
DELIMITER //
CREATE TRIGGER trg_after_maintenance_done
AFTER UPDATE ON Maintenance
FOR EACH ROW
BEGIN
    IF NEW.status = 'Done' AND OLD.status != 'Done' THEN
        UPDATE Vehicle
        SET availability_status = 'Available'
        WHERE vehicle_id = NEW.vehicle_id;

        INSERT INTO AuditLog (action, details)
        VALUES ('MAINTENANCE_DONE',
                CONCAT('Vehicle #', NEW.vehicle_id, ' maintenance complete. Now Available.'));
    END IF;
END //
DELIMITER ;


-- 
-- TRIGGER 7: Prevent Double-Booking (BEFORE INSERT guard)
-- 
DROP TRIGGER IF EXISTS trg_before_rental_insert;
DELIMITER //
CREATE TRIGGER trg_before_rental_insert
BEFORE INSERT ON Rental
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(30);
    SELECT availability_status INTO v_status
    FROM Vehicle WHERE vehicle_id = NEW.vehicle_id;

    IF v_status != 'Available' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Vehicle is not available for booking. Please choose another vehicle.';
    END IF;
END //
DELIMITER ;


SELECT '✅ All 7 triggers created successfully!' AS result;


-- ============================================================
-- SOURCE: sample_data.sql
-- ============================================================
-- 
-- CAMPUSRide - Restored Original Sample Data for MySQL
-- Restores original students, vehicles, coupons, maintenance & insurance
-- Passwords: 'secret123' (students/owners), 'admin123' (admin)
-- Hashed using SHA2(CONCAT('vitcampus', password), 256)
-- 

USE campusride;

SET @old_checks = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

-- Clean existing data
TRUNCATE TABLE AuditLog;
TRUNCATE TABLE Dispute;
TRUNCATE TABLE Review;
TRUNCATE TABLE Payment;
TRUNCATE TABLE Rental;
TRUNCATE TABLE Maintenance;
TRUNCATE TABLE Insurance;
TRUNCATE TABLE Coupon;
TRUNCATE TABLE Vehicle;
TRUNCATE TABLE Student;

-- 
-- 1. STUDENT DATA (Original: Prathamesh, Aisha, Rohit, Neha, Owner One, Admin)
-- 
INSERT INTO Student (student_id, full_name, email, phone, department, hostel, password_hash, role, roll_number, trust_score, account_status) VALUES
(1, 'Prathamesh Patil', 'prathamesh@campus.edu', '9876543210', 'Computer Science',        'Hostel A',    SHA2(CONCAT('vitcampus', 'secret123'), 256), 'student', 'CAMPUS202401', 4.8, 'Active'),
(2, 'Aisha Khan',       'aisha@campus.edu',      '9876543211', 'Electronics',             'Hostel B',    SHA2(CONCAT('vitcampus', 'secret123'), 256), 'student', 'CAMPUS202402', 4.6, 'Active'),
(3, 'Rohit Sharma',     'rohit@campus.edu',      '9876543212', 'Mechanical',              'Hostel C',    SHA2(CONCAT('vitcampus', 'secret123'), 256), 'student', 'CAMPUS202403', 4.5, 'Active'),
(4, 'Neha Joshi',       'neha@campus.edu',       '9876543213', 'Information Technology',   'Hostel D',    SHA2(CONCAT('vitcampus', 'secret123'), 256), 'student', 'CAMPUS202404', 4.7, 'Active'),
(5, 'Owner One',        'owner1@campus.edu',     '9876543214', 'Electronics',             'Hostel E',    SHA2(CONCAT('vitcampus', 'secret123'), 256), 'owner',   'CAMPUS202405', 4.9, 'Active'),
(6, 'Admin User',       'admin@campus.edu',      '9876543215', 'Administration',          'Admin Block', SHA2(CONCAT('vitcampus', 'admin123'), 256),  'admin',   'ADMIN-001',   10.0, 'Active'),
-- Also preserve admin@vit.edu as an alias for convenience:
(7, 'Campus Admin',     'admin@vit.edu',         '9000000001', 'Administration',          'Admin Block', SHA2(CONCAT('vitcampus', 'admin123'), 256),  'admin',   'ADMIN-002',   10.0, 'Active');

-- 
-- 2. VEHICLE DATA (Original 8 vehicles from previous dataset)
-- 
INSERT INTO Vehicle (vehicle_id, owner_id, vehicle_type, brand, model, seating_capacity, fuel_type, hourly_rate, availability_status, license_plate, location, description) VALUES
-- Owned by Owner One (student_id=5)
(1, 5, 'Scooter', 'Honda',         'Activa',      2, 'Petrol',  50.00, 'Available',   'MH02AB1234', 'Hostel E Parking', 'Well-maintained Honda Activa. Clean & reliable.'),
(2, 5, 'Scooter', 'TVS',           'Jupiter',     2, 'Petrol',  55.00, 'Available',   'MH02AB1235', 'Hostel E Gate',    'Smooth TVS Jupiter. Helmet included.'),
(3, 5, 'Bike',    'Royal Enfield', 'Classic 350', 2, 'Petrol', 100.00, 'Available',   'MH02AB1236', 'Main Gate',        'Royal Enfield Classic 350. Great for weekend trips.'),
(4, 5, 'Scooter', 'Honda',         'Dio',         2, 'Petrol',  60.00, 'Available',   'MH02AB1237', 'Hostel E Parking', 'Sporty Honda Dio. Fuel efficient.'),
-- Owned by individual students
(5, 1, 'Scooter', 'Honda',         'Activa',      2, 'Petrol',  50.00, 'Available',   'MH02CD5678', 'Hostel A Gate',    'Activa owned by Prathamesh Patil.'),
(6, 2, 'Car',     'Maruti',        'Swift',       5, 'Petrol', 200.00, 'Available',   'MH02CD5679', 'Hostel B Gate',    'Comfortable 5-seater Swift car. AC & music system.'),
(7, 3, 'Bike',    'Yamaha',        'FZ-S',        2, 'Petrol',  70.00, 'Available',   'MH02CD5680', 'Hostel C Parking', 'Yamaha FZ-S bike owned by Rohit Sharma.'),
(8, 4, 'Scooter', 'Hero',          'Splendor',    2, 'Petrol',  45.00, 'Available',   'MH02CD5681', 'Hostel D Gate',    'Hero Splendor, daily campus commuter.');

-- 
-- 3. COUPONS (Original coupons)
-- 
INSERT INTO Coupon (coupon_id, code, discount_percentage, valid_from, valid_to, is_active) VALUES
(1, 'SAVE10',  10.00, '2026-01-01', '2026-12-31', TRUE),
(2, 'SAVE20',  20.00, '2026-01-01', '2026-12-31', TRUE),
(3, 'WELCOME', 15.00, '2026-01-01', '2026-12-31', TRUE);

-- 
-- 4. RENTALS (Historical + Active Rented matching Vehicle 3)
-- 
INSERT INTO Rental (rental_id, student_id, vehicle_id, start_time, end_time, pickup_location, return_location, total_hours, subtotal, discount, final_amount, coupon_id, status) VALUES
(1, 1, 3, '2026-10-04 10:00:00', '2026-10-06 18:00:00', 'Main Gate',        'Hostel A',    8.00,  800.00, 80.00, 720.00, 1, 'Active'),
(2, 2, 1, '2026-09-10 09:00:00', '2026-09-10 12:00:00', 'Hostel E Parking', 'Hostel B',    3.00,  150.00,  0.00, 150.00, NULL, 'Completed'),
(3, 3, 2, '2026-09-15 14:00:00', '2026-09-15 17:00:00', 'Hostel E Gate',    'Hostel C',    3.00,  165.00, 24.75, 140.25, 3, 'Completed'),
(4, 4, 6, '2026-09-20 10:00:00', '2026-09-20 14:00:00', 'Hostel B Gate',    'City Center', 4.00,  800.00, 160.00, 640.00, 2, 'Completed');

-- 
-- 5. PAYMENTS
-- 
INSERT INTO Payment (payment_id, rental_id, amount, payment_method, payment_status, transaction_id) VALUES
(1, 1, 720.00, 'UPI',  'Completed', 'TXN202610040001'),
(2, 2, 150.00, 'Card', 'Completed', 'TXN202609100001'),
(3, 3, 140.25, 'UPI',  'Completed', 'TXN202609150001'),
(4, 4, 640.00, 'Cash', 'Completed', 'TXN202609200001');

-- 
-- 6. REVIEWS
-- 
INSERT INTO Review (rental_id, reviewer_id, vehicle_id, rating, comment) VALUES
(2, 2, 1, 5, 'Great Activa, very smooth and easy to handle around campus.'),
(3, 3, 2, 4, 'TVS Jupiter was great, helmet was provided and clean.'),
(4, 4, 6, 5, 'Swift was super comfortable with chilled AC. Highly recommend!');

-- 
-- 7. MAINTENANCE (Original 6 records from previous dataset)
-- 
INSERT INTO Maintenance (vehicle_id, maintenance_type, description, cost, maintenance_date, status) VALUES
(1, 'Regular Service',  'Oil change, air filter, spark plug',  800.00, '2026-08-15', 'Done'),
(2, 'Brake Check',      'Front and rear brake pad inspection', 500.00, '2026-08-20', 'Done'),
(3, 'Tire Replacement', 'Both tires replaced with new',       1200.00, '2026-08-25', 'Done'),
(4, 'Regular Service',  'Full service check',                  800.00, '2026-08-18', 'Done'),
(5, 'Engine Tuning',    'Carburetor cleaning and tuning',     1500.00, '2026-08-22', 'Scheduled'),
(6, 'Regular Service',  'Oil change and filter',               800.00, '2026-08-16', 'Done');

-- 
-- 8. INSURANCE (Original 6 records from previous dataset)
-- 
INSERT INTO Insurance (vehicle_id, provider, policy_number, coverage_amount, valid_from, valid_to) VALUES
(1, 'New India Assurance',    'NIA123456',  50000.00, '2026-01-01', '2027-01-01'),
(2, 'National Insurance',     'NI789012',   50000.00, '2026-01-01', '2027-01-01'),
(3, 'United India Insurance', 'UIA345678', 100000.00, '2026-01-01', '2027-01-01'),
(4, 'New India Assurance',    'NIA234567',  50000.00, '2026-01-01', '2027-01-01'),
(5, 'Bajaj Allianz',          'BA567890',  200000.00, '2026-01-01', '2027-01-01'),
(6, 'National Insurance',     'NI890123',   50000.00, '2026-01-01', '2027-01-01');

-- 
-- 9. AUDIT LOG (Sample historical audit records)
-- 
INSERT INTO AuditLog (student_id, action, details, ip_address, timestamp) VALUES
(1, 'REGISTER', 'New student registered: prathamesh@campus.edu', '192.168.1.15', '2026-09-01 08:30:00'),
(2, 'REGISTER', 'New student registered: aisha@campus.edu', '192.168.1.20', '2026-09-01 08:45:00'),
(3, 'REGISTER', 'New student registered: rohit@campus.edu', '192.168.1.22', '2026-09-01 09:00:00'),
(4, 'REGISTER', 'New student registered: neha@campus.edu', '192.168.1.25', '2026-09-01 09:15:00'),
(5, 'REGISTER', 'New owner registered: owner1@campus.edu', '192.168.1.30', '2026-09-01 09:30:00'),
(6, 'LOGIN', 'Admin login successful from campus network', '192.168.1.2', '2026-10-05 08:00:00'),
(1, 'LOGIN', 'Login from prathamesh@campus.edu', '192.168.1.15', '2026-10-04 09:55:00'),
(1, 'RENTAL_CREATED', 'Rental #1 created for vehicle #3 (Royal Enfield Classic 350) | Amount: ₹720.00', '192.168.1.15', '2026-10-04 10:00:00'),
(1, 'PAYMENT_COMPLETED', 'Payment #1 | Rental #1 | TxnID: TXN202610040001 | Amount: ₹720.00 | Method: UPI', '192.168.1.15', '2026-10-04 10:02:00'),
(2, 'LOGIN', 'Login from aisha@campus.edu', '192.168.1.20', '2026-09-10 08:50:00'),
(2, 'RENTAL_CREATED', 'Rental #2 created for vehicle #1 (Honda Activa) | Amount: ₹150.00', '192.168.1.20', '2026-09-10 09:00:00'),
(2, 'PAYMENT_COMPLETED', 'Payment #2 | Rental #2 | TxnID: TXN202609100001 | Amount: ₹150.00 | Method: Card', '192.168.1.20', '2026-09-10 09:01:00'),
(2, 'RENTAL_Completed', 'Rental #2 marked as Completed | Vehicle #1 now Available', '192.168.1.20', '2026-09-10 12:00:00'),
(3, 'RENTAL_CREATED', 'Rental #3 created for vehicle #2 (TVS Jupiter) | Amount: ₹140.25', '192.168.1.22', '2026-09-15 14:00:00'),
(3, 'PAYMENT_COMPLETED', 'Payment #3 | Rental #3 | TxnID: TXN202609150001 | Amount: ₹140.25 | Method: UPI', '192.168.1.22', '2026-09-15 14:02:00'),
(3, 'RENTAL_Completed', 'Rental #3 marked as Completed | Vehicle #2 now Available', '192.168.1.22', '2026-09-15 17:00:00'),
(4, 'RENTAL_CREATED', 'Rental #4 created for vehicle #6 (Maruti Swift) | Amount: ₹640.00', '192.168.1.25', '2026-09-20 10:00:00'),
(4, 'PAYMENT_COMPLETED', 'Payment #4 | Rental #4 | TxnID: TXN202609200001 | Amount: ₹640.00 | Method: Cash', '192.168.1.25', '2026-09-20 10:01:00'),
(4, 'RENTAL_Completed', 'Rental #4 marked as Completed | Vehicle #6 now Available', '192.168.1.25', '2026-09-20 14:00:00');

-- Ensure final availability status
UPDATE Vehicle SET availability_status = 'Available' WHERE vehicle_id IN (1, 2, 4, 5, 6, 7, 8);
UPDATE Vehicle SET availability_status = 'Rented' WHERE vehicle_id = 3;

SET FOREIGN_KEY_CHECKS = @old_checks;

 SELECT * FROM STUDENT;
 SELECT * FROM VEHICLE;