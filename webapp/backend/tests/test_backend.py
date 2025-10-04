#!/usr/bin/env python3
"""
Simple FastAPI Backend Test for Phase 1 Validation with WebSocket Support
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import socketio
from collections import defaultdict
import time

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    async_mode='asgi'
)

# Create FastAPI app
app = FastAPI(
    title="Secure RAG System - Test Backend",
    description="Phase 1 Testing Backend with WebSocket Support",
    version="1.0.0"
)

# Custom exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": "ValidationError",
            "message": str(exc),
            "details": "Invalid input provided"
        }
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "NotFound",
            "message": "Resource not found",
            "details": f"The requested resource '{request.url.path}' was not found"
        }
    )

# Rate limiting storage
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 30  # requests per minute
RATE_LIMIT_WINDOW = 60    # seconds

def check_rate_limit(client_ip: str) -> bool:
    """Check if client IP is within rate limit"""
    now = time.time()
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if now - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if within limit
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False

    # Add current request
    request_counts[client_ip].append(now)
    return True

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = request.client.host

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "RateLimitExceeded",
                "message": "Too many requests",
                "details": f"Rate limit exceeded: {RATE_LIMIT_REQUESTS} requests per minute"
            }
        )

    response = await call_next(request)
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )

# CORS configuration for localhost testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' ws: wss:; "
        "font-src 'self'"
    )

    return response

# Mount Socket.IO to FastAPI
socket_app = socketio.ASGIApp(sio, app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "security_mode": "local_only"
    }

# Authentication endpoints
@app.post("/auth/login")
async def login():
    return {
        "success": True,
        "data": {
            "token": "test-jwt-token-12345",
            "user": {
                "id": "admin-user-1",
                "username": "admin",
                "email": "admin@localhost",
                "fullName": "System Administrator",
                "isAdmin": True,
                "createdAt": "2024-01-01T00:00:00Z"
            }
        },
        "message": "Login successful"
    }

@app.post("/auth/register")
async def register():
    return {
        "success": True,
        "data": {
            "id": "new-user-1",
            "username": "newuser",
            "email": "newuser@localhost",
            "fullName": "New User",
            "isAdmin": False,
            "createdAt": "2024-01-01T00:00:00Z"
        },
        "message": "Registration successful"
    }

@app.get("/auth/me")
async def get_current_user():
    return {"user": "test-user", "email": "test@localhost"}

# Document endpoints
@app.post("/documents/upload")
async def upload_document():
    return {
        "success": True,
        "data": {"id": "test-doc-1", "filename": "test.pdf", "status": "processing"},
        "message": "Document uploaded successfully"
    }

@app.get("/documents")
async def get_documents():
    return {
        "success": True,
        "data": [
            {"id": "test-doc-1", "filename": "test.pdf", "status": "completed"}
        ],
        "message": "Documents retrieved successfully"
    }

# Chat endpoints
@app.post("/chat/message")
async def send_message(request: dict = None):
    return {
        "success": True,
        "data": {
            "id": "msg-1",
            "role": "assistant",
            "content": "Echo: Test message",
            "model": "mistral",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "message": "Message sent successfully"
    }

@app.post("/chat/{conversation_id}/message")
async def send_conversation_message(conversation_id: str, request: dict = None):
    return {
        "success": True,
        "data": {
            "id": f"msg-{conversation_id}",
            "role": "assistant",
            "content": "Echo: Hello from conversation!",
            "model": "mistral",
            "timestamp": "2024-01-01T00:00:00Z",
            "conversationId": conversation_id
        },
        "message": "Message sent successfully"
    }

@app.post("/chat/{conversation_id}/regenerate/{message_id}")
async def regenerate_message(conversation_id: str, message_id: str):
    return {
        "success": True,
        "data": {
            "id": message_id,
            "role": "assistant",
            "content": "Regenerated: This is a new response!",
            "model": "mistral",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "message": "Message regenerated successfully"
    }

@app.post("/chat/messages/{message_id}/rate")
async def rate_message(message_id: str, request: dict = None):
    return {
        "success": True,
        "data": {"messageId": message_id, "rating": request.get("rating", 5) if request else 5},
        "message": "Message rated successfully"
    }

@app.get("/conversations")
async def get_conversations():
    return {
        "success": True,
        "data": [
            {"id": "conv-1", "title": "Test Conversation", "messageCount": 2}
        ],
        "message": "Conversations retrieved successfully"
    }

@app.post("/conversations")
async def create_conversation():
    return {
        "success": True,
        "data": {
            "id": "conv-new",
            "title": "New Conversation",
            "messageCount": 0,
            "createdAt": "2024-01-01T00:00:00Z"
        },
        "message": "Conversation created successfully"
    }

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    # Return different data based on conversation ID
    if conversation_id == "conv-new":
        return {
            "success": True,
            "data": {
                "conversation": {"id": conversation_id, "title": "New Conversation", "messageCount": 0},
                "messages": []
            },
            "message": "Conversation retrieved successfully"
        }
    else:
        return {
            "success": True,
            "data": {
                "conversation": {"id": conversation_id, "title": "Test Conversation", "messageCount": 2},
                "messages": [
                    {"id": "msg-1", "role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00Z"},
                    {"id": "msg-2", "role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:01:00Z"}
                ]
            },
            "message": "Conversation retrieved successfully"
        }

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    return {
        "success": True,
        "data": {"id": conversation_id},
        "message": "Conversation deleted successfully"
    }

# Model endpoints
@app.get("/models")
async def get_available_models():
    return {
        "success": True,
        "data": ["mistral", "llama2", "codellama"],
        "message": "Models retrieved successfully"
    }

@app.get("/models/{model_name}")
async def get_model_info(model_name: str):
    # Valid models for the test backend
    valid_models = ["mistral", "llama2", "codellama"]

    if model_name not in valid_models:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "ModelNotFound",
                "message": f"Model '{model_name}' not found",
                "details": f"Available models: {', '.join(valid_models)}"
            }
        )

    return {
        "success": True,
        "data": {
            "name": model_name,
            "family": "transformer",
            "size": "7B",
            "parameters": "7.3B"
        },
        "message": "Model info retrieved successfully"
    }

@app.get("/system/status")
async def get_system_status():
    return {
        "success": True,
        "data": {
            "ollama": {"status": "running", "models": ["mistral", "llama2"]},
            "database": {"status": "connected", "connections": 5},
            "security": {"score": 96, "violations": 0}
        },
        "message": "System status retrieved successfully"
    }

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    print(f"Client {sid} connected")
    await sio.emit('connected', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def message(sid, data):
    print(f"Message from {sid}: {data}")
    # Handle both string and dict data
    if isinstance(data, str):
        message_content = data
        model = 'mistral'
    else:
        message_content = data.get('message', 'No message content') if data else 'No message content'
        model = data.get('model', 'mistral') if data else 'mistral'

    # Echo the message back with a test response
    response = {
        "id": "msg-test",
        "role": "assistant",
        "content": f"Echo: {message_content}",
        "model": model,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    await sio.emit('message', response, room=sid)

@sio.event
async def send_message(sid, data):
    print(f"Send message from {sid}: {data}")
    # Handle message sending event
    if isinstance(data, str):
        message_content = data
        conversation_id = 'default'
        model = 'mistral'
    else:
        message_content = data.get('content', 'No message content') if data else 'No message content'
        conversation_id = data.get('conversationId', 'default') if data else 'default'
        model = data.get('model', 'mistral') if data else 'mistral'

    response = {
        "id": f"msg-{conversation_id}-{sid[:8]}",
        "role": "assistant",
        "content": f"WebSocket Echo: {message_content}",
        "model": model,
        "timestamp": "2024-01-01T00:00:00Z",
        "conversationId": conversation_id
    }
    await sio.emit('message', response, room=sid)

@sio.event
async def join_conversation(sid, data):
    # Handle both string and dict data
    if isinstance(data, str):
        conversation_id = data
    else:
        conversation_id = data.get('conversationId', 'default') if data else 'default'

    await sio.enter_room(sid, conversation_id)
    print(f"Client {sid} joined conversation {conversation_id}")

@sio.event
async def leave_conversation(sid, data):
    # Handle both string and dict data
    if isinstance(data, str):
        conversation_id = data
    else:
        conversation_id = data.get('conversationId', 'default') if data else 'default'

    await sio.leave_room(sid, conversation_id)
    print(f"Client {sid} left conversation {conversation_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="127.0.0.1", port=8000)