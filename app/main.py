# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .Routers import (
    auth,
    facilities,
    activities,
    factors,
    reports,
    targets,
    forecast,
    planner
)
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

templates = Jinja2Templates(directory="app/templates")

app = FastAPI()

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ---------------------------------------------------
# Static files (CSS, JS)
# ---------------------------------------------------
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------
# PUBLIC PAGE ROUTES (must be FIRST)
# These serve HTML pages in /templates
# ---------------------------------------------------
app.include_router(auth.pages)
app.include_router(facilities.pages)
app.include_router(activities.pages)
app.include_router(factors.pages)
app.include_router(reports.pages)
app.include_router(targets.pages)
app.include_router(forecast.pages)
app.include_router(planner.pages)

# ---------------------------------------------------
# API ROUTES (JSON only)
# ---------------------------------------------------
app.include_router(auth.router)
app.include_router(facilities.api)
app.include_router(activities.api)
app.include_router(factors.api)
app.include_router(reports.api)
app.include_router(targets.api)
app.include_router(forecast.api)
app.include_router(planner.api)
