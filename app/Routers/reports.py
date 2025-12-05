# app/Routers/reports.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.orm import Session
from ..security import get_current_user
from ..database import get_db
from ..models import ActivityLog, Facility, ActivityType


router = APIRouter(prefix="/api/reports", tags=["reports"])
pages = APIRouter(tags=["reports:pages"])

templates = Jinja2Templates(directory="app/templates")

# -------- PAGE ROUTES (HTML) --------
@pages.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports.html", {"request": request})

# -------- API ROUTES (JSON) --------
@router.get("/reports/summary")
def emissions_summary(
    scope: int | None = Query(default=None),          # 1,2,3 or None
    facility_id: int | None = Query(default=None),
    period: str = Query(default="monthly"),           # 'monthly' or 'yearly'
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == user.org_id)
    )

    if facility_id is not None:
        q = q.filter(ActivityLog.facility_id == facility_id)

    if scope is not None:
        q = (
            q.join(ActivityType, ActivityLog.activity_type_id == ActivityType.activity_type_id)
             .filter(ActivityType.scope == scope)
        )

    rows = q.all()

    total = Decimal("0")
    by_facility = defaultdict(lambda: Decimal("0"))
    by_period = defaultdict(lambda: Decimal("0"))

    for r in rows:
        co2 = Decimal(str(r.co2e_kg or 0))
        total += co2

        by_facility[r.facility_id] += co2

        if not r.activity_date:
            continue
        if period == "yearly":
            key = str(r.activity_date.year)
        else:
            key = r.activity_date.strftime("%Y-%m")
        by_period[key] += co2

    return {
        "organization_id": user.org_id,
        "scope": scope,
        "facility_id": facility_id,
        "period": period,
        "total_co2e_kg": float(total),
        "by_facility": [
            {"facility_id": fid, "co2e_kg": float(v)}
            for fid, v in sorted(by_facility.items())
        ],
        "by_period": [
            {"period": k, "co2e_kg": float(v)}
            for k, v in sorted(by_period.items())
        ],
        "activity_count": len(rows),
    }