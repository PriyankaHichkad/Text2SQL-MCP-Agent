import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import classify_intent
from src.engine import LLMRouter, SchemaCatalog

def test_multidate():
    load_dotenv()
    question = "how many furnitures were sold in Europe in July 2014 and September 2015"
    
    catalog = {
        "ecommerce_benchmark": {
            "table_name": "ecommerce_benchmark",
            "columns": [
                {"name": "category", "type": "VARCHAR", "samples": ["Furniture"]},
                {"name": "region", "type": "VARCHAR", "samples": ["Europe"]},
                {"name": "quantity", "type": "INT", "samples": [10]},
                {"name": "order_date", "type": "DATE", "samples": ["2014-07-01"]}
            ]
        }
    }

    intent = classify_intent(question, catalog)
    print("=" * 60)
    print("🧪 MULTI-DATE QUERY INTENT & SQL TEST")
    print("=" * 60)
    print(f"Question      : \"{question}\"")
    print(f"Detected Intent: {intent}")

    router = LLMRouter()
    prompt = (
        "Database Schema:\n"
        "Table `ecommerce_benchmark`:\n"
        "- category (VARCHAR) (Samples: ['Furniture'])\n"
        "- region (VARCHAR) (Samples: ['Europe'])\n"
        "- quantity (INT)\n"
        "- order_date (DATE)\n\n"
        f"Question: \"{question}\""
    )
    
    sql = router._dynamic_fallback_generator(prompt)
    print(f"\nZero-Shot Generated SQL:\n{sql}")
    print("=" * 60)

if __name__ == "__main__":
    test_multidate()
