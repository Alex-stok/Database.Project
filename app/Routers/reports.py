# app/Routers/reports.py
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from collections import defaultdict
from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, Facility, ActivityType

router = APIRouter(prefix="/api/reports", tags=["reports"])
pages = APIRouter(tags=["reports:pages"])

@pages.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse("reports.html", {"request": request})

@router.get("/summary")
def summary(
    scope: int | None = Query(default=None),
    facility_id: int | None = Query(default=None),
    period: str = Query(default="monthly"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(ActivityLog)
        .join(Facility)
        .filter(Facility.org_id == user.org_id)
    )

    if facility_id:
        q = q.filter(ActivityLog.facility_id == facility_id)
    if scope:
        q = (
            q.join(ActivityType, ActivityType.activity_type_id == ActivityLog.activity_type_id)
            .filter(ActivityType.scope == scope)
        )

    rows = q.all()

    total_co2 = Decimal("0")
    by_fac = defaultdict(Decimal)
    by_period = defaultdict(Decimal)
    raw_quantities = defaultdict(lambda: Decimal("0"))

    for r in rows:
        total_co2 += Decimal(str(r.co2e_kg or 0))
        by_fac[r.facility_id] += Decimal(str(r.co2e_kg or 0))

        if r.activity_date:
            key = r.activity_date.strftime("%Y-%m") if period == "monthly" else str(r.activity_date.year)
            by_period[key] += Decimal(str(r.co2e_kg or 0))

        if r.activity_type_fk:
            raw_quantities[r.activity_type_fk.label] += Decimal(str(r.quantity or 0))

    return {
        "facility_id": facility_id,
        "scope": scope,
        "period": period,
        "activity_count": len(rows),
        "total_co2e_kg": float(total_co2),
        "by_facility": [{"facility_id": k, "co2e_kg": float(v)} for k, v in by_fac.items()],
        "by_period": [{"period": k, "co2e_kg": float(v)} for k, v in by_period.items()],
        "raw_quantities": [{"type": k, "quantity": float(v)} for k, v in raw_quantities.items()],
    }
