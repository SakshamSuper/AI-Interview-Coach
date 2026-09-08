import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.backend.schemas.profiles import ResumeUploadResponse, CandidateProfile
from app.backend.dependencies.db import get_db
from database.repositories.user_repository import UserRepository
from nlp.preprocessing import extract_text_from_file, clean_text
from nlp.resume_parser import resume_parser
from config.settings import get_settings

router = APIRouter(prefix="/resumes", tags=["Resumes"])
settings = get_settings()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Only PDF, DOCX, and TXT are supported."
        )

    # Save to disk securely
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text & parse profile
        raw_text = extract_text_from_file(file_path)
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract readable text from document.")

        profile = resume_parser.parse(raw_text, file.filename)

        # Save to database
        repo = UserRepository(db)
        resume_record = repo.save_resume(
            user_id=user_id,
            filename=file.filename,
            file_type=ext.replace(".", ""),
            raw_text=raw_text,
            parsed_profile=profile.model_dump()
        )

        return ResumeUploadResponse(
            resume_id=resume_record.id,
            filename=file.filename,
            profile=profile
        )

    finally:
        # Clean up temporary uploaded file if desired or keep in uploads
        pass


@router.get("/{resume_id}", response_model=ResumeUploadResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    rec = repo.get_resume(resume_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Resume not found.")
    try:
        profile = resume_parser.parse(rec.raw_text, rec.filename) if rec.raw_text else CandidateProfile(**rec.parsed_profile)
    except Exception:
        profile = CandidateProfile(**rec.parsed_profile)
    return ResumeUploadResponse(
        resume_id=rec.id,
        filename=rec.filename,
        profile=profile
    )
