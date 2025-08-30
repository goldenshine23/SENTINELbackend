from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Optional, Dict
from datetime import datetime, timedelta

# Local imports
from app.database import get_db, fake_users_db, get_user as get_user_from_db
from app.models import User as DBUser
from app.utils import hash_password, verify_password  # Optional utility functions

# === Config ===
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

auth_router = APIRouter()


# === Schemas ===
class User(BaseModel):
    username: str
    full_name: str
    email: str

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True


# === Utility functions ===
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_from_fake_db(username: str) -> Optional[UserInDB]:
    user = fake_users_db.get(username)
    return UserInDB(**user) if user else None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user_from_fake_db(username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user


# === Routes (mock database) ===
@auth_router.post("/register")
def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "hashed_password": hashed_password,
    }
    return {"msg": "User registered successfully"}

@auth_router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/users")
def get_users():
    return list(fake_users_db.keys())

@auth_router.post("/change-password")
def change_password(req: ChangePasswordRequest):
    user = get_user_from_fake_db(req.username)
    if not user or not pwd_context.verify(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    fake_users_db[req.username]["hashed_password"] = pwd_context.hash(req.new_password)
    return {"msg": "Password changed successfully"}

@auth_router.post("/reset-password")
def reset_password(username: str = Body(...), new_password: str = Body(...)):
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    fake_users_db[username]["hashed_password"] = pwd_context.hash(new_password)
    return {"msg": "Password reset successfully"}


# === Routes (SQLAlchemy DB version) ===
@auth_router.post("/db/register", response_model=UserOut)
def db_register(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = DBUser(email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@auth_router.post("/db/login", response_model=Token)
def db_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/db/users/{user_id}", response_model=UserOut)
def db_get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/register")
async def register_user(user_data: dict):
    return {"message": "User registered"}

@router.post("/login")
async def login_user(credentials: dict):
    return {"message": "Login successful"}
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

auth_router = APIRouter()

class UserIn(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@auth_router.post("/register")
def register_user(user: UserIn):
    # Your logic to create and save user
    return {"msg": "User registered"}

@auth_router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    # Your login logic
    return {"access_token": "fake-token", "token_type": "bearer"}
