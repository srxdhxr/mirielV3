"""
Pydantic schemas for tenant onboarding
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime


class OnboardingRequest(BaseModel):
    """Schema for onboarding a new tenant"""
    
    # Tenant info
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    website_url: str = Field(None, max_length=512, description="Company website URL")
    short_name: str = Field(..., min_length=2, max_length=100, description="Short name/slug for the tenant")
    
    # Root admin user info
    admin_name: str = Field(..., min_length=2, max_length=255, description="Admin user full name")
    admin_email: EmailStr = Field(..., description="Admin user email")
    password: str = Field(..., min_length=8, description="Admin user password")
    
    @field_validator('short_name')
    @classmethod
    def validate_short_name(cls, v):
        """Validate short name format"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Short name can only contain letters, numbers, hyphens, and underscores')
        return v.lower().strip()
    
    @field_validator('company_name', 'admin_name')
    @classmethod
    def validate_not_empty(cls, v):
        """Validate name fields are not empty"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class OnboardingResponse(BaseModel):
    """Schema for onboarding response"""
    
    # Tenant info
    tenant_id: int
    tenant_name: str
    tenant_slug: str
    
    # Admin user info
    admin_user_id: int
    admin_user_name: str
    admin_user_email: str
    admin_user_role: str
    
    # Success message
    message: str = "Tenant onboarded successfully"
    
    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)

