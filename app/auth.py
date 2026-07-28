from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    if len(password) > 72:
        raise ValueError("Password cannot be longer than 72 characters")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


from sqlalchemy.orm import Session
from . import models
from .auth import verify_password

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if user is None:
        return None

    if not verify_password(password, user.password):
        return None

    return user