"""
Authentication routes.

A single login endpoint serves both roles. We look the email up in the authors
table first, then the admins table, and issue a JWT stamped with the role. The
frontend uses the returned `role` to decide which portal to show.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Author, Admin
from ..auth import verify_password, create_access_token, get_current_principal, Principal
from ..schemas import Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 password form: `username` is the email, `password` is the password.
    (Using the standard form means Swagger's Authorize button works out of the box.)
    """
    email = form.username.strip().lower()

    author = db.query(Author).filter(Author.email == email).first()
    if author and verify_password(form.password, author.hashed_password):
        token = create_access_token(user_id=author.id, role="author")
        return Token(access_token=token, role="author", name=author.name)

    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(form.password, admin.hashed_password):
        token = create_access_token(user_id=admin.id, role="admin")
        return Token(access_token=token, role="admin", name=admin.name)

    # Same message whether the email or the password was wrong — don't leak
    # which emails exist.
    raise HTTPException(status_code=401, detail="Incorrect email or password")


@router.get("/me", tags=["auth"])
def who_am_i(principal: Principal = Depends(get_current_principal)):
    """Return the current user's role and name (used by the SPA on reload)."""
    name = principal.author.name if principal.role == "author" else principal.admin.name
    return {"role": principal.role, "name": name, "id": principal.id}
