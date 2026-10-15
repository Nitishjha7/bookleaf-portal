"""
Authentication & authorisation.

- Passwords are hashed with bcrypt (never stored in plain text).
- Login returns a JWT that encodes the user's id and role.
- Three dependencies enforce access:
    get_current_author  -> route is author-only
    get_current_admin   -> route is admin-only
    get_current_principal -> either; used where both may read
RBAC is therefore enforced in one place and reused, not re-implemented per route.
"""
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Author, Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# --- password helpers -----------------------------------------------------
# We use the `bcrypt` library directly (rather than passlib) to avoid a known
# version-detection incompatibility between passlib 1.7 and bcrypt 4.x.
# bcrypt has a 72-byte input limit, so we encode and truncate defensively.

def hash_password(raw: str) -> str:
    pw = raw.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- token helpers --------------------------------------------------------

def create_access_token(*, user_id: int, role: Literal["author", "admin"]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- principal objects ----------------------------------------------------

class Principal:
    """A lightweight 'who is calling' object attached to the request."""
    def __init__(self, role: str, author: Author | None = None, admin: Admin | None = None):
        self.role = role
        self.author = author
        self.admin = admin

    @property
    def id(self) -> int:
        return self.author.id if self.role == "author" else self.admin.id


# --- dependencies ---------------------------------------------------------

def get_current_principal(token: str = Depends(oauth2_scheme),
                          db: Session = Depends(get_db)) -> Principal:
    data = _decode(token)
    user_id, role = int(data.get("sub", 0)), data.get("role")
    if role == "author":
        author = db.query(Author).get(user_id)
        if not author:
            raise HTTPException(status_code=401, detail="Author not found")
        return Principal("author", author=author)
    if role == "admin":
        admin = db.query(Admin).get(user_id)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin not found")
        return Principal("admin", admin=admin)
    raise HTTPException(status_code=401, detail="Unknown role in token")


def get_current_author(principal: Principal = Depends(get_current_principal)) -> Author:
    if principal.role != "author":
        raise HTTPException(status_code=403, detail="This route is for authors only")
    return principal.author


def get_current_admin(principal: Principal = Depends(get_current_principal)) -> Admin:
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="This route is for admins only")
    return principal.admin
