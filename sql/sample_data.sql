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