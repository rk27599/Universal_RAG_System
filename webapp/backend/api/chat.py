from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import socketio
import asyncio
import logging
from jose import jwt, JWTError

from core.database import get_db
from core.security import get_current_user
from core.config import Settings
from models.user import User
from models.conversation import Conversation, Message
from models.document import Document
from services.ollama_service import generate_response, OllamaService

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = Settings()
logger = logging.getLogger(__name__)

# Material Studio Expert System Prompt (Default)
DEFAULT_MATERIAL_STUDIO_PROMPT = """You are an expert technical assistant specializing in Material Studio. Your role is to provide accurate, helpful answers about Material Studio using ONLY the retrieved documentation and code context provided to you.

## Core Principles

### 1. Accuracy and Grounding
- Answer questions using ONLY the information from the retrieved context below
- NEVER generate information that is not present in the provided documentation or code
- If the context doesn't contain enough information to answer completely, acknowledge this limitation
- When uncertain, explicitly state your uncertainty rather than guessing

### 2. Citation and Transparency
- Always cite specific sources when making claims (e.g., "According to the Forcite Module API documentation…")
- Reference specific code files, function names, or documentation sections when applicable
- If information comes from multiple sources, acknowledge all relevant sources

### 3. Response Quality
- Provide clear, concise answers (2–4 sentences for simple queries, longer for complex topics)
- Use proper formatting: code blocks for code snippets, bullet points for lists, headers for organization
- Include relevant code examples when they help clarify the answer
- Explain technical concepts in accessible language while maintaining accuracy

## Handling Limitations

When you CANNOT answer a query:
- Clearly state: "I don't have sufficient information in the documentation to answer this question."
- Suggest alternative resources if appropriate (e.g., "You may want to check the Materials Studio support portal or contact Dassault Systèmes support")
- NEVER make up answers or hallucinate information

## Scope and Boundaries

STAY WITHIN SCOPE:
- Answer questions specifically about Material Studio's modules, APIs, configuration, usage, and code examples
- Provide guidance on implementation, optimization, troubleshooting, and best practices
- Explain code snippets and architecture details found in the documentation

OUT OF SCOPE:
- Refuse questions about unrelated products or technologies
- Do not provide opinions on competitor products
- Do not answer questions about future or unreleased features unless explicitly documented
- Do not provide legal, financial, or medical advice

## Response Format

For code-related queries:
1. Provide a brief explanation
2. Include the relevant code snippet in a markdown code block with the appropriate language identifier
3. Explain key parameters, return values, and components
4. Mention any important caveats or version-specific behavior

For conceptual queries:
1. Provide a clear, direct answer first
2. Elaborate with supporting details from the documentation
3. Include examples or use cases when helpful
4. Cross-reference related features or modules

For troubleshooting queries:
1. Acknowledge the issue
2. Provide step-by-step guidance based on documentation
3. Suggest common solutions drawn from known issues
4. Recommend where to find additional help if needed

## Quality Standards

- Maintain a helpful, professional, and patient tone
- Use proper technical terminology as defined in the Material Studio documentation
- Structure longer responses with clear headings and sections
- Prioritize security and performance best practices when discussing implementation

Remember: Only use information from the provided context. If you cannot answer based on the context, say so clearly."""

# Initialize Redis manager for Socket.IO session management (multi-worker support)
redis_manager = None
if settings.REDIS_ENABLED:
    try:
        redis_manager = socketio.AsyncRedisManager(
            url=settings.REDIS_URL,
            redis_options={
                'db': settings.REDIS_DB,
                # Note: decode_responses MUST be False for Socket.IO binary messages
                'decode_responses': False,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'socket_keepalive': True,
                'health_check_interval': 30
            }
        )
        logger.info(f"✅ Redis manager initialized: {settings.REDIS_URL}")
    except Exception as e:
        logger.warning(f"⚠️  Redis initialization failed: {e}")
        logger.warning("⚠️  Falling back to non-Redis mode (single worker only)")
        redis_manager = None

# Create Socket.IO server for real-time communication
sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=redis_manager,  # Use Redis for session management (supports multi-worker)
    cors_allowed_origins="*",  # Update for network access (configure specific IPs in production)
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000
)


class ChatRequest(BaseModel):
    conversationId: str
    content: str
    model: str = "mistral"
    temperature: float = 0.7
    maxTokens: int = 4096
    useRAG: bool = True
    topK: Optional[int] = 20
    documentIds: Optional[List[str]] = None
    # Enhanced RAG features (optional)
    useReranker: Optional[bool] = True  # ✅ Enabled (model downloaded)
    useHybridSearch: Optional[bool] = False  # Disabled until BM25 index is built
    useQueryExpansion: Optional[bool] = False  # Disabled by default (requires Ollama)
    useCorrectiveRAG: Optional[bool] = False
    promptTemplate: Optional[str] = None  # Options: "cot", "extractive", "citation"


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None


@router.post("/message")
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get AI response"""
    try:
        # Find conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversationId,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.content
        )
        db.add(user_message)
        conversation.message_count += 1
        db.commit()

        # Generate AI response
        start_time = datetime.now()

        # Retrieve document context if RAG is enabled
        document_sources = []
        context = None
        pipeline_info = None

        if request.useRAG:
            try:
                from services.document_service import DocumentProcessingService
                from services.enhanced_search_service import EnhancedSearchService

                doc_service = DocumentProcessingService(db, user_id=current_user.id)

                # Initialize enhanced search service with optional features
                enhanced_search = EnhancedSearchService(
                    document_service=doc_service,
                    enable_reranker=request.useReranker,
                    enable_hybrid_search=request.useHybridSearch,
                    enable_query_expansion=request.useQueryExpansion,
                    enable_corrective_rag=request.useCorrectiveRAG,
                    enable_web_search=False  # Keep disabled for privacy
                )

                # Use enhanced search with prompt template if specified
                if request.promptTemplate:
                    search_result = await enhanced_search.search_with_template(
                        query=request.content,
                        template=request.promptTemplate,
                        top_k=request.topK,
                        document_ids=request.documentIds,
                        min_similarity=0.1  # Lower threshold for reranker
                    )
                    # Use the pre-built prompt with context
                    context = search_result.get('prompt')
                    search_results = search_result.get('results', [])
                    pipeline_info = search_result.get('pipeline_info')
                else:
                    # Standard enhanced search
                    search_result = await enhanced_search.search(
                        query=request.content,
                        top_k=request.topK,
                        document_ids=request.documentIds,
                        min_similarity=0.1  # Lower threshold for reranker
                    )
                    search_results = search_result.get('results', [])
                    pipeline_info = search_result.get('pipeline_info')

                    # Build context from results
                    if search_results:
                        doc_parts = []
                        for result in search_results:
                            doc_parts.append(
                                f"Document: {result['document_title']}\n"
                                f"Section: {result.get('section_path', 'N/A')}\n"
                                f"{result['content']}"
                            )
                        context = "\n\n---\n\n".join(doc_parts)

                # Build document sources metadata
                if search_results:
                    for result in search_results:
                        document_sources.append({
                            'documentId': result['document_id'],
                            'documentTitle': result['document_title'],
                            'section': result.get('section_path', 'N/A'),
                            'similarity': result.get('similarity'),
                            'rerankerScore': result.get('reranker_score'),
                            'chunkId': result['chunk_id']
                        })

                    logger.info(f"Retrieved {len(search_results)} document chunks using enhanced search")
                    if pipeline_info:
                        logger.info(f"Pipeline: {pipeline_info.get('retrieval_method')}, "
                                  f"reranking={pipeline_info.get('reranking_applied')}, "
                                  f"expansion={len(pipeline_info.get('expanded_queries', []))}")

            except Exception as e:
                logger.error(f"Error retrieving document context: {e}")
                # Fallback to basic search on error
                try:
                    from services.document_service import DocumentProcessingService
                    doc_service = DocumentProcessingService(db, user_id=current_user.id)
                    search_results = await doc_service.search_documents(
                        query=request.content,
                        top_k=request.topK,
                        document_ids=request.documentIds,
                        min_similarity=0.1  # Lower threshold for reranker fallback
                    )
                    if search_results:
                        doc_parts = []
                        for result in search_results:
                            doc_parts.append(
                                f"Document: {result['document_title']}\n"
                                f"Section: {result.get('section_path', 'N/A')}\n"
                                f"{result['content']}"
                            )
                            document_sources.append({
                                'documentId': result['document_id'],
                                'documentTitle': result['document_title'],
                                'section': result.get('section_path', 'N/A'),
                                'similarity': result['similarity'],
                                'chunkId': result['chunk_id']
                            })
                        context = "\n\n---\n\n".join(doc_parts)
                        logger.info(f"Fallback: Retrieved {len(search_results)} chunks with basic search")
                except Exception as fallback_error:
                    logger.error(f"Fallback search also failed: {fallback_error}")

        # Generate response with context
        try:
            ai_response = await generate_response(
                prompt=request.content,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.maxTokens,
                context=context
            )

            if not ai_response:
                ai_response = f"I received your message: '{request.content}'. (Ollama connection pending)"
        except Exception as ollama_error:
            # Handle Ollama errors gracefully
            error_message = str(ollama_error)
            logger.error(f"Ollama error: {error_message}")

            # Provide user-friendly error message
            if "more system memory" in error_message.lower():
                raise HTTPException(
                    status_code=503,
                    detail=f'Model "{request.model}" requires more system memory than available. Please try a smaller model like "mistral:latest".'
                )
            elif "not found" in error_message.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f'Model "{request.model}" not found. Please select a different model.'
                )
            elif "timeout" in error_message.lower():
                raise HTTPException(
                    status_code=504,
                    detail=f'Request timed out. The model may be too large or Ollama is not responding.'
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f'Failed to generate response: {error_message}'
                )

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        # Calculate average similarity from actual sources (not hardcoded)
        avg_similarity = None
        if request.useRAG and document_sources:
            avg_similarity = sum(s['similarity'] for s in document_sources) / len(document_sources)

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response,
            model_name=request.model,
            response_time=response_time,
            token_count=len(ai_response.split()),
            similarity_score=avg_similarity,
            context_documents=document_sources if document_sources else None
        )
        db.add(assistant_message)
        conversation.message_count += 1
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(assistant_message)

        # Return response
        response_metadata = {
            "model": request.model,
            "responseTime": response_time,
            "tokenCount": assistant_message.token_count,
            "similarity": assistant_message.similarity_score,
            "useRAG": request.useRAG,
            "temperature": request.temperature,
            "maxTokens": request.maxTokens,
            "sources": document_sources if document_sources else None
        }

        # Add enhanced RAG pipeline info if available
        if pipeline_info:
            response_metadata["pipelineInfo"] = {
                "retrievalMethod": pipeline_info.get('retrieval_method'),
                "rerankingApplied": pipeline_info.get('reranking_applied'),
                "queryExpanded": len(pipeline_info.get('expanded_queries', [])) > 0,
                "expandedQueries": pipeline_info.get('expanded_queries', []),
                "correctiveApplied": pipeline_info.get('corrective_applied'),
                "webSearchUsed": pipeline_info.get('web_search_used')
            }

        response_message = {
            "id": str(assistant_message.id),
            "role": "assistant",
            "content": ai_response,
            "timestamp": assistant_message.created_at.isoformat(),
            "metadata": response_metadata
        }

        return {
            "success": True,
            "data": response_message,
            "message": "Message processed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@router.get("/conversations")
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all conversations for current user"""
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.updated_at.desc()).all()

        conversation_list = [
            {
                "id": str(conv.id),
                "title": conv.title,
                "messageCount": conv.message_count,
                "lastActivity": conv.updated_at.isoformat(),
                "isActive": conv.is_active,
                "modelName": conv.model_name or "mistral"
            }
            for conv in conversations
        ]

        return {
            "success": True,
            "data": conversation_list,
            "message": "Conversations retrieved successfully"
        }
    except Exception as e:
        print(f"❌ Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversations")


@router.post("/conversations")
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        title = request.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        new_conversation = Conversation(
            user_id=current_user.id,
            title=title,
            is_active=True,
            model_name="mistral"
        )

        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)

        conversation_data = {
            "id": str(new_conversation.id),
            "title": new_conversation.title,
            "messageCount": 0,
            "lastActivity": new_conversation.updated_at.isoformat(),
            "isActive": True,
            "modelName": new_conversation.model_name
        }

        return {
            "success": True,
            "data": conversation_data,
            "message": "Conversation created successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    limit: int = 10,  # Load last 10 messages by default
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single conversation with messages (paginated for performance)"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get total message count
        total_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).count()

        # Get messages with pagination (most recent first, then reverse)
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()

        # Reverse to get chronological order
        messages.reverse()

        message_list = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "metadata": {
                    "model": msg.model_name,
                    "responseTime": msg.response_time,
                    "tokenCount": msg.token_count,
                    "similarity": msg.similarity_score,
                    "rating": msg.user_rating,
                    "sources": msg.context_documents
                }
            }
            for msg in messages
        ]

        conversation_data = {
            "id": str(conversation.id),
            "title": conversation.title,
            "messageCount": conversation.message_count,
            "lastActivity": conversation.updated_at.isoformat(),
            "isActive": conversation.is_active,
            "modelName": conversation.model_name
        }

        return {
            "success": True,
            "data": {
                "conversation": conversation_data,
                "messages": message_list,
                "pagination": {
                    "total": total_messages,
                    "limit": limit,
                    "offset": offset,
                    "hasMore": offset + len(messages) < total_messages
                }
            },
            "message": "Conversation retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch conversation")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation"""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db.delete(conversation)
        db.commit()

        return {
            "success": True,
            "message": "Conversation deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.post("/conversations/{conversation_id}/regenerate/{message_id}")
async def regenerate_message(
    conversation_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate a message"""
    try:
        # Find the message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message or message.role != "assistant":
            raise HTTPException(status_code=404, detail="Message not found")

        # Find previous user message
        user_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user",
            Message.created_at < message.created_at
        ).order_by(Message.created_at.desc()).first()

        if not user_messages:
            raise HTTPException(status_code=400, detail="No previous user message found")

        # Regenerate response
        ai_response = await generate_response(
            prompt=user_messages.content,
            model=message.model_name or "mistral"
        )

        if not ai_response:
            ai_response = "Regenerated response (Ollama connection pending)"

        # Update message
        message.content = ai_response
        message.token_count = len(ai_response.split())
        message.updated_at = datetime.utcnow()
        db.commit()

        response_data = {
            "id": str(message.id),
            "role": "assistant",
            "content": ai_response,
            "timestamp": message.updated_at.isoformat(),
            "metadata": {
                "model": message.model_name,
                "tokenCount": message.token_count
            }
        }

        return {
            "success": True,
            "data": response_data,
            "message": "Message regenerated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error regenerating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate message")


@router.post("/messages/{message_id}/rate")
async def rate_message(
    message_id: str,
    rating: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rate a message"""
    try:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.user_rating = rating
        message.user_feedback = feedback
        db.commit()

        return {
            "success": True,
            "message": "Message rated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error rating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to rate message")


# ============================================================================
# Socket.IO Event Handlers for Real-Time Messaging
# ============================================================================

# Store connected clients with their auth info
connected_clients = {}

# Track cancellation flags for message generation per session
cancellation_flags = {}


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection with JWT authentication"""
    try:
        # Verify authentication token
        token = auth.get('token') if auth else None
        if not token:
            print(f"❌ Connection rejected for {sid}: No token provided")
            return False

        user_data = verify_token(token)
        if not user_data:
            print(f"❌ Connection rejected for {sid}: Invalid token")
            return False

        # Store authenticated user info
        connected_clients[sid] = {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('sub'),
            'session_id': user_data.get('session_id')
        }

        print(f"✅ WebSocket connected: {user_data.get('sub')} (sid: {sid})")
        return True

    except Exception as e:
        print(f"❌ Connection error for {sid}: {e}")
        return False


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    if sid in connected_clients:
        username = connected_clients[sid].get('username', 'unknown')
        print(f"👋 WebSocket disconnected: {username} (sid: {sid})")
        del connected_clients[sid]

    # Clean up cancellation flag
    if sid in cancellation_flags:
        del cancellation_flags[sid]


@sio.event
async def stop_generation(sid, data):
    """Handle request to stop message generation"""
    if sid not in connected_clients:
        return

    try:
        conversation_id = data.get('conversationId')
        username = connected_clients[sid].get('username', 'unknown')

        # Set cancellation flag
        cancellation_flags[sid] = True

        # Stop typing indicator immediately
        await sio.emit('typing_stop', {}, room=sid)

        logger.info(f"🛑 Generation stopped by {username} for conversation {conversation_id}")
        print(f"🛑 Generation stopped by {username} (sid: {sid})")

    except Exception as e:
        logger.error(f"Error stopping generation: {e}")
        print(f"❌ Error stopping generation for {sid}: {e}")


@sio.event
async def join_conversation(sid, conversation_id):
    """Join a conversation room for targeted messaging"""
    if sid in connected_clients:
        await sio.enter_room(sid, f"conversation_{conversation_id}")
        print(f"📝 {connected_clients[sid]['username']} joined conversation {conversation_id}")


@sio.event
async def send_message(sid, data):
    """Handle incoming message and stream AI response"""
    if sid not in connected_clients:
        await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
        return

    try:
        conversation_id = data.get('conversationId')
        content = data.get('content')
        model = data.get('model', 'mistral')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('maxTokens', 4096)
        use_rag = data.get('useRAG', True)
        top_k = data.get('topK', 20)

        # Expert system prompt configuration (NEW)
        use_expert_prompt = data.get('useExpertPrompt', True)  # Default ON
        custom_system_prompt = data.get('customSystemPrompt', None)

        user_id = connected_clients[sid]['user_id']

        # Get database session
        from core.database import SessionLocal
        db = SessionLocal()

        try:
            # Verify conversation ownership
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()

            if not conversation:
                await sio.emit('error', {'message': 'Conversation not found'}, room=sid)
                return

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=content
            )
            db.add(user_message)
            conversation.message_count += 1
            db.commit()
            db.refresh(user_message)

            # Note: Don't send user message back - frontend already displays it immediately

            # Retrieve conversation history for context (last 20 messages)
            history_messages = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(Message.created_at.desc()).limit(20).all()
            history_messages.reverse()  # Chronological order

            # Build context from conversation history
            context_parts = []
            for msg in history_messages:
                role_prefix = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{role_prefix}: {msg.content}")

            conversation_context = "\n\n".join(context_parts) if context_parts else None

            # Retrieve document context if RAG is enabled
            document_context = None
            document_sources = []
            use_rag = data.get('useRAG', False)
            document_ids = data.get('documentIds', [])

            # Enhanced RAG options
            use_reranker = data.get('useReranker', True)  # ✅ Enabled (model downloaded)
            use_hybrid_search = data.get('useHybridSearch', False)  # Requires BM25 index
            use_query_expansion = data.get('useQueryExpansion', False)  # Requires Ollama
            use_corrective_rag = data.get('useCorrectiveRAG', False)
            prompt_template = data.get('promptTemplate', None)

            logger.info(f"🔍 RAG Debug: useRAG={use_rag}, documentIds={document_ids}")
            logger.info(f"🔍 Enhanced RAG received: reranker={use_reranker}, hybrid={use_hybrid_search}, "
                       f"expansion={use_query_expansion}, corrective={use_corrective_rag}, template={prompt_template}")

            if use_rag:
                try:
                    from services.document_service import DocumentProcessingService
                    from services.enhanced_search_service import EnhancedSearchService

                    doc_service = DocumentProcessingService(db, user_id=user_id)

                    # If no specific documents selected, use None to search all user documents
                    search_doc_ids = document_ids if document_ids else None

                    # Check if user has any completed documents first
                    doc_count = db.query(Document).filter(
                        Document.user_id == connected_clients[sid]['user_id'],
                        Document.processing_status == "completed"
                    ).count()

                    if doc_count == 0:
                        logger.warning(f"⚠️ User {connected_clients[sid]['username']} has no completed documents in database")
                        search_results = []
                    else:
                        # Initialize enhanced search service
                        enhanced_search = EnhancedSearchService(
                            document_service=doc_service,
                            enable_reranker=use_reranker,
                            enable_hybrid_search=use_hybrid_search,
                            enable_query_expansion=use_query_expansion,
                            enable_corrective_rag=use_corrective_rag,
                            enable_web_search=False  # Keep disabled for privacy
                        )

                        logger.info(f"🔍 Enhanced search with {doc_count} documents: "
                                  f"reranker={use_reranker}, hybrid={use_hybrid_search}, "
                                  f"expansion={use_query_expansion}, corrective={use_corrective_rag}")

                        # Use enhanced search with prompt template if specified
                        if prompt_template:
                            search_result = await enhanced_search.search_with_template(
                                query=content,
                                template=prompt_template,
                                top_k=top_k,
                                document_ids=search_doc_ids,
                                min_similarity=0.1  # Lower threshold for reranker
                            )
                            # Use pre-built prompt with context
                            document_context = search_result.get('prompt')
                            search_results = search_result.get('results', [])
                        else:
                            # Standard enhanced search
                            search_result = await enhanced_search.search(
                                query=content,
                                top_k=top_k,
                                document_ids=search_doc_ids,
                                min_similarity=0.1  # Lower threshold for reranker
                            )
                            search_results = search_result.get('results', [])

                        logger.info(f"📊 Enhanced search returned {len(search_results)} results")

                    # Build document context from search results
                    if search_results and not prompt_template:
                        doc_parts = []
                        for result in search_results:
                            doc_parts.append(
                                f"Document: {result['document_title']}\n"
                                f"Section: {result.get('section_path', 'N/A')}\n"
                                f"{result['content']}"
                            )
                        document_context = "\n\n---\n\n".join(doc_parts)

                    # Store source metadata for response
                    if search_results:
                        for result in search_results:
                            document_sources.append({
                                'documentId': result['document_id'],
                                'documentTitle': result['document_title'],
                                'section': result.get('section_path', 'N/A'),
                                'similarity': result.get('similarity'),
                                'rerankerScore': result.get('reranker_score'),
                                'chunkId': result['chunk_id']
                            })

                        logger.info(f"Retrieved {len(search_results)} document chunks for RAG")
                except Exception as e:
                    logger.error(f"Error retrieving document context: {e}")
                    # Fallback to basic search
                    try:
                        from services.document_service import DocumentProcessingService
                        doc_service = DocumentProcessingService(db, user_id=user_id)
                        search_doc_ids = document_ids if document_ids else None
                        search_results = await doc_service.search_documents(
                            query=content,
                            top_k=top_k,
                            document_ids=search_doc_ids,
                            min_similarity=0.1  # Lower threshold for reranker fallback
                        )
                        if search_results:
                            doc_parts = []
                            for result in search_results:
                                doc_parts.append(
                                    f"Document: {result['document_title']}\n"
                                    f"Section: {result.get('section_path', 'N/A')}\n"
                                    f"{result['content']}"
                                )
                                document_sources.append({
                                    'documentId': result['document_id'],
                                    'documentTitle': result['document_title'],
                                    'section': result.get('section_path', 'N/A'),
                                    'similarity': result['similarity'],
                                    'chunkId': result['chunk_id']
                                })
                            document_context = "\n\n---\n\n".join(doc_parts)
                            logger.info(f"Fallback: Retrieved {len(search_results)} chunks")
                    except Exception as fallback_error:
                        logger.error(f"Fallback search failed: {fallback_error}")

            # Combine conversation history and document context
            full_context_parts = []
            if conversation_context:
                full_context_parts.append(f"Previous Conversation:\n{conversation_context}")
            if document_context:
                full_context_parts.append(f"Relevant Documents:\n{document_context}")

            final_context = "\n\n=====\n\n".join(full_context_parts) if full_context_parts else None

            # Determine system prompt to use
            system_prompt = None
            if use_rag and document_context:  # Only for RAG queries with actual document context
                if use_expert_prompt:
                    # Use custom prompt if provided, otherwise default Material Studio prompt
                    system_prompt = custom_system_prompt or DEFAULT_MATERIAL_STUDIO_PROMPT
                    prompt_type = "custom" if custom_system_prompt else "default"
                    logger.info(f"🎯 Using Material Studio expert system prompt ({prompt_type})")
                else:
                    logger.info(f"ℹ️ Expert prompt disabled by user")

            # Clear any previous cancellation flag
            cancellation_flags[sid] = False

            # Start typing indicator
            await sio.emit('typing', {}, room=sid)

            # Stream AI response with full context (conversation + documents)
            start_time = datetime.now()
            ollama_service = OllamaService()
            full_response = ""
            was_cancelled = False

            try:
                async for chunk in ollama_service.generate_stream(
                    prompt=content,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,  # Pass expert prompt here
                    context=final_context
                ):
                    # Check for cancellation
                    if cancellation_flags.get(sid, False):
                        was_cancelled = True
                        print(f"🛑 Generation cancelled mid-stream for {connected_clients[sid]['username']}")
                        break

                    if chunk:
                        full_response += chunk
                        # Send incremental updates
                        await sio.emit('message_chunk', {
                            'content': chunk
                        }, room=sid)
            except Exception as stream_error:
                # Handle Ollama errors (memory issues, model not found, etc.)
                error_message = str(stream_error)
                logger.error(f"Ollama streaming error: {error_message}")

                # Stop typing indicator
                await sio.emit('typing_stop', {}, room=sid)

                # Send user-friendly error message
                if "more system memory" in error_message.lower():
                    await sio.emit('error', {
                        'message': f'Model "{model}" requires more system memory than available. Please try a smaller model like "mistral:latest".'
                    }, room=sid)
                elif "not found" in error_message.lower():
                    await sio.emit('error', {
                        'message': f'Model "{model}" not found. Please select a different model.'
                    }, room=sid)
                elif "timeout" in error_message.lower():
                    await sio.emit('error', {
                        'message': f'Request timed out. The model may be too large or Ollama is not responding.'
                    }, room=sid)
                else:
                    await sio.emit('error', {
                        'message': f'Failed to generate response: {error_message}'
                    }, room=sid)

                # Clean up and return without saving incomplete message
                cancellation_flags[sid] = False
                return

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            # Clear cancellation flag
            cancellation_flags[sid] = False

            # Stop typing indicator
            await sio.emit('typing_stop', {}, room=sid)

            # If cancelled and no content, don't save message
            if was_cancelled and not full_response.strip():
                print(f"⚠️ Generation cancelled before any content - no message saved")
                return

            # Calculate average similarity from actual sources (not hardcoded)
            avg_similarity = None
            if use_rag and document_sources:
                avg_similarity = sum(s['similarity'] for s in document_sources) / len(document_sources)

            # Save assistant message to database
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
                model_name=model,
                response_time=response_time,
                token_count=len(full_response.split()),
                similarity_score=avg_similarity,
                context_documents=document_sources if document_sources else None
            )
            db.add(assistant_message)
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(assistant_message)

            # Send final complete message with metadata
            logger.info(f"📊 Sending message with {len(document_sources)} sources")
            await sio.emit('message', {
                'id': str(assistant_message.id),
                'role': 'assistant',
                'content': full_response,
                'timestamp': assistant_message.created_at.isoformat(),
                'metadata': {
                    'model': model,
                    'responseTime': response_time,
                    'tokenCount': assistant_message.token_count,
                    'similarity': assistant_message.similarity_score,
                    'sources': document_sources if document_sources else []
                }
            }, room=sid)

            print(f"✅ Message processed for {connected_clients[sid]['username']}: {len(full_response)} chars, {len(document_sources)} sources")

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        await sio.emit('error', {'message': f'Failed to process message: {str(e)}'}, room=sid)
