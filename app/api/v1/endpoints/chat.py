"""
Chat API endpoint
Send messages and get AI responses (synchronous)
PUBLIC ENDPOINT - No authentication required (for widget use)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat_session import ChatSession
from app.models.tenant import Tenant
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI response (PUBLIC - no auth required)
    
    - **tenant_id**: Tenant ID (from widget)
    - **session_id**: Optional session ID (creates new if not provided)
    - **message**: User's message
    
    Returns AI response with sources
    """
    try:
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == chat_request.tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Create session if not provided
        session_id = chat_request.session_id
        if not session_id:
            new_session = ChatSession(
                tenant_id=chat_request.tenant_id,
                title="New Chat"
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            session_id = new_session.id
            logger.info(f"Created new session {session_id}")
        else:
            # Verify session exists and belongs to tenant
            session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.tenant_id == chat_request.tenant_id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
        
        # Initialize chat service
        chat_service = ChatService(
            tenant_id=chat_request.tenant_id,
            session_id=session_id
        )
        
        # Generate response
        logger.info(f"Processing message for session {session_id}: {chat_request.message[:50]}...")
        response = chat_service.generate_response(
            db=db,
            user_message=chat_request.message
        )
        
        return ChatResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

