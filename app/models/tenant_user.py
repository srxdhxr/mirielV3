"""
Tenant User model - represents users within a tenant
"""
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TenantUser(Base):
    """User model belonging to a tenant"""
    __tablename__ = "tenant_users"
    
    # Primary key
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to tenant
    tenant_id = Column(
        BigInteger, 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # User info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Password (hashed)
    password_hash = Column(LargeBinary(64), nullable=False)
    password_salt = Column(LargeBinary(32), nullable=False)
    
    # Role
    role = Column(
        Enum('admin', 'user', name='user_role'),
        nullable=False,
        default='user'
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
    
    # Relationship (belongs to one tenant)
    tenant = relationship("Tenant", back_populates="users")

