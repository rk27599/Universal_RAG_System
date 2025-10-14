"""
Redis Service for Session Management
Provides centralized session storage for Socket.IO multi-worker support
"""

import redis
from redis.connection import ConnectionPool
from typing import Optional, Dict, Any
import logging
import json
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for managing Socket.IO sessions across multiple workers"""

    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0, decode_responses: bool = True):
        """
        Initialize Redis service with connection pooling

        Args:
            redis_url: Redis connection URL (default: localhost)
            db: Redis database number (default: 0)
            decode_responses: Auto-decode bytes to strings (default: True)
        """
        self.redis_url = redis_url
        self.db = db
        self.decode_responses = decode_responses
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None

        logger.info(f"🔧 Redis service initializing with URL: {redis_url}, DB: {db}")

    def connect(self) -> bool:
        """
        Establish connection to Redis server

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=self.decode_responses,
                max_connections=50,  # Support multiple workers
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )

            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()

            logger.info("✅ Redis connection established successfully")
            return True

        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Falling back to non-Redis mode (single worker only)")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected Redis error: {e}")
            return False

    def disconnect(self):
        """Close Redis connection and cleanup resources"""
        try:
            if self._client:
                self._client.close()
            if self._pool:
                self._pool.disconnect()
            logger.info("👋 Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client instance"""
        if self._client is None:
            self.connect()
        return self._client

    def is_connected(self) -> bool:
        """
        Check if Redis is connected and responsive

        Returns:
            bool: True if connected, False otherwise
        """
        try:
            if self._client is None:
                return False
            self._client.ping()
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis connection and session statistics

        Returns:
            dict: Statistics including connection info, memory usage, etc.
        """
        if not self.is_connected():
            return {
                "connected": False,
                "error": "Not connected to Redis"
            }

        try:
            info = self._client.info()
            return {
                "connected": True,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "total_keys": self._client.dbsize()
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {
                "connected": True,
                "error": str(e)
            }

    def set_session(self, session_id: str, data: Dict[str, Any], expire_seconds: int = 3600) -> bool:
        """
        Store session data with expiration

        Args:
            session_id: Unique session identifier
            data: Session data dictionary
            expire_seconds: TTL in seconds (default: 1 hour)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            key = f"socketio:session:{session_id}"
            self._client.setex(
                key,
                timedelta(seconds=expire_seconds),
                json.dumps(data)
            )
            return True
        except Exception as e:
            logger.error(f"Error setting session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data

        Args:
            session_id: Unique session identifier

        Returns:
            dict: Session data if found, None otherwise
        """
        if not self.is_connected():
            return None

        try:
            key = f"socketio:session:{session_id}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session data

        Args:
            session_id: Unique session identifier

        Returns:
            bool: True if deleted, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            key = f"socketio:session:{session_id}"
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def get_active_sessions(self) -> int:
        """
        Count active Socket.IO sessions

        Returns:
            int: Number of active sessions
        """
        if not self.is_connected():
            return 0

        try:
            pattern = "socketio:session:*"
            return len(list(self._client.scan_iter(match=pattern, count=100)))
        except Exception as e:
            logger.error(f"Error counting sessions: {e}")
            return 0

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles TTL automatically, this is for monitoring)

        Returns:
            int: Number of active sessions after cleanup
        """
        return self.get_active_sessions()

    def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for Redis service

        Returns:
            dict: Health status including connectivity, latency, and stats
        """
        health_data = {
            "service": "redis",
            "status": "unknown",
            "connected": False,
            "latency_ms": None,
            "active_sessions": 0,
            "stats": {}
        }

        if not self.is_connected():
            health_data["status"] = "disconnected"
            health_data["error"] = "Cannot connect to Redis"
            return health_data

        try:
            # Measure latency
            import time
            start = time.time()
            self._client.ping()
            latency = (time.time() - start) * 1000

            health_data.update({
                "status": "healthy",
                "connected": True,
                "latency_ms": round(latency, 2),
                "active_sessions": self.get_active_sessions(),
                "stats": self.get_stats()
            })

        except Exception as e:
            health_data.update({
                "status": "error",
                "error": str(e)
            })

        return health_data


# Global Redis service instance
_redis_service: Optional[RedisService] = None


def get_redis_service(redis_url: str = "redis://localhost:6379", db: int = 0) -> RedisService:
    """
    Get or create global Redis service instance

    Args:
        redis_url: Redis connection URL
        db: Redis database number

    Returns:
        RedisService: Global Redis service instance
    """
    global _redis_service

    if _redis_service is None:
        _redis_service = RedisService(redis_url=redis_url, db=db)
        _redis_service.connect()

    return _redis_service


async def check_redis_connection(redis_url: str = "redis://localhost:6379") -> bool:
    """
    Async helper to check Redis connectivity

    Args:
        redis_url: Redis connection URL

    Returns:
        bool: True if connected, False otherwise
    """
    service = get_redis_service(redis_url)
    return service.is_connected()
