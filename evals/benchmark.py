import time
import os
import sys
import duckdb
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow
from src.sandbox import SQLValidator

TEST_EVAL_QUERIES = [
    {
        "question": "What is total net revenue for completed orders in 2025?",
        "expected_clause": "SUM(net_amount)"
    },
    {
        "question": "top 5 product categories by total net revenue",
        "expected_clause": "GROUP BY category"
    },
    {
        "question": "percentage of returned orders from all orders",
        "expected_clause": "ROUND(100.0 *"
    },
    {
        "question": "total discount amount given in North America",
        "expected_clause": "North America"
    },
    {
        "question": "monthly net revenue for 2024",
        "expected_clause": "DATE_TRUNC"
    }
]

def run_benchmark():
    print("=" * 60)
    print("TEXT-TO-SQL FINE-TUNING BENCHMARK EVALUATION")
    print("=" * 60)

    con = duckdb.connect()
    benchmark_csv = "data/ecommerce_benchmark.csv"
    if os.path.exists(benchmark_csv):
        con.execute(f"CREATE TABLE ecommerce_benchmark AS SELECT * FROM read_csv_auto('{benchmark_csv}')")

    wf = Text2SQLWorkflow()
    validator = SQLValidator(dialect="duckdb")

    total_queries = len(TEST_EVAL_QUERIES)
    valid_sql_count = 0
    execution_success_count = 0
    total_latency_ms = 0.0

    print(f"\nRunning evaluation on {total_queries} test questions...\n")

    for i, test in enumerate(TEST_EVAL_QUERIES, 1):
        start_t = time.time()
        state = wf.run(test["question"], connection=con)
        end_t = time.time()
        
        latency = (end_t - start_t) * 1000.0
        total_latency_ms += latency

        is_valid = state.is_valid
        exec_ok = state.execution_success

        if is_valid:
            valid_sql_count += 1
        if exec_ok:
            execution_success_count += 1

        print(f"[{i}/{total_queries}] Question: \"{test['question']}\"")
        print(f"      Engine Used   : {state.used_engine}")
        print(f"      AST Valid     : {'YES' if is_valid else 'NO'}")
        print(f"      Execution OK  : {'YES' if exec_ok else 'NO'}")
        print(f"      Latency       : {latency:.2f} ms")
        print("-" * 60)

    avg_latency = total_latency_ms / total_queries
    ast_valid_pct = (valid_sql_count / total_queries) * 100.0
    exec_accuracy_pct = (execution_success_count / total_queries) * 100.0

    print("\n" + "=" * 60)
    print("📊 BENCHMARK EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Test Questions     : {total_queries}")
    print(f"AST Syntax Validity      : {ast_valid_pct:.1f}% ({valid_sql_count}/{total_queries})")
    print(f"Execution Accuracy (EX %): {exec_accuracy_pct:.1f}% ({execution_success_count}/{total_queries})")
    print(f"Average Latency          : {avg_latency:.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
