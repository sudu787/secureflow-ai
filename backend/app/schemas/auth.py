"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = "analyst"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: str
    is_active: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
