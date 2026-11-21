"""Dispute management routes for CampusRide."""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import Dispute, Rental, Student
import auth

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@router.post("")
def raise_dispute(
    rental_id: int = Form(...),
    issue_type: str = Form(...),
    description: str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Raise a dispute for a rental."""
    payload = auth.verify_token(token)
    user_id = int(payload.get("sub"))

    rental = db.query(Rental).filter(Rental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    dispute = Dispute(
        rental_id=rental_id,
        raised_by=user_id,
        issue_type=issue_type,
        description=description,
        status="Open"
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return {"message": "Dispute raised", "dispute_id": dispute.dispute_id}


@router.get("/my")
def get_my_disputes(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Get disputes raised by the current user."""
    payload = auth.verify_token(token)
    user_id = int(payload.get("sub"))
    disputes = db.query(Dispute).filter(Dispute.raised_by == user_id).order_by(Dispute.dispute_id.desc()).all()
    result = []
    for d in disputes:
        rental = db.query(Rental).filter(Rental.rental_id == d.rental_id).first()
        result.append({
            "dispute_id": d.dispute_id,
            "rental_id": d.rental_id,
            "issue_type": d.issue_type,
            "description": d.description,
            "status": d.status,
            "resolution": d.resolution,
            "created_at": str(d.created_at),
            "resolved_at": str(d.resolved_at) if d.resolved_at else None
        })
    return result


@router.get("")
def get_all_disputes(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Admin: get all disputes."""
    payload = auth.verify_token(token)
    disputes = db.query(Dispute).order_by(Dispute.dispute_id.desc()).all()
    result = []
    for d in disputes:
        raiser = db.query(Student).filter(Student.student_id == d.raised_by).first()
        result.append({
            "dispute_id": d.dispute_id,
            "rental_id": d.rental_id,
            "raised_by_name": raiser.full_name if raiser else "Student",
            "issue_type": d.issue_type,
            "description": d.description,
            "status": d.status,
            "resolution": d.resolution,
            "created_at": str(d.created_at)
        })
    return result


@router.put("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    resolution: str = Form(...),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Admin/Owner: resolve a dispute."""
    from datetime import datetime
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.resolution = resolution
    dispute.status = "Resolved"
    dispute.resolved_at = datetime.now()
    db.commit()
    return {"message": "Dispute resolved"}
