from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# === For user registration/login ===
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# === User response ===
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    bot_active: Optional[bool] = False
    created_at: datetime

    class Config:
        orm_mode = True

# === Token response ===
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str
