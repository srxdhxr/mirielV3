"""
Chat Sessions API endpoints
Manage chat sessions (create, list, get, delete)
PUBLIC ENDPOINTS - No authentication required (for widget use)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.tenant import Tenant
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageListResponse,
    ChatMessageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new chat session (PUBLIC - no auth required)
    
    - **tenant_id**: Tenant ID (from widget)
    - **title**: Optional session title (will be auto-generated from first message if not provided)
    """
    try:
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == session_data.tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Create new session (anonymous, no user tracking)
        new_session = ChatSession(
            tenant_id=session_data.tenant_id,
            title=session_data.title or "New Chat"
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"Created public chat session {new_session.id} for tenant {session_data.tenant_id}")
        
        return ChatSessionResponse.model_validate(new_session)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@router.get("", response_model=ChatSessionListResponse)
def list_sessions(
    tenant_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for a tenant (PUBLIC - no auth required)
    
    - **tenant_id**: Tenant ID (from widget)
    - **skip**: Number of sessions to skip (pagination)
    - **limit**: Maximum number of sessions to return
    """
    try:
        # Query sessions for tenant
        query = db.query(ChatSession).filter(
            ChatSession.tenant_id == tenant_id
        ).order_by(ChatSession.updated_at.desc())
        
        total = query.count()
        sessions = query.offset(skip).limit(limit).all()
        
        return ChatSessionListResponse(
            sessions=[ChatSessionResponse.model_validate(s) for s in sessions],
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list chat sessions"
        )


@router.get("/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific chat session by ID (PUBLIC - no auth required)
    """
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return ChatSessionResponse.model_validate(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat session"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its messages (PUBLIC - no auth required)
    """
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        db.delete(session)
        db.commit()
        
        logger.info(f"Deleted chat session {session_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )


@router.get("/{session_id}/messages", response_model=ChatMessageListResponse)
def get_session_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all messages in a chat session (PUBLIC - no auth required)
    
    - **skip**: Number of messages to skip (pagination)
    - **limit**: Maximum number of messages to return
    """
    try:
        # Verify session exists
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Query messages
        query = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc())
        
        total = query.count()
        messages = query.offset(skip).limit(limit).all()
        
        return ChatMessageListResponse(
            messages=[ChatMessageResponse.model_validate(msg) for msg in messages],
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session messages"
        )

