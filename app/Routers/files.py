# app/Routers/files.py
import os
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..security import get_current_user

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/list")
def list_files(user=Depends(get_current_user)):
    items = []
    for name in os.listdir(UPLOAD_DIR):
        p = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(p):
            items.append({"name": name, "size": os.path.getsize(p)})
    return {"files": items}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"ok": True, "filename": file.filename}

# PAGE route for Files (renders templates/files.html)
@router.get("/page", response_class=HTMLResponse)
def files_page(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("files.html", {"request": request})
