# app/Routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Organization
from ..schemas import UserCreate, UserOut, Token, ProfileUpdate
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

templates = Jinja2Templates(directory="app/templates")

# JSON auth endpoints (/api/auth/...)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# HTML pages (login/register)
pages = APIRouter(tags=["auth:pages"])

# JSON profile endpoints (/api/profile/...)
profile_router = APIRouter(prefix="/api/profile", tags=["profile"])


# ---------------------------
# Page routes
# ---------------------------
@pages.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@pages.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ---------------------------
# Auth API
# ---------------------------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org_id = None
    if payload.org_name:
        org = (
            db.query(Organization)
            .filter(Organization.name == payload.org_name)
            .first()
        )
        if not org:
            org = Organization(name=payload.org_name)
            db.add(org)
            db.flush()  # assigns id without commit
        org_id = org.org_id

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        org_id=org_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user.user_id)})

    resp = JSONResponse({"access_token": token, "token_type": "bearer"})
    resp.set_cookie(
        key="access_token",
        value=f"Bearer {token}",  # NOTE: "Bearer " prefix
        httponly=True,
        secure=False,  # True in prod behind HTTPS
        samesite="lax",
        path="/",
        max_age=60 * 60 * 24,
    )
    return resp


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    # Simple wrapper so other parts of the app can get the current user
    return current_user


# ---------------------------
# Profile API (/api/profile/me)
# matches profile.html JS: fetch('/api/profile/me', ...)
# ---------------------------
@profile_router.get("/me")
def get_profile_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = None
    if current_user.org_id:
        org = (
            db.query(Organization)
            .filter(Organization.org_id == current_user.org_id)
            .first()
        )

    return {
        "user": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
        },
        "organization": {
            "name": org.name if org else None,
            "industry": org.industry if org else None,
            "address": org.address if org else None,
            "size": org.size if org else None,
        },
    }


@profile_router.put("/me")
def update_profile_me(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update user
    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    org = None
    # If any org fields are supplied, update/create org
    if any(
        [
            payload.org_name,
            payload.org_industry,
            payload.org_address,
            payload.org_size,
        ]
    ):
        if current_user.org_id:
            org = (
                db.query(Organization)
                .filter(Organization.org_id == current_user.org_id)
                .first()
            )
        else:
            # Create a new org if user doesn't have one yet
            org = Organization(name=payload.org_name or current_user.email)
            db.add(org)
            db.flush()
            current_user.org_id = org.org_id

        if payload.org_name is not None:
            org.name = payload.org_name
        if payload.org_industry is not None:
            org.industry = payload.org_industry
        if payload.org_address is not None:
            org.address = payload.org_address
        if payload.org_size is not None:
            org.size = payload.org_size

    db.commit()
    db.refresh(current_user)

    if current_user.org_id and not org:
        org = (
            db.query(Organization)
            .filter(Organization.org_id == current_user.org_id)
            .first()
        )

    return {
        "user": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
        },
        "organization": {
            "name": org.name if org else None,
            "industry": org.industry if org else None,
            "address": org.address if org else None,
            "size": org.size if org else None,
        },
    }
