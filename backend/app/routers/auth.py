"""Login for both authors and admins."""
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
    """`username` is the email. Standard OAuth2 form so the Swagger Authorize button works."""
    email = form.username.strip().lower()

    author = db.query(Author).filter(Author.email == email).first()
    if author and verify_password(form.password, author.hashed_password):
        token = create_access_token(user_id=author.id, role="author")
        return Token(access_token=token, role="author", name=author.name)

    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(form.password, admin.hashed_password):
        token = create_access_token(user_id=admin.id, role="admin")
        return Token(access_token=token, role="admin", name=admin.name)

    # same message for wrong email and wrong password
    raise HTTPException(status_code=401, detail="Incorrect email or password")


@router.get("/me", tags=["auth"])
def who_am_i(principal: Principal = Depends(get_current_principal)):
    """used by the frontend on page reload"""
    name = principal.author.name if principal.role == "author" else principal.admin.name
    return {"role": principal.role, "name": name, "id": principal.id}
