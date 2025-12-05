# app/main.py
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File,
    Form, Query
)
from .models import (
    Facility, EmissionFactor, ActivityLog, UploadedFile,
    Target, ActivityType, Organization
)
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from collections import defaultdict
from .database import engine, Base, SessionLocal, get_db
from .Routers import auth as auth_router
from .Routers import facilities as facilities_router
from .Routers import factors as factors_router
from .security import get_current_user
from .Routers import reports, forecast, planner
from .seed import seed_all
from .Routers import profile as profile_router
from .Routers import files as files_router
from .Routers import activities

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

# ---------- Page routes (HTML) ----------
@app.get("/logout", response_class=HTMLResponse)
def logout_page(request: Request):
    return templates.TemplateResponse("logout.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/files", response_class=HTMLResponse)
def files_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("files.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/targets", response_class=HTMLResponse)
def targets_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("targets.html", {"request": request})

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("reports_overview.html", {"request": request})


# ---------- Facilities API ----------

@app.get("/api/facilities")
def list_facilities(db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    return (
        db.query(Facility)
        .filter(Facility.org_id == user.org_id)
        .order_by(Facility.facility_id)
        .all()
    )


@app.post("/api/facilities")
def create_facility(payload: dict,
                    db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    # expected keys: name, location, grid_region_code
    fac = Facility(
        org_id=user.org_id,
        name=payload.get("name"),
        location=payload.get("location"),
        grid_region_code=payload.get("grid_region_code"),
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac

@app.post("/api/targets")
def create_target(payload: dict,
                  db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    t = Target(
        org_id=user.org_id,
        baseline_year=int(payload["baseline_year"]),
        baseline_co2e_kg=None,
        target_year=int(payload["target_year"]),
        reduction_percent=Decimal(str(payload["reduction_percent"])),
        created_by=user.user_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

# Factors pages (your HTML expects these exact paths)
@app.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_list.html", {"request": request})

@app.get("/factors/import", response_class=HTMLResponse)
def factors_import_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("factors_import.html", {"request": request})

# Activities page placeholder so /activities/new works
@app.get("/activities/new", response_class=HTMLResponse)
def activities_new_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("activities_new.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, user=Depends(get_current_user)):
    # Placeholder dashboard — you already wired this up
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
# ---------- end page routes ----------

app.include_router(auth_router.router)
app.include_router(facilities_router.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(facilities_router.pages)
app.include_router(factors_router.router,    prefix="/api/factors",    tags=["factors"])
app.include_router(reports.router)
app.include_router(reports.pages)
app.include_router(forecast.router)
app.include_router(forecast.pages)
app.include_router(planner.router)
app.include_router(planner.pages)
app.include_router(profile_router.router)
app.include_router(files_router.router)
app.include_router(activities.router)