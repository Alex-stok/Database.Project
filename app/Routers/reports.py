# app/Routers/reports.py

from fastapi import APIRouter, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from sqlalchemy.orm import Session
from collections import defaultdict
from decimal import Decimal

from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, ActivityType, Facility

router = APIRouter(prefix="/api/reports", tags=["reports"])
pages = APIRouter(tags=["reports:pages"])

templates = Jinja2Templates(directory="app/templates")


# ------------------------------
# Page route
# ------------------------------
@pages.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports_overview.html", {"request": request})


# ------------------------------
# API: Summary across all metrics
# ------------------------------
@router.get("/summary")
def summary(
    facility_id: int | None = Query(default=None),
    scope: int | None = Query(default=None),
    period: str = Query(default="monthly"),  # monthly or yearly
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    q = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == user.org_id)
        .join(ActivityType, ActivityLog.activity_type_id == ActivityType.activity_type_id)
    )

    if facility_id:
        q = q.filter(ActivityLog.facility_id == facility_id)

    if scope:
        q = q.filter(ActivityType.scope == scope)

    rows = q.all()

    # Aggregation structures
    total_co2e = Decimal("0")
    by_facility = defaultdict(lambda: Decimal("0"))
    by_period = defaultdict(lambda: Decimal("0"))

    # Non-CO₂ metrics
    by_activity_type = defaultdict(lambda: Decimal("0"))

    for r in rows:
        qty = Decimal(str(r.quantity or 0))

        # Track raw quantities by activity type code
        by_activity_type[r.activity_type] += qty

        # CO₂e (optional)
        if r.co2e_kg:
            co2 = Decimal(str(r.co2e_kg))
            total_co2e += co2
            by_facility[r.facility_id] += co2

            if r.activity_date:
                if period == "yearly":
                    key = str(r.activity_date.year)
                else:
                    key = r.activity_date.strftime("%Y-%m")
                by_period[key] += co2

    return {
        "facility_id": facility_id,
        "scope": scope,
        "period": period,
        "activity_count": len(rows),

        # CO₂ data
        "total_co2e_kg": float(total_co2e),
        "by_facility": [
            {"facility_id": fid, "co2e_kg": float(v)}
            for fid, v in sorted(by_facility.items())
        ],
        "by_period": [
            {"period": k, "co2e_kg": float(v)}
            for k, v in sorted(by_period.items())
        ],

        # Non-CO₂ metrics (energy usage, water, shipping, etc.)
        "raw_quantities": [
            {"activity_type": t, "quantity": float(v)}
            for t, v in sorted(by_activity_type.items())
        ],
    }
