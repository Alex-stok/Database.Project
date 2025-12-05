# app/routes_activities.py
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, EmissionFactor, Facility
from ..schemas import ActivityCreate

router = APIRouter(prefix="/api/activities", tags=["activities"], dependencies=[Depends(get_current_user)])

@router.post("/activities")
def create_activity(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Expected payload keys (from activities_new.html):
      - activity_type (e.g. 'Electricity')
      - quantity (number)
      - unit (e.g. 'kWh (electricity)')
      - activity_date (YYYY-MM-DD)
      - facility_id (int)
    """
    activity_type_label = (payload.get("activity_type") or "").strip()
    unit_label = (payload.get("unit") or "").strip()
    qty_raw = payload.get("quantity")
    facility_id_raw = payload.get("facility_id")
    date_raw = payload.get("activity_date")

    if not activity_type_label or not unit_label or qty_raw in (None, "") or not facility_id_raw:
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        quantity = Decimal(str(qty_raw))
    except Exception:
        raise HTTPException(status_code=400, detail="Quantity must be numeric")

    try:
        facility_id = int(facility_id_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Facility ID must be an integer")

    facility = (
        db.query(Facility)
        .filter(
            Facility.facility_id == facility_id,
            Facility.org_id == user.org_id,
        )
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    try:
        activity_date = date.fromisoformat(date_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="activity_date must be YYYY-MM-DD")

    # Use DB emission factor only – no hard-coded factors
    factor = (
        db.query(EmissionFactor)
        .filter(
            EmissionFactor.category == activity_type_label,
            EmissionFactor.unit == unit_label,
        )
        .order_by(EmissionFactor.year.desc())
        .first()
    )
    if not factor:
        raise HTTPException(
            status_code=400,
            detail="No emission factor found for that activity type and unit",
        )

    co2e_kg = quantity * (factor.factor or Decimal("0"))

    activity = ActivityLog(
        facility_id=facility.facility_id,
        factor_id=factor.factor_id,
        activity_type=activity_type_label,
        quantity=quantity,
        unit=unit_label,
        activity_date=activity_date,
        co2e_kg=co2e_kg,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity