import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from mistralai import Mistral

from app.core.config import settings
from app.services.pipeline.vectorizer import Vectorizer
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat service with RAG (Retrieval Augmented Generation)
    Integrates ChromaDB for context retrieval and Mistral AI for response generation
    """
    
    def __init__(self, tenant_id: int, session_id: int):
        """
        Initialize ChatService
        
        Args:
            tenant_id: Tenant ID
            session_id: Chat session ID
        """
        self.tenant_id = tenant_id
        self.session_id = session_id
        
        # Initialize Mistral client
        if not settings.MISTRAL_API:
            raise ValueError("MISTRAL_API key not configured")
        
        self.mistral_client = Mistral(api_key=settings.MISTRAL_API)
        
        # Initialize vectorizer for RAG
        self.vectorizer = Vectorizer(tenant_id=tenant_id, user_id=0)
        
        logger.info(f"ChatService initialized for tenant {tenant_id}, session {session_id}")
    
    def get_chat_history(self, db, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent chat history
        
        Args:
            db: Database session
            limit: Number of recent messages (default 10 = last 5 exchanges)
            
        Returns:
            List of messages in format [{"role": "human/ai", "content": "..."}]
        """
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == self.session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def search_context(self, query: str, top_k: int = 5) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Search vector database for relevant context
        
        Args:
            query: Search query (user's message)
            top_k: Number of results to return (default 5)
            
        Returns:
            Tuple of (context_chunks, source_documents)
        """
        try:
            results = self.vectorizer.search(query=query, n_results=top_k)
            
            if not results:
                logger.warning(f"No context found for query: {query}")
                return [], []
            
            # Extract text chunks and sources
            context_chunks = [r['text'] for r in results]
            
            # Build source documents (deduplicate by URL, keep top 3)
            sources_dict = {}
            for r in results:
                url = r['metadata'].get('url')
                if url and url not in sources_dict:
                    sources_dict[url] = {
                        'url': url,
                        'relevance': 1.0 - r.get('distance', 0.0)  # Convert distance to relevance score
                    }
            
            sources = list(sources_dict.values())[:3]  # Top 3 unique sources
            
            logger.info(f"Found {len(context_chunks)} context chunks from {len(sources)} sources")
            return context_chunks, sources
            
        except Exception as e:
            logger.error(f"Error searching context: {e}")
            return [], []
    
    def build_prompt(self, user_message: str, context_chunks: List[str], chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Build prompt for Mistral AI with RAG context and chat history
        
        Args:
            user_message: User's current message
            context_chunks: Relevant context from knowledge base
            chat_history: Previous conversation messages
            
        Returns:
            List of messages for Mistral API
        """
        # System prompt
        system_prompt = """You are a helpful AI assistant. Answer questions based on the provided context from the knowledge base.

Guidelines:
- Use the context provided to answer accurately
- If the answer is not in the context, politely say you don't have that information
- Be concise and friendly
- If asked about topics outside the context, offer to help with what you do know"""

        # Build context section
        context_section = ""
        if context_chunks:
            context_section = "\n\nKnowledge Base Context:\n---\n" + "\n\n".join(context_chunks) + "\n---"
        
        # Build chat history section
        history_section = ""
        if chat_history:
            history_section = "\n\nPrevious conversation:\n"
            for msg in chat_history[-10:]:  # Last 5 exchanges
                role_label = "User" if msg['role'] == 'human' else "Assistant"
                history_section += f"{role_label}: {msg['content']}\n"
        
        # Combine into messages for Mistral
        messages = [
            {"role": "system", "content": system_prompt + context_section + history_section},
            {"role": "user", "content": user_message}
        ]
        
        return messages
    
    def generate_response(self, db, user_message: str) -> Dict[str, Any]:
        """
        Generate AI response using RAG + Mistral
        
        Args:
            db: Database session
            user_message: User's message
            
        Returns:
            Dict with response content, message_id, and sources
        """
        try:
            # Step 1: Save user message to DB
            user_msg = ChatMessage(
                session_id=self.session_id,
                role='human',
                content=user_message,
                meta=None
            )
            db.add(user_msg)
            db.commit()
            db.refresh(user_msg)
            
            logger.info(f"Saved user message {user_msg.id}")
            
            # Step 2: Get chat history
            chat_history = self.get_chat_history(db, limit=10)
            
            # Step 3: Search for relevant context
            context_chunks, sources = self.search_context(user_message, top_k=5)
            
            # Step 4: Build prompt
            messages = self.build_prompt(user_message, context_chunks, chat_history)
            
            # Step 5: Call Mistral API
            logger.info("Calling Mistral API...")
            
            chat_response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_content = chat_response.choices[0].message.content
            
            logger.info(f"Received response from Mistral ({len(ai_content)} chars)")
            
            # Step 6: Save AI response to DB
            ai_msg = ChatMessage(
                session_id=self.session_id,
                role='ai',
                content=ai_content,
                meta={'sources': sources} if sources else None
            )
            db.add(ai_msg)
            db.commit()
            db.refresh(ai_msg)
            
            logger.info(f"Saved AI message {ai_msg.id}")
            
            # Step 7: Return response
            return {
                'message_id': ai_msg.id,
                'session_id': self.session_id,
                'content': ai_content,
                'sources': sources,
                'created_at': ai_msg.created_at
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating response: {e}")
            raise


if __name__ == "__main__":
    # Example usage (for testing)
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        chat_service = ChatService(tenant_id=2, session_id=1)
        response = chat_service.generate_response(
            db=db,
            user_message="What is your routing number?"
        )
        print(f"Response: {response['content']}")
        print(f"Sources: {response['sources']}")
    finally:
        db.close()

