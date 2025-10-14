#!/usr/bin/env python3
"""
Redis Health Monitoring Script
Monitor Redis connection, sessions, and performance
"""

import sys
import os
import redis
import time
import json
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Settings

settings = Settings()


class RedisHealthMonitor:
    """Monitor Redis health and performance"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.client = None

    def connect(self) -> bool:
        """Connect to Redis server"""
        try:
            self.client = redis.Redis.from_url(
                self.redis_url,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            self.client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False

    def get_basic_info(self) -> Dict[str, Any]:
        """Get basic Redis information"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            info = self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "redis_mode": info.get("redis_mode", "standalone"),
                "os": info.get("os"),
                "arch_bits": info.get("arch_bits"),
                "process_id": info.get("process_id"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "uptime_in_days": info.get("uptime_in_days")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "client_longest_output_list": info.get("client_longest_output_list"),
                "client_biggest_input_buf": info.get("client_biggest_input_buf"),
                "blocked_clients": info.get("blocked_clients"),
                "total_connections_received": info.get("total_connections_received"),
                "rejected_connections": info.get("rejected_connections")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            info = self.client.info()
            return {
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_rss_human": info.get("used_memory_rss_human"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "total_system_memory_human": info.get("total_system_memory_human"),
                "used_memory_dataset": info.get("used_memory_dataset"),
                "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_session_stats(self) -> Dict[str, Any]:
        """Get Socket.IO session statistics"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            # Count Socket.IO sessions
            session_pattern = "socketio:session:*"
            sessions = list(self.client.scan_iter(match=session_pattern, count=100))

            session_details = []
            for session_key in sessions[:10]:  # Show first 10 sessions
                ttl = self.client.ttl(session_key)
                session_data = self.client.get(session_key)
                try:
                    data = json.loads(session_data) if session_data else {}
                    session_details.append({
                        "key": session_key,
                        "ttl_seconds": ttl,
                        "user_id": data.get("user_id", "unknown"),
                        "username": data.get("username", "unknown")
                    })
                except:
                    pass

            return {
                "total_sessions": len(sessions),
                "active_sessions": session_details
            }
        except Exception as e:
            return {"error": str(e)}

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            info = self.client.info()
            return {
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "instantaneous_input_kbps": info.get("instantaneous_input_kbps"),
                "instantaneous_output_kbps": info.get("instantaneous_output_kbps"),
                "total_commands_processed": info.get("total_commands_processed"),
                "total_net_input_bytes": info.get("total_net_input_bytes"),
                "total_net_output_bytes": info.get("total_net_output_bytes")
            }
        except Exception as e:
            return {"error": str(e)}

    def measure_latency(self, iterations: int = 100) -> Dict[str, float]:
        """Measure Redis operation latency"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            # Warm up
            for _ in range(10):
                self.client.ping()

            # Measure PING latency
            start = time.time()
            for _ in range(iterations):
                self.client.ping()
            ping_elapsed = (time.time() - start) / iterations * 1000

            # Measure GET latency
            self.client.set("latency:test", "value")
            start = time.time()
            for _ in range(iterations):
                self.client.get("latency:test")
            get_elapsed = (time.time() - start) / iterations * 1000

            # Measure SET latency
            start = time.time()
            for _ in range(iterations):
                self.client.set("latency:test", "value")
            set_elapsed = (time.time() - start) / iterations * 1000

            # Cleanup
            self.client.delete("latency:test")

            return {
                "ping_ms": round(ping_elapsed, 2),
                "get_ms": round(get_elapsed, 2),
                "set_ms": round(set_elapsed, 2),
                "iterations": iterations
            }
        except Exception as e:
            return {"error": str(e)}

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles TTL, this is for reporting)"""
        if not self.client:
            return 0

        try:
            pattern = "socketio:session:*"
            sessions = list(self.client.scan_iter(match=pattern, count=100))
            return len(sessions)
        except Exception as e:
            print(f"Error cleaning sessions: {e}")
            return 0

    def print_health_report(self):
        """Print comprehensive health report"""
        print("=" * 80)
        print("🏥 Redis Health Report")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Basic Info
        print("\n📊 Basic Information:")
        basic_info = self.get_basic_info()
        for key, value in basic_info.items():
            print(f"   {key}: {value}")

        # Connection Stats
        print("\n🔌 Connection Statistics:")
        conn_stats = self.get_connection_stats()
        for key, value in conn_stats.items():
            print(f"   {key}: {value}")

        # Memory Stats
        print("\n💾 Memory Statistics:")
        mem_stats = self.get_memory_stats()
        for key, value in mem_stats.items():
            print(f"   {key}: {value}")

        # Session Stats
        print("\n👥 Socket.IO Session Statistics:")
        session_stats = self.get_session_stats()
        print(f"   Total Sessions: {session_stats.get('total_sessions', 0)}")
        if "active_sessions" in session_stats:
            print(f"   Active Sessions (sample):")
            for session in session_stats["active_sessions"][:5]:
                print(f"      • {session['username']} (TTL: {session['ttl_seconds']}s)")

        # Performance Stats
        print("\n⚡ Performance Statistics:")
        perf_stats = self.get_performance_stats()
        for key, value in perf_stats.items():
            print(f"   {key}: {value}")

        # Latency
        print("\n⏱️  Latency Measurements:")
        latency = self.measure_latency()
        for key, value in latency.items():
            print(f"   {key}: {value}")

        print("\n" + "=" * 80)

        # Health Status
        is_healthy = (
            latency.get("ping_ms", 999) < 10 and
            session_stats.get("total_sessions", 0) >= 0
        )

        if is_healthy:
            print("✅ Redis Status: HEALTHY")
        else:
            print("⚠️  Redis Status: DEGRADED")

        print("=" * 80)


def main():
    """Main entry point"""
    print("\n🔧 Initializing Redis Health Monitor...")

    monitor = RedisHealthMonitor()

    if not monitor.connect():
        print("❌ Failed to connect to Redis")
        print("   Please ensure Redis server is running:")
        print("   • sudo service redis-server start")
        print("   • redis-cli ping")
        sys.exit(1)

    print("✅ Connected to Redis successfully\n")

    # Print health report
    monitor.print_health_report()

    # Optional: Continuous monitoring
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        print("\n👁️  Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                time.sleep(5)
                os.system('clear' if os.name == 'posix' else 'cls')
                monitor.print_health_report()
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")


if __name__ == "__main__":
    main()
