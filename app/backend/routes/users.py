from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.backend.schemas.common import UserCreateRequest, UserResponse
from app.backend.dependencies.db import get_db
from database.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse)
def create_user(req: UserCreateRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_or_create_user(name=req.name, email=req.email, target_role=req.target_role)
    return user


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    repo = UserRepository(db)
    return repo.list_users()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
