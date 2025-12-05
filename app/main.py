# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

# Import routers
from app.Routers import (
    auth,
    facilities,
    activities,
    factors,
    reports,
    forecast,
    planner,
    targets
)

app = FastAPI()

# ---------------------------
# Static files
# ---------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates   # ← add this line


# ---------------------------
# ROOT → LANDING PAGE
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})  # ← changed file name


# ---------------------------
# DASHBOARD PAGE (REQUIRED)
# ---------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# =======================================================
# PAGE ROUTERS (ALL FRONT-END HTML PAGES)
# These MUST be included or nothing loads visually.
# =======================================================

app.include_router(auth.pages)          # login + logout pages
app.include_router(facilities.pages)    # facility list + detail
app.include_router(activities.pages)    # new activity form
app.include_router(factors.pages)       # emission factor pages
app.include_router(reports.pages)       # reports UI
app.include_router(forecast.pages)      # forecasting UI
app.include_router(planner.pages)       # planner UI
app.include_router(targets.pages)       # emissions target page


# =======================================================
# API ROUTERS (ALL BACK-END JSON ENDPOINTS)
# =======================================================

app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(activities.router)
app.include_router(factors.router)
app.include_router(reports.router)
app.include_router(forecast.router)
app.include_router(planner.router)
app.include_router(targets.router)


# ---------------------------
# Optional Redirect for /home
# ---------------------------
@app.get("/home")
def home_redirect():
    return RedirectResponse("/dashboard")
