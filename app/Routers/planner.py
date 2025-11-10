# app/Routers/planner.py
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from ..security import get_current_user

router = APIRouter(prefix="/api/planner", tags=["planner"])
pages = APIRouter(tags=["planner:pages"])

templates = Jinja2Templates(directory="app/templates")

# -------- PAGE ROUTES (HTML) --------
@pages.get("/planner", response_class=HTMLResponse)
def planner_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("planner.html", {"request": request})

# -------- API ROUTES (JSON) --------
@router.post("/evaluate")
def evaluate_actions(payload: dict, user=Depends(get_current_user)):
    """
    payload actions (placeholders):
      {
        "led_retrofit_pct": 50,        # percent of facilities lighting converted
        "solar_share_pct": 25,         # percent annual kWh from solar
        "fleet_hybrid_pct": 30         # percent fleet moved to hybrid/EV
      }
    """
    led = float(payload.get("led_retrofit_pct", 0))
    solar = float(payload.get("solar_share_pct", 0))
    fleet = float(payload.get("fleet_hybrid_pct", 0))

    # fake impact math; replace with real factors later
    baseline = 12000.0
    led_cut = baseline * (led / 100.0) * 0.12
    solar_cut = baseline * (solar / 100.0) * 0.30
    fleet_cut = baseline * (fleet / 100.0) * 0.15

    total_cut = led_cut + solar_cut + fleet_cut
    projected = max(baseline - total_cut, 0)

    return {
        "baseline_kg_co2e": baseline,
        "reductions": {
            "led_retrofit": round(led_cut, 2),
            "solar": round(solar_cut, 2),
            "fleet": round(fleet_cut, 2)
        },
        "projected_kg_co2e": round(projected, 2),
        "unit": "kg CO2e"
    }
