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
-- 1. Student Spending Report Procedure
CALL sp_student_spending_report(1);

-- 2. Vehicle Utilization Report Procedure
CALL sp_vehicle_utilization_report();

SELECT fn_calculate_rental_cost(1, 4.5) AS rental_subtotal;  -- Returns 225.00


SELECT fn_calculate_discount(225.00, 'WELCOME20') AS discount_amount;  -- Returns 45.00

SELECT (225.00 - fn_calculate_discount(225.00, 'WELCOME20')) AS net_payable; -- Returns 180.00
