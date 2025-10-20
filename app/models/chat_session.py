from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    """Chat session model - tracks anonymous conversations between website visitors and AI"""
    
    __tablename__ = "chat_sessions"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp(), server_default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp(), server_default=func.current_timestamp())
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    tenant = relationship("Tenant")

