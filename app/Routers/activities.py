# app/Routers/activities.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, Facility, EmissionFactor, ActivityType, Unit
from decimal import Decimal
from datetime import date

router = APIRouter(prefix="/api/activities", tags=["activities"])
pages = APIRouter(tags=["activities:pages"])

# ---------------- PAGE: new activity ----------------
@pages.get("/activities/new", response_class=HTMLResponse)
def new_activity_page(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    types = db.query(ActivityType).all()
    units = db.query(Unit).all()
    facilities = db.query(Facility).filter(Facility.org_id == user.org_id).all()

    return request.app.state.templates.TemplateResponse(
        "activities_new.html",
        {
            "request": request,
            "types": types,
            "units": units,
            "facilities": facilities,
        }
    )

# ---------------- CREATE activity ----------------
@router.post("")
def create_activity(payload: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    facility_id = payload.get("facility_id")
    activity_type_id = payload.get("activity_type_id")
    unit_id = payload.get("unit_id")
    quantity = Decimal(str(payload.get("quantity", 0)))
    activity_date = payload.get("activity_date")

    fac = db.query(Facility).filter(Facility.org_id == user.org_id, Facility.facility_id == facility_id).first()
    if not fac:
        raise HTTPException(403, "Invalid facility")

    # Find factor
    factor = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.category == db.query(ActivityType).get(activity_type_id).label)
        .order_by(EmissionFactor.year.desc())
        .first()
    )
    if not factor:
        raise HTTPException(400, "No emission factor exists for this activity type")

    co2e = quantity * Decimal(str(factor.factor or 0))

    row = ActivityLog(
        facility_id=facility_id,
        activity_type_id=activity_type_id,
        unit_id=unit_id,
        quantity=quantity,
        activity_date=date.fromisoformat(activity_date),
        factor_id=factor.factor_id,
        co2e_kg=co2e,
    )

    db.add(row)
    db.commit()
    return {"saved": True, "co2e_kg": float(co2e)}
