# app/Routers/targets.py
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import Target, ActivityLog, Facility

router = APIRouter(prefix="/api/targets", tags=["targets"])
pages = APIRouter(tags=["targets:pages"])


@pages.get("/targets", response_class=HTMLResponse)
def page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "targets.html",
        {"request": request},
    )


from pydantic import BaseModel


class TargetIn(BaseModel):
    baseline_year: int
    target_percent: float  # reduction percent
    target_year: int


@router.post("")
def create_target(
    payload: TargetIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Sum all emissions for this org between baseline_year and target_year
    start_date = date(payload.baseline_year, 1, 1)
    end_date = date(payload.target_year, 12, 31)

    q = (
        db.query(ActivityLog)
        .join(Facility, Facility.facility_id == ActivityLog.facility_id)
        .filter(Facility.org_id == user.org_id)
        .filter(ActivityLog.activity_date >= start_date)
        .filter(ActivityLog.activity_date <= end_date)
    )

    baseline_total = Decimal("0")
    for row in q:
        baseline_total += Decimal(str(row.co2e_kg or 0))

    t = Target(
        org_id=user.org_id,
        baseline_year=payload.baseline_year,
        target_year=payload.target_year,
        reduction_percent=Decimal(str(payload.target_percent)),
        baseline_co2e_kg=baseline_total,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    return {
        "target_id": t.target_id,
        "baseline_year": t.baseline_year,
        "target_year": t.target_year,
        "reduction_percent": float(t.reduction_percent),
        "baseline_co2e_kg": float(t.baseline_co2e_kg or 0),
    }