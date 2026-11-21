-- ============================================================
-- CampusRide — Comprehensive DBMS Queries
-- Demonstrates: INSERT, SELECT, UPDATE, DELETE, JOIN,
-- Subqueries, Views, Stored Procedures, Triggers, Transactions
-- ============================================================

USE campusride;

-- ============================================================
-- SECTION A: INSERT Operations
-- ============================================================

-- A1. Student Registration
INSERT INTO Student (full_name, email, phone, department, hostel, password_hash, role, roll_number)
VALUES ('Rohit Sharma', 'rohit@vit.edu', '9876543210', 'CSE', 'Hostel A', SHA2('pass123',256), 'student', 'VIT2024001');

-- A2. Add Vehicle
INSERT INTO Vehicle (owner_id, vehicle_type, brand, model, seating_capacity, fuel_type, hourly_rate, license_plate, location)
VALUES (2, 'Scooter', 'Honda', 'Activa', 2, 'Petrol', 50.00, 'TN01AB1234', 'Hostel E Parking');

-- A3. Add Coupon
INSERT INTO Coupon (code, discount_percentage, valid_from, valid_to)
VALUES ('WELCOME10', 10.00, '2026-01-01', '2026-12-31');

-- A4. Add Rental (manually — normally via sp_create_rental)
INSERT INTO Rental (student_id, vehicle_id, start_time, end_time, pickup_location, return_location, total_hours, subtotal, discount, final_amount, status)
VALUES (1, 1, '2026-10-06 10:00:00', '2026-10-06 13:00:00', 'Hostel A', 'Main Gate', 3.00, 150.00, 15.00, 135.00, 'Confirmed');

-- A5. Record Payment
INSERT INTO Payment (rental_id, amount, payment_method, payment_status, transaction_id)
VALUES (1, 135.00, 'UPI', 'Completed', CONCAT('TXN', UNIX_TIMESTAMP(), FLOOR(RAND()*9999)));

-- A6. Add Review
INSERT INTO Review (rental_id, reviewer_id, vehicle_id, rating, comment)
VALUES (1, 1, 1, 5, 'Excellent scooter! Very clean and well-maintained.');

-- A7. Add Maintenance
INSERT INTO Maintenance (vehicle_id, maintenance_type, description, cost, maintenance_date)
VALUES (1, 'Oil Change', 'Regular oil change and filter replacement', 500.00, '2026-10-15');

-- A8. Add Insurance
INSERT INTO Insurance (vehicle_id, provider, policy_number, coverage_amount, valid_from, valid_to)
VALUES (1, 'New India Assurance', 'POL-2026-001', 200000.00, '2026-01-01', '2026-12-31');


-- ============================================================
-- SECTION B: SELECT Operations
-- ============================================================

-- B1. View All Students
SELECT student_id, full_name, email, role, trust_score, account_status, created_at
FROM Student ORDER BY created_at DESC;

-- B2. View Available Vehicles
SELECT v.vehicle_id, v.brand, v.model, v.vehicle_type, v.hourly_rate,
       v.fuel_type, v.location, v.avg_rating, v.seating_capacity,
       s.full_name AS owner
FROM Vehicle v
JOIN Student s ON v.owner_id = s.student_id
WHERE v.availability_status = 'Available'
ORDER BY v.hourly_rate ASC;

-- B3. Search Vehicles by Type
SELECT * FROM Vehicle
WHERE vehicle_type = 'Scooter'
  AND availability_status = 'Available'
  AND hourly_rate BETWEEN 40 AND 100;

-- B4. View Rental History with Full Details
SELECT r.rental_id, s.full_name AS student, v.brand, v.model,
       r.start_time, r.end_time, r.total_hours,
       r.subtotal, r.discount, r.final_amount, r.status
FROM Rental r
JOIN Student s ON r.student_id = s.student_id
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
ORDER BY r.created_at DESC;

-- B5. Payment Summary
SELECT p.payment_id, p.transaction_id, p.amount, p.payment_method,
       p.payment_status, p.payment_date,
       s.full_name AS student
FROM Payment p
JOIN Rental r ON p.rental_id = r.rental_id
JOIN Student s ON r.student_id = s.student_id
ORDER BY p.payment_date DESC;

-- B6. Check Vehicle Availability
SELECT vehicle_id, brand, model, availability_status,
       CASE availability_status
           WHEN 'Available'   THEN 'Can be booked'
           WHEN 'Rented'      THEN 'Currently rented'
           WHEN 'Maintenance' THEN 'Under maintenance'
       END AS availability_message
FROM Vehicle
WHERE vehicle_id = 1;

-- B7. View Audit Log (Security Monitoring)
SELECT al.log_id, s.full_name, al.action, al.details, al.timestamp
FROM AuditLog al
LEFT JOIN Student s ON al.student_id = s.student_id
ORDER BY al.timestamp DESC LIMIT 50;


-- ============================================================
-- SECTION C: UPDATE Operations
-- ============================================================

-- C1. Update Student Profile
UPDATE Student
SET full_name = 'Rohit Kumar Sharma', phone = '9876543299', bio = 'CSE final year student'
WHERE student_id = 1;

-- C2. Update Vehicle Availability (done automatically via trigger, but also manual)
UPDATE Vehicle SET availability_status = 'Available' WHERE vehicle_id = 1;

-- C3. Update Vehicle Rate
UPDATE Vehicle SET hourly_rate = 55.00 WHERE vehicle_id = 1;

-- C4. Complete Rental (triggers auto-frees the vehicle)
UPDATE Rental SET status = 'Completed' WHERE rental_id = 1;

-- C5. Cancel Rental with Reason
UPDATE Rental
SET status = 'Cancelled', cancel_reason = 'Plan changed'
WHERE rental_id = 2 AND status IN ('Confirmed', 'Active');

-- C6. Complete Maintenance (trigger auto-marks vehicle Available)
UPDATE Maintenance SET status = 'Done' WHERE maintenance_id = 1;

-- C7. Suspend Student (Admin action)
UPDATE Student SET account_status = 'Suspended' WHERE student_id = 5;

-- C8. Update Vehicle Rating after Review
UPDATE Vehicle
SET avg_rating = (SELECT AVG(rating) FROM Review WHERE vehicle_id = 1),
    total_reviews = (SELECT COUNT(*) FROM Review WHERE vehicle_id = 1)
WHERE vehicle_id = 1;


-- ============================================================
-- SECTION D: DELETE Operations
-- ============================================================

-- D1. Delete a Coupon (only if never used)
DELETE FROM Coupon
WHERE coupon_id = 5
  AND coupon_id NOT IN (SELECT DISTINCT coupon_id FROM Rental WHERE coupon_id IS NOT NULL);

-- D2. Delete Cancelled Rental (old cleanup)
DELETE FROM Rental WHERE status = 'Cancelled' AND created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- D3. Delete Audit Logs older than 1 year (archival)
DELETE FROM AuditLog WHERE timestamp < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- D4. Remove unapproved vehicle
DELETE FROM Vehicle WHERE is_approved = FALSE AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);


-- ============================================================
-- SECTION E: JOIN Queries
-- ============================================================

-- E1. INNER JOIN — Rental + Student + Vehicle + Payment
SELECT r.rental_id, s.full_name, s.email,
       CONCAT(v.brand, ' ', v.model) AS vehicle,
       r.total_hours, r.final_amount,
       p.payment_method, p.payment_status,
       p.transaction_id
FROM Rental r
INNER JOIN Student s  ON r.student_id = s.student_id
INNER JOIN Vehicle v  ON r.vehicle_id = v.vehicle_id
INNER JOIN Payment p  ON r.rental_id  = p.rental_id
ORDER BY r.created_at DESC;

-- E2. LEFT JOIN — All Vehicles including those never rented
SELECT v.vehicle_id, CONCAT(v.brand, ' ', v.model) AS vehicle,
       v.vehicle_type, v.hourly_rate,
       COUNT(r.rental_id)             AS total_rentals,
       COALESCE(SUM(r.final_amount), 0) AS total_earned
FROM Vehicle v
LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id AND r.status = 'Completed'
GROUP BY v.vehicle_id
ORDER BY total_earned DESC;

-- E3. Multi-table JOIN — Student rental + coupon details
SELECT s.full_name, r.rental_id, r.start_time,
       r.subtotal, c.code AS coupon_code,
       c.discount_percentage, r.discount, r.final_amount
FROM Rental r
JOIN Student s ON r.student_id = s.student_id
LEFT JOIN Coupon c ON r.coupon_id = c.coupon_id
ORDER BY r.created_at DESC;

-- E4. JOIN with Review — Vehicle ratings summary
SELECT v.vehicle_id, CONCAT(v.brand, ' ', v.model) AS vehicle,
       COUNT(rv.review_id) AS review_count,
       AVG(rv.rating)      AS avg_rating,
       MIN(rv.rating)      AS min_rating,
       MAX(rv.rating)      AS max_rating
FROM Vehicle v
LEFT JOIN Review rv ON v.vehicle_id = rv.vehicle_id
GROUP BY v.vehicle_id
ORDER BY avg_rating DESC;

-- E5. JOIN — Insurance validity with vehicle info
SELECT v.license_plate, CONCAT(v.brand, ' ', v.model) AS vehicle,
       i.provider, i.policy_number, i.valid_to,
       DATEDIFF(i.valid_to, CURDATE()) AS days_remaining,
       CASE WHEN i.valid_to >= CURDATE() THEN 'Valid' ELSE 'Expired' END AS status
FROM Insurance i
JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
ORDER BY days_remaining ASC;

-- E6. Maintenance JOIN — History per vehicle
SELECT v.license_plate, CONCAT(v.brand, ' ', v.model) AS vehicle,
       m.maintenance_type, m.description, m.cost,
       m.maintenance_date, m.status,
       s.full_name AS reported_by
FROM Maintenance m
JOIN Vehicle v ON m.vehicle_id = v.vehicle_id
LEFT JOIN Student s ON m.reported_by = s.student_id
ORDER BY m.maintenance_date DESC;


-- ============================================================
-- SECTION F: Subqueries
-- ============================================================

-- F1. Students who have rented more than once
SELECT full_name, email, trust_score
FROM Student
WHERE student_id IN (
    SELECT student_id FROM Rental
    GROUP BY student_id HAVING COUNT(*) > 1
);

-- F2. Vehicles that earned more than average
SELECT brand, model, vehicle_type, hourly_rate
FROM Vehicle
WHERE vehicle_id IN (
    SELECT vehicle_id FROM Rental
    WHERE status = 'Completed'
    GROUP BY vehicle_id
    HAVING SUM(final_amount) > (
        SELECT AVG(total_vehicle_earnings) FROM (
            SELECT vehicle_id, SUM(final_amount) AS total_vehicle_earnings
            FROM Rental WHERE status = 'Completed'
            GROUP BY vehicle_id
        ) sub
    )
);

-- F3. Students who never completed a rental
SELECT student_id, full_name, email
FROM Student
WHERE student_id NOT IN (
    SELECT DISTINCT student_id FROM Rental WHERE status = 'Completed'
);

-- F4. Most expensive rental per student (correlated subquery)
SELECT r.rental_id, s.full_name, r.final_amount
FROM Rental r
JOIN Student s ON r.student_id = s.student_id
WHERE r.final_amount = (
    SELECT MAX(final_amount) FROM Rental r2
    WHERE r2.student_id = r.student_id
);

-- F5. Vehicles with no current active rentals (EXISTS)
SELECT v.vehicle_id, v.brand, v.model
FROM Vehicle v
WHERE NOT EXISTS (
    SELECT 1 FROM Rental r
    WHERE r.vehicle_id = v.vehicle_id
      AND r.status IN ('Confirmed', 'Active')
);

-- F6. Top 3 highest-paying students
SELECT full_name, email, total_spent
FROM (
    SELECT s.student_id, s.full_name, s.email,
           COALESCE(SUM(r.final_amount), 0) AS total_spent
    FROM Student s
    LEFT JOIN Rental r ON s.student_id = r.student_id AND r.status = 'Completed'
    GROUP BY s.student_id
    ORDER BY total_spent DESC
    LIMIT 3
) AS top_spenders;


-- ============================================================
-- SECTION G: Aggregate & Group Queries (Reports)
-- ============================================================

-- G1. Revenue by Month
SELECT DATE_FORMAT(r.start_time, '%Y-%m') AS month,
       COUNT(r.rental_id)                  AS total_rentals,
       SUM(r.final_amount)                 AS total_revenue,
       AVG(r.final_amount)                 AS avg_rental_value
FROM Rental r
WHERE r.status = 'Completed'
GROUP BY DATE_FORMAT(r.start_time, '%Y-%m')
ORDER BY month DESC;

-- G2. Revenue by Vehicle Type
SELECT v.vehicle_type,
       COUNT(r.rental_id)         AS rentals,
       SUM(r.final_amount)        AS revenue,
       AVG(r.total_hours)         AS avg_hours,
       AVG(v.avg_rating)          AS avg_vehicle_rating
FROM Rental r
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
WHERE r.status = 'Completed'
GROUP BY v.vehicle_type
ORDER BY revenue DESC;

-- G3. Payment Method Distribution
SELECT payment_method,
       COUNT(*) AS count,
       SUM(amount) AS total_amount,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Payment WHERE payment_status = 'Completed'), 2) AS percentage
FROM Payment
WHERE payment_status = 'Completed'
GROUP BY payment_method;

-- G4. Daily demand forecast (historical pattern)
SELECT DAYNAME(start_time) AS day_of_week,
       HOUR(start_time)    AS hour_of_day,
       COUNT(*)            AS booking_count
FROM Rental
GROUP BY DAYNAME(start_time), HOUR(start_time)
ORDER BY booking_count DESC;

-- G5. Owner Earnings Summary
SELECT s.full_name AS owner,
       COUNT(DISTINCT v.vehicle_id)   AS vehicles_owned,
       COUNT(r.rental_id)             AS total_rentals,
       SUM(r.final_amount)            AS total_earnings
FROM Student s
JOIN Vehicle v ON s.student_id = v.owner_id
LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id AND r.status = 'Completed'
WHERE s.role = 'owner'
GROUP BY s.student_id
ORDER BY total_earnings DESC;


-- ============================================================
-- SECTION H: Views (Querying the Defined Views)
-- ============================================================

-- H1. Available Vehicles View
SELECT * FROM vw_available_vehicles;

-- H2. Rental History View
SELECT * FROM vw_rental_history ORDER BY rental_id DESC LIMIT 20;

-- H3. Payment History View
SELECT * FROM vw_payment_history ORDER BY payment_date DESC;

-- H4. Owner Earnings View
SELECT * FROM vw_owner_earnings WHERE total_rentals > 0;

-- H5. Active Maintenance View
SELECT * FROM vw_active_maintenance;

-- H6. Insurance Status View
SELECT * FROM vw_insurance_status ORDER BY days_remaining ASC;


-- ============================================================
-- SECTION I: Stored Procedure Calls
-- ============================================================

-- I1. Register Student
SET @status = '';
CALL sp_register('Priya Mehta','priya@vit.edu','9123456789','ECE','Hostel B','mypassword','VIT2024010',@status);
SELECT @status AS registration_status;

-- I2. Login
SET @status = '';
CALL sp_login('priya@vit.edu','mypassword',@status);
SELECT @status AS login_status;

-- I3. Create Rental (Booking)
SET @status = '';
CALL sp_create_rental(
    1, 2,
    '2026-10-10 09:00:00', '2026-10-10 12:00:00',
    'Hostel A Gate', 'Main Gate', 'WELCOME10', @status
);
SELECT @status AS booking_status;

-- I4. Process Payment
SET @txn = ''; SET @status = '';
CALL sp_process_payment(1, 'UPI', @txn, @status);
SELECT @txn AS transaction_id, @status AS payment_status;

-- I5. Complete Rental
SET @status = '';
CALL sp_complete_rental(1, @status);
SELECT @status AS complete_status;

-- I6. Cancel Rental
SET @status = '';
CALL sp_cancel_rental(2, 1, 'Changed plans', @status);
SELECT @status AS cancel_status;

-- I7. Add Vehicle
SET @status = '';
CALL sp_add_vehicle(
    2, 'Bike', 'Royal Enfield', 'Classic 350',
    2, 'Petrol', 120.00, 'TN02XY9999',
    'Hostel C', 'Classic 350 in excellent condition', @status
);
SELECT @status AS add_vehicle_status;

-- I8. Schedule Maintenance
SET @status = '';
CALL sp_add_maintenance(1, 'Tire Change', 'Front tire worn out', 800.00, '2026-10-20', @status);
SELECT @status AS maintenance_status;

-- I9. Vehicle Utilization Report
CALL sp_vehicle_utilization_report();

-- I10. Student Spending Report
CALL sp_student_spending_report(1);


-- ============================================================
-- SECTION J: Trigger Demonstrations
-- ============================================================
-- (Triggers fire automatically — these show the effects)

-- J1. trg_after_student_insert: fires on new student → logs to AuditLog
-- Demo: After INSERT INTO Student → check AuditLog for REGISTER action
SELECT * FROM AuditLog WHERE action = 'REGISTER' ORDER BY timestamp DESC LIMIT 5;

-- J2. trg_after_rental_insert: fires on rental → vehicle becomes 'Rented'
-- Demo: After a rental INSERT → check Vehicle status
SELECT vehicle_id, brand, model, availability_status FROM Vehicle WHERE vehicle_id = 1;

-- J3. trg_after_rental_update: fires when rental Completed/Cancelled → vehicle becomes 'Available'
SELECT * FROM AuditLog WHERE action IN ('RENTAL_Completed','RENTAL_Cancelled') ORDER BY timestamp DESC LIMIT 5;

-- J4. trg_after_payment_insert: fires on payment → logs PAYMENT_COMPLETED
SELECT * FROM AuditLog WHERE action = 'PAYMENT_COMPLETED' ORDER BY timestamp DESC LIMIT 5;

-- J5. trg_after_maintenance_insert: fires → vehicle set to 'Maintenance'
-- J6. trg_after_maintenance_done: fires → vehicle set back to 'Available'
SELECT * FROM AuditLog WHERE action IN ('MAINTENANCE_SCHEDULED','MAINTENANCE_DONE') ORDER BY timestamp DESC LIMIT 5;

-- J7. trg_before_rental_insert: GUARD — prevents booking unavailable vehicle
-- (This would raise SIGNAL SQLSTATE '45000' if vehicle not Available)
SELECT action, details, timestamp FROM AuditLog ORDER BY timestamp DESC LIMIT 20;


-- ============================================================
-- SECTION K: Transactions
-- ============================================================

-- K1. Atomic Rental Booking (Transaction)
START TRANSACTION;
    -- Step 1: Insert rental
    INSERT INTO Rental (student_id, vehicle_id, start_time, end_time,
                        pickup_location, return_location, total_hours,
                        subtotal, discount, final_amount, status)
    VALUES (1, 3, '2026-10-12 10:00:00', '2026-10-12 14:00:00',
            'Library', 'Main Gate', 4.00, 200.00, 0.00, 200.00, 'Confirmed');

    -- Step 2: Mark vehicle as Rented
    UPDATE Vehicle SET availability_status = 'Rented' WHERE vehicle_id = 3;

    -- Step 3: Log action
    INSERT INTO AuditLog (student_id, action, details)
    VALUES (1, 'RENTAL_CREATED', 'Transaction: Rental booked for vehicle 3');
COMMIT;

-- K2. Atomic Payment + Rental Activation
START TRANSACTION;
    SET @txn_id = CONCAT('TXN', UNIX_TIMESTAMP(), FLOOR(RAND()*9999));
    INSERT INTO Payment (rental_id, amount, payment_method, payment_status, transaction_id)
    VALUES (LAST_INSERT_ID(), 200.00, 'Card', 'Completed', @txn_id);
    UPDATE Rental SET status = 'Active' WHERE rental_id = LAST_INSERT_ID();
COMMIT;

-- K3. Rollback Example — failed double payment
START TRANSACTION;
    SAVEPOINT before_payment;
    -- Attempt duplicate payment → will fail due to UNIQUE constraint on rental_id
    INSERT INTO Payment (rental_id, amount, payment_method, payment_status, transaction_id)
    VALUES (1, 200.00, 'Cash', 'Completed', 'DUPLICATE-TXN-001');
    -- If duplicate, rollback to savepoint
ROLLBACK TO before_payment;
ROLLBACK;

-- K4. Atomic Cancellation + Refund
START TRANSACTION;
    UPDATE Rental SET status = 'Cancelled', cancel_reason = 'Weather conditions'
    WHERE rental_id = 3;
    UPDATE Vehicle SET availability_status = 'Available' WHERE vehicle_id = 3;
    UPDATE Payment SET payment_status = 'Refunded', refund_amount = 200.00, refund_date = NOW()
    WHERE rental_id = 3;
    INSERT INTO AuditLog (student_id, action, details)
    VALUES (1, 'REFUND_ISSUED', 'Refund Rs.200 for Rental #3 cancellation');
COMMIT;


-- ============================================================
-- SECTION L: AI/ML Support Queries (Used by ML routes)
-- ============================================================

-- L1. Vehicles for Recommendation Engine
SELECT v.vehicle_id, v.vehicle_type, v.brand, v.model,
       v.hourly_rate, v.seating_capacity, v.fuel_type,
       v.avg_rating, v.total_reviews, v.location,
       COUNT(r.rental_id) AS popularity_score
FROM Vehicle v
LEFT JOIN Rental r ON v.vehicle_id = r.vehicle_id
WHERE v.availability_status = 'Available'
GROUP BY v.vehicle_id
ORDER BY popularity_score DESC, v.avg_rating DESC;

-- L2. Student Rental History for Personalization
SELECT r.student_id, v.vehicle_type, v.fuel_type,
       v.seating_capacity, r.total_hours,
       r.final_amount, rv.rating
FROM Rental r
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
LEFT JOIN Review rv ON r.rental_id = rv.rental_id
WHERE r.student_id = 1 AND r.status = 'Completed'
ORDER BY r.created_at DESC;

-- L3. Hourly Demand Pattern (for Demand Prediction ML)
SELECT HOUR(start_time) AS hour, DAYOFWEEK(start_time) AS day_of_week,
       vehicle_type, COUNT(*) AS booking_count
FROM Rental r
JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
GROUP BY HOUR(start_time), DAYOFWEEK(start_time), vehicle_type
ORDER BY booking_count DESC;

-- L4. Payment Anomaly Detection Data
SELECT payment_id, amount, payment_method, payment_date,
       (SELECT AVG(amount) FROM Payment WHERE payment_status = 'Completed') AS avg_payment,
       (amount - (SELECT AVG(amount) FROM Payment WHERE payment_status = 'Completed'))
           / NULLIF((SELECT STDDEV(amount) FROM Payment WHERE payment_status = 'Completed'), 0)
           AS z_score
FROM Payment
WHERE payment_status = 'Completed'
ORDER BY ABS(z_score) DESC;

-- L5. Suspicious Payment Flag Query
SELECT p.payment_id, p.amount, p.transaction_id, p.payment_date,
       s.full_name, s.email
FROM Payment p
JOIN Rental r ON p.rental_id = r.rental_id
JOIN Student s ON r.student_id = s.student_id
WHERE p.amount > (SELECT AVG(amount) + 3 * STDDEV(amount) FROM Payment WHERE payment_status='Completed')
   OR p.amount < 0;

SELECT 'All DBMS Operations Demonstrated Successfully!' AS result;
