# app/routes_activities.py
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user
from ..models import ActivityLog, EmissionFactor
from ..schemas import ActivityCreate

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create a new activity log entry and compute CO2e using an emission factor.
    """

    # 1) Find a matching emission factor (very simple heuristic)
    factor = (
        db.query(EmissionFactor)
        .filter(
            EmissionFactor.category == payload.activity_type,
            EmissionFactor.unit.ilike(f"%{payload.unit}%"),
        )
        .first()
    )
    if not factor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No matching emission factor for this activity_type + unit. "
                   "Add factors first on the Emission Factors page.",
        )

    # 2) Compute CO2e
    qty = Decimal(str(payload.quantity))
    co2e_kg = qty * factor.factor  # factor.factor is Numeric(14,6)

    # 3) Insert ActivityLog row
    activity = ActivityLog(
        facility_id=payload.facility_id,
        factor_id=factor.factor_id,
        activity_type=payload.activity_type,
        quantity=qty,
        unit=payload.unit,
        activity_date=payload.activity_date,
        co2e_kg=co2e_kg,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity
