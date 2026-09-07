from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import numpy as np
from app.backend.dependencies.db import get_db
from database.repositories.interview_repository import InterviewRepository
from vision.feature_extraction import vision_pipeline

router = APIRouter(prefix="/vision", tags=["Computer Vision & Movement Analytics"])


class VisionAnalyzeRequest(BaseModel):
    session_id: int
    frame_count: Optional[int] = 30
    fps: Optional[float] = 30.0


class VisionAnalyzeResponse(BaseModel):
    session_id: int
    frame_count: int
    avg_posture_stability: float
    avg_movement_magnitude: float
    movement_frequency: float
    head_stability: float
    objective_observations: List[str]


@router.post("/analyze", response_model=VisionAnalyzeResponse)
def analyze_session_movement(req: VisionAnalyzeRequest, db: Session = Depends(get_db)):
    int_repo = InterviewRepository(db)
    session = int_repo.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Generate or process frame sequence
    frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(req.frame_count or 30)]
    metrics = vision_pipeline.process_frames(frames, fps=req.fps or 30.0)

    # Save to database
    int_repo.record_vision_metrics(
        session_id=req.session_id,
        avg_posture_stability=metrics["avg_posture_stability"],
        avg_movement_magnitude=metrics["avg_movement_magnitude"],
        movement_frequency=metrics["movement_frequency"],
        frame_count=metrics["frame_count"]
    )

    return VisionAnalyzeResponse(
        session_id=req.session_id,
        frame_count=metrics["frame_count"],
        avg_posture_stability=metrics["avg_posture_stability"],
        avg_movement_magnitude=metrics["avg_movement_magnitude"],
        movement_frequency=metrics["movement_frequency"],
        head_stability=metrics["head_stability"],
        objective_observations=metrics["objective_observations"]
    )
