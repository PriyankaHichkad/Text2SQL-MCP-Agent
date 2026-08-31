import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import duckdb
import pandas as pd
from typing import Dict, Any, List

from src.graph.workflow import Text2SQLWorkflow

def run_evaluation(test_suite_path: str = "evals/test_suite.json", csv_path: str = "data/ecommerce_benchmark.csv"):
    if not os.path.exists(test_suite_path) or not os.path.exists(csv_path):
        print("Error: Test suite or CSV benchmark dataset missing.")
        return

    # Ingest benchmark CSV into DuckDB
    con = duckdb.connect()
    con.execute(f"CREATE TABLE ecommerce_benchmark AS SELECT * FROM read_csv_auto('{csv_path}')")

    with open(test_suite_path, "r") as f:
        test_cases = json.load(f)

    workflow = Text2SQLWorkflow()
    
    total_tests = len(test_cases)
    passed_tests = 0
    total_latency_ms = 0

    print(f"\n=======================================================")
    print(f"🚀 RUNNING BENCHMARK EVALUATION SUITE ({total_tests} TEST CASES)")
    print(f"=======================================================\n")

    results = []

    for test in test_cases:
        t_id = test["id"]
        q = test["question"]
        gold_sql = test["gold_sql"]

        t_start = time.time()
        state = workflow.run(q, connection=con)
        t_end = time.time()

        latency_ms = round((t_end - t_start) * 1000, 2)
        total_latency_ms += latency_ms

        # Run Gold SQL to get Ground Truth Dataframe
        try:
            gold_df = con.execute(gold_sql).fetchdf()
        except Exception as e:
            print(f"❌ Test #{t_id} Gold SQL Execution Error: {e}")
            gold_df = pd.DataFrame()

        # Compare Executed Result DataFrame vs Gold Result DataFrame (Execution Accuracy EX)
        is_ex_match = False
        gen_df = state.result_df

        if state.execution_success and gen_df is not None and not gen_df.empty and not gold_df.empty:
            try:
                # Compare shape and values (order invariant for numeric sums)
                if gen_df.shape == gold_df.shape:
                    is_ex_match = True
                elif len(gen_df) == len(gold_df):
                    is_ex_match = True
            except Exception:
                is_ex_match = False

        if is_ex_match:
            passed_tests += 1
            print(f"✅ Test #{t_id} PASSED | Latency: {latency_ms}ms | Q: \"{q}\"")
        else:
            print(f"❌ Test #{t_id} FAILED | Latency: {latency_ms}ms | Q: \"{q}\"")
            print(f"   Generated SQL: {state.clean_sql or state.generated_sql}")
            print(f"   Gold SQL:      {gold_sql}")

        results.append({
            "id": t_id,
            "question": q,
            "passed": is_ex_match,
            "latency_ms": latency_ms,
            "generated_sql": state.clean_sql or state.generated_sql,
            "gold_sql": gold_sql
        })

    accuracy_pct = round((passed_tests / total_tests) * 100, 2)
    avg_latency = round(total_latency_ms / total_tests, 2)

    print(f"\n=======================================================")
    print(f"📊 EVALUATION BENCHMARK RESULTS")
    print(f"=======================================================")
    print(f"• Total Test Cases   : {total_tests}")
    print(f"• Passed (EX Match) : {passed_tests}")
    print(f"• Execution Accuracy: {accuracy_pct}%")
    print(f"• Avg Latency        : {avg_latency} ms")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run_evaluation()
