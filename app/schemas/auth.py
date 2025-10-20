"""
Pydantic schemas for authentication
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=1, description="User password")


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds
    
    # User info
    user_id: int
    tenant_id: int
    email: str
    name: str
    role: str


class UserInfo(BaseModel):
    """Schema for current user info"""
    user_id: int
    tenant_id: int
    email: str
    name: str
    role: str
    
    class Config:
        from_attributes = True