"""
Reviews and ratings routes for CampusRide — 100% SQL-Driven.
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from database import get_db
import auth

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("")
def add_review(
    rental_id: int = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Add a review after completing a rental."""
    payload = auth.verify_token(token)
    reviewer_id = int(payload.get("sub"))

    rental = db.execute(
        text("SELECT rental_id, student_id, vehicle_id, status FROM Rental WHERE rental_id = :rid"),
        {"rid": rental_id}
    ).fetchone()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    r_map = rental._mapping
    if r_map["student_id"] != reviewer_id:
        raise HTTPException(status_code=403, detail="You can only review your own rentals")
    if r_map["status"] != "Completed":
        raise HTTPException(status_code=400, detail="Can only review completed rentals")

    existing = db.execute(
        text("SELECT review_id FROM Review WHERE rental_id = :rid"),
        {"rid": rental_id}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Review already submitted for this rental")

    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    vehicle_id = r_map["vehicle_id"]
    db.execute(
        text("""
            INSERT INTO Review (rental_id, reviewer_id, vehicle_id, rating, comment)
            VALUES (:rental_id, :reviewer_id, :vehicle_id, :rating, :comment)
        """),
        {
            "rental_id": rental_id,
            "reviewer_id": reviewer_id,
            "vehicle_id": vehicle_id,
            "rating": rating,
            "comment": comment
        }
    )

    # Update vehicle average rating and total reviews
    stats = db.execute(
        text("SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt FROM Review WHERE vehicle_id = :vid"),
        {"vid": vehicle_id}
    ).fetchone()
    if stats:
        avg_r = round(float(stats._mapping["avg_r"] or rating), 1)
        cnt = int(stats._mapping["cnt"] or 1)
        db.execute(
            text("UPDATE Vehicle SET avg_rating = :avg_r, total_reviews = :cnt WHERE vehicle_id = :vid"),
            {"avg_r": avg_r, "cnt": cnt, "vid": vehicle_id}
        )

    db.commit()
    return {"message": "Review submitted successfully"}


@router.get("/vehicle/{vehicle_id}")
def get_vehicle_reviews(vehicle_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a vehicle."""
    rows = db.execute(
        text("""
            SELECT r.review_id, r.rating, r.comment, r.created_at,
                   s.full_name AS reviewer_name
            FROM Review r
            JOIN Student s ON r.reviewer_id = s.student_id
            WHERE r.vehicle_id = :vid
            ORDER BY r.review_id DESC
        """),
        {"vid": vehicle_id}
    ).fetchall()
    return [
        {
            "review_id": r._mapping["review_id"],
            "rating": r._mapping["rating"],
            "comment": r._mapping["comment"],
            "reviewer_name": r._mapping["reviewer_name"],
            "created_at": str(r._mapping["created_at"])
        }
        for r in rows
    ]


@router.get("/my")
def get_my_reviews(token: str = Depends(auth.oauth2_scheme), db: Session = Depends(get_db)):
    """Get all reviews written by the current user."""
    payload = auth.verify_token(token)
    reviewer_id = int(payload.get("sub"))
    rows = db.execute(
        text("""
            SELECT r.review_id, r.rating, r.comment, r.created_at,
                   CONCAT(v.brand, ' ', v.model) AS vehicle_name
            FROM Review r
            JOIN Vehicle v ON r.vehicle_id = v.vehicle_id
            WHERE r.reviewer_id = :uid
            ORDER BY r.review_id DESC
        """),
        {"uid": reviewer_id}
    ).fetchall()
    return [
        {
            "review_id": r._mapping["review_id"],
            "vehicle_name": r._mapping["vehicle_name"],
            "rating": r._mapping["rating"],
            "comment": r._mapping["comment"],
            "created_at": str(r._mapping["created_at"])
        }
        for r in rows
    ]
