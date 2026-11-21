import os
from copy import deepcopy
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_paragraph_text_preserve_format(paragraph, text, font_size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """Replaces all runs in an existing paragraph while preserving its exact template pPr/style."""
    # Remove all existing run/drawing children except pPr
    for child in list(paragraph._p):
        if child.tag != qn('w:pPr'):
            paragraph._p.remove(child)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(font_size)
    run.bold = bold
    run.italic = italic
    return paragraph


def insert_paragraph_after(ref_paragraph, text, font_size=12, bold=False, italic=False,
                           align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=None, space_after=6):
    """Inserts a new paragraph directly after ref_paragraph copying its base pPr (without list numPr)."""
    new_p = OxmlElement('w:p')
    ref_pPr = ref_paragraph._p.find(qn('w:pPr'))
    if ref_pPr is not None:
        cloned_pPr = deepcopy(ref_pPr)
        # Ensure we never accidentally inherit auto-numbering numPr
        numPr = cloned_pPr.find(qn('w:numPr'))
        if numPr is not None:
            cloned_pPr.remove(numPr)
        new_p.append(cloned_pPr)
    ref_paragraph._p.addnext(new_p)
    p_obj = docx.text.paragraph.Paragraph(new_p, ref_paragraph._parent)
    if align is not None:
        p_obj.alignment = align
    if space_before is not None:
        p_obj.paragraph_format.space_before = Pt(space_before)
    if space_after is not None:
        p_obj.paragraph_format.space_after = Pt(space_after)
    if text:
        run = p_obj.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(font_size)
        run.bold = bold
        run.italic = italic
    return p_obj


def remove_paragraph(paragraph):
    p = paragraph._p
    parent = p.getparent()
    if parent is not None:
        parent.remove(p)


def fill_patent_proposal():
    scratch_dir = r"C:\Users\HP\.gemini\antigravity\brain\f3255e1c-82ec-45a0-9e0a-4bb1cdf5a518\scratch"
    template_path = os.path.join(scratch_dir, "patent_template.docx")
    fig1_path = os.path.join(scratch_dir, "patent_fig1.png")
    fig2_path = os.path.join(scratch_dir, "patent_fig2.png")
    out_path = r"c:\Users\HP\OneDrive\Documents\cp\report\CampusRide_Patent_Proposal.docx"

    doc = docx.Document(template_path)

    # Snapshot paragraph references BEFORE any insertion/deletion so indices never shift!
    paras = list(doc.paragraphs)

    # Verify anchor headings match the exact template before modifying anything
    assert "Title of the invention" in paras[16].text, f"Unexpected P16: {paras[16].text}"
    assert "Technical field" in paras[21].text, f"Unexpected P21: {paras[21].text}"
    assert "Prior art" in paras[25].text, f"Unexpected P25: {paras[25].text}"
    assert "Objective(s)" in paras[29].text, f"Unexpected P29: {paras[29].text}"
    assert "Synopsis" in paras[34].text, f"Unexpected P34: {paras[34].text}"
    assert "Brief description of drawings" in paras[38].text, f"Unexpected P38: {paras[38].text}"
    assert "Detailed description" in paras[53].text, f"Unexpected P53: {paras[53].text}"
    assert "Best method" in paras[57].text, f"Unexpected P57: {paras[57].text}"
    assert "CLAIMS" in paras[61].text, f"Unexpected P61: {paras[61].text}"
    assert "Inventive step" in paras[65].text, f"Unexpected P65: {paras[65].text}"
    assert "Industrial application" in paras[69].text, f"Unexpected P69: {paras[69].text}"
    assert "Abstract" in paras[73].text, f"Unexpected P73: {paras[73].text}"
    assert "Drawing" in paras[77].text, f"Unexpected P77: {paras[77].text}"

    # -------------------------------------------------------------------------
    # SECTION 3: Title of the invention (P18) — Strictly <= 15 words, 1 sentence
    # -------------------------------------------------------------------------
    set_paragraph_text_preserve_format(
        paras[18],
        "SQL-Driven Peer-to-Peer Campus Vehicle Rental System with Predictive Fleet Analytics and Geofencing.",
        font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT
    )

    # -------------------------------------------------------------------------
    # SECTION 4: Technical field of the invention (P23)
    # -------------------------------------------------------------------------
    set_paragraph_text_preserve_format(
        paras[23],
        "The present invention relates generally to the fields of Computer Science and Engineering, Relational Database Management Systems (RDBMS), Applied Artificial Intelligence and Machine Learning, Geospatial Perimeter Monitoring (Geofencing), and Intelligent Peer-to-Peer Campus Micro-Mobility Systems. More particularly, the invention relates to a database-centric peer-to-peer vehicle sharing architecture executing atomic transactional control, concurrency guarding, and cryptographic auditing natively inside a relational database engine coupled with real-time predictive analytics and Haversine perimeter enforcement.",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 5: Prior art (P27)
    # -------------------------------------------------------------------------
    p27 = set_paragraph_text_preserve_format(
        paras[27],
        "Existing shared mobility and vehicle rental platforms generally fall into four categories: (i) commercial cab aggregators (such as Uber and Ola), (ii) centralized company-owned self-drive and dockless scooter rental networks (such as Zoomcar, Bounce, and Yulu), (iii) conventional web rental portals built over stateless application-layer Object-Relational Mapping (ORM) frameworks, and (iv) informal peer-to-peer vehicle lending among university students.",
        font_size=12
    )
    p27_2 = insert_paragraph_after(
        p27,
        "Commercial cab services impose steep base fares (typically exceeding INR 100 per short trip) and are frequently restricted from entering gated university academic and hostel zones. Centralized dockless rental operators require substantial capital expenditure for proprietary fleets, charging docks, and battery-swapping logistics, and suffer from vehicle unavailability in peripheral campus sectors. Informal peer lending lacks structured identity verification, contractual accountability, automated fare calculation, and tamper-proof trip logs.",
        font_size=12
    )
    insert_paragraph_after(
        p27_2,
        "From a computing systems standpoint, conventional web-based vehicle rental applications delegate inventory availability checks, pricing calculations, booking state transitions, and security logging to stateless application-layer ORM services. Under high-concurrency reservation intervals (such as campus lecture transitions), application-level read-then-write patterns remain vulnerable to double-booking race conditions, desynchronized inventory statuses, bypassable audit logs, and brute-force credential attacks. Furthermore, existing campus rental tools lack an integrated, real-time intelligence pipeline capable of simultaneously generating content-based vehicle recommendations, detecting anomalous payment transactions without labeled fraud datasets, scoring mechanical wear degradation directly from relational trip records, and enforcing localized campus GPS perimeter boundaries. The present invention overcomes all of these technical and economic limitations.",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 6: Objective(s) of Invention (P31)
    # -------------------------------------------------------------------------
    p31 = set_paragraph_text_preserve_format(
        paras[31],
        "The principal objective of the present invention is to provide a secure, economical, and race-condition-free peer-to-peer campus vehicle rental system driven natively by a relational database engine and enhanced with artificial intelligence and geospatial perimeter monitoring. Specific objectives of the invention include:",
        font_size=12
    )
    objectives = [
        "1. To eliminate application-layer double-booking race conditions and multi-table synchronization failures by enforcing atomic reservation workflows, availability verification, and automated status transitions natively within relational database stored procedures and row-level triggers.",
        "2. To reduce intra-campus commuting costs and eliminate commercial fleet capital expenditure by enabling verified students and faculty members to monetize idle privately owned two-wheelers and four-wheelers on an hourly peer-to-peer basis.",
        "3. To enforce robust database-level authentication security incorporating salted SHA-256 password hashing, automated brute-force account lockout after five consecutive failed login attempts, role-based access control (Renter, Owner, Administrator), and an append-only immutable audit trail.",
        "4. To provide personalized vehicle matching using Term Frequency-Inverse Document Frequency (TF-IDF) vectorization and Cosine Similarity based on student preferences, budget constraints, and historical rental patterns.",
        "5. To detect suspicious payment amounts and abnormal booking velocity spikes in real time using an unsupervised Isolation Forest anomaly detection model without requiring pre-labeled fraud training data.",
        "6. To compute real-time predictive vehicle maintenance health scores and supply-demand dynamic pricing suggestions directly from live relational rental duration, trip frequency, and driver rating records.",
        "7. To enforce authorized institutional geographical boundaries through continuous Haversine great-circle GPS distance verification against a configurable campus perimeter radius (2.5 km) with automated security breach alerting."
    ]
    curr = p31
    for obj in objectives:
        curr = insert_paragraph_after(curr, obj, font_size=12, space_after=4)

    # -------------------------------------------------------------------------
    # SECTION 7: Synopsis (P36)
    # -------------------------------------------------------------------------
    p36 = set_paragraph_text_preserve_format(
        paras[36],
        "The present invention discloses a SQL-driven peer-to-peer campus vehicle rental and predictive fleet management system (100) structured across a decoupled three-tier architecture. The system (100) comprises a multi-role client presentation interface (101) providing dedicated Renter, Vehicle Owner, and System Administrator portals; a stateless application gateway and JSON Web Token (JWT) authentication proxy (102) operating with zero Object-Relational Mapping (ORM) overhead; a relational database management engine (103); an artificial intelligence and machine learning analytics engine (108); and a Haversine spatial perimeter geofencing unit (109) receiving external GPS telemetry (110).",
        font_size=12
    )
    insert_paragraph_after(
        p36,
        "Inside the relational database management engine (103), ten normalized relational tables and six pre-compiled views form the relational data storage unit (104), ten ACID-compliant stored procedures and seven deterministic user-defined functions form the atomic execution unit (105), seven automated row-level triggers form the trigger guard unit (106), and an append-only table forms the immutable security audit trail ledger (107). The gateway (102) routes all state-altering requests directly to the atomic execution unit (105), where the trigger guard unit (106) blocks concurrent double-bookings via a BEFORE INSERT exception guard, synchronizes vehicle availability statuses, and writes tamper-evident logs into the audit ledger (107). Concurrently, the AI/ML engine (108) queries operational records from the storage unit (104) to deliver TF-IDF cosine similarity recommendations, time-series demand forecasting, heuristic wear-based predictive maintenance, dynamic pricing, and Isolation Forest fraud detection, while the geofencing unit (109) continuously validates GPS coordinates (110) against the campus boundary and records out-of-bounds alerts in the audit ledger (107).",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 8: Brief description of drawings (P40..P51)
    # Keep exact style of template example ("Figure 1 illustrates ... Whereas, 100 denotes ...")
    # -------------------------------------------------------------------------
    p40 = set_paragraph_text_preserve_format(
        paras[40],
        "The accompanying drawings illustrate embodiments of the present invention using common single reference numerals across all figures without any text labels inside the drawings:",
        font_size=12
    )
    # Remove example paragraphs P41..P51
    for idx in range(41, 52):
        remove_paragraph(paras[idx])

    draw_lines = [
        "Figure 1 illustrates the overall three-tier system architecture and component interconnection diagram of the proposed SQL-driven peer-to-peer campus vehicle rental and predictive fleet management system (100).",
        "Figure 2 illustrates the end-to-end operational execution, trigger-guarded transaction validation, machine learning inference, and perimeter geofencing workflow of the proposed invention (100) using the same common reference numerals. Whereas,",
        "100 denotes the overall SQL-driven peer-to-peer campus vehicle rental and predictive fleet management system,",
        "101 denotes the multi-role client presentation interface comprising Renter, Vehicle Owner, and System Administrator web portals,",
        "102 denotes the stateless application gateway and JWT authentication proxy dispatching parameterized database procedure calls,",
        "103 denotes the relational database management engine (MySQL 8.0 InnoDB storage engine),",
        "104 denotes the normalized relational data storage unit comprising ten 3NF tables and six pre-compiled relational views,",
        "105 denotes the atomic stored procedure and deterministic user-defined function execution unit,",
        "106 denotes the automated row-level trigger guard unit enforcing double-booking prevention and status synchronization,",
        "107 denotes the append-only immutable security audit trail ledger,",
        "108 denotes the artificial intelligence and machine learning analytics engine executing vehicle recommendation, demand forecasting, predictive maintenance wear modeling, dynamic pricing, and Isolation Forest anomaly detection,",
        "109 denotes the Haversine spatial perimeter geofencing and boundary breach alerting unit, and",
        "110 denotes the external GPS coordinate telemetry stream and authorized institutional campus perimeter boundary (2.5 km radius)."
    ]
    curr = p40
    for ln in draw_lines:
        curr = insert_paragraph_after(curr, ln, font_size=12, space_after=3)

    # -------------------------------------------------------------------------
    # SECTION 9: Detailed description of the invention (P55)
    # -------------------------------------------------------------------------
    p55 = set_paragraph_text_preserve_format(
        paras[55],
        "Referring to Figure 1 and Figure 2, the present invention provides an integrated SQL-driven peer-to-peer campus vehicle rental system (100) combining strict database-layer ACID transactional enforcement with real-time machine learning analytics and spatial perimeter security. The architecture deliberately eliminates Object-Relational Mapping (ORM) business logic in the application server and consolidates data integrity enforcement inside the relational database management engine (103).",
        font_size=12
    )
    detail_paras = [
        "1. Client Presentation Interface (101) and Stateless Application Gateway (102): The client interface (101) is implemented using responsive HTML5, CSS3, and asynchronous JavaScript Fetch API calls supporting three role-specific operational views: a Renter Portal for vehicle discovery, personalized AI recommendations, coupon application, booking management, and reviewing; a Vehicle Owner Portal for fleet CRUD operations, earnings breakdown, maintenance reporting, dynamic pricing suggestions, and predictive health monitoring; and an Administrator Console for institutional KPIs, student trust governance, immutable audit inspection, fraud detection, and geofence monitoring. All HTTP requests pass through the stateless FastAPI gateway (102), which validates JSON Web Token (JWT) bearer credentials and dispatches raw parameterized SQL calls directly to the relational database engine (103) and inference requests to the AI/ML engine (108).",
        "2. Normalized Relational Data Storage Unit (104): Inside the MySQL 8.0 InnoDB engine (103), the storage unit (104) is normalized to Third Normal Form (3NF) across ten relational tables with foreign key cascades, domain CHECK constraints, UNIQUE constraints, and secondary B-Tree indexes: (i) Student (16 fields storing identity, role ENUM, salted password hash, trust_score, account_status, failed_attempts, and locked_until), (ii) Vehicle (16 fields storing owner_id, vehicle_type, brand, model, fuel_type, hourly_rate CHECK > 0, availability_status ENUM, unique license_plate, pickup hub location, and avg_rating), (iii) Coupon (7 fields storing unique promo code, discount_percentage CHECK 1–100, and validity interval), (iv) Rental (16 fields storing timestamps, pickup/return hubs, total_hours, subtotal, discount, final_amount, status ENUM, and pickup_code OTP), (v) Payment (9 fields enforcing 1:1 unique rental_id, payment_method ENUM, unique transaction_id, and refund tracking), (vi) Review (7 fields enforcing rating CHECK 1–5), (vii) Maintenance (9 fields tracking scheduled/completed service cost and status), (viii) Insurance (8 fields tracking policy validity), (ix) Dispute (9 fields tracking grievance resolution), and (x) AuditLog (6 fields forming the append-only ledger 107). Six pre-compiled views (vw_available_vehicles, vw_rental_history, vw_payment_history, vw_owner_earnings, vw_active_maintenance, and vw_insurance_status) optimize multi-table reads.",
        "3. Atomic Stored Procedures, Functions (105), and Trigger Guards (106): All state transitions execute within ten ACID stored procedures and seven user-defined functions in unit (105). Password hashing uses deterministic function fn_hash_password computing SHA2(CONCAT('vitcampus', p_password), 256). Procedure sp_login validates credentials, increments failed_attempts upon mismatch, automatically locks the account for 15 minutes when failed_attempts reaches 5, and writes a LOGIN event to the audit ledger (107) upon success. Procedure sp_create_rental verifies availability via fn_is_vehicle_available, computes exact fractional duration via fn_total_hours, calculates base cost via fn_calculate_rental_cost, applies valid coupon discounts via fn_calculate_discount, and commits the booking inside an explicit START TRANSACTION block with an SQLEXCEPTION ROLLBACK handler. Concurrently, seven automated triggers in unit (106) provide deterministic protection: trg_before_rental_insert acts as a BEFORE INSERT double-booking guard that inspects Vehicle.availability_status and raises SIGNAL SQLSTATE '45000' if the vehicle is not 'Available'; trg_after_rental_insert atomically flips the vehicle status to 'Rented' and logs RENTAL_CREATED into ledger (107); trg_after_rental_update restores the vehicle to 'Available' upon Completed or Cancelled status; trg_after_payment_insert records PAYMENT_COMPLETED with unique transaction ID (generated by fn_generate_txn_id) in ledger (107); trg_after_student_insert logs REGISTER events; and trg_after_maintenance_insert and trg_after_maintenance_done toggle vehicle status between 'Maintenance' and 'Available'.",
        "4. Artificial Intelligence and Machine Learning Analytics Engine (108): The ML engine (108) integrates five real-time modules built with Scikit-learn, NumPy, and Pandas: (a) Vehicle Recommender applying TfidfVectorizer and cosine_similarity across vehicle metadata and student preference profiles to rank top-3 personalized vehicles with percentage match scores; (b) Time-Series Demand Predictor forecasting next-day booking shares across vehicle categories (Scooter, Bike, Car) and campus hotspots (Main Gate, Hostel A, Library, Sports Ground) for proactive fleet rebalancing; (c) Unsupervised Fraud & Anomaly Detector utilizing an IsolationForest model (contamination=0.05) trained on historical payment distributions to flag anomalous transaction amounts and compute a Student Risk & Trust Assessment Matrix evaluating 24-hour booking velocity and cancellation ratios; (d) Predictive Fleet Maintenance module executing live SQL aggregate queries (SUM(total_hours), COUNT(*), and Vehicle.avg_rating) to calculate component wear risk, health scores (0–100%), and days remaining until recommended service; and (e) Dynamic Pricing Suggester computing supply-demand elasticity multipliers within institutional price guardrails.",
        "5. Haversine Spatial Perimeter Geofencing Unit (109) and Telemetry (110): The geofencing unit (109) continuously evaluates incoming vehicle GPS coordinates (latitude, longitude) from telemetry source (110) against the configured campus center coordinates (Lat 13.0020 N, Lng 80.2350 E) using the Haversine great-circle distance equation: d = 2R * arcsin(sqrt(sin^2((lat2 - lat1)/2) + cos(lat1)*cos(lat2)*sin^2((lon2 - lon1)/2))), where R = 6371 km. Whenever the computed distance exceeds the authorized 2.5 km campus perimeter radius, unit (109) immediately generates a live SECURITY ALERT on the Administrator Console (101) and appends a permanent breach entry into the audit ledger (107).",
        "6. Experimental Implementation and Validation Study: A complete prototype of system (100) was implemented and validated on MySQL Community Server 8.0 and Python 3.11 / FastAPI (Uvicorn port 15501) across 7 verified user accounts, 8 listed vehicles, and 9 rentals generating INR 2,210 in verified payments (Bike: INR 860, Car: INR 640, Scooter: INR 710). Validation confirmed: (i) 100% rejection of concurrent booking attempts on already-rented vehicles by trigger trg_before_rental_insert; (ii) automated 15-minute lockout enforcement by sp_login upon 5 invalid password submissions; (iii) continuous generation of 65+ sequential immutable entries in AuditLog; (iv) real-time Isolation Forest classification flagging INR 8,500 as HIGH RISK (is_anomaly=True) while clearing INR 250 as LOW RISK; (v) live predictive maintenance scoring yielding a 90.2% fleet average health score across all 8 vehicles; and (vi) immediate geofence breach capture when coordinates (13.0650 N, 80.2850 E), situated ~8.5 km outside the campus center, were injected for vehicle MH02AB1236."
    ]
    curr = p55
    for dp in detail_paras:
        curr = insert_paragraph_after(curr, dp, font_size=12, space_after=6)

    # -------------------------------------------------------------------------
    # SECTION 10: Best method of performance of the invention (P59)
    # -------------------------------------------------------------------------
    p59 = set_paragraph_text_preserve_format(
        paras[59],
        "In a preferred operational embodiment of the invention (100), a student renter (for example, Rohit Sharma, Roll No. CAMPUS202403) accesses the Renter Portal (101) and submits login credentials to the FastAPI gateway (102). The gateway (102) dispatches CALL sp_login to the execution unit (105), which hashes the submitted password using fn_hash_password, verifies it against Student.password_hash in storage unit (104), resets failed_attempts, writes a LOGIN entry to the audit ledger (107), and returns status 'OK', whereupon the gateway (102) issues a 24-hour signed JWT token. Upon loading the dashboard, the client interface (101) retrieves live available inventory via view vw_available_vehicles from unit (104) while concurrently requesting personalized vehicle rankings from the AI/ML engine (108), which returns the top three recommended vehicles with cosine similarity match percentages.",
        font_size=12
    )
    insert_paragraph_after(
        p59,
        "After selecting a vehicle (such as a Hero Splendor scooter at INR 45/hour), specifying a 2-hour booking interval, and optionally entering a promotional code (such as WELCOME20), the gateway (102) invokes CALL sp_create_rental in unit (105). Before the INSERT commits, trigger trg_before_rental_insert in unit (106) verifies that the vehicle is strictly 'Available'; upon commit, trg_after_rental_insert automatically marks the vehicle 'Rented' and logs RENTAL_CREATED in ledger (107). Next, the renter settles INR 90 via UPI through CALL sp_process_payment, which generates a unique transaction reference via fn_generate_txn_id, activates the rental, triggers trg_after_payment_insert to record PAYMENT_COMPLETED in ledger (107), and screens the transaction amount through the Isolation Forest detector in engine (108). During the active trip, GPS telemetry (110) is checked by the Haversine geofencing unit (109) against the 2.5 km campus boundary. Upon return, CALL sp_complete_rental completes the booking, triggering trg_after_rental_update to restore the vehicle to 'Available' while updating owner earnings in vw_owner_earnings and recalculating mechanical wear health scores in engine (108).",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 11: CLAIMS (P63)
    # -------------------------------------------------------------------------
    p63 = set_paragraph_text_preserve_format(
        paras[63],
        "We claim:",
        font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT
    )
    claims = [
        "1. A database-driven peer-to-peer campus vehicle rental and predictive fleet management system (100), comprising: a multi-role client presentation interface (101) providing dedicated Renter, Vehicle Owner, and Administrator portals; a stateless application gateway (102) operating without Object-Relational Mapping (ORM) business logic and configured to authenticate sessions via JSON Web Tokens (JWT) and dispatch parameterized procedure calls; a relational database management engine (103) comprising a normalized relational data storage unit (104), an atomic stored procedure and deterministic user-defined function execution unit (105), an automated row-level trigger guard unit (106), and an append-only immutable security audit trail ledger (107); an artificial intelligence and machine learning analytics engine (108) coupled to live operational records of the storage unit (104); and a Haversine spatial perimeter geofencing unit (109) receiving GPS coordinate telemetry (110) to enforce an authorized institutional operational boundary.",
        "2. The system (100) as claimed in claim 1, wherein the automated row-level trigger guard unit (106) includes a BEFORE INSERT trigger (trg_before_rental_insert) that queries real-time vehicle availability prior to committing any booking record and raises a database exception signal (SQLSTATE '45000') when the vehicle status is not 'Available', thereby preventing concurrent double-booking race conditions directly inside the database engine (103).",
        "3. The system (100) as claimed in claim 1, wherein the atomic execution unit (105) enforces authentication via a compiled stored procedure (sp_login) executing deterministic salted SHA-256 hashing (fn_hash_password), tracking consecutive failed password attempts, automatically locking user accounts for a 15-minute duration after five consecutive failures, and wherein the trigger guard unit (106) autonomously records registration, booking creation, status completion, payment settlement, and maintenance transitions into the append-only audit trail ledger (107).",
        "4. The system (100) as claimed in claim 1, wherein the artificial intelligence and machine learning analytics engine (108) comprises a content-based vehicle recommender applying TF-IDF vectorization and cosine similarity to rank available campus vehicles for individual students, and an unsupervised Isolation Forest anomaly detector configured to flag abnormal payment amounts and compute a student risk and trust matrix from booking velocity and cancellation ratios.",
        "5. The system (100) as claimed in claim 1, wherein the artificial intelligence and machine learning analytics engine (108) further comprises a predictive fleet maintenance module that aggregates cumulative rental hours, trip frequency, service intervals, and vehicle ratings directly from the relational storage unit (104) to compute real-time vehicle health scores and breakdown risk classifications, alongside a dynamic pricing suggester computing supply-demand elasticity hourly rates within bounded institutional limits.",
        "6. The system (100) as claimed in claim 1, wherein the Haversine spatial perimeter geofencing unit (109) continuously computes great-circle distances between external GPS coordinates (110) and institutional campus center coordinates, triggering real-time security breach alerts on the Administrator portal (101) and logging breach events in the immutable audit trail ledger (107) whenever vehicle displacement exceeds a configurable 2.5 km boundary radius.",
        "7. A computer-implemented method for operating a peer-to-peer campus vehicle rental system (100), the method comprising the steps of: authenticating a campus user through a database stored procedure (105) with salted SHA-256 verification and brute-force lockout protection; querying available peer-listed vehicles through a pre-compiled database view (104) ranked by a TF-IDF cosine similarity recommender (108); executing an atomic booking transaction via a stored procedure (105) guarded by a BEFORE INSERT trigger (106) that prevents double-booking and an AFTER INSERT trigger (106) that synchronizes vehicle status and appends an immutable audit record (107); validating payment transactions through an unsupervised Isolation Forest anomaly detector (108); monitoring active trip GPS telemetry (110) via a Haversine perimeter geofencing unit (109) to detect boundary departures; and restoring vehicle availability upon trip completion via an AFTER UPDATE trigger (106) while updating predictive fleet maintenance health metrics (108)."
    ]
    curr = p63
    for cl in claims:
        curr = insert_paragraph_after(curr, cl, font_size=12, space_after=5)

    # -------------------------------------------------------------------------
    # SECTION 12: Inventive step of your invention (P67)
    # Must explicitly state Technical Advantage + Cost Reduction + HOW achieved
    # -------------------------------------------------------------------------
    p67 = set_paragraph_text_preserve_format(
        paras[67],
        "The inventive step of the present invention lies in the synergistic integration of a zero-ORM, 100% SQL-driven transactional concurrency architecture (103–107) with real-time predictive machine learning (108) and localized Haversine geofencing (109–110), achieving both substantial technical advancement and major cost reduction over existing mobility technologies:",
        font_size=12
    )
    inv_points = [
        "1. Technical Advantage (Elimination of Race Conditions & Tamper-Evident Auditing — HOW Achieved): Unlike conventional rental platforms that perform availability checks and status updates in stateless application code (allowing concurrent requests to double-book the same vehicle), the present invention achieves strict ACID serializability by compiling a BEFORE INSERT exception guard trigger (trg_before_rental_insert) and explicit START TRANSACTION / ROLLBACK stored procedures (sp_create_rental, sp_process_payment) directly inside the relational engine (103). Because state transitions and audit logging are fired atomically by row-level triggers (106), even direct database writes cannot violate booking integrity or bypass the immutable AuditLog (107).",
        "2. Technical Advantage (Unified Operational Telemetry & Proactive AI/Geofence Security — HOW Achieved): Rather than operating static CRUD tables, the stateless gateway (102) feeds live SQL aggregates (rental hours, trip counts, ratings, payment distributions) directly into Scikit-learn models (108) and the Haversine engine (109). This achieves zero-label fraud detection via Isolation Forest (flagging outlier amounts automatically), early mechanical breakdown prevention via multi-factor wear health scoring, and instant detection of unauthorized off-campus departures beyond 2.5 km.",
        "3. Cost Reduction Advantage (Zero-CapEx Fleet & 55–65% Lower Commute Cost — HOW Achieved): Existing commercial dockless rental operators incur heavy capital costs for purchasing dedicated vehicle fleets, smart docking stations, and battery-swapping personnel, passing those overheads to users. The present invention completely eliminates fleet acquisition and docking infrastructure expenditure by unlocking privately owned student and faculty two-wheelers that otherwise remain idle for 8–10 hours daily, reducing intra-campus student transit costs from INR 100+ commercial cab fares down to INR 45–60 per hour while creating passive income for vehicle owners."
    ]
    curr = p67
    for ip in inv_points:
        curr = insert_paragraph_after(curr, ip, font_size=12, space_after=5)

    # -------------------------------------------------------------------------
    # SECTION 13: Industrial application (P71)
    # -------------------------------------------------------------------------
    set_paragraph_text_preserve_format(
        paras[71],
        "The present invention has broad industrial applicability across higher-education university campuses, residential engineering and medical institutes, corporate IT parks, integrated research townships, smart-city residential complexes, and large gated industrial estates. In all such closed or semi-closed institutional environments where commuting distances are significant yet privately owned vehicles sit idle during working hours, the system (100) provides an immediately deployable, low-cost, environmentally sustainable, and security-audited peer-to-peer micro-mobility infrastructure that maximizes existing vehicular asset utilization, reduces campus traffic congestion and carbon emissions, and equips institutional administrators with automated financial, maintenance, and perimeter security governance.",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 14: Abstract (P75) — Concise 1 paragraph referencing numerals
    # -------------------------------------------------------------------------
    set_paragraph_text_preserve_format(
        paras[75],
        "A SQL-driven peer-to-peer campus vehicle rental and predictive fleet management system (100) is disclosed for secure, affordable intra-campus micro-mobility. The system (100) comprises a multi-role client presentation interface (101), a stateless zero-ORM application gateway (102), a relational database management engine (103), an artificial intelligence and machine learning analytics engine (108), and a Haversine spatial perimeter geofencing unit (109). Within the database engine (103), ten normalized tables and six pre-compiled views (104), ten ACID stored procedures and seven deterministic functions (105), and seven automated row-level triggers (106) execute salted SHA-256 authentication with brute-force lockout, block concurrent double-booking via a BEFORE INSERT exception guard, synchronize vehicle availability statuses, and populate an immutable security audit ledger (107). Concurrently, the analytics engine (108) delivers TF-IDF cosine similarity vehicle recommendations, time-series demand forecasting, Isolation Forest payment anomaly detection, predictive maintenance health scoring, and dynamic pricing, while the geofencing unit (109) validates GPS telemetry (110) against a 2.5 km campus perimeter to detect boundary breaches in real time.",
        font_size=12
    )

    # -------------------------------------------------------------------------
    # SECTION 15: Drawing (P79..P85) — Unlabeled numeral-only Figure 1 & Figure 2
    # -------------------------------------------------------------------------
    # Remove instruction/example paragraphs P79..P83, replace P84 with Figure 1, P85 with 'Figure 1', then add Figure 2!
    for idx in range(79, 84):
        remove_paragraph(paras[idx])

    # Clear P84 (old example drawing) and insert patent_fig1.png
    p84 = paras[84]
    for child in list(p84._p):
        if child.tag != qn('w:pPr'):
            p84._p.remove(child)
    p84.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p84.paragraph_format.space_before = Pt(6)
    p84.paragraph_format.space_after = Pt(4)
    p84.paragraph_format.keep_with_next = True
    p84.add_run().add_picture(fig1_path, width=Inches(5.3))

    # Update P85 to clean centered bold 'Figure 1'
    p85 = set_paragraph_text_preserve_format(
        paras[85], "Figure 1", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER
    )
    p85.paragraph_format.space_after = Pt(14)

    # Insert Figure 2 cleanly below Figure 1
    p_fig2_img = insert_paragraph_after(p85, "", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=4)
    p_fig2_img.paragraph_format.keep_with_next = True
    p_fig2_img.add_run().add_picture(fig2_path, width=Inches(4.5))

    insert_paragraph_after(p_fig2_img, "Figure 2", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=8)

    doc.save(out_path)
    print(f"Patent Proposal successfully created -> {out_path}")


if __name__ == "__main__":
    fill_patent_proposal()
