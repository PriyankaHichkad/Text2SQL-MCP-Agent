import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine import LLMRouter, SchemaCatalog
from src.sandbox import SQLExecutionSandbox

def test_app_model_access():
    load_dotenv()
    print("=" * 60)
    print("🔍 TESTING APP ACCESS TO FINE-TUNED MODEL & COMPLEX ROUTING")
    print("=" * 60)

    # 1. Initialize Engine Router
    router = LLMRouter()
    print(f"\n📡 Active LLM Engine Status: {router.active_engine}")
    
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    hf_repo = os.getenv("HF_MODEL_REPO", "Priyanka221105/text2sql-qwen2.5-duckdb")

    if hf_token and "HuggingFace" in router.active_engine:
        print(f"✅ App successfully connected to Fine-Tuned Model: {hf_repo}")
    elif os.getenv("GEMINI_API_KEY"):
        print(f"ℹ️ App running with Gemini Cloud Engine fallback: {router.model_name}")
    else:
        print("ℹ️ App running with Zero-Shot Engine fallback.")

    # 2. Test Complex Analytical Query Generation
    complex_prompt = (
        "Database Schema:\n"
        "Table `ecommerce_benchmark`: order_id (INT), category (VARCHAR), net_amount (DOUBLE), order_date (DATE)\n\n"
        "Question: \"Calculate month-over-month revenue growth percentage using lag window function for 2024\""
    )

    print("\n------------------------------------------------------------")
    print("🧪 Testing Difficult Analytical Query Generation:")
    print("------------------------------------------------------------")
    print(f"Prompt Question: Calculate MoM Growth with LAG Window Function")
    
    generated_sql = router.generate(complex_prompt)
    print(f"\nGenerated Output:\n{generated_sql}")

    # 3. Test Query Execution in DuckDB Sandbox
    print("\n------------------------------------------------------------")
    print("🛡️ Sandbox Validation & Execution Check:")
    print("------------------------------------------------------------")
    sandbox = SQLExecutionSandbox()
    valid_ast, exec_res, error_msg, latency = sandbox.execute_query(generated_sql)
    
    exec_ok = isinstance(exec_res, pd.DataFrame)
    print(f"AST Valid   : {'✅ YES' if valid_ast else '❌ NO'}")
    print(f"Execution OK: {'✅ YES' if exec_ok else '❌ NO'}")
    print(f"Latency     : {latency} ms")
    print("=" * 60)

if __name__ == "__main__":
    test_app_model_access()
