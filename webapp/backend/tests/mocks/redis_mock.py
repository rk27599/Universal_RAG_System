"""
Mock Redis Client for Testing
Simulates Redis operations without requiring actual Redis server
"""

from typing import Any, Optional, Dict
from unittest.mock import AsyncMock


class MockRedisClient:
    """Mock Redis client for testing"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._pubsub_channels: Dict[str, list] = {}

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Mock SET operation"""
        self._data[key] = value
        return True

    async def get(self, key: str) -> Optional[Any]:
        """Mock GET operation"""
        return self._data.get(key)

    async def delete(self, *keys: str) -> int:
        """Mock DELETE operation"""
        deleted = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                deleted += 1
        return deleted

    async def exists(self, *keys: str) -> int:
        """Mock EXISTS operation"""
        return sum(1 for key in keys if key in self._data)

    async def ping(self) -> bool:
        """Mock PING operation"""
        return True

    async def publish(self, channel: str, message: Any) -> int:
        """Mock PUBLISH operation"""
        if channel not in self._pubsub_channels:
            self._pubsub_channels[channel] = []
        self._pubsub_channels[channel].append(message)
        return len(self._pubsub_channels[channel])

    def pubsub(self):
        """Mock PUBSUB operation"""
        return MockRedisPubSub(self._pubsub_channels)

    async def close(self):
        """Mock close operation"""
        pass


class MockRedisPubSub:
    """Mock Redis PubSub for testing"""

    def __init__(self, channels: Dict[str, list]):
        self._channels = channels
        self._subscriptions = []

    async def subscribe(self, *channels: str):
        """Mock SUBSCRIBE operation"""
        self._subscriptions.extend(channels)

    async def unsubscribe(self, *channels: str):
        """Mock UNSUBSCRIBE operation"""
        for channel in channels:
            if channel in self._subscriptions:
                self._subscriptions.remove(channel)

    async def get_message(self) -> Optional[Dict[str, Any]]:
        """Mock GET_MESSAGE operation"""
        for channel in self._subscriptions:
            if channel in self._channels and self._channels[channel]:
                message = self._channels[channel].pop(0)
                return {
                    "type": "message",
                    "channel": channel.encode(),
                    "data": message
                }
        return None
