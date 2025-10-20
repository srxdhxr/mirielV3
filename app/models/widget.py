from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import secrets


class Widget(Base):
    """Widget model - represents a chat widget for a tenant"""
    
    __tablename__ = "widgets"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    api_key = Column(String(64), unique=True, nullable=False, index=True)  # Unique API key for widget
    status = Column(Enum('active', 'inactive', name='widget_status'), nullable=False, default='active')
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp(), server_default=func.current_timestamp())
    
    # Relationships
    tenant = relationship("Tenant")
    customization = relationship("WidgetCustomization", back_populates="widget", uselist=False, cascade="all, delete-orphan")
    
    @staticmethod
    def generate_api_key():
        """Generate a unique API key for the widget"""
        return f"mrw_{secrets.token_urlsafe(32)}"

