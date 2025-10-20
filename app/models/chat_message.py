from sqlalchemy import Column, BigInteger, String, Text, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatMessage(Base):
    """Chat message model - stores individual messages in a conversation"""
    
    __tablename__ = "chat_messages"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum('human', 'ai', name='message_role'), nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)  # For sources, confidence, etc. (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp(), server_default=func.current_timestamp())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

