# app/Routers/files.py
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..models import UploadedFile
from ..database import get_db
from ..security import get_current_user

router = APIRouter()

UPLOAD_ROOT = Path("uploads")
UPLOAD_ROOT.mkdir(exist_ok=True)

@router.post("/files/upload")
async def upload_file(
    purpose: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not user.org_id:
        raise HTTPException(status_code=400, detail="User is not attached to an organization")

    org_dir = UPLOAD_ROOT / f"org_{user.org_id}"
    org_dir.mkdir(parents=True, exist_ok=True)

    dest = org_dir / file.filename
    data = await file.read()
    with dest.open("wb") as f:
        f.write(data)

    rec = UploadedFile(
        org_id=user.org_id,
        user_id=user.user_id,
        purpose=purpose,
        storage_path=str(dest),
        original_name=file.filename,
        content_type=file.content_type,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/files/list")
def list_files(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    items = (
        db.query(UploadedFile)
        .filter(UploadedFile.org_id == user.org_id)
        .order_by(UploadedFile.uploaded_at.desc())
        .all()
    )
    return {"items": items}


@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rec = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.file_id == file_id,
            UploadedFile.org_id == user.org_id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        if rec.storage_path and os.path.exists(rec.storage_path):
            os.remove(rec.storage_path)
    except OSError:
        pass

    db.delete(rec)
    db.commit()
    return {"ok": True}