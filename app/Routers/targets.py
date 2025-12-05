# app/Routers/targets.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from ..database import get_db
from ..security import get_current_user
from ..models import Target, ActivityLog, Facility

router = APIRouter(prefix="/api/targets", tags=["targets"])


# ---------------------------------------------------------
# Compute baseline from ActivityLog
# ---------------------------------------------------------
def compute_baseline(db: Session, org_id: int, year: int) -> Decimal:
    rows = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(
            Facility.org_id == org_id,
            ActivityLog.activity_date.isnot(None),
            ActivityLog.activity_date.between(f"{year}-01-01", f"{year}-12-31")
        )
        .all()
    )

    baseline = Decimal("0")
    for r in rows:
        if r.co2e_kg:
            baseline += Decimal(str(r.co2e_kg))

    return baseline


# ---------------------------------------------------------
# Create target
# ---------------------------------------------------------
@router.post("")
def create_target(payload: dict,
                  db: Session = Depends(get_db),
                  user=Depends(get_current_user)):

    baseline_year = payload["baseline_year"]
    target_year = payload["target_year"]
    reduction_pct = Decimal(str(payload["reduction_percent"]))

    baseline_val = compute_baseline(db, user.org_id, baseline_year)

    t = Target(
        org_id=user.org_id,
        baseline_year=baseline_year,
        baseline_co2e_kg=baseline_val,
        target_year=target_year,
        reduction_percent=reduction_pct,
        created_by=user.user_id
    )

    db.add(t)
    db.commit()
    db.refresh(t)

    return {
        "target_id": t.target_id,
        "baseline_year": baseline_year,
        "baseline_co2e_kg": float(baseline_val),
        "target_year": target_year,
        "reduction_percent": float(reduction_pct)
    }


# ---------------------------------------------------------
# Compute progress toward target
# ---------------------------------------------------------
@router.get("/progress/{target_id}")
def get_progress(target_id: int,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):

    t = db.query(Target).filter(
        Target.target_id == target_id,
        Target.org_id == user.org_id
    ).first()

    if not t:
        raise HTTPException(404, "Target not found")

    current = compute_baseline(db, user.org_id, t.target_year)

    required = t.baseline_co2e_kg * (Decimal("1") - (t.reduction_percent / 100))

    return {
        "baseline": float(t.baseline_co2e_kg),
        "current_emissions": float(current),
        "required_emissions": float(required),
        "on_track": current <= required
    }
