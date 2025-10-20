"""
Tenant onboarding endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import hash_password, validate_password_strength
from app.models.tenant import Tenant
from app.models.tenant_user import TenantUser
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=OnboardingResponse, status_code=201)
def onboard_tenant(
    onboarding_data: OnboardingRequest,
    db: Session = Depends(get_db)
):
    """
    Onboard a new tenant with admin user
    
    This endpoint:
    1. Validates all input data
    2. Checks if email/slug already exists
    3. Creates a new tenant
    4. Creates the admin user with hashed password
    5. Returns success response
    """
    logger.info(f"🚀 Starting tenant onboarding for: {onboarding_data.company_name}")
    
    try:
        # Step 1: Validate password strength
        is_valid_password, password_error = validate_password_strength(onboarding_data.password)
        if not is_valid_password:
            logger.warning(f"❌ Password validation failed: {password_error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {password_error}"
            )
        
        # Step 2: Check if email already exists
        existing_user = db.query(TenantUser).filter(
            TenantUser.email == onboarding_data.admin_email
        ).first()
        
        if existing_user:
            logger.warning(f"❌ Email already exists: {onboarding_data.admin_email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists"
            )
        
        # Step 3: Check if slug already exists
        existing_tenant = db.query(Tenant).filter(
            Tenant.slug == onboarding_data.short_name
        ).first()
        
        if existing_tenant:
            logger.warning(f"❌ Slug already exists: {onboarding_data.short_name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A tenant with this short name already exists"
            )
        
        # Step 4: Create the tenant
        logger.info(f"📊 Creating tenant: {onboarding_data.company_name}")
        new_tenant = Tenant(
            name=onboarding_data.company_name,
            website_url=onboarding_data.website_url,
            slug=onboarding_data.short_name,
            status='active'
        )
        
        db.add(new_tenant)
        db.flush()  # Flush to get the tenant ID without committing
        
        logger.info(f"✅ Tenant created with ID: {new_tenant.id}")
        
        # Step 5: Hash the password
        logger.info("🔒 Hashing password for admin user")
        password_hash, password_salt = hash_password(onboarding_data.password)
        
        # Step 6: Create the admin user
        logger.info(f"👤 Creating admin user: {onboarding_data.admin_email}")
        admin_user = TenantUser(
            tenant_id=new_tenant.id,
            name=onboarding_data.admin_name,
            email=onboarding_data.admin_email,
            password_hash=password_hash,
            password_salt=password_salt,
            role='admin'
        )
        
        db.add(admin_user)
        
        # Step 7: Commit all changes
        db.commit()
        
        logger.info(f"✅ Successfully onboarded tenant {new_tenant.id} with admin user {admin_user.id}")
        
        # Step 8: Return success response
        return OnboardingResponse(
            tenant_id=new_tenant.id,
            tenant_name=new_tenant.name,
            tenant_slug=new_tenant.slug,
            admin_user_id=admin_user.id,
            admin_user_name=admin_user.name,
            admin_user_email=admin_user.email,
            admin_user_role=admin_user.role
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (our validation errors)
        db.rollback()
        raise
        
    except IntegrityError as e:
        # Handle database constraint violations
        db.rollback()
        logger.error(f"❌ Database integrity error during onboarding: {str(e)}")
        
        if "email" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address already exists"
            )
        elif "slug" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Short name already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data validation error"
            )
    
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logger.error(f"❌ Unexpected error during tenant onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during onboarding"
        )

