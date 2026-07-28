from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
 
from ..dependencies import get_db
from ..schemas import UserCreate, UserLogin
from .. import crud, models
 
router = APIRouter(prefix="/auth", tags=["Auth"])
 
 
# ---------------- REGISTER ----------------
@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_email = db.query(models.User).filter(
        models.User.email == user.email
    ).first()
 
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
 
    # Check if username already exists
    existing_username = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
 
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
 
    new_user = crud.create_user(db, user)
 
    return {
        "message": "Account created successfully",
        "user_id": new_user.id,
        "username": new_user.username,
    }
 
 
# ---------------- LOGIN ----------------
@router.post("/login")
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, credentials.email, credentials.password)
 
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
 
    request.session["user_id"] = user.id
    request.session["username"] = user.username
 
    return {
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
    }
 
 
# ---------------- LOGOUT ----------------
@router.get("/logout")
def logout(request: Request):
    request.session.clear()
 
    return {"message": "Logged out"}
 












