#!/usr/bin/env python3
"""
Benchmarking and performance testing for the Enhanced RAG System
"""

import sys
import os
import time
from typing import List, Dict

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_system import RAGSystem


class RAGBenchmark:
    """Benchmarking suite for RAG system performance"""

    def __init__(self):
        self.rag_system = RAGSystem()
        self.test_queries = [
            # Technical concept queries
            "tensor operations broadcasting",
            "neural network backpropagation",
            "gradient computation autograd",
            "data loading DataLoader",
            "model training optimization",

            # Specific API queries
            "torch.nn.Module forward method",
            "torch.utils.data.Dataset custom",
            "torch.optim.SGD parameters",
            "torch.cuda memory management",
            "torch.tensor creation methods",

            # Complex queries
            "How to implement custom loss functions for multi-task learning?",
            "What are the performance implications of different tensor storage formats?",
            "Best practices for distributed training with PyTorch?",
            "Memory-efficient techniques for processing large datasets?",
            "How to debug gradient flow in deep neural networks?"
        ]

    def setup_system(self) -> bool:
        """Initialize and prepare the RAG system"""
        print("🔧 Setting up RAG system for benchmarking...")

        start_time = time.time()
        success = self.rag_system.process_structured_documents("data/website_docs.json")
        setup_time = time.time() - start_time

        if success:
            print(f"   ✅ Setup completed in {setup_time:.2f} seconds")
            print(f"   📊 Processed {len(self.rag_system.chunks)} chunks")
            return True
        else:
            print("   ❌ Setup failed")
            return False

    def benchmark_retrieval_speed(self, num_iterations: int = 5) -> Dict:
        """Benchmark retrieval speed across multiple queries"""
        print(f"\n⚡ Benchmarking retrieval speed ({num_iterations} iterations per query)...")

        results = {
            'query_times': [],
            'avg_scores': [],
            'total_time': 0,
            'queries_tested': 0
        }

        start_total = time.time()

        for query in self.test_queries:
            query_times = []
            query_scores = []

            for _ in range(num_iterations):
                start_time = time.time()
                result = self.rag_system.demo_query(query, top_k=3)
                query_time = time.time() - start_time

                query_times.append(query_time)

                if 'top_results' in result and result['top_results']:
                    query_scores.append(result['top_results'][0]['score'])

            avg_time = sum(query_times) / len(query_times)
            avg_score = sum(query_scores) / len(query_scores) if query_scores else 0

            results['query_times'].append(avg_time)
            results['avg_scores'].append(avg_score)
            results['queries_tested'] += 1

            print(f"   Query: '{query[:40]}...' | Time: {avg_time:.3f}s | Score: {avg_score:.3f}")

        results['total_time'] = time.time() - start_total

        return results

    def benchmark_retrieval_quality(self, top_k_values: List[int] = [1, 3, 5, 7]) -> Dict:
        """Benchmark retrieval quality with different top_k values"""
        print(f"\n🎯 Benchmarking retrieval quality with top_k values: {top_k_values}...")

        results = {
            'top_k_performance': {},
            'score_distributions': {}
        }

        for top_k in top_k_values:
            print(f"\n   Testing with top_k = {top_k}:")

            all_scores = []
            high_quality_matches = 0
            total_queries = 0

            for query in self.test_queries:
                result = self.rag_system.demo_query(query, top_k=top_k)

                if 'top_results' in result and result['top_results']:
                    scores = [doc['score'] for doc in result['top_results']]
                    all_scores.extend(scores)

                    if scores[0] > 0.5:  # High-quality threshold
                        high_quality_matches += 1

                    total_queries += 1

            if all_scores:
                avg_score = sum(all_scores) / len(all_scores)
                max_score = max(all_scores)
                min_score = min(all_scores)
                quality_rate = high_quality_matches / total_queries if total_queries > 0 else 0

                results['top_k_performance'][top_k] = {
                    'avg_score': avg_score,
                    'max_score': max_score,
                    'min_score': min_score,
                    'quality_rate': quality_rate,
                    'total_results': len(all_scores)
                }

                print(f"      Avg Score: {avg_score:.3f}")
                print(f"      High Quality Rate: {quality_rate:.1%}")
                print(f"      Total Results: {len(all_scores)}")

        return results

    def benchmark_content_types(self) -> Dict:
        """Analyze performance across different content types"""
        print(f"\n📋 Benchmarking performance by content type...")

        if not self.rag_system.chunk_metadata:
            print("   ❌ No metadata available for analysis")
            return {}

        # Group chunks by content type
        content_type_groups = {}
        for i, metadata in enumerate(self.rag_system.chunk_metadata):
            content_type = metadata.get('content_type', 'unknown')
            if content_type not in content_type_groups:
                content_type_groups[content_type] = []
            content_type_groups[content_type].append(i)

        results = {
            'content_type_distribution': {},
            'performance_by_type': {}
        }

        print(f"   Content Type Distribution:")
        for content_type, indices in content_type_groups.items():
            count = len(indices)
            percentage = (count / len(self.rag_system.chunk_metadata)) * 100
            results['content_type_distribution'][content_type] = {
                'count': count,
                'percentage': percentage
            }
            print(f"      {content_type}: {count} chunks ({percentage:.1f}%)")

        return results

    def run_comprehensive_benchmark(self) -> Dict:
        """Run all benchmark tests"""
        print("🚀 Running Comprehensive RAG System Benchmark")
        print("=" * 60)

        if not self.setup_system():
            return {'error': 'Failed to setup system'}

        # Run all benchmarks
        speed_results = self.benchmark_retrieval_speed()
        quality_results = self.benchmark_retrieval_quality()
        content_results = self.benchmark_content_types()

        # Compile final report
        final_results = {
            'speed': speed_results,
            'quality': quality_results,
            'content_analysis': content_results,
            'system_info': {
                'total_chunks': len(self.rag_system.chunks),
                'vectorizer_features': self.rag_system.tfidf_matrix.shape[1] if self.rag_system.tfidf_matrix is not None else 0,
                'test_queries': len(self.test_queries)
            }
        }

        # Print summary
        self.print_benchmark_summary(final_results)

        return final_results

    def print_benchmark_summary(self, results: Dict):
        """Print a comprehensive benchmark summary"""
        print(f"\n📊 BENCHMARK SUMMARY")
        print("=" * 40)

        # Speed summary
        if 'speed' in results:
            speed = results['speed']
            avg_query_time = sum(speed['query_times']) / len(speed['query_times'])
            avg_score = sum(speed['avg_scores']) / len(speed['avg_scores'])

            print(f"\n⚡ Speed Performance:")
            print(f"   Average Query Time: {avg_query_time:.3f} seconds")
            print(f"   Average Similarity Score: {avg_score:.3f}")
            print(f"   Queries per Second: {1/avg_query_time:.1f}")

        # Quality summary
        if 'quality' in results:
            quality = results['quality']
            print(f"\n🎯 Quality Performance:")

            for top_k, perf in quality['top_k_performance'].items():
                print(f"   top_k={top_k}: Avg={perf['avg_score']:.3f}, Quality Rate={perf['quality_rate']:.1%}")

        # System info
        if 'system_info' in results:
            info = results['system_info']
            print(f"\n🔧 System Configuration:")
            print(f"   Total Chunks: {info['total_chunks']}")
            print(f"   TF-IDF Features: {info['vectorizer_features']}")
            print(f"   Test Queries: {info['test_queries']}")

        print(f"\n✅ Benchmark completed successfully!")


def main():
    """Run the benchmarking suite"""
    benchmark = RAGBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    # Optionally save results to file
    if results and 'error' not in results:
        print(f"\n💾 Results saved to benchmark_results.json")
        import json
        with open('benchmark_results.json', 'w') as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()