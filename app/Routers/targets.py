# app/Routers/targets.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from ..database import get_db
from ..security import get_current_user
from ..models import Target, ActivityLog, Facility

router = APIRouter(prefix="/api/targets", tags=["targets"])
pages = APIRouter(tags=["targets:pages"])

@pages.get("/targets", response_class=HTMLResponse)
def page(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse("targets.html", {"request": request})

def compute_baseline(org_id: int, year: int, db: Session) -> Decimal:
    q = (
        db.query(ActivityLog)
        .join(Facility)
        .filter(Facility.org_id == org_id)
        .filter(ActivityLog.activity_date != None)
        .filter(ActivityLog.activity_date.between(f"{year}-01-01", f"{year}-12-31"))
    )
    total = Decimal("0")
    for r in q.all():
        total += Decimal(str(r.co2e_kg or 0))
    return total

@router.post("")
def save(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    baseline_year = payload["baseline_year"]
    target_year = payload["target_year"]
    reduction_pct = payload["reduction_percent"]

    baseline = compute_baseline(user.org_id, baseline_year, db)

    existing = (
        db.query(Target)
        .filter(Target.org_id == user.org_id)
        .filter(Target.baseline_year == baseline_year)
        .filter(Target.target_year == target_year)
        .first()
    )

    if existing:
        existing.reduction_percent = reduction_pct
        existing.baseline_co2e_kg = baseline
    else:
        t = Target(
            org_id=user.org_id,
            baseline_year=baseline_year,
            baseline_co2e_kg=baseline,
            target_year=target_year,
            reduction_percent=reduction_pct,
            created_by=user.user_id,
        )
        db.add(t)

    db.commit()
    return {"saved": True, "baseline": float(baseline)}
