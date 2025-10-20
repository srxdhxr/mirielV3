"""
Widget API endpoints
Manage chat widgets and customizations
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies.auth import get_current_user
from app.models.tenant_user import TenantUser
from app.models.widget import Widget
from app.models.widget_customization import WidgetCustomization
from app.models.tenant import Tenant
from app.schemas.widget import (
    WidgetCreate,
    WidgetResponse,
    WidgetCustomizationUpdate,
    WidgetCustomizationResponse,
    WidgetConfigResponse,
    WidgetCustomizationBase,
    WidgetEmbedCodeResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
def create_widget(
    widget_data: WidgetCreate,
    current_user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a widget for a tenant (authenticated)
    Only one widget per tenant
    """
    try:
        # Verify user belongs to tenant
        if current_user.tenant_id != widget_data.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create widget for another tenant"
            )
        
        # Check if widget already exists
        existing = db.query(Widget).filter(Widget.tenant_id == widget_data.tenant_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Widget already exists for this tenant"
            )
        
        # Create widget
        widget = Widget(
            tenant_id=widget_data.tenant_id,
            api_key=Widget.generate_api_key(),
            status='active'
        )
        db.add(widget)
        db.flush()  # Get widget.id
        
        # Create default customization
        customization = WidgetCustomization(
            widget_id=widget.id
        )
        db.add(customization)
        db.commit()
        db.refresh(widget)
        
        logger.info(f"Created widget {widget.id} for tenant {widget_data.tenant_id}")
        
        return widget
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create widget"
        )


@router.get("/my", response_model=WidgetResponse)
def get_my_widget(
    current_user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the widget for current user's tenant
    """
    try:
        widget = db.query(Widget).filter(
            Widget.tenant_id == current_user.tenant_id
        ).first()
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found. Create one first."
            )
        
        return widget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get widget"
        )


@router.put("/customization", response_model=WidgetCustomizationResponse)
def update_customization(
    customization_data: WidgetCustomizationUpdate,
    current_user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update widget customization colors
    """
    try:
        # Get widget for user's tenant
        widget = db.query(Widget).filter(
            Widget.tenant_id == current_user.tenant_id
        ).first()
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found. Create one first."
            )
        
        # Update customization
        customization = widget.customization
        if not customization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget customization not found"
            )
        
        # Update fields
        for field, value in customization_data.model_dump().items():
            setattr(customization, field, value)
        
        db.commit()
        db.refresh(customization)
        
        logger.info(f"Updated customization for widget {widget.id}")
        
        return customization
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customization"
        )


@router.get("/embed-code", response_model=WidgetEmbedCodeResponse)
def get_embed_code(
    current_user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get widget embed code for current user's tenant
    """
    try:
        widget = db.query(Widget).filter(
            Widget.tenant_id == current_user.tenant_id
        ).first()
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found. Create one first."
            )
        
        # Generate embed code
        base_url = f"http://{settings.HOST}:{settings.PORT}" if settings.PORT != 80 else f"http://{settings.HOST}"
        widget_url = f"{base_url}/widget.js"
        
        embed_code = f"""<script 
  src="{widget_url}" 
  data-api-key="{widget.api_key}">
</script>"""
        
        return WidgetEmbedCodeResponse(
            embed_code=embed_code,
            widget_url=widget_url,
            api_key=widget.api_key
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embed code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embed code"
        )


# ============= Public Endpoint (for widget.js) =============

@router.get("/config", response_model=WidgetConfigResponse)
def get_widget_config(
    api_key: str = Query(..., description="Widget API key"),
    db: Session = Depends(get_db)
):
    """
    Get widget configuration by API key (PUBLIC - no auth required)
    Used by widget.js to load customization
    """
    try:
        # Find widget by API key
        widget = db.query(Widget).filter(
            Widget.api_key == api_key,
            Widget.status == 'active'
        ).first()
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Widget not found or inactive"
            )
        
        # Get tenant info
        tenant = db.query(Tenant).filter(Tenant.id == widget.tenant_id).first()
        
        # Get customization
        customization = widget.customization
        if not customization:
            # Return defaults
            colors = WidgetCustomizationBase()
            chatbot_name = "Chat Support"
        else:
            colors = WidgetCustomizationBase(
                chatbot_name=customization.chatbot_name,
                chat_header_color=customization.chat_header_color,
                close_icon_color=customization.close_icon_color,
                chat_bg_color=customization.chat_bg_color,
                ai_bubble_color=customization.ai_bubble_color,
                human_bubble_color=customization.human_bubble_color,
                text_box_color=customization.text_box_color,
                send_button_color=customization.send_button_color
            )
            chatbot_name = customization.chatbot_name
        
        return WidgetConfigResponse(
            tenant_id=widget.tenant_id,
            chatbot_name=chatbot_name,
            colors=colors,
            company_name=tenant.name if tenant else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get widget configuration"
        )

