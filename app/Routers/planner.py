# app/Routers/planner.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from collections import defaultdict

from ..database import get_db
from ..security import get_current_user
from ..models import OrgAction, ActionLibrary, Facility, ActivityLog

router = APIRouter(prefix="/api/planner", tags=["planner"])


# ---------------------------------------------------------
# Compute current org emissions
# ---------------------------------------------------------
def compute_current_emissions(db: Session, org_id: int) -> Decimal:
    rows = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == org_id)
        .all()
    )

    total = Decimal("0")
    for r in rows:
        if r.co2e_kg:
            total += Decimal(str(r.co2e_kg))

    return total


# ---------------------------------------------------------
# Create an organization action
# ---------------------------------------------------------
@router.post("/action")
def add_action(payload: dict,
               db: Session = Depends(get_db),
               user=Depends(get_current_user)):

    action_id = payload.get("action_id")
    lib = db.query(ActionLibrary).filter(ActionLibrary.action_id == action_id).first()
    if not lib:
        raise HTTPException(400, "Unknown action_id")

    oa = OrgAction(
        org_id=user.org_id,
        action_id=action_id,
        facility_id=payload.get("facility_id"),
        custom_params=payload.get("custom_params") or {},
        est_reduction_kg=None,
        est_capex_usd=payload.get("capex"),
        planned_year=payload.get("year"),
        status="planned",
    )

    db.add(oa)
    db.commit()
    db.refresh(oa)

    return {"org_action_id": oa.org_action_id}


# ---------------------------------------------------------
# Evaluate savings
# ---------------------------------------------------------
@router.get("/impact")
def impact(db: Session = Depends(get_db), user=Depends(get_current_user)):

    actions = db.query(OrgAction).filter(OrgAction.org_id == user.org_id).all()
    baseline = compute_current_emissions(db, user.org_id)

    total_reduction = Decimal("0")
    breakdown = []

    for a in actions:
        pct = Decimal(str(a.action.expected_reduction_pct or 0)) / Decimal("100")
        red = baseline * pct

        breakdown.append({
            "action": a.action.name,
            "expected_pct": float(pct * 100),
            "reduction_kg": float(red),
        })

        total_reduction += red

    return {
        "baseline_emissions_kg": float(baseline),
        "total_reduction_kg": float(total_reduction),
        "projected_after_actions_kg": float(baseline - total_reduction),
        "actions": breakdown,
    }
