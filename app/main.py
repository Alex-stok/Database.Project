# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

# Routers
from app.Routers import (
    auth,
    facilities,
    activities,
    factors,
    reports,
    targets,
    forecast,
    planner,
)

app = FastAPI(title="CarbonOps Production")

# Static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Pages
app.include_router(facilities.pages)
app.include_router(activities.pages)
app.include_router(factors.pages)
app.include_router(reports.pages)
app.include_router(targets.pages)
app.include_router(forecast.pages)
app.include_router(planner.pages)

# API Routers
app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(activities.router)
app.include_router(factors.router)
app.include_router(reports.router)
app.include_router(targets.router)
app.include_router(forecast.router)
app.include_router(planner.router)

@app.get("/")
def root():
    return {"status": "ok"}
