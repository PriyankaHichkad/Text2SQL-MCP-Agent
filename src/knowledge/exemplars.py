from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

DEFAULT_EXEMPLARS = [
    {
        "question": "What is total revenue for completed orders in 2025?",
        "sql": "SELECT SUM(net_amount) AS total_revenue FROM ecommerce_benchmark WHERE order_status = 'completed' AND YEAR(CAST(order_date AS DATE)) = 2025;"
    },
    {
        "question": "Show top 5 product categories by revenue in Europe",
        "sql": "SELECT category, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark WHERE LOWER(region) = 'europe' GROUP BY category ORDER BY total_revenue DESC LIMIT 5;"
    },
    {
        "question": "Show monthly net revenue for 2024",
        "sql": "SELECT DATE_TRUNC('month', CAST(order_date AS DATE)) AS month, SUM(net_amount) AS monthly_revenue FROM ecommerce_benchmark GROUP BY month ORDER BY month;"
    },
    {
        "question": "List total quantity sold by subcategory for Electronics",
        "sql": "SELECT subcategory, SUM(quantity) AS total_quantity FROM ecommerce_benchmark WHERE category = 'Electronics' GROUP BY subcategory ORDER BY total_quantity DESC;"
    },
    {
        "question": "Which 3 product subcategories have the highest return rate or returned orders?",
        "sql": "SELECT subcategory, COUNT(*) AS returned_orders FROM ecommerce_benchmark WHERE order_status = 'returned' GROUP BY subcategory ORDER BY returned_orders DESC LIMIT 3;"
    }
]

class ExemplarRetriever:
    """
    Dynamic Few-Shot Exemplar Retriever based on HKUST NL2SQL Handbook & Spider 2.0 research.
    Retrieves the top N worked question-to-SQL exemplars matching the input question's intent.
    """
    def __init__(self, exemplars: List[Dict[str, str]] = None):
        self.exemplars = exemplars or DEFAULT_EXEMPLARS
        corpus = [e["question"].lower().split() for e in self.exemplars]
        self.bm25 = BM25Okapi(corpus)

    def retrieve_exemplars(self, question: str, top_k: int = 2) -> str:
        """
        Retrieves top K formatted exemplars for prompt context.
        """
        tokenized_q = re.findall(r'\w+', question.lower())
        scores = self.bm25.get_scores(tokenized_q)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        lines = ["### Worked SQL Exemplars (Few-Shot Prompting):"]
        for idx in top_indices:
            if scores[idx] > 0.1:
                ex = self.exemplars[idx]
                lines.append(f"Question: \"{ex['question']}\"")
                lines.append(f"SQL: {ex['sql']}\n")

        return "\n".join(lines) if len(lines) > 1 else ""
