# app/Routers/activities.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from ..database import get_db
from ..security import get_current_user
from ..models import (
    ActivityLog,
    ActivityType,
    Unit,
    Facility,
    EmissionFactor,
)

router = APIRouter(prefix="/api", tags=["activities"])


# ------------------------------------------------------
# Helper: parse date safely
# ------------------------------------------------------
def parse_date(val: str | None) -> date:
    if not val:
        return date.today()
    try:
        return datetime.fromisoformat(val).date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD expected)")


# ------------------------------------------------------
# Helper: compute CO2e if possible
# ------------------------------------------------------
def compute_co2e(quantity: Decimal, factor: EmissionFactor | None) -> Decimal | None:
    if not factor:
        return None
    if factor.factor is None:
        return None
    try:
        return quantity * Decimal(str(factor.factor))
    except:
        return None


# ------------------------------------------------------
# POST /api/activities — main activity creation
# ------------------------------------------------------
@router.post("/activities")
def create_activity(payload: dict,
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):

    # Required: facility_id
    facility_id = payload.get("facility_id")
    if not facility_id:
        raise HTTPException(400, "facility_id is required")

    fac = db.query(Facility).filter(
        Facility.facility_id == facility_id,
        Facility.org_id == user.org_id
    ).first()

    if not fac:
        raise HTTPException(404, "Facility not found or not part of your organization")

    # Quantity
    try:
        qty = Decimal(str(payload.get("quantity")))
    except:
        raise HTTPException(400, "Quantity must be numeric")

    # Activity date
    act_date = parse_date(payload.get("activity_date"))

    # ActivityType resolution
    activity_type_id = payload.get("activity_type_id")
    type_row = None
    if activity_type_id:
        type_row = db.query(ActivityType).filter(ActivityType.activity_type_id == activity_type_id).first()
        if not type_row:
            raise HTTPException(400, "Invalid activity_type_id")
    else:
        # Legacy fallback: use free-text label
        label = (payload.get("activity_type") or "").strip()
        type_row = db.query(ActivityType).filter(ActivityType.label.ilike(label)).first()

    if not type_row:
        raise HTTPException(400, "Unknown activity type")

    # Unit resolution
    unit_id = payload.get("unit_id")
    unit_row = None
    if unit_id:
        unit_row = db.query(Unit).filter(Unit.unit_id == unit_id).first()
        if not unit_row:
            raise HTTPException(400, "Invalid unit_id")
    else:
        # Fallback to default unit for type
        unit_row = type_row.default_unit

    if not unit_row:
        raise HTTPException(400, "No valid unit available")

    # Emission factor selection
    factor_id = payload.get("factor_id")
    factor_row = None

    if factor_id:
        factor_row = db.query(EmissionFactor).filter(EmissionFactor.factor_id == factor_id).first()
        if not factor_row:
            raise HTTPException(400, "Invalid factor_id")
    else:
        # Auto-factor selection: category + unit match
        factor_row = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.category.ilike(type_row.label),
                EmissionFactor.unit.ilike(f"%{unit_row.code}%")
            )
            .order_by(EmissionFactor.year.desc())
            .first()
        )

    co2e = compute_co2e(qty, factor_row)

    # Create activity
    activity = ActivityLog(
        facility_id=facility_id,
        factor_id=factor_row.factor_id if factor_row else None,
        activity_type=type_row.label,      # legacy compatibility
        quantity=qty,
        unit=unit_row.code,                # legacy compatibility
        activity_date=act_date,
        activity_type_id=type_row.activity_type_id,
        unit_id=unit_row.unit_id,
        co2e_kg=co2e,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return {
        "activity_id": activity.activity_id,
        "facility_id": activity.facility_id,
        "activity_type": activity.activity_type,
        "quantity": str(activity.quantity),
        "unit": activity.unit,
        "date": activity.activity_date.isoformat(),
        "co2e_kg": str(activity.co2e_kg) if activity.co2e_kg is not None else None,
        "factor_id": activity.factor_id,
    }


# ------------------------------------------------------
# POST /api/activities/quick/{facility_id}
# Dynamic Quick Metrics
# ------------------------------------------------------
@router.post("/activities/quick/{facility_id}")
def quick_metrics(
    facility_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    fac = db.query(Facility).filter(
        Facility.facility_id == facility_id,
        Facility.org_id == user.org_id
    ).first()

    if not fac:
        raise HTTPException(404, "Facility not found")

    # Dynamic quick metrics: allow ANY activity_type.* fields
    # Example payload:
    # { "electricity": 500, "diesel": 200, "water": 20 }
    created = []

    for key, raw_val in payload.items():

        if raw_val in (None, "", 0, "0"):
            continue

        # find matching ActivityType by code
        type_row = db.query(ActivityType).filter(ActivityType.code == key).first()
        if not type_row:
            raise HTTPException(400, f"Unknown quick metric type '{key}'")

        # unit
        unit_row = type_row.default_unit
        if not unit_row:
            raise HTTPException(400, f"No default unit defined for quick metric '{key}'")

        try:
            qty = Decimal(str(raw_val))
        except:
            raise HTTPException(400, f"Value for {key} must be numeric")

        # auto-factor selection
        factor_row = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.category.ilike(type_row.label),
                EmissionFactor.unit.ilike(f"%{unit_row.code}%")
            )
            .order_by(EmissionFactor.year.desc())
            .first()
        )

        co2e = compute_co2e(qty, factor_row)

        act = ActivityLog(
            facility_id=facility_id,
            factor_id=factor_row.factor_id if factor_row else None,
            activity_type=type_row.label,
            quantity=qty,
            unit=unit_row.code,
            activity_date=date.today(),      # Quick metrics use today's date
            activity_type_id=type_row.activity_type_id,
            unit_id=unit_row.unit_id,
            co2e_kg=co2e,
        )
        db.add(act)
        db.flush()  # so activity_id is available

        created.append({
            "activity_id": act.activity_id,
            "type": type_row.label,
            "quantity": str(qty),
            "unit": unit_row.code,
            "co2e_kg": str(co2e) if co2e is not None else None,
        })

    if not created:
        raise HTTPException(400, "No valid quick metrics submitted")

    db.commit()
    return {"facility_id": facility_id, "created": created}


# ------------------------------------------------------
# GET /api/activities
# ------------------------------------------------------
@router.get("/activities")
def list_activities(db: Session = Depends(get_db), user=Depends(get_current_user)):
    activities = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == user.org_id)
        .order_by(ActivityLog.activity_date.desc())
        .all()
    )

    return [
        {
            "activity_id": a.activity_id,
            "facility_id": a.facility_id,
            "activity_type": a.activity_type,
            "quantity": float(a.quantity or 0),
            "unit": a.unit,
            "activity_date": a.activity_date.isoformat() if a.activity_date else None,
            "co2e_kg": float(a.co2e_kg or 0),
            "factor_id": a.factor_id,
        }
        for a in activities
    ]


# ------------------------------------------------------
# DELETE /api/activities/{id}
# ------------------------------------------------------
@router.delete("/activities/{activity_id}")
def delete_activity(activity_id: int,
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):

    act = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(ActivityLog.activity_id == activity_id,
                Facility.org_id == user.org_id)
        .first()
    )

    if not act:
        raise HTTPException(404, "Activity not found")

    db.delete(act)
    db.commit()

    return {"deleted": activity_id}
