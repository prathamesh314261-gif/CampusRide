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
