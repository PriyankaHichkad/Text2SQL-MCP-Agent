import os
import sys
import pandas as pd
import duckdb
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLGraphNodes, AgentState

def test_user_question():
    load_dotenv()
    nodes = Text2SQLGraphNodes()
    
    # Test 1: 2014
    q_2014 = "Show the highest net order amount in europe in 2014"
    state_2014 = AgentState(
        question=q_2014,
        catalog={
            "ecommerce_benchmark": {
                "table_name": "ecommerce_benchmark",
                "columns": [
                    {"name": "net_amount", "type": "DOUBLE", "samples": [299.99]},
                    {"name": "region", "type": "VARCHAR", "samples": ["Europe"]},
                    {"name": "order_date", "type": "DATE", "samples": ["2024-06-15"]}
                ]
            }
        }
    )
    state_2014 = nodes.generate_sql_node(state_2014)

    print("=" * 60)
    print("🧪 TEST 1: QUESTION FOR 2014")
    print("=" * 60)
    print(f"Question   : \"{q_2014}\"")
    print(f"Generated SQL:\n{state_2014.generated_sql}")

    # Test 2: 2024 against actual dataset
    q_2024 = "Show the highest net order amount in europe in 2024"
    state_2024 = AgentState(
        question=q_2024,
        catalog={
            "ecommerce_benchmark": {
                "table_name": "ecommerce_benchmark",
                "columns": [
                    {"name": "net_amount", "type": "DOUBLE", "samples": [299.99]},
                    {"name": "region", "type": "VARCHAR", "samples": ["Europe"]},
                    {"name": "order_date", "type": "DATE", "samples": ["2024-06-15"]}
                ]
            }
        }
    )
    state_2024 = nodes.generate_sql_node(state_2024)

    print("\n=" * 60)
    print("🧪 TEST 2: QUESTION FOR 2024")
    print("=" * 60)
    print(f"Question   : \"{q_2024}\"")
    print(f"Generated SQL:\n{state_2024.generated_sql}")
    
    csv_file = "data/ecommerce_benchmark.csv"
    if os.path.exists(csv_file):
        con = duckdb.connect()
        df_raw = pd.read_csv(csv_file)
        con.execute("CREATE TABLE ecommerce_benchmark AS SELECT * FROM df_raw")
        res_df = con.execute("SELECT MAX(net_amount) AS highest_net_amount FROM ecommerce_benchmark WHERE UPPER(region) = 'EUROPE' AND YEAR(CAST(order_date AS DATE)) = 2024").fetchdf()
        print(f"\nActual Database Result for 2024:\n{res_df}")

if __name__ == "__main__":
    test_user_question()
