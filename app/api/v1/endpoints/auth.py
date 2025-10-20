"""
Authentication endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.models.tenant_user import TenantUser
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.api.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token
    
    Steps:
    1. Find user by email
    2. Verify password
    3. Generate JWT token
    4. Return token + user info
    """
    logger.info(f"🔐 Login attempt for: {login_data.email}")
    
    # Step 1: Find user by email
    user = db.query(TenantUser).filter(
        TenantUser.email == login_data.email
    ).first()
    
    if not user:
        logger.warning(f"❌ User not found: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Step 2: Verify password
    if not verify_password(login_data.password, user.password_salt, user.password_hash):
        logger.warning(f"❌ Invalid password for: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Step 3: Generate JWT token
    access_token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email
    )
    
    logger.info(f"✅ Login successful for: {login_data.email}")
    
    # Step 4: Return token + user info
    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        name=user.name,
        role=user.role
    )


@router.get("/me", response_model=UserInfo)
def get_current_user_info(
    current_user: TenantUser = Depends(get_current_user)
):
    """
    Get current authenticated user info
    
    Protected route example - requires valid JWT token
    """
    logger.info(f"👤 Getting user info for: {current_user.email}")
    
    return UserInfo(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role
    )


@router.post("/logout")
def logout():
    """
    Logout endpoint
    
    Note: With JWT, logout is handled client-side by deleting the token
    Server-side logout requires token blacklisting (advanced topic)
    """
    return {"message": "Logged out successfully"}