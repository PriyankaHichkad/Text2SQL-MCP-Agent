import os
import sys
import time
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine import LLMRouter

def run_heuristic_benchmark(num_iterations: int = 1000):
    router = LLMRouter()
    
    # Representative prompt with schema and question
    sample_prompt = """Database Schema & Sample Values:
Table `ecommerce_benchmark`:
  - category (VARCHAR) (Samples: ['Furniture', 'Technology', 'Office Supplies'])
  - region (VARCHAR) (Samples: ['Europe', 'North America', 'Asia'])
  - net_amount (DOUBLE)
  - quantity (INT)
  - order_date (VARCHAR)
Question: "total net_amount in Europe for 2024"
"""

    # 1. Warm-up Phase (100 runs) to eliminate JIT / caching / Python imports cold start
    for _ in range(100):
        _ = router._dynamic_fallback_generator(sample_prompt)

    # 2. Timing Phase (1,000 runs) using time.perf_counter_ns()
    latencies_us = []  # microseconds
    for _ in range(num_iterations):
        t0 = time.perf_counter_ns()
        sql = router._dynamic_fallback_generator(sample_prompt)
        t1 = time.perf_counter_ns()
        latencies_us.append((t1 - t0) / 1000.0)

    # Convert to milliseconds
    latencies_ms = [us / 1000.0 for us in latencies_us]
    
    median_ms = statistics.median(latencies_ms)
    mean_ms = statistics.mean(latencies_ms)
    p95_ms = sorted(latencies_ms)[int(0.95 * len(latencies_ms))]
    p99_ms = sorted(latencies_ms)[int(0.99 * len(latencies_ms))]
    min_ms = min(latencies_ms)
    max_ms = max(latencies_ms)

    print("=" * 60)
    print("⚡ DETERMINISTIC HEURISTIC ENGINE LATENCY BENCHMARK (N=1,000)")
    print("=" * 60)
    print(f"• Generated Sample SQL : {sql.strip()}")
    print(f"• Minimum Latency      : {min_ms:.4f} ms ({min_ms*1000:.1f} µs)")
    print(f"• Median Latency (P50) : {median_ms:.4f} ms ({median_ms*1000:.1f} µs)")
    print(f"• Mean Latency         : {mean_ms:.4f} ms ({mean_ms*1000:.1f} µs)")
    print(f"• 95th Percentile (P95): {p95_ms:.4f} ms ({p95_ms*1000:.1f} µs)")
    print(f"• 99th Percentile (P99): {p99_ms:.4f} ms ({p99_ms*1000:.1f} µs)")
    print(f"• Maximum Latency      : {max_ms:.4f} ms ({max_ms*1000:.1f} µs)")
    print("=" * 60)
    
    is_sub_millisecond = p95_ms < 1.0
    print(f"✅ Verified Sub-Millisecond (<1.0 ms) at P95: {is_sub_millisecond}")
    print("=" * 60)

if __name__ == "__main__":
    run_heuristic_benchmark()
