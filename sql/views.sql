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
