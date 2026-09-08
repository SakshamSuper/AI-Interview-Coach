from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str
    database: str
    llm_provider: str
    vector_store: str
    knowledge_base_ready: bool
    version: str = "1.0.0"


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = None
    target_role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    target_role: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
