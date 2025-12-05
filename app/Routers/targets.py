# app/routers/targets.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from ..database import get_db
from ..models import Target
from ..security import get_current_user

router = APIRouter()

@router.post("/targets")
def create_target(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    baseline_year_raw = payload.get("baseline_year")
    target_year_raw = payload.get("target_year")
    reduction_percent_raw = payload.get("reduction_percent")

    if baseline_year_raw in (None, "") or target_year_raw in (None, ""):
        raise HTTPException(status_code=400, detail="Baseline and target years are required")

    try:
        baseline_year = int(baseline_year_raw)
        target_year = int(target_year_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Years must be integers")

    try:
        reduction_percent = Decimal(str(reduction_percent_raw or "0"))
    except Exception:
        raise HTTPException(status_code=400, detail="Target reduction must be numeric")

    t = Target(
        org_id=user.org_id,
        baseline_year=baseline_year,
        baseline_co2e_kg=None,
        target_year=target_year,
        reduction_percent=reduction_percent,
        created_by=user.user_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
