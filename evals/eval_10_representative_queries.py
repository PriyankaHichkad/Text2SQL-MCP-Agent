import os
import sys
import duckdb
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow

load_dotenv()

# 10 Representative Text-to-SQL Benchmark Questions covering all SQL complexity tiers
REPRESENTATIVE_TEST_CASES = [
    {
        "id": 1,
        "category": "Multi-Table Join",
        "question": "List orders with customer name and total net amount joining customers and orders",
        "reference_sql": "SELECT o.order_id, c.customer_name, o.net_amount FROM orders o JOIN customers c ON o.customer_id = c.customer_id;"
    },
    {
        "id": 2,
        "category": "Aggregate Metrics (SUM & AVG)",
        "question": "What is the total revenue and average discount amount for Furniture in Europe?",
        "reference_sql": "SELECT SUM(net_amount) AS total_revenue, AVG(discount_amount) AS avg_discount FROM orders WHERE category = 'Furniture' AND region = 'Europe';"
    },
    {
        "id": 3,
        "category": "Window Function (RANK OVER)",
        "question": "Rank orders in each region by net_amount in descending order",
        "reference_sql": "SELECT order_id, region, net_amount, RANK() OVER (PARTITION BY region ORDER BY net_amount DESC) AS region_rank FROM orders;"
    },
    {
        "id": 4,
        "category": "Common Table Expression (CTE)",
        "question": "Use a CTE to find categories whose total sales exceed 10000",
        "reference_sql": "WITH cat_sales AS (SELECT category, SUM(net_amount) AS total_sales FROM orders GROUP BY category) SELECT * FROM cat_sales WHERE total_sales > 10000;"
    },
    {
        "id": 5,
        "category": "Relative Date Arithmetic",
        "question": "How many orders were completed on the last day of each month in 2024?",
        "reference_sql": "SELECT order_date, COUNT(*) AS order_count FROM orders WHERE order_date = LAST_DAY(TRY_CAST(order_date AS DATE)) AND YEAR(TRY_CAST(order_date AS DATE)) = 2024 GROUP BY order_date;"
    },
    {
        "id": 6,
        "category": "GROUP BY with HAVING",
        "question": "Show product categories having average order value greater than 500",
        "reference_sql": "SELECT category, AVG(net_amount) AS avg_val FROM orders GROUP BY category HAVING AVG(net_amount) > 500;"
    },
    {
        "id": 7,
        "category": "Scalar Subquery",
        "question": "Find all orders where net_amount is greater than the overall average net amount",
        "reference_sql": "SELECT order_id, net_amount FROM orders WHERE net_amount > (SELECT AVG(net_amount) FROM orders);"
    },
    {
        "id": 8,
        "category": "Value-Aware Categorical Filtering",
        "question": "Total sales for Technology products with completed order status",
        "reference_sql": "SELECT SUM(net_amount) AS total_sales FROM orders WHERE category = 'Technology' AND order_status = 'completed';"
    },
    {
        "id": 9,
        "category": "N-th Ordinal Ranking (LIMIT / OFFSET)",
        "question": "What was the 2nd highest distinct net order amount in 2025?",
        "reference_sql": "SELECT DISTINCT net_amount FROM orders WHERE YEAR(TRY_CAST(order_date AS DATE)) = 2025 ORDER BY net_amount DESC LIMIT 1 OFFSET 1;"
    },
    {
        "id": 10,
        "category": "Complex Multi-Condition Metric",
        "question": "Calculate the return percentage for completed vs returned orders in North America",
        "reference_sql": "SELECT ROUND(100.0 * COUNT(CASE WHEN order_status = 'returned' THEN 1 END) / COUNT(*), 2) AS return_pct FROM orders WHERE region = 'North America';"
    }
]

def run_representative_eval():
    print("=" * 80)
    print("📊 RUNNING 10 REPRESENTATIVE TEXT-TO-SQL EVALUATION BENCHMARKS")
    print("=" * 80)

    # Ingest benchmark database
    con = duckdb.connect()
    csv_file = "data/ecommerce_benchmark.csv"
    if os.path.exists(csv_file):
        con.execute(f"CREATE TABLE orders AS SELECT * FROM read_csv_auto('{csv_file}')")
        con.execute("CREATE TABLE customers AS SELECT DISTINCT customer_id, 'Customer_' || customer_id AS customer_name FROM orders")

    wf = Text2SQLWorkflow()
    results = []

    for item in REPRESENTATIVE_TEST_CASES:
        print(f"\n[{item['id']}/10] Category: {item['category']}")
        print(f"Question : \"{item['question']}\"")
        
        state = wf.run(item['question'], connection=con)
        
        exec_ok = state.execution_success
        generated_sql = state.clean_sql or state.generated_sql
        
        # Ground-Truth Execution Accuracy (EX %): Compare query result against reference SQL
        exact_match = False
        try:
            ref_df = con.execute(item['reference_sql']).fetchdf()
            if exec_ok and state.result_df is not None:
                gen_df = state.result_df
                # Normalize column names & shape comparison
                if gen_df.shape == ref_df.shape:
                    if (gen_df.values == ref_df.values).all() or (pd.to_numeric(gen_df.iloc[:, 0], errors='coerce').fillna(0).round(2).equals(pd.to_numeric(ref_df.iloc[:, 0], errors='coerce').fillna(0).round(2))):
                        exact_match = True
        except Exception:
            exact_match = False

        print(f"Engine     : {state.used_engine}")
        print(f"Executed   : {'✅ SUCCESS' if exec_ok else '❌ FAILED'}")
        print(f"EX Match   : {'🎯 MATCH (EX)' if exact_match else '⚠️ MISMATCH / PENDING'}")
        print(f"SQL        : {generated_sql.strip()[:100]}...")
        if not exec_ok:
            print(f"Error      : {state.execution_error}")
            
        results.append({
            "id": item['id'],
            "category": item['category'],
            "success": exec_ok,
            "exact_match": exact_match,
            "engine": state.used_engine,
            "sql": generated_sql
        })

    valid_count = sum(1 for r in results if r["success"])
    ex_count = sum(1 for r in results if r["exact_match"])
    print("\n" + "=" * 80)
    print(f"🏆 EVALUATION SUMMARY:")
    print(f"   • Valid Execution Rate (%): {valid_count}/10 ({valid_count * 10}%)")
    print(f"   • Ground-Truth Accuracy (EX %): {ex_count}/10 ({ex_count * 10}%)")
    print("=" * 80)

if __name__ == "__main__":
    run_representative_eval()
