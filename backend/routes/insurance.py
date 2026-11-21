"""
Insurance routes — 100% SQL-Driven.
Manage Vehicle Insurance Records (INSERT, SELECT, UPDATE, DELETE).
Demonstrates: INSERT, SELECT, UPDATE, DELETE, JOIN, Subqueries, Views.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import auth
from database import get_db

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


@router.post("")
def add_insurance(
    vehicle_id:      int   = Form(...),
    provider:        str   = Form(...),
    policy_number:   str   = Form(...),
    coverage_amount: float = Form(...),
    valid_from:      str   = Form(...),
    valid_to:        str   = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Add insurance record for a vehicle.
    DBMS: INSERT with ownership validation.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # Ownership check — only owner or admin can add insurance
    v = db.execute(
        text("SELECT owner_id FROM Vehicle WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    db_role = db.execute(
        text("SELECT role FROM Student WHERE student_id = :sid"),
        {"sid": student_id}
    ).fetchone()._mapping["role"]

    if v._mapping["owner_id"] != student_id and db_role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Check for existing active insurance (Subquery)
    existing = db.execute(
        text("""
            SELECT insurance_id FROM Insurance
            WHERE vehicle_id = :vid AND valid_to >= CURDATE()
            LIMIT 1
        """),
        {"vid": vehicle_id}
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vehicle already has active insurance. Update or delete existing policy first."
        )

    # INSERT insurance record
    db.execute(
        text("""
            INSERT INTO Insurance
                (vehicle_id, provider, policy_number, coverage_amount, valid_from, valid_to)
            VALUES
                (:vid, :provider, :policy, :coverage, :from_d, :to_d)
        """),
        {
            "vid":      vehicle_id,
            "provider": provider,
            "policy":   policy_number,
            "coverage": coverage_amount,
            "from_d":   valid_from,
            "to_d":     valid_to
        }
    )
    db.commit()

    ins = db.execute(
        text("SELECT * FROM Insurance WHERE insurance_id = LAST_INSERT_ID()")
    ).fetchone()
    m = ins._mapping
    return {
        "message":         "Insurance policy added successfully",
        "insurance_id":    m["insurance_id"],
        "vehicle_id":      m["vehicle_id"],
        "provider":        m["provider"],
        "policy_number":   m["policy_number"],
        "coverage_amount": float(m["coverage_amount"]),
        "valid_from":      str(m["valid_from"]),
        "valid_to":        str(m["valid_to"])
    }


@router.get("")
def get_all_insurance(db: Session = Depends(get_db)):
    """
    All insurance records with vehicle details.
    DBMS: SELECT + JOIN + vw_insurance_status VIEW.
    """
    rows = db.execute(text("SELECT * FROM vw_insurance_status ORDER BY insurance_id DESC")).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/my")
def get_my_insurance(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """
    Insurance records for vehicles owned by current user.
    DBMS: SELECT + JOIN.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    rows = db.execute(
        text("""
            SELECT i.insurance_id, i.vehicle_id,
                   CONCAT(v.brand, ' ', v.model) AS vehicle_name,
                   v.license_plate,
                   i.provider, i.policy_number, i.coverage_amount,
                   i.valid_from, i.valid_to,
                   CASE WHEN i.valid_to >= CURDATE() THEN 'Active' ELSE 'Expired' END AS status,
                   DATEDIFF(i.valid_to, CURDATE()) AS days_remaining
            FROM Insurance i
            JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
            WHERE v.owner_id = :oid
            ORDER BY i.insurance_id DESC
        """),
        {"oid": student_id}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.get("/vehicle/{vehicle_id}")
def get_vehicle_insurance(vehicle_id: int, db: Session = Depends(get_db)):
    """
    Insurance for a specific vehicle.
    DBMS: SELECT with Subquery — finds expired insurance too.
    """
    rows = db.execute(
        text("""
            SELECT i.*,
                   CASE WHEN i.valid_to >= CURDATE() THEN 'Active' ELSE 'Expired' END AS status,
                   DATEDIFF(i.valid_to, CURDATE()) AS days_remaining
            FROM Insurance i
            WHERE i.vehicle_id = :vid
            ORDER BY i.valid_to DESC
        """),
        {"vid": vehicle_id}
    ).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]


@router.put("/{insurance_id}")
def update_insurance(
    insurance_id:    int,
    coverage_amount: Optional[float] = Form(None),
    valid_to:        Optional[str]   = Form(None),
    provider:        Optional[str]   = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Update insurance policy (renewal/coverage change).
    DBMS: UPDATE with IFNULL pattern.
    """
    auth.verify_token(token)

    row = db.execute(
        text("SELECT insurance_id FROM Insurance WHERE insurance_id = :iid"),
        {"iid": insurance_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Insurance record not found")

    db.execute(
        text("""
            UPDATE Insurance SET
                coverage_amount = IFNULL(:coverage, coverage_amount),
                valid_to        = IFNULL(:to_d,     valid_to),
                provider        = IFNULL(:provider,  provider)
            WHERE insurance_id = :iid
        """),
        {
            "coverage": coverage_amount,
            "to_d":     valid_to,
            "provider": provider,
            "iid":      insurance_id
        }
    )
    db.commit()
    return {"message": "Insurance policy updated successfully"}


@router.delete("/{insurance_id}")
def delete_insurance(
    insurance_id: int,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Delete an insurance record.
    DBMS: DELETE with ownership validation.
    """
    payload    = auth.verify_token(token)
    student_id = int(payload.get("sub"))

    # Check exists
    ins = db.execute(
        text("""
            SELECT i.insurance_id, v.owner_id FROM Insurance i
            JOIN Vehicle v ON i.vehicle_id = v.vehicle_id
            WHERE i.insurance_id = :iid
        """),
        {"iid": insurance_id}
    ).fetchone()
    if not ins:
        raise HTTPException(status_code=404, detail="Insurance record not found")

    db_role = db.execute(
        text("SELECT role FROM Student WHERE student_id = :sid"),
        {"sid": student_id}
    ).fetchone()._mapping["role"]

    if ins._mapping["owner_id"] != student_id and db_role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.execute(
        text("DELETE FROM Insurance WHERE insurance_id = :iid"),
        {"iid": insurance_id}
    )
    db.commit()
    return {"message": "Insurance record deleted"}


@router.get("/expired")
def get_expired_insurance(db: Session = Depends(get_db)):
    """
    Find vehicles with expired insurance.
    DBMS: Subquery (IN clause).
    """
    rows = db.execute(text("""
        SELECT v.vehicle_id, v.brand, v.model, v.license_plate,
               i.provider, i.policy_number, i.valid_to,
               DATEDIFF(CURDATE(), i.valid_to) AS days_expired
        FROM Vehicle v
        JOIN Insurance i ON v.vehicle_id = i.vehicle_id
        WHERE v.vehicle_id IN (
            SELECT vehicle_id FROM Insurance WHERE valid_to < CURDATE()
        )
        ORDER BY i.valid_to ASC
    """)).fetchall()
    return [dict(zip(r._mapping.keys(), r._mapping.values())) for r in rows]
