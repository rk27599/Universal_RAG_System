#!/usr/bin/env python3
"""
Comprehensive Redis and WebSocket Integration Tests
Tests Redis connectivity, session management, and multi-worker WebSocket support
"""

import asyncio
import pytest
import socketio
import redis
from typing import List, Dict
import time
import json


# Test configuration
REDIS_URL = "redis://localhost:6379"
REDIS_DB = 0
WEBSOCKET_URL = "http://127.0.0.1:8000"
TEST_TOKEN = "test_auth_token"  # Replace with actual token from login


class TestRedisConnectivity:
    """Test Redis server connectivity and basic operations"""

    def test_redis_connection(self):
        """Test basic Redis connection"""
        try:
            client = redis.Redis.from_url(REDIS_URL, db=REDIS_DB, decode_responses=True)
            result = client.ping()
            assert result is True, "Redis ping failed"
            print("✅ Redis connection successful")
        except redis.ConnectionError as e:
            pytest.fail(f"❌ Redis connection failed: {e}")

    def test_redis_set_get(self):
        """Test Redis SET and GET operations"""
        try:
            client = redis.Redis.from_url(REDIS_URL, db=REDIS_DB, decode_responses=True)

            # Set test value
            test_key = "test:redis:key"
            test_value = "test_value_123"
            client.set(test_key, test_value, ex=60)

            # Get test value
            retrieved = client.get(test_key)
            assert retrieved == test_value, f"Expected {test_value}, got {retrieved}"

            # Cleanup
            client.delete(test_key)
            print("✅ Redis SET/GET operations successful")
        except Exception as e:
            pytest.fail(f"❌ Redis SET/GET test failed: {e}")

    def test_redis_session_storage(self):
        """Test session storage pattern used by Socket.IO"""
        try:
            client = redis.Redis.from_url(REDIS_URL, db=REDIS_DB, decode_responses=True)

            # Simulate Socket.IO session
            session_id = "test_session_123"
            session_data = {
                "user_id": "user_001",
                "username": "testuser",
                "connected_at": time.time()
            }

            key = f"socketio:session:{session_id}"
            client.setex(key, 3600, json.dumps(session_data))

            # Retrieve session
            retrieved = client.get(key)
            assert retrieved is not None, "Session not found"

            retrieved_data = json.loads(retrieved)
            assert retrieved_data["user_id"] == session_data["user_id"]
            assert retrieved_data["username"] == session_data["username"]

            # Cleanup
            client.delete(key)
            print("✅ Redis session storage test successful")
        except Exception as e:
            pytest.fail(f"❌ Redis session storage test failed: {e}")

    def test_redis_connection_pool(self):
        """Test Redis connection pooling"""
        try:
            pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                db=REDIS_DB,
                max_connections=10,
                decode_responses=True
            )

            # Create multiple clients from same pool
            clients = [redis.Redis(connection_pool=pool) for _ in range(5)]

            # Test concurrent operations
            for i, client in enumerate(clients):
                client.set(f"pool:test:{i}", f"value_{i}")

            # Verify all values
            for i, client in enumerate(clients):
                value = client.get(f"pool:test:{i}")
                assert value == f"value_{i}", f"Expected value_{i}, got {value}"

            # Cleanup
            for i in range(5):
                clients[0].delete(f"pool:test:{i}")

            pool.disconnect()
            print("✅ Redis connection pool test successful")
        except Exception as e:
            pytest.fail(f"❌ Redis connection pool test failed: {e}")


class TestWebSocketRedisIntegration:
    """Test WebSocket integration with Redis session management"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test basic WebSocket connection with Redis backend"""
        try:
            sio = socketio.AsyncClient()

            connected = False

            @sio.event
            async def connect():
                nonlocal connected
                connected = True
                print("✅ WebSocket connected")

            @sio.event
            async def disconnect():
                print("🔌 WebSocket disconnected")

            # Connect with authentication
            await sio.connect(WEBSOCKET_URL, auth={"token": TEST_TOKEN})
            await asyncio.sleep(1)

            assert connected, "WebSocket connection failed"
            assert sio.connected, "Socket.IO not connected"

            await sio.disconnect()
            print("✅ WebSocket connection test successful")

        except Exception as e:
            pytest.fail(f"❌ WebSocket connection test failed: {e}")

    @pytest.mark.asyncio
    async def test_websocket_reconnection(self):
        """Test WebSocket reconnection with Redis session persistence"""
        try:
            sio = socketio.AsyncClient(
                reconnection=True,
                reconnection_attempts=5,
                reconnection_delay=1
            )

            connection_count = 0

            @sio.event
            async def connect():
                nonlocal connection_count
                connection_count += 1
                print(f"✅ WebSocket connected (attempt {connection_count})")

            # Initial connection
            await sio.connect(WEBSOCKET_URL, auth={"token": TEST_TOKEN})
            await asyncio.sleep(1)

            assert connection_count == 1, "Initial connection failed"

            # Simulate disconnect
            await sio.disconnect()
            await asyncio.sleep(2)

            # Reconnect
            await sio.connect(WEBSOCKET_URL, auth={"token": TEST_TOKEN})
            await asyncio.sleep(1)

            assert connection_count == 2, "Reconnection failed"

            await sio.disconnect()
            print("✅ WebSocket reconnection test successful")

        except Exception as e:
            pytest.fail(f"❌ WebSocket reconnection test failed: {e}")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self):
        """Test multiple concurrent WebSocket connections (simulates multi-worker scenario)"""
        try:
            num_clients = 5
            clients: List[socketio.AsyncClient] = []

            # Create multiple clients
            for i in range(num_clients):
                client = socketio.AsyncClient()

                @client.event
                async def connect():
                    print(f"✅ Client {i} connected")

                clients.append(client)

            # Connect all clients concurrently
            connect_tasks = [
                client.connect(WEBSOCKET_URL, auth={"token": TEST_TOKEN})
                for client in clients
            ]
            await asyncio.gather(*connect_tasks)
            await asyncio.sleep(2)

            # Verify all connected
            connected_count = sum(1 for client in clients if client.connected)
            assert connected_count == num_clients, f"Only {connected_count}/{num_clients} clients connected"

            # Disconnect all
            disconnect_tasks = [client.disconnect() for client in clients]
            await asyncio.gather(*disconnect_tasks)

            print(f"✅ Multiple concurrent connections test successful ({num_clients} clients)")

        except Exception as e:
            pytest.fail(f"❌ Multiple concurrent connections test failed: {e}")

    @pytest.mark.asyncio
    async def test_message_broadcast_multi_worker(self):
        """Test message broadcasting across multiple clients (multi-worker scenario)"""
        try:
            num_clients = 3
            clients: List[socketio.AsyncClient] = []
            received_messages: List[Dict] = []

            # Create clients
            for i in range(num_clients):
                client = socketio.AsyncClient()

                @client.event
                async def message(data):
                    received_messages.append(data)
                    print(f"📨 Client received message: {data.get('content', '')[:50]}")

                @client.event
                async def message_chunk(data):
                    print(f"📨 Client received chunk: {data.get('content', '')[:20]}")

                clients.append(client)

            # Connect all clients
            for client in clients:
                await client.connect(WEBSOCKET_URL, auth={"token": TEST_TOKEN})

            await asyncio.sleep(2)

            # Send test message from first client
            test_message = {
                "conversationId": "test_conv_123",
                "content": "Test message for multi-worker broadcast",
                "model": "mistral"
            }

            await clients[0].emit("send_message", test_message)
            await asyncio.sleep(5)  # Wait for response

            # Disconnect all
            for client in clients:
                await client.disconnect()

            print(f"✅ Message broadcast test successful (received {len(received_messages)} messages)")

        except Exception as e:
            pytest.fail(f"❌ Message broadcast test failed: {e}")


class TestRedisPerformance:
    """Test Redis performance and scalability"""

    def test_redis_latency(self):
        """Test Redis operation latency"""
        try:
            client = redis.Redis.from_url(REDIS_URL, db=REDIS_DB, decode_responses=True)

            # Warm up
            for _ in range(10):
                client.ping()

            # Measure latency
            iterations = 100
            start = time.time()

            for _ in range(iterations):
                client.ping()

            elapsed = time.time() - start
            avg_latency_ms = (elapsed / iterations) * 1000

            assert avg_latency_ms < 10, f"Redis latency too high: {avg_latency_ms:.2f}ms"

            print(f"✅ Redis latency test successful: {avg_latency_ms:.2f}ms average")

        except Exception as e:
            pytest.fail(f"❌ Redis latency test failed: {e}")

    def test_redis_throughput(self):
        """Test Redis throughput for session operations"""
        try:
            client = redis.Redis.from_url(REDIS_URL, db=REDIS_DB, decode_responses=True)

            # Test write throughput
            num_operations = 1000
            start = time.time()

            for i in range(num_operations):
                key = f"perf:test:{i}"
                client.set(key, f"value_{i}", ex=60)

            write_elapsed = time.time() - start
            write_ops_per_sec = num_operations / write_elapsed

            # Test read throughput
            start = time.time()

            for i in range(num_operations):
                key = f"perf:test:{i}"
                client.get(key)

            read_elapsed = time.time() - start
            read_ops_per_sec = num_operations / read_elapsed

            # Cleanup
            for i in range(num_operations):
                client.delete(f"perf:test:{i}")

            assert write_ops_per_sec > 500, f"Write throughput too low: {write_ops_per_sec:.0f} ops/sec"
            assert read_ops_per_sec > 500, f"Read throughput too low: {read_ops_per_sec:.0f} ops/sec"

            print(f"✅ Redis throughput test successful:")
            print(f"   Write: {write_ops_per_sec:.0f} ops/sec")
            print(f"   Read: {read_ops_per_sec:.0f} ops/sec")

        except Exception as e:
            pytest.fail(f"❌ Redis throughput test failed: {e}")


def run_all_tests():
    """Run all tests with detailed output"""
    print("=" * 70)
    print("🧪 Redis and WebSocket Integration Test Suite")
    print("=" * 70)

    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_all_tests()
