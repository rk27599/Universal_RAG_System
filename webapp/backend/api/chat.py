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
    topK: Optional[int] = 10
    documentIds: Optional[List[str]] = None


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

        if request.useRAG:
            try:
                from services.document_service import DocumentProcessingService
                doc_service = DocumentProcessingService(db, user_id=current_user.id)

                # Search for relevant document chunks with improved parameters
                search_results = await doc_service.search_documents(
                    query=request.content,
                    top_k=request.topK,  # User-configurable source count
                    document_ids=request.documentIds,
                    min_similarity=0.2  # Lower threshold for TF-IDF
                )

                # Build document context and sources
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
                    logger.info(f"Retrieved {len(search_results)} document chunks for RAG")
            except Exception as e:
                logger.error(f"Error retrieving document context: {e}")

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
        response_message = {
            "id": str(assistant_message.id),
            "role": "assistant",
            "content": ai_response,
            "timestamp": assistant_message.created_at.isoformat(),
            "metadata": {
                "model": request.model,
                "responseTime": response_time,
                "tokenCount": assistant_message.token_count,
                "similarity": assistant_message.similarity_score,
                "useRAG": request.useRAG,
                "temperature": request.temperature,
                "maxTokens": request.maxTokens,
                "sources": document_sources if document_sources else None
            }
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
        top_k = data.get('topK', 10)

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

            logger.info(f"🔍 RAG Debug: useRAG={use_rag}, documentIds={document_ids}")

            if use_rag:
                try:
                    from services.document_service import DocumentProcessingService
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
                        # Search for relevant document chunks with improved parameters
                        logger.info(f"🔍 Searching {doc_count} documents with top_k={top_k}, document_ids={search_doc_ids}")
                        search_results = await doc_service.search_documents(
                            query=content,
                            top_k=top_k,  # User-configurable source count
                            document_ids=search_doc_ids,
                            min_similarity=0.1  # Lowered threshold to get more results (embeddings often have lower scores)
                        )
                        logger.info(f"📊 Search returned {len(search_results) if search_results else 0} results")

                    # Build document context from search results
                    if search_results:
                        doc_parts = []
                        for result in search_results:
                            doc_parts.append(
                                f"Document: {result['document_title']}\n"
                                f"Section: {result.get('section_path', 'N/A')}\n"
                                f"{result['content']}"
                            )

                            # Store source metadata for response
                            document_sources.append({
                                'documentId': result['document_id'],
                                'documentTitle': result['document_title'],
                                'section': result.get('section_path', 'N/A'),
                                'similarity': result['similarity'],
                                'chunkId': result['chunk_id']
                            })

                        document_context = "\n\n---\n\n".join(doc_parts)
                        logger.info(f"Retrieved {len(search_results)} document chunks for RAG")
                except Exception as e:
                    logger.error(f"Error retrieving document context: {e}")
                    # Continue without document context

            # Combine conversation history and document context
            full_context_parts = []
            if conversation_context:
                full_context_parts.append(f"Previous Conversation:\n{conversation_context}")
            if document_context:
                full_context_parts.append(f"Relevant Documents:\n{document_context}")

            final_context = "\n\n=====\n\n".join(full_context_parts) if full_context_parts else None

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
