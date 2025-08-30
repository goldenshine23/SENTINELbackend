from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session
from app.auth import router as auth_router
from app.bot import bot_router
from app.auth import auth_router
from app.auth import get_current_user

from app import models, schemas, auth, database
from app.auth import (
    router as auth_router,
    get_current_user,
    register_user,
    login,
    reset_password,
    change_password,
)
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from execution import run_trading_for_user

# --- Main Unified Router ---
router = APIRouter()

# --- Include all /api/auth endpoints from auth.py ---
router.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# --- Additional Pydantic Models ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# --- Extra Auth Routes (if needed) ---
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(data.username, data.email, data.password, db)

@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(form_data, db)

@router.post("/forgot-password")
def forgot(email: str = Form(...)):
    raise HTTPException(status_code=501, detail="Forgot password not implemented")

@router.post("/reset-password")
def reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    return reset_password(data.token, data.new_password, db)

@router.post("/change-password")
def change(data: ChangePasswordRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return change_password(user, data.old_password, data.new_password, db)

@router.get("/me")
def get_profile(user=Depends(get_current_user)):
    return {"user": user}

# --- Manual Auth Routes ---
@router.post("/manual-register", response_model=schemas.UserResponse)
def manual_register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, full_name=user.full_name, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/manual-login", response_model=schemas.TokenResponse)
def manual_login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

# --- Bot Control ---
@router.post("/bot/start")
def start_bot(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.bot_active = True
    db.commit()
    return {"message": "Bot started for user"}

@router.post("/bot/stop")
def stop_bot(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.bot_active = False
    db.commit()
    return {"message": "Bot stopped for user"}

# --- Trade Execution ---
@router.post("/trade/{user_id}")
async def trade_for_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await run_trading_for_user(user)
    return {"message": f"Trade executed for user {user.username}"}

# --- Debug / Utility ---
@router.get("/users")
def get_users():
    return {"message": "Users endpoint works"}

@router.get("/")
def read_root():
    return {"message": "Welcome to SentinelAI"}
# app/routes.py

from fastapi import APIRouter
from app.auth import auth_router

router = APIRouter()

# Mount auth endpoints under /auth
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# app/routes.py

from fastapi import APIRouter
from app.auth import auth_router
from app.bot import bot_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(bot_router, prefix="/bot", tags=["bot"])
# app/routes.py

from fastapi import APIRouter
from . import auth

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
from fastapi import APIRouter
from app.auth import auth_router
from app.bot import bot_router

router = APIRouter()

router.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
router.include_router(bot_router, prefix="/api/bot", tags=["Bot"])
from app.auth import auth_router
router.include_router(auth_router)
from app.bot import bot_router
router.include_router(bot_router)
from app.auth import router as auth_router  # ✅ No need to import `reset_password` or `change_password`
from fastapi import APIRouter
from app.auth import auth_router  # Make sure this import works
from app.bot import bot_router

router = APIRouter()

# Include auth routes
router.include_router(auth_router, prefix="/auth", tags=["auth"])

# Include bot routes
router.include_router(bot_router, prefix="/api/bot", tags=["bot"])
