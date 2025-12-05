# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import routers (matches your actual files)
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


# ---------------------------
# Root → login
# ---------------------------
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ---------------------------
# PAGE ROUTERS ONLY FOR FILES THAT HAVE `pages`
# ---------------------------
app.include_router(facilities.pages)
app.include_router(activities.pages)
app.include_router(factors.pages)
app.include_router(reports.pages)
app.include_router(forecast.pages)
app.include_router(planner.pages)
# (targets has no pages router)

# ---------------------------
# API ROUTERS
# ---------------------------
app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(activities.router)
app.include_router(factors.router)
app.include_router(reports.router)
app.include_router(forecast.router)
app.include_router(planner.router)
app.include_router(targets.router)
