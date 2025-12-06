# app/Routers/activities.py
from fastapi import APIRouter, Depends, Request, HTTPException, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date

from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, Facility, EmissionFactor, ActivityType, Unit

router = APIRouter(prefix="/api/activities", tags=["activities"])
pages = APIRouter(tags=["activities:pages"])

# Map ActivityType.code -> EmissionFactor.category
TYPE_CODE_TO_CATEGORY = {
    "ELEC_USE": "Electricity",
    "NAT_GAS": "NaturalGas",
    "DIESEL": "Diesel",
    "GASOLINE": "Gasoline",
    "FREIGHT_TRUCK": "Freight_Truck",
    "FREIGHT_SHIP": "Freight_Ship",
    "WASTE": "Waste",
    "WATER": "Water",
}


# ---------------- PAGE: new activity ----------------
@pages.get("/activities/new", response_class=HTMLResponse)
def new_activity_page(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    types = db.query(ActivityType).all()
    units = db.query(Unit).all()
    facilities = (
        db.query(Facility)
        .filter(Facility.org_id == user.org_id)
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        "activities_new.html",
        {
            "request": request,
            "types": types,
            "units": units,
            "facilities": facilities,
        },
    )


# ---------------- CREATE activity ----------------
@router.post("")
def create_activity(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    facility_id = payload.get("facility_id")
    activity_type_id = payload.get("activity_type_id")
    unit_id = payload.get("unit_id")
    quantity = Decimal(str(payload.get("quantity", 0)))
    activity_date = payload.get("activity_date")

    # Facility must belong to the current org
    fac = (
        db.query(Facility)
        .filter(
            Facility.org_id == user.org_id,
            Facility.facility_id == facility_id,
        )
        .first()
    )
    if not fac:
        raise HTTPException(status_code=403, detail="Invalid facility")

    # Look up the ActivityType row
    atype = (
        db.query(ActivityType)
        .filter(ActivityType.activity_type_id == activity_type_id)
        .first()
    )
    if not atype:
        raise HTTPException(status_code=400, detail="Invalid activity type")

    # Map ActivityType.code -> EmissionFactor.category
    category = TYPE_CODE_TO_CATEGORY.get(atype.code)
    if not category:
        # Fallback: try first word of label if mapping missing
        category = atype.label.split()[0]

    # Find the most recent emission factor for that category
    factor = (
        db.query(EmissionFactor)
        .filter(EmissionFactor.category == category)
        .order_by(EmissionFactor.year.desc())
        .first()
    )
    if not factor:
        raise HTTPException(
            status_code=400,
            detail="No emission factor exists for this activity type",
        )

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


@router.get("/activity-types")
def list_activity_types(db: Session = Depends(get_db)):
    return db.query(ActivityType).all()


@router.get("/units")
def list_units(db: Session = Depends(get_db)):
    return db.query(Unit).all()


# Alias endpoint (for any old JS that might still post here)
@router.post("/activities")
def alias_create_activity(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return create_activity(payload, db=db, user=user)
