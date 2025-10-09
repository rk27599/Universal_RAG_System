#!/usr/bin/env python3
"""
Performance Comparison: Sync vs Async Web Scraping
Demonstrates the performance improvements of the async scraper
"""

import sys
import os
import time
import asyncio
import json
from typing import Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem
from src.async_web_scraper import scrape_website_fast


class PerformanceComparison:
    """Compare sync vs async scraping performance"""

    def __init__(self):
        self.test_urls = [
            "https://example.com/",
            # Add more test URLs as needed
        ]
        self.results = {}

    def test_sync_scraper(self, max_pages: int = 15) -> Dict:
        """Test original synchronous scraper"""
        print("🐌 Testing Synchronous Scraper")
        print("=" * 50)

        start_time = time.time()

        # Clear any existing cache to ensure fair comparison
        output_file = "data/sync_performance_test.json"
        for ext in ['.json', '.txt', '_cache.pkl']:
            cache_file = output_file.replace('.json', ext)
            if os.path.exists(cache_file):
                os.remove(cache_file)

        # Test sync scraper
        rag_system = RAGSystem()
        success = rag_system.scrape_and_process_website(
            start_urls=self.test_urls,
            max_pages=max_pages,
            output_file=output_file,
            use_cache=False  # Disable cache for fair timing
        )

        duration = time.time() - start_time

        if success and os.path.exists(output_file):
            with open(output_file, 'r') as f:
                data = json.load(f)

            pages_scraped = len(data.get('documents', []))
            chunks_created = len(data.get('semantic_chunks', []))
        else:
            pages_scraped = 0
            chunks_created = 0

        result = {
            "method": "synchronous",
            "success": success,
            "duration": duration,
            "pages_scraped": pages_scraped,
            "chunks_created": chunks_created,
            "pages_per_second": pages_scraped / duration if duration > 0 else 0,
            "avg_page_time": duration / pages_scraped if pages_scraped > 0 else 0
        }

        print(f"⏱️ Duration: {duration:.2f}s")
        print(f"📄 Pages: {pages_scraped}")
        print(f"🧩 Chunks: {chunks_created}")
        print(f"📊 Rate: {result['pages_per_second']:.2f} pages/sec")
        print(f"🕐 Avg per page: {result['avg_page_time']:.2f}s")

        return result

    async def test_async_scraper(self, max_pages: int = 15, concurrent_limit: int = 8) -> Dict:
        """Test new asynchronous scraper"""
        print(f"\n⚡ Testing Asynchronous Scraper ({concurrent_limit} workers)")
        print("=" * 50)

        start_time = time.time()

        # Clear cache for fair comparison
        output_file = "data/async_performance_test.json"
        for ext in ['.json', '.txt']:
            cache_file = output_file.replace('.json', ext)
            if os.path.exists(cache_file):
                os.remove(cache_file)

        # Test async scraper
        try:
            results = await scrape_website_fast(
                start_urls=self.test_urls,
                max_pages=max_pages,
                concurrent_limit=concurrent_limit,
                requests_per_second=12.0,  # Higher rate for async
                output_file=output_file
            )

            duration = time.time() - start_time
            metadata = results.get("metadata", {})

            pages_scraped = metadata.get("total_pages", 0)
            chunks_created = metadata.get("total_chunks", 0)
            actual_rps = metadata.get("requests_per_second", 0)

            result = {
                "method": "asynchronous",
                "success": True,
                "duration": duration,
                "pages_scraped": pages_scraped,
                "chunks_created": chunks_created,
                "pages_per_second": pages_scraped / duration if duration > 0 else 0,
                "avg_page_time": duration / pages_scraped if pages_scraped > 0 else 0,
                "concurrent_workers": concurrent_limit,
                "actual_rps": actual_rps,
                "success_rate": metadata.get("success_rate", 0)
            }

            print(f"⏱️ Duration: {duration:.2f}s")
            print(f"📄 Pages: {pages_scraped}")
            print(f"🧩 Chunks: {chunks_created}")
            print(f"📊 Rate: {result['pages_per_second']:.2f} pages/sec")
            print(f"🕐 Avg per page: {result['avg_page_time']:.2f}s")
            print(f"🚀 Actual RPS: {actual_rps:.1f}")
            print(f"✅ Success rate: {metadata.get('success_rate', 0):.1f}%")

            return result

        except Exception as e:
            print(f"❌ Async test failed: {e}")
            return {
                "method": "asynchronous",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
                "concurrent_workers": concurrent_limit
            }

    async def compare_methods(self, max_pages: int = 15) -> Dict:
        """Run full performance comparison"""
        print("🏁 Performance Comparison: Sync vs Async Web Scraping")
        print("=" * 70)
        print(f"📋 Test Parameters:")
        print(f"   • URLs: {len(self.test_urls)}")
        print(f"   • Max pages: {max_pages}")
        print(f"   • Test site: {self.test_urls[0]}")
        print()

        # Test synchronous method
        sync_result = self.test_sync_scraper(max_pages)
        self.results['sync'] = sync_result

        # Test asynchronous method with different worker counts
        async_configs = [
            {"workers": 4, "name": "Conservative"},
            {"workers": 8, "name": "Balanced"},
            {"workers": 12, "name": "Aggressive"}
        ]

        async_results = []
        for config in async_configs:
            async_result = await self.test_async_scraper(
                max_pages, config["workers"]
            )
            async_result["config_name"] = config["name"]
            async_results.append(async_result)

        self.results['async'] = async_results

        # Generate comparison report
        return self.generate_performance_report()

    def generate_performance_report(self) -> Dict:
        """Generate detailed performance comparison report"""
        print(f"\n📊 Performance Analysis Report")
        print("=" * 70)

        sync_result = self.results.get('sync', {})
        async_results = self.results.get('async', [])

        if not sync_result.get('success'):
            print("❌ Sync test failed - cannot generate comparison")
            return self.results

        successful_async = [r for r in async_results if r.get('success')]
        if not successful_async:
            print("❌ All async tests failed - cannot generate comparison")
            return self.results

        # Find best async result
        best_async = max(successful_async, key=lambda x: x.get('pages_per_second', 0))

        print(f"🐌 Synchronous Performance:")
        print(f"   • Duration: {sync_result['duration']:.2f}s")
        print(f"   • Pages/sec: {sync_result['pages_per_second']:.2f}")
        print(f"   • Avg per page: {sync_result['avg_page_time']:.2f}s")

        print(f"\n⚡ Best Async Performance ({best_async.get('config_name', 'Unknown')}):")
        print(f"   • Duration: {best_async['duration']:.2f}s")
        print(f"   • Pages/sec: {best_async['pages_per_second']:.2f}")
        print(f"   • Avg per page: {best_async['avg_page_time']:.2f}s")
        print(f"   • Workers: {best_async.get('concurrent_workers', 'N/A')}")
        print(f"   • Actual RPS: {best_async.get('actual_rps', 0):.1f}")

        # Calculate improvements
        speed_improvement = best_async['pages_per_second'] / sync_result['pages_per_second']
        time_reduction = (sync_result['duration'] - best_async['duration']) / sync_result['duration'] * 100

        print(f"\n🎯 Performance Improvements:")
        print(f"   • Speed increase: {speed_improvement:.1f}x faster")
        print(f"   • Time reduction: {time_reduction:.1f}%")
        print(f"   • Efficiency gain: {(speed_improvement - 1) * 100:.1f}% better throughput")

        # All async results summary
        print(f"\n📈 All Async Configurations:")
        for result in successful_async:
            improvement = result['pages_per_second'] / sync_result['pages_per_second']
            print(f"   • {result.get('config_name', 'Unknown'):12}: "
                  f"{improvement:.1f}x faster, "
                  f"{result.get('concurrent_workers', 0):2d} workers, "
                  f"{result['duration']:.1f}s duration")

        # Save detailed results
        report_file = "data/performance_comparison_report.json"
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    "timestamp": time.time(),
                    "test_parameters": {
                        "urls": self.test_urls,
                        "max_pages": sync_result.get('pages_scraped', 0)
                    },
                    "results": self.results,
                    "summary": {
                        "best_async_improvement": speed_improvement,
                        "time_reduction_percent": time_reduction,
                        "recommended_config": best_async.get('config_name', 'Unknown')
                    }
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save report file: {e}")

        print(f"\n💾 Detailed report saved to: {report_file}")

        return self.results


async def main():
    """Run performance comparison"""
    print("🚀 Web Scraping Performance Comparison Tool")
    print("This will compare sync vs async scraping performance")
    print()

    # Create comparison instance
    comparison = PerformanceComparison()

    # Run comparison with a reasonable test size
    results = await comparison.compare_methods(max_pages=20)

    print(f"\n🎉 Performance comparison complete!")
    print(f"Check data/ directory for detailed results and scraped content.")

    return results


if __name__ == "__main__":
    asyncio.run(main())