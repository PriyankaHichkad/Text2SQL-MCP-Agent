import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLGraphNodes, AgentState

def test_user_question():
    load_dotenv()
    nodes = Text2SQLGraphNodes()
    
    question = "show the highest net order amount in europe in 2014 and 2015"
    state = AgentState(
        question=question,
        catalog={
            "ecommerce_benchmark": {
                "table_name": "ecommerce_benchmark",
                "columns": [
                    {"name": "net_amount", "type": "DOUBLE", "samples": [299.99]},
                    {"name": "region", "type": "VARCHAR", "samples": ["Europe"]},
                    {"name": "order_date", "type": "DATE", "samples": ["2014-06-15"]}
                ]
            }
        }
    )

    state = nodes.generate_sql_node(state)
    print("=" * 60)
    print("🧪 USER QUESTION GENERATION TEST")
    print("=" * 60)
    print(f"Question   : \"{question}\"")
    print(f"Engine Used: {state.used_engine}")
    print(f"\nGenerated SQL:\n{state.generated_sql}")
    print("=" * 60)

if __name__ == "__main__":
    test_user_question()
