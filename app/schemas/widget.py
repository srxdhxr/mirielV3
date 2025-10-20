from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============= Widget Customization Schemas =============

class WidgetCustomizationBase(BaseModel):
    """Base schema for widget customization"""
    chatbot_name: str = Field(default='Chat Support', max_length=100)
    chat_header_color: str = Field(default='#007bff', pattern='^#[0-9A-Fa-f]{6}$')
    close_icon_color: str = Field(default='#ffffff', pattern='^#[0-9A-Fa-f]{6}$')
    chat_bg_color: str = Field(default='#f8f9fa', pattern='^#[0-9A-Fa-f]{6}$')
    ai_bubble_color: str = Field(default='#ffffff', pattern='^#[0-9A-Fa-f]{6}$')
    human_bubble_color: str = Field(default='#007bff', pattern='^#[0-9A-Fa-f]{6}$')
    text_box_color: str = Field(default='#ffffff', pattern='^#[0-9A-Fa-f]{6}$')
    send_button_color: str = Field(default='#007bff', pattern='^#[0-9A-Fa-f]{6}$')


class WidgetCustomizationUpdate(WidgetCustomizationBase):
    """Schema for updating widget customization"""
    pass


class WidgetCustomizationResponse(WidgetCustomizationBase):
    """Schema for widget customization response"""
    id: int
    widget_id: int
    
    class Config:
        from_attributes = True


# ============= Widget Schemas =============

class WidgetCreate(BaseModel):
    """Schema for creating a widget (admin only)"""
    tenant_id: int


class WidgetResponse(BaseModel):
    """Schema for widget response"""
    id: int
    tenant_id: int
    api_key: str
    status: str
    created_at: datetime
    customization: Optional[WidgetCustomizationResponse] = None
    
    class Config:
        from_attributes = True


class WidgetConfigResponse(BaseModel):
    """Public schema for widget configuration (loaded by widget.js)"""
    tenant_id: int
    chatbot_name: str
    colors: WidgetCustomizationBase
    company_name: Optional[str] = None


class WidgetEmbedCodeResponse(BaseModel):
    """Schema for embed code response"""
    embed_code: str
    widget_url: str
    api_key: str

