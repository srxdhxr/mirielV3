from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= Chat Session Schemas =============

class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    tenant_id: int = Field(..., description="Tenant ID (from widget)")
    title: Optional[str] = Field(None, max_length=255, description="Optional session title")


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    tenant_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Schema for listing chat sessions"""
    sessions: List[ChatSessionResponse]
    total: int


# ============= Chat Message Schemas =============

class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    session_id: int
    role: str  # 'human' or 'ai'
    content: str
    meta: Optional[Dict[str, Any]] = None  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageListResponse(BaseModel):
    """Schema for listing messages in a session"""
    messages: List[ChatMessageResponse]
    total: int


# ============= Chat Request/Response Schemas =============

class ChatRequest(BaseModel):
    """Schema for sending a chat message"""
    tenant_id: int = Field(..., description="Tenant ID (from widget)")
    session_id: Optional[int] = Field(None, description="Chat session ID (creates new if not provided)")
    message: str = Field(..., min_length=1, max_length=5000, description="User message")


class ChatResponse(BaseModel):
    """Schema for chat response (synchronous)"""
    message_id: int = Field(..., description="ID of the AI message saved in DB")
    session_id: int
    content: str = Field(..., description="AI response content")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Top 3 source references")
    created_at: datetime

