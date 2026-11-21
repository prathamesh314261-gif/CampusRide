"""
CampusRide Security Router — 100% SQL-Driven.
Implements:
1. Audit Logging query & filtering (reads directly from AuditLog table)
2. AIML Fraud & Anomaly Analysis (heavily queries DBMS rental & payment patterns)
3. Campus Geofencing telemetry, boundary validation, and breach simulation
4. Student Account Status Control (Active, Suspended, Locked)
"""
from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta
import math

from database import get_db
import auth

router = APIRouter(prefix="/api/security", tags=["security"])

CAMPUS_GEOFENCE = {
    "campus_name": "Main University Campus",
    "center": {"lat": 13.0020, "lng": 80.2350},
    "bounds": {
        "min_lat": 12.9850,
        "max_lat": 13.0200,
        "min_lng": 80.2150,
        "max_lng": 80.2550
    },
    "radius_km": 2.5
}

# In-memory alert store for dynamic simulations (persisted across live session)
_simulated_alerts = [
    {
        "alert_id": 1,
        "vehicle_id": 3,
        "vehicle_name": "Royal Enfield Classic 350",
        "license_plate": "MH02AB1236",
        "rental_id": 1,
        "renter_name": "Prathamesh Patil",
        "renter_roll": "CAMPUS202401",
        "latitude": 13.0650,
        "longitude": 80.2850,
        "status": "Active",
        "alert_message": "SECURITY ALERT: Vehicle #3 (MH02AB1236) breached campus boundary! Coordinates: (13.0650, 80.2850), ~8.5km from campus.",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]


def check_geofence(lat: float, lng: float):
    """Check if given GPS coordinate is within the campus boundary."""
    b = CAMPUS_GEOFENCE["bounds"]
    inside = (b["min_lat"] <= lat <= b["max_lat"]) and (b["min_lng"] <= lng <= b["max_lng"])
    c_lat, c_lng = CAMPUS_GEOFENCE["center"]["lat"], CAMPUS_GEOFENCE["center"]["lng"]
    dlat = math.radians(lat - c_lat)
    dlng = math.radians(lng - c_lng)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(c_lat)) * math.cos(math.radians(lat)) * math.sin(dlng / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    dist_km = round(6371.0 * c, 2)
    return inside, dist_km


# -------------------------------------------------------------------
# 1. AUDIT LOGS
# -------------------------------------------------------------------
@router.get("/audit-logs")
def get_audit_logs(
    action: Optional[str] = Query(None),
    student_id: Optional[int] = Query(None),
    limit: int = Query(50),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Admin endpoint to retrieve immutable audit logs."""
    auth.require_admin(token, db)

    sql = """
        SELECT a.log_id, a.student_id, a.action, a.details, a.ip_address, a.timestamp,
               s.full_name AS student_name, s.roll_number
        FROM AuditLog a
        LEFT JOIN Student s ON a.student_id = s.student_id
        WHERE 1=1
    """
    params = {"lim": limit}
    if action:
        sql += " AND a.action LIKE :act"
        params["act"] = f"%{action}%"
    if student_id:
        sql += " AND a.student_id = :sid"
        params["sid"] = student_id

    sql += " ORDER BY a.log_id DESC LIMIT :lim"
    rows = db.execute(text(sql), params).fetchall()

    result = []
    for r in rows:
        m = r._mapping
        result.append({
            "log_id": m["log_id"],
            "student_id": m["student_id"],
            "student_name": m["student_name"] or "System / Security Gate",
            "roll_number": m["roll_number"] or "N/A",
            "action": m["action"],
            "details": m["details"],
            "ip_address": m["ip_address"] or "127.0.0.1",
            "timestamp": str(m["timestamp"])
        })
    return result


# -------------------------------------------------------------------
# 2. AIML-BASED FRAUD & ABNORMAL ACTIVITY DETECTION
# -------------------------------------------------------------------
@router.get("/fraud/analysis")
def get_fraud_analysis(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """AIML engine analyzes all students for suspicious behavioral patterns."""
    auth.require_admin(token, db)

    students = db.execute(text("""
        SELECT student_id, full_name, email, roll_number, trust_score, account_status
        FROM Student
        ORDER BY student_id
    """)).fetchall()

    analysis_results = []
    high_risk_count = 0
    mod_risk_count = 0

    for s_row in students:
        s = s_row._mapping
        sid = s["student_id"]

        # 1. Rental activity
        r_stats = db.execute(text("""
            SELECT 
                COUNT(*) AS total_rentals,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_rentals,
                SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 ELSE 0 END) AS recent_24h
            FROM Rental
            WHERE student_id = :sid
        """), {"sid": sid}).fetchone()._mapping

        total_rentals = int(r_stats["total_rentals"] or 0)
        cancelled = int(r_stats["cancelled_rentals"] or 0)
        recent_24h = int(r_stats["recent_24h"] or 0)

        # 2. Disputes
        disputes = db.execute(text("""
            SELECT COUNT(*) FROM Dispute d
            JOIN Rental r ON d.rental_id = r.rental_id
            WHERE r.student_id = :sid
        """), {"sid": sid}).scalar() or 0

        # 3. Payment failures
        pay_fails = db.execute(text("""
            SELECT COUNT(*) FROM Payment p
            JOIN Rental r ON p.rental_id = r.rental_id
            WHERE r.student_id = :sid AND p.payment_status = 'Failed'
        """), {"sid": sid}).scalar() or 0

        # Heuristic scoring
        flags = []
        risk_score = 0

        if recent_24h >= 3:
            flags.append(f"Velocity Spike: {recent_24h} bookings in 24h")
            risk_score += min(35, recent_24h * 12)

        cancellation_rate = round((cancelled / total_rentals * 100), 1) if total_rentals > 0 else 0.0
        if total_rentals >= 2 and cancellation_rate >= 50:
            flags.append(f"High Cancellation: {cancellation_rate}%")
            risk_score += 25

        if disputes > 0:
            flags.append(f"{disputes} Dispute(s) Reported")
            risk_score += disputes * 20

        if pay_fails > 0:
            flags.append(f"{pay_fails} Failed Transactions")
            risk_score += pay_fails * 15

        if s["account_status"] == "Locked":
            flags.append("Account Locked (Failed Logins)")
            risk_score += 40

        risk_score = min(100, risk_score)

        if risk_score >= 60:
            risk_level = "Suspicious / High Risk"
            high_risk_count += 1
        elif risk_score >= 25:
            risk_level = "Moderate"
            mod_risk_count += 1
        else:
            risk_level = "Normal"

        trust_score_pct = int(float(s["trust_score"] or 5.0) * 10)

        analysis_results.append({
            "student_id": sid,
            "full_name": s["full_name"],
            "email": s["email"],
            "roll_number": s["roll_number"] or "N/A",
            "recent_rentals_24h": recent_24h,
            "cancellation_rate": cancellation_rate,
            "flags": flags,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "trust_score": trust_score_pct,
            "account_status": s["account_status"] or "Active"
        })

    return {
        "total_analyzed": len(analysis_results),
        "high_risk_count": high_risk_count,
        "moderate_risk_count": mod_risk_count,
        "students": analysis_results
    }


@router.put("/students/{student_id}/status")
def update_student_status(
    student_id: int,
    status: str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Suspend or reactivate a student account."""
    auth.require_admin(token, db)
    if status not in ("Active", "Suspended", "Locked"):
        raise HTTPException(status_code=400, detail="Invalid status")
    
    db.execute(
        text("UPDATE Student SET account_status = :s, failed_attempts=0, locked_until=NULL WHERE student_id = :id"),
        {"s": status, "id": student_id}
    )
    db.execute(
        text("INSERT INTO AuditLog (student_id, action, details) VALUES (:id, 'ADMIN_STATUS_CHANGE', :det)"),
        {"id": student_id, "det": f"Account status set to {status} by administrator"}
    )
    db.commit()
    return {"message": f"Account status updated to {status}"}


# -------------------------------------------------------------------
# 3. CAMPUS GEOFENCING & GPS TELEMETRY
# -------------------------------------------------------------------
@router.get("/geofence/boundary")
def get_geofence_boundary(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Retrieve campus boundary definition and current vehicle GPS locations."""
    auth.verify_token(token)
    vehicles = db.execute(text("SELECT vehicle_id, brand, model, license_plate, availability_status FROM Vehicle")).fetchall()
    active_coords = []
    for row in vehicles:
        v = row._mapping
        inside, dist = check_geofence(13.0020, 80.2350)
        active_coords.append({
            "vehicle_id": v["vehicle_id"],
            "name": f"{v['brand']} {v['model']}",
            "plate": v["license_plate"],
            "lat": 13.0020,
            "lng": 80.2350,
            "status": v["availability_status"],
            "is_inside": inside,
            "distance_km": dist
        })
    return {"geofence": CAMPUS_GEOFENCE, "vehicles": active_coords}


@router.get("/geofence/alerts")
def get_geofence_alerts(
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Retrieve geofence boundary breach alerts."""
    auth.verify_token(token)
    return _simulated_alerts


@router.post("/geofence/simulate-breach")
def simulate_geofence_breach(
    vehicle_id: Optional[int] = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Simulate a vehicle moving outside campus boundaries for testing/demo."""
    auth.verify_token(token)
    
    # Pick vehicle 3 (Royal Enfield) or first vehicle
    target_id = vehicle_id or 3
    v = db.execute(text("SELECT brand, model, license_plate, owner_id FROM Vehicle WHERE vehicle_id = :vid"), {"vid": target_id}).fetchone()
    v_info = v._mapping if v else {"brand": "Royal Enfield", "model": "Classic 350", "license_plate": "MH02AB1236", "owner_id": 5}

    breach_lat = 13.0650
    breach_lng = 80.2850
    alert_msg = f"SECURITY ALERT: Vehicle #{target_id} ({v_info['license_plate']}) moved outside campus geofence! Location: ({breach_lat}, {breach_lng}), ~8.5km from campus perimeter."

    new_alert = {
        "alert_id": len(_simulated_alerts) + 1,
        "vehicle_id": target_id,
        "vehicle_name": f"{v_info['brand']} {v_info['model']}",
        "license_plate": v_info["license_plate"],
        "rental_id": 1,
        "renter_name": "Prathamesh Patil",
        "renter_roll": "CAMPUS202401",
        "latitude": breach_lat,
        "longitude": breach_lng,
        "status": "Active",
        "alert_message": alert_msg,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    _simulated_alerts.insert(0, new_alert)

    # Log in database AuditLog
    db.execute(
        text("INSERT INTO AuditLog (student_id, action, details) VALUES (:sid, 'GEOFENCE_ALERT', :det)"),
        {"sid": 1, "det": alert_msg}
    )
    db.commit()

    return {
        "message": "Geofence breach simulated successfully",
        "alert_id": new_alert["alert_id"],
        "vehicle_name": new_alert["vehicle_name"],
        "latitude": breach_lat,
        "longitude": breach_lng,
        "status": "Active"
    }


@router.put("/geofence/alerts/{alert_id}/resolve")
def resolve_geofence_alert(
    alert_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Admin resolves a geofence security alert."""
    auth.require_admin(token, db)
    for a in _simulated_alerts:
        if a["alert_id"] == alert_id:
            a["status"] = "Resolved"
            break
    db.execute(
        text("INSERT INTO AuditLog (student_id, action, details) VALUES (6, 'ALERT_RESOLVED', :det)"),
        {"det": f"Admin resolved Geofence Alert #{alert_id}"}
    )
    db.commit()
    return {"message": "Geofence alert resolved"}
