# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .database import engine, Base, SessionLocal, get_db
from .security import get_current_user

# Routers
from .Routers import auth as auth_router
from .Routers import activities as activities_router
from .Routers import factors as factors_router
from .Routers import facilities as facilities_router
from .Routers import reports, forecast, planner
from .Routers import profile as profile_router
from .Routers import files as files_router
from .Routers import targets as targets_router

from .seed import seed_all


# ---------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------
# STARTUP: create tables + seed
# ---------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


# ---------------------------------------------------------------
# PAGE ROUTES (HTML)
# ---------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/logout", response_class=HTMLResponse)
def logout_page(request: Request):
    return templates.TemplateResponse("logout.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/files", response_class=HTMLResponse)
def files_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("files.html", {"request": request})


@app.get("/facilities", response_class=HTMLResponse)
def facilities_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("facilities_list.html", {"request": request})


@app.get("/facilities/{facility_id}", response_class=HTMLResponse)
def facility_detail_page(facility_id: int, request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "facility_detail.html",
        {"request": request, "FACILITY_ID": facility_id}
    )


@app.get("/factors", response_class=HTMLResponse)
def factors_page_route(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_list.html", {"request": request})


@app.get("/factors/import", response_class=HTMLResponse)
def factors_import_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_import.html", {"request": request})


@app.get("/activities/new", response_class=HTMLResponse)
def activities_new_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("activities_new.html", {"request": request})


@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports_overview.html", {"request": request})


@app.get("/forecast", response_class=HTMLResponse)
def forecast_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("forecast.html", {"request": request})


@app.get("/planner", response_class=HTMLResponse)
def planner_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("planner.html", {"request": request})


@app.get("/targets", response_class=HTMLResponse)
def targets_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("targets.html", {"request": request})


# ---------------------------------------------------------------
# API ROUTERS
# ---------------------------------------------------------------
app.include_router(auth_router.router)

# Facilities
app.include_router(facilities_router.router)   # prefix already /api/facilities inside file

# Factors
app.include_router(factors_router.router)      # prefix /api/factors

# Activities (logs + quick metrics)
app.include_router(activities_router.router)   # prefix /api/activities

# Reports
app.include_router(reports.router)             # prefix /api/reports

# Forecast (no pages router anymore)
app.include_router(forecast.router)            # prefix /api/forecast

# Planner
app.include_router(planner.router)             # prefix /api/planner

# Targets
app.include_router(targets_router.router)      # prefix /api/targets

# Files uploads
app.include_router(files_router.router)        # prefix /api/files

# Profile updates
app.include_router(profile_router.router)      # prefix inside module

