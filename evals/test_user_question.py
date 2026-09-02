import os
import sys
import pandas as pd
import duckdb
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow

def test_routing_tiers():
    load_dotenv()
    
    con = duckdb.connect()
    csv_file = "data/ecommerce_benchmark.csv"
    if os.path.exists(csv_file):
        df_raw = pd.read_csv(csv_file)
        con.execute("CREATE TABLE ecommerce_benchmark AS SELECT * FROM df_raw")

    wf = Text2SQLWorkflow()
    
    # Test Tier 1: Easy Query
    q_easy = "total net revenue in 2024"
    state_easy = wf.run(q_easy, connection=con)
    print("=" * 60)
    print(f"EASY QUESTION : \"{q_easy}\"")
    print(f"Engine Used   : {state_easy.used_engine}")
    print(f"Confidence    : {state_easy.confidence_score}")
    print(f"Generated SQL : {state_easy.clean_sql.strip()}")
    print("=" * 60)

    # Test Tier 2: Hard / Analytical Query
    q_hard = "Show the 2nd highest net order amount in North America"
    state_hard = wf.run(q_hard, connection=con)
    print("\nHARD QUESTION : \"{q_hard}\"")
    print(f"Engine Used   : {state_hard.used_engine}")
    print(f"Confidence    : {state_hard.confidence_score}")
    print(f"Generated SQL :\n{state_hard.clean_sql.strip()}")
    print("=" * 60)

if __name__ == "__main__":
    test_routing_tiers()
