import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine import LLMRouter

def test_generic_nth():
    load_dotenv()
    router = LLMRouter()
    
    catalog_str = (
        "Table `ecommerce_benchmark`:\n"
        "  - net_amount (DOUBLE)\n"
        "  - region (VARCHAR) (Samples: ['North America'])\n"
    )
    
    for q in [
        "Show the second highest net order amount in North America",
        "Show the 2nd highest net order amount in North America",
        "Show the 4th highest net order amount in North America",
        "Show the 10th highest net order amount in North America"
    ]:
        prompt = f"{catalog_str}\nQuestion: \"{q}\""
        sql = router._dynamic_fallback_generator(prompt)
        print("=" * 60)
        print(f"Question: \"{q}\"")
        print(f"Fallback SQL:\n{sql}")

if __name__ == "__main__":
    test_generic_nth()
