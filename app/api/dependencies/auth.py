"""
Authentication dependencies for protected routes
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import verify_token
from app.models.tenant_user import TenantUser

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TenantUser:
    """
    Dependency to get current authenticated user from JWT token
    
    Usage in endpoint:
        @router.get("/protected")
        def protected_route(current_user: TenantUser = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    # Extract token from Authorization header
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("user_id")
    user = db.query(TenantUser).filter(TenantUser.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user