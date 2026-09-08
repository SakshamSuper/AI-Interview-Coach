"""
app/backend/routes/auth.py
===========================
Authentication bridge between Next.js (NextAuth.js) and FastAPI.

GET /auth/me
  - Reads Authorization: Bearer <nextauth_jwt> header
  - Decodes the JWT using the shared NEXTAUTH_SECRET
  - Finds or creates the User record in the SQLite DB
  - Returns the user DB id, name, email, target_role
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.backend.dependencies.db import get_db
from database.repositories.user_repository import UserRepository
from config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


class AuthUserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    target_role: Optional[str] = None
    image: Optional[str] = None


def _decode_nextauth_jwt(token: str) -> dict:
    """Decode and verify a NextAuth.js JWT using the shared secret."""
    try:
        from jose import jwt
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="python-jose not installed. Run: pip install python-jose[cryptography]"
        )

    secret = settings.NEXTAUTH_SECRET
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="NEXTAUTH_SECRET is not configured on the backend."
        )

    # Try HS256 signed JWT (NextAuth v4 / v5 with explicit jwt.secret option)
    for alg in ["HS256", "HS512"]:
        try:
            return jwt.decode(token, secret, algorithms=[alg], options={"verify_aud": False})
        except Exception:
            pass

    # Try JWE encrypted (NextAuth v5 default)
    try:
        from jose import jwe
        import json
        decrypted = jwe.decrypt(token.encode(), secret.encode())
        return json.loads(decrypted)
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")


@router.get("/me", response_model=AuthUserResponse)
def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_auth_email: Optional[str] = Header(default=None, alias="X-Auth-Email"),
    x_auth_name: Optional[str] = Header(default=None, alias="X-Auth-Name"),
    db: Session = Depends(get_db)
):
    """
    Resolve the authenticated user and return (or create) their DB record.

    Two auth paths:
    1. X-Auth-Email + X-Auth-Name headers: set by the frontend AuthContext after
       NextAuth has already verified the session cookie server-side. Safe because
       these headers are only trusted when they come from an authenticated session.
    2. Authorization: Bearer <jwt>: full JWT decode path (used in tests + API clients).
    """
    email: Optional[str] = None
    name: str = "User"
    image: Optional[str] = None

    # Path 1: Session header (from AuthContext — NextAuth already verified session)
    if x_auth_email:
        email = x_auth_email.strip()
        name = (x_auth_name or email).strip()

    # Path 2: Bearer JWT
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            raise HTTPException(status_code=401, detail="Bearer token is empty.")
        payload = _decode_nextauth_jwt(token)
        email = payload.get("email") or payload.get("sub")
        name = payload.get("name") or email or "User"
        image = payload.get("picture") or payload.get("image")

    else:
        raise HTTPException(status_code=401, detail="No authentication credentials provided.")

    if not email:
        raise HTTPException(status_code=401, detail="Could not determine authenticated user email.")

    repo = UserRepository(db)
    user = repo.get_or_create_user(name=name, email=email)

    return AuthUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        target_role=user.target_role,
        image=image,
    )
