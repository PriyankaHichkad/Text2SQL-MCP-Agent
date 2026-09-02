import os
import sys
import pandas as pd
import duckdb
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow

def test_last_day_question():
    load_dotenv()
    
    con = duckdb.connect()
    csv_file = "data/ecommerce_benchmark.csv"
    if os.path.exists(csv_file):
        df_raw = pd.read_csv(csv_file)
        con.execute("CREATE TABLE ecommerce_benchmark AS SELECT * FROM df_raw")

    wf = Text2SQLWorkflow()
    
    question = "how many furniture were sold on the last day of the july month"
    print("=" * 60)
    print("🧪 TESTING LLM JUDGE EVALUATION & LAST DAY OF MONTH QUERY")
    print("=" * 60)
    print(f"Question        : \"{question}\"")
    
    state = wf.run(question, connection=con)
    
    print(f"Engine Used     : {state.used_engine}")
    print(f"Confidence Score: {state.confidence_score}")
    print(f"Retries         : {state.retry_count}")
    print(f"Final Answer    : {state.final_answer}")
    print(f"\nGenerated SQL:\n{state.clean_sql}")
    print("=" * 60)

if __name__ == "__main__":
    test_last_day_question()
