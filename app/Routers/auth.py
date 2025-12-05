# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi import Form
from fastapi.responses import JSONResponse, HTMLResponse
from ..database import get_db
from ..models import User, Organization
from ..schemas import UserCreate, UserOut, Token
from ..security import hash_password, verify_password, create_access_token
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/api/auth", tags=["auth"])
pages = APIRouter(tags=["auth:pages"])

@pages.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@pages.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org_id = None
    if payload.org_name:
        org = db.query(Organization).filter(Organization.name == payload.org_name).first()
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
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.user_id)})
    
    resp = JSONResponse({"access_token": token, "token_type": "bearer"})
    resp.set_cookie(
        key="access_token",
        value=f"Bearer {token}",   # NOTE: "Bearer " prefix
        httponly=True,
        secure=False,               # True in prod behind HTTPS
        samesite="lax",
        path="/",
        max_age=60*60*24
    )
    return resp


@router.get("/me", response_model=UserOut)
def me():
    raise HTTPException(status_code=501, detail="Not implemented yet")
