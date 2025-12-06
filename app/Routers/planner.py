# app/Routers/planner.py
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..security import get_current_user
from ..models import ActionLibrary, OrgAction, Facility, ActivityLog

router = APIRouter(prefix="/api/planner", tags=["planner"])
pages = APIRouter(tags=["planner:pages"])


@pages.get("/planner", response_class=HTMLResponse)
def planner_page(request: Request, user=Depends(get_current_user)):
    return request.app.state.templates.TemplateResponse(
        "planner.html",
        {"request": request},
    )

# ----------------------------
# Action library management
# ----------------------------
@router.get("/library")
def get_library(db: Session = Depends(get_db)):
    return db.query(ActionLibrary).all()


@router.post("/library")
def add_action(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    a = ActionLibrary(
        code=payload["code"],
        name=payload["name"],
        description=payload.get("description"),
        expected_reduction_pct=payload.get("expected_reduction_pct"),
        default_capex_usd=payload.get("default_capex_usd"),
        default_life_years=payload.get("default_life_years"),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"created": True, "id": a.action_id}

# ----------------------------
# Apply an action to org/facility
# ----------------------------
@router.post("/apply")
def apply_action(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fac_id = payload.get("facility_id")

    if fac_id:
        fac = (
            db.query(Facility)
            .filter(Facility.facility_id == fac_id, Facility.org_id == user.org_id)
            .first()
        )
        if not fac:
            raise HTTPException(403, "Invalid facility")

    # currently red_pct not used directly; we still accept it so payload stays flexible
    red_pct = Decimal(str(payload.get("estimated_reduction_pct", 0))) / Decimal("100")
    capex = Decimal(str(payload.get("capex_usd", 0)))

    act = OrgAction(
        org_id=user.org_id,
        action_id=payload["action_id"],
        facility_id=fac_id,
        est_reduction_kg=payload.get("est_reduction_kg"),
        est_capex_usd=capex,
        planned_year=payload.get("planned_year"),
        status="planned",
    )
    db.add(act)
    db.commit()
    return {"applied": True}

# ----------------------------
# Planner evaluation endpoint
# ----------------------------

@router.post("/evaluate")
def evaluate_plan(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Evaluate a simple reduction scenario based on sliders from planner.html.

    Expects JSON body like:
    {
      "led_retrofit_pct": 50,
      "solar_share_pct": 25,
      "fleet_hybrid_pct": 30
    }
    """

    # Read slider values (default to 0 if missing)
    led = float(payload.get("led_retrofit_pct", 0) or 0.0)
    solar = float(payload.get("solar_share_pct", 0) or 0.0)
    fleet = float(payload.get("fleet_hybrid_pct", 0) or 0.0)

    # Baseline: total CO2e from all activities for this org
    baseline_co2e = (
        db.query(func.coalesce(func.sum(ActivityLog.co2e_kg), 0))
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == user.org_id)
        .scalar()
    )

    # Very simple toy model:
    #   LED retrofits -> 10% of their slider value
    #   Solar share   -> 50% of slider value
    #   Fleet hybrid  -> 30% of slider value
    reduction_fraction = (
        (led / 100.0) * 0.10 +
        (solar / 100.0) * 0.50 +
        (fleet / 100.0) * 0.30
    )
    if reduction_fraction > 1.0:
        reduction_fraction = 1.0

    baseline = float(baseline_co2e)
    reduction_kg = baseline * reduction_fraction
    projected_kg = baseline - reduction_kg

    return {
        "inputs": {
            "led_retrofit_pct": led,
            "solar_share_pct": solar,
            "fleet_hybrid_pct": fleet,
        },
        "baseline_co2e_kg": baseline,
        "estimated_reduction_fraction": reduction_fraction,
        "estimated_reduction_kg": reduction_kg,
        "projected_emissions_kg": projected_kg,
    }


@router.get("/evaluate")
def evaluate_help():
    """
    Convenience endpoint so visiting /api/planner/evaluate in the browser
    doesn't 404. The real logic is the POST above.
    """
    return {"message": "POST JSON to /api/planner/evaluate to evaluate a plan."}
