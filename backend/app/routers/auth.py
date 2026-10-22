"""Login for both authors and admins."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Author, Admin
from ..auth import (
    COOKIE_NAME, verify_password, create_access_token, get_current_principal, Principal,
)
from ..config import settings
from ..ratelimit import login_limiter, client_key
from ..schemas import Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _start_session(request: Request, response: Response, key: str, token: str) -> None:
    login_limiter.reset(key)
    https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    response.set_cookie(
        COOKIE_NAME, token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True, secure=https, samesite="lax", path="/",
    )


@router.post("/login", response_model=Token)
def login(request: Request, response: Response,
          form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """`username` is the email. Standard OAuth2 form so the Swagger Authorize button works."""
    email = form.username.strip().lower()
    key = client_key(request, email)
    login_limiter.check(key)

    author = db.query(Author).filter(Author.email == email).first()
    if author and verify_password(form.password, author.hashed_password):
        token = create_access_token(user_id=author.id, role="author")
        _start_session(request, response, key, token)
        return Token(access_token=token, role="author", name=author.name)

    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(form.password, admin.hashed_password):
        token = create_access_token(user_id=admin.id, role="admin")
        _start_session(request, response, key, token)
        return Token(access_token=token, role="admin", name=admin.name)

    login_limiter.record_failure(key)
    # same message for wrong email and wrong password
    raise HTTPException(status_code=401, detail="Incorrect email or password")


@router.get("/me", tags=["auth"])
def who_am_i(principal: Principal = Depends(get_current_principal)):
    """used by the frontend on page reload"""
    name = principal.author.name if principal.role == "author" else principal.admin.name
    return {"role": principal.role, "name": name, "id": principal.id}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
