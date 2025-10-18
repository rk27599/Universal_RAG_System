"""
Memory Manager - Intelligent memory management for ML models
Provides adaptive batch sizing and model lifecycle management
"""

import logging
import psutil
import gc
import torch
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Centralized memory management for ML models

    Features:
    - Monitor system RAM and swap usage
    - Calculate adaptive batch sizes based on available memory
    - Track model last access time for idle unloading
    - Provide memory statistics and recommendations
    """

    # Default thresholds (in GB)
    HIGH_MEMORY_THRESHOLD = 8.0
    MEDIUM_MEMORY_THRESHOLD = 4.0
    LOW_MEMORY_THRESHOLD = 2.0
    CRITICAL_MEMORY_THRESHOLD = 1.0

    # Default batch sizes
    BATCH_SIZE_HIGH = 32
    BATCH_SIZE_MEDIUM = 16
    BATCH_SIZE_LOW = 8
    BATCH_SIZE_CRITICAL = 4

    # Model idle timeout (seconds)
    DEFAULT_IDLE_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
        enable_auto_unload: bool = True
    ):
        """
        Initialize Memory Manager

        Args:
            idle_timeout: Seconds before unloading idle models (default: 300)
            enable_auto_unload: Enable automatic model unloading (default: True)
        """
        self.idle_timeout = idle_timeout
        self.enable_auto_unload = enable_auto_unload
        self.model_access_times: Dict[str, datetime] = {}

        logger.info(f"📊 MemoryManager initialized")
        logger.info(f"  Idle timeout: {idle_timeout}s")
        logger.info(f"  Auto-unload: {enable_auto_unload}")

    def get_memory_stats(self) -> Dict[str, float]:
        """
        Get current memory statistics

        Returns:
            Dict with memory metrics in GB
        """
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        stats = {
            'total_ram_gb': memory.total / (1024**3),
            'used_ram_gb': memory.used / (1024**3),
            'free_ram_gb': memory.available / (1024**3),
            'ram_percent': memory.percent,
            'total_swap_gb': swap.total / (1024**3),
            'used_swap_gb': swap.used / (1024**3),
            'free_swap_gb': swap.free / (1024**3),
            'swap_percent': swap.percent
        }

        return stats

    def get_gpu_memory_stats(self) -> Optional[Dict[str, float]]:
        """
        Get GPU memory statistics if CUDA is available

        Returns:
            Dict with GPU memory metrics in GB, or None if no GPU
        """
        if not torch.cuda.is_available():
            return None

        try:
            allocated = torch.cuda.memory_allocated() / (1024**3)
            reserved = torch.cuda.memory_reserved() / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)

            return {
                'gpu_allocated_gb': allocated,
                'gpu_reserved_gb': reserved,
                'gpu_total_gb': total,
                'gpu_free_gb': total - allocated
            }
        except Exception as e:
            logger.warning(f"Failed to get GPU memory stats: {e}")
            return None

    def calculate_adaptive_batch_size(
        self,
        default_batch_size: int = 16,
        model_name: str = "unknown"
    ) -> int:
        """
        Calculate optimal batch size based on available memory

        Args:
            default_batch_size: Fallback batch size
            model_name: Model identifier for logging

        Returns:
            Recommended batch size
        """
        try:
            stats = self.get_memory_stats()
            free_ram_gb = stats['free_ram_gb']

            # Determine batch size based on free RAM
            if free_ram_gb >= self.HIGH_MEMORY_THRESHOLD:
                batch_size = self.BATCH_SIZE_HIGH
                level = "HIGH"
            elif free_ram_gb >= self.MEDIUM_MEMORY_THRESHOLD:
                batch_size = self.BATCH_SIZE_MEDIUM
                level = "MEDIUM"
            elif free_ram_gb >= self.LOW_MEMORY_THRESHOLD:
                batch_size = self.BATCH_SIZE_LOW
                level = "LOW"
            elif free_ram_gb >= self.CRITICAL_MEMORY_THRESHOLD:
                batch_size = self.BATCH_SIZE_CRITICAL
                level = "CRITICAL"
                logger.warning(f"⚠️ Critical memory: {free_ram_gb:.1f}GB free")
            else:
                batch_size = 2
                level = "EMERGENCY"
                logger.error(f"🚨 Emergency low memory: {free_ram_gb:.1f}GB free")

            logger.debug(
                f"📊 Adaptive batch size for {model_name}: {batch_size} "
                f"({level} - {free_ram_gb:.1f}GB free)"
            )

            return batch_size

        except Exception as e:
            logger.error(f"Error calculating adaptive batch size: {e}")
            return default_batch_size

    def record_model_access(self, model_name: str):
        """
        Record that a model was accessed (reset idle timer)

        Args:
            model_name: Model identifier
        """
        self.model_access_times[model_name] = datetime.now()

    def should_unload_model(self, model_name: str) -> bool:
        """
        Check if a model should be unloaded due to idle timeout

        Args:
            model_name: Model identifier

        Returns:
            True if model should be unloaded
        """
        if not self.enable_auto_unload:
            return False

        last_access = self.model_access_times.get(model_name)
        if last_access is None:
            return False

        idle_time = (datetime.now() - last_access).total_seconds()
        should_unload = idle_time > self.idle_timeout

        if should_unload:
            logger.info(
                f"🔄 Model {model_name} idle for {idle_time:.0f}s "
                f"(threshold: {self.idle_timeout}s) - marking for unload"
            )

        return should_unload

    def get_idle_models(self) -> Dict[str, float]:
        """
        Get all models that have exceeded idle timeout

        Returns:
            Dict mapping model_name to idle_time_seconds
        """
        idle_models = {}
        now = datetime.now()

        for model_name, last_access in self.model_access_times.items():
            idle_time = (now - last_access).total_seconds()
            if idle_time > self.idle_timeout:
                idle_models[model_name] = idle_time

        return idle_models

    def clear_cuda_cache(self):
        """
        Clear CUDA cache to free GPU memory
        """
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("🧹 CUDA cache cleared")

    def force_garbage_collection(self):
        """
        Force Python garbage collection to free memory
        """
        collected = gc.collect()
        logger.debug(f"🧹 Garbage collection: {collected} objects collected")

    def cleanup_after_unload(self, model_name: str):
        """
        Perform cleanup after unloading a model

        Args:
            model_name: Model identifier
        """
        # Clear CUDA cache
        self.clear_cuda_cache()

        # Force garbage collection
        self.force_garbage_collection()

        # Remove from access times
        if model_name in self.model_access_times:
            del self.model_access_times[model_name]

        logger.info(f"✅ Cleanup complete for {model_name}")

    def log_memory_status(self):
        """
        Log current memory status for monitoring
        """
        stats = self.get_memory_stats()
        gpu_stats = self.get_gpu_memory_stats()

        logger.info(
            f"💾 Memory Status: "
            f"RAM {stats['free_ram_gb']:.1f}GB free / {stats['total_ram_gb']:.1f}GB total "
            f"({stats['ram_percent']:.1f}% used) | "
            f"Swap {stats['free_swap_gb']:.1f}GB free / {stats['total_swap_gb']:.1f}GB total "
            f"({stats['swap_percent']:.1f}% used)"
        )

        if gpu_stats:
            logger.info(
                f"🎮 GPU Memory: "
                f"{gpu_stats['gpu_free_gb']:.1f}GB free / {gpu_stats['gpu_total_gb']:.1f}GB total"
            )

    def check_memory_health(self) -> Dict[str, any]:
        """
        Check overall memory health and return recommendations

        Returns:
            Dict with status and recommendations
        """
        stats = self.get_memory_stats()
        free_ram = stats['free_ram_gb']
        swap_percent = stats['swap_percent']

        status = "healthy"
        recommendations = []

        # Check RAM
        if free_ram < self.CRITICAL_MEMORY_THRESHOLD:
            status = "critical"
            recommendations.append("CRITICAL: Free RAM below 1GB - unload models immediately")
        elif free_ram < self.LOW_MEMORY_THRESHOLD:
            status = "warning"
            recommendations.append("Warning: Low RAM - consider unloading idle models")
        elif free_ram < self.MEDIUM_MEMORY_THRESHOLD:
            status = "moderate"
            recommendations.append("Moderate memory pressure - using reduced batch sizes")

        # Check swap
        if swap_percent > 90:
            status = "critical"
            recommendations.append("CRITICAL: Swap usage >90% - system may become unresponsive")
        elif swap_percent > 75:
            if status != "critical":
                status = "warning"
            recommendations.append("Warning: High swap usage - consider increasing RAM or swap space")

        return {
            'status': status,
            'free_ram_gb': free_ram,
            'swap_percent': swap_percent,
            'recommendations': recommendations
        }


# Global instance (singleton)
_memory_manager_instance: Optional[MemoryManager] = None


def get_memory_manager(
    idle_timeout: int = MemoryManager.DEFAULT_IDLE_TIMEOUT,
    enable_auto_unload: bool = True
) -> MemoryManager:
    """
    Get or create the global memory manager instance

    Args:
        idle_timeout: Model idle timeout in seconds
        enable_auto_unload: Enable automatic model unloading

    Returns:
        MemoryManager instance
    """
    global _memory_manager_instance

    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(
            idle_timeout=idle_timeout,
            enable_auto_unload=enable_auto_unload
        )
        logger.info("✅ Global memory manager created")

    return _memory_manager_instance


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    mm = MemoryManager(idle_timeout=60)

    print("\n=== Memory Statistics ===")
    stats = mm.get_memory_stats()
    for key, value in stats.items():
        print(f"{key}: {value:.2f}")

    print("\n=== GPU Memory ===")
    gpu_stats = mm.get_gpu_memory_stats()
    if gpu_stats:
        for key, value in gpu_stats.items():
            print(f"{key}: {value:.2f}")
    else:
        print("No GPU available")

    print("\n=== Adaptive Batch Size ===")
    batch_size = mm.calculate_adaptive_batch_size(model_name="test_model")
    print(f"Recommended batch size: {batch_size}")

    print("\n=== Memory Health ===")
    health = mm.check_memory_health()
    print(f"Status: {health['status']}")
    print(f"Free RAM: {health['free_ram_gb']:.1f}GB")
    print(f"Swap usage: {health['swap_percent']:.1f}%")
    if health['recommendations']:
        print("Recommendations:")
        for rec in health['recommendations']:
            print(f"  - {rec}")
