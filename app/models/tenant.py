"""
Tenant model - represents an organization/company
"""
from sqlalchemy import Column, BigInteger, String, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tenant(Base):
    """Tenant model for multi-tenant architecture"""
    __tablename__ = "tenants"
    
    # Primary key
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    website_url = Column(String(512), nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Status
    status = Column(
        Enum('active', 'inactive', 'suspended', name='tenant_status'),
        nullable=False,
        default='active'
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        server_default=func.current_timestamp()
    )
    modified_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        server_default=func.current_timestamp()
    )
    
    # Relationships (one tenant has many users)
    users = relationship("TenantUser", back_populates="tenant")

