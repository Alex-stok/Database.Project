# app/Routers/forecast.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
from decimal import Decimal
from datetime import date

from ..database import get_db
from ..security import get_current_user
from ..models import ForecastScenario, ActivityLog, ActivityType, Facility

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


# ---------------------------------------------------------
# Load historical data grouped by year & activity type
# ---------------------------------------------------------
def compute_historical_baseline(db: Session, org_id: int):

    rows = (
        db.query(ActivityLog)
        .join(Facility, ActivityLog.facility_id == Facility.facility_id)
        .filter(Facility.org_id == org_id)
        .all()
    )

    baseline = defaultdict(lambda: defaultdict(Decimal))  # {year: {type: total_qty}}

    for r in rows:
        if not r.activity_date:
            continue
        year = r.activity_date.year
        baseline[year][r.activity_type] += Decimal(str(r.quantity or 0))

    return baseline


# ---------------------------------------------------------
# Create scenario
# ---------------------------------------------------------
@router.post("/scenario")
def create_scenario(payload: dict,
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):

    scen = ForecastScenario(
        org_id=user.org_id,
        name=payload["name"],
        description=payload.get("description"),
        annual_growth_pct=payload.get("annual_growth_pct") or 0,
        renewable_share_pct=payload.get("renewable_share_pct") or 0,
        start_year=payload["start_year"],
        end_year=payload["end_year"],
        created_by=user.user_id,
    )

    db.add(scen)
    db.commit()
    db.refresh(scen)

    return {"scenario_id": scen.scenario_id}
    

# ---------------------------------------------------------
# Compute forecast for scenario
# ---------------------------------------------------------
@router.get("/scenario/{scenario_id}")
def run_scenario(scenario_id: int,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):

    scen = db.query(ForecastScenario).filter(
        ForecastScenario.scenario_id == scenario_id,
        ForecastScenario.org_id == user.org_id
    ).first()

    if not scen:
        raise HTTPException(404, "Scenario not found")

    baseline = compute_historical_baseline(db, scen.org_id)

    if not baseline:
        raise HTTPException(400, "No historical activity data to forecast")

    # Use most recent available year as baseline
    base_year = max(baseline.keys())
    base_data = baseline[base_year]

    growth = Decimal(str(scen.annual_growth_pct)) / Decimal("100")
    renewable = Decimal(str(scen.renewable_share_pct)) / Decimal("100")

    projections = []

    for year in range(scen.start_year, scen.end_year + 1):

        factor = (Decimal("1") + growth) ** (year - scen.start_year)

        year_data = {}
        for activity_type, qty in base_data.items():

            q = qty * factor

            # Special rule: renewable adjusts ELECTRICITY CO₂ ONLY  
            if activity_type.lower() == "electricity":
                q = q * (Decimal("1") - renewable)

            year_data[activity_type] = float(q)

        projections.append({"year": year, "quantities": year_data})

    return {
        "scenario_id": scen.scenario_id,
        "name": scen.name,
        "baseline_year": base_year,
        "projections": projections,
    }
