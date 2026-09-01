from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

DEFAULT_EXEMPLARS = [
    # 1. Aggregate & Simple Filtering Exemplars
    {
        "question": "What is total revenue for completed orders in 2025?",
        "sql": "SELECT SUM(net_amount) AS total_revenue FROM ecommerce_benchmark WHERE order_status = 'completed' AND YEAR(CAST(order_date AS DATE)) = 2025;"
    },
    {
        "question": "How many total unique customers placed an order in North America?",
        "sql": "SELECT COUNT(DISTINCT customer_id) AS unique_customers FROM ecommerce_benchmark WHERE LOWER(region) = 'north america';"
    },
    {
        "question": "What is the average order value for Consumer segment?",
        "sql": "SELECT AVG(net_amount) AS avg_order_value FROM ecommerce_benchmark WHERE segment = 'Consumer';"
    },
    
    # 2. Date & Time Functions Exemplars
    {
        "question": "Show monthly net revenue for 2024",
        "sql": "SELECT DATE_TRUNC('month', CAST(order_date AS DATE)) AS month, SUM(net_amount) AS monthly_revenue FROM ecommerce_benchmark WHERE YEAR(CAST(order_date AS DATE)) = 2024 GROUP BY month ORDER BY month;"
    },
    {
        "question": "Total amount of revenue in October 2025",
        "sql": "SELECT SUM(net_amount) AS total_net_amount FROM ecommerce_benchmark WHERE (MONTH(TRY_CAST(order_date AS DATE)) = 10 OR CAST(order_date AS VARCHAR) LIKE '%-10-%') AND YEAR(CAST(order_date AS DATE)) = 2025;"
    },
    {
        "question": "Find average shipping duration in days by region",
        "sql": "SELECT region, AVG(DATEDIFF('day', CAST(order_date AS DATE), CAST(ship_date AS DATE))) AS avg_ship_days FROM ecommerce_benchmark GROUP BY region;"
    },

    # 3. Window & Analytic Functions (Rank, Row Number, Lag, Running Total) Exemplars
    {
        "question": "Rank product categories by total net revenue",
        "sql": "SELECT category, SUM(net_amount) AS total_revenue, RANK() OVER (ORDER BY SUM(net_amount) DESC) AS category_rank FROM ecommerce_benchmark GROUP BY category;"
    },
    {
        "question": "Find the latest order placed by each customer",
        "sql": "WITH ranked_orders AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rn FROM ecommerce_benchmark) SELECT * FROM ranked_orders WHERE rn = 1;"
    },
    {
        "question": "Calculate cumulative running total revenue by month for 2025",
        "sql": "WITH monthly_rev AS (SELECT DATE_TRUNC('month', CAST(order_date AS DATE)) AS month, SUM(net_amount) AS rev FROM ecommerce_benchmark WHERE YEAR(CAST(order_date AS DATE)) = 2025 GROUP BY month) SELECT month, rev, SUM(rev) OVER (ORDER BY month) AS running_total FROM monthly_rev ORDER BY month;"
    },
    {
        "question": "Calculate month-over-month revenue growth using lag",
        "sql": "WITH monthly_rev AS (SELECT DATE_TRUNC('month', CAST(order_date AS DATE)) AS month, SUM(net_amount) AS rev FROM ecommerce_benchmark GROUP BY month) SELECT month, rev, LAG(rev, 1) OVER (ORDER BY month) AS prev_month_rev, ROUND(100.0 * (rev - LAG(rev, 1) OVER (ORDER BY month)) / LAG(rev, 1) OVER (ORDER BY month), 2) AS mom_growth_pct FROM monthly_rev ORDER BY month;"
    },

    # 4. Multi-Table JOIN Exemplars
    {
        "question": "Join orders and customers to find total net revenue by customer segment",
        "sql": "SELECT c.segment, SUM(o.net_amount) AS total_revenue FROM orders o INNER JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.segment ORDER BY total_revenue DESC;"
    },
    {
        "question": "Find customers who placed orders for products in Electronics",
        "sql": "SELECT DISTINCT c.customer_name, c.email FROM customers c INNER JOIN orders o ON c.customer_id = o.customer_id INNER JOIN products p ON o.product_id = p.product_id WHERE p.category = 'Electronics';"
    },

    # 5. Group By & HAVING Exemplars
    {
        "question": "Which subcategories generated more than $50,000 in net revenue?",
        "sql": "SELECT subcategory, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark GROUP BY subcategory HAVING SUM(net_amount) > 50000 ORDER BY total_revenue DESC;"
    },
    {
        "question": "Find customer segments with at least 100 total orders",
        "sql": "SELECT segment, COUNT(order_id) AS order_count FROM ecommerce_benchmark GROUP BY segment HAVING COUNT(order_id) >= 100 ORDER BY order_count DESC;"
    },

    # 6. CTE (Common Table Expressions) & Subquery Exemplars
    {
        "question": "Find product categories with revenue higher than the average category revenue",
        "sql": "WITH category_rev AS (SELECT category, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark GROUP BY category) SELECT category, total_revenue FROM category_rev WHERE total_revenue > (SELECT AVG(total_revenue) FROM category_rev) ORDER BY total_revenue DESC;"
    },

    # 7. Percentage & Conditional Ratio Exemplars
    {
        "question": "What percentage of total orders were returned in Europe?",
        "sql": "SELECT ROUND(100.0 * COUNT(CASE WHEN order_status = 'returned' THEN 1 END) / COUNT(*), 2) AS returned_percentage FROM ecommerce_benchmark WHERE LOWER(region) = 'europe';"
    },

    # 8. Distinct, Ordering, Limit & Offset Exemplars
    {
        "question": "Show top 5 product categories by revenue",
        "sql": "SELECT category, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark GROUP BY category ORDER BY total_revenue DESC LIMIT 5;"
    },
    {
        "question": "List unique product categories and subcategories",
        "sql": "SELECT DISTINCT category, subcategory FROM ecommerce_benchmark ORDER BY category, subcategory;"
    }
]

class ExemplarRetriever:
    """
    Dynamic Few-Shot Exemplar Retriever based on HKUST NL2SQL Handbook & Spider 2.0 research.
    Retrieves the top N worked question-to-SQL exemplars matching the input question's intent.
    Covers Aggregations, Dates, Window Functions, Joins, Group By/Having, CTEs, Ratios, and Limits.
    """
    def __init__(self, exemplars: List[Dict[str, str]] = None):
        self.exemplars = exemplars or DEFAULT_EXEMPLARS
        corpus = [e["question"].lower().split() for e in self.exemplars]
        self.bm25 = BM25Okapi(corpus)

    def retrieve_exemplars(self, question: str, top_k: int = 3) -> str:
        """
        Retrieves top K formatted exemplars for prompt context.
        """
        tokenized_q = re.findall(r'\w+', question.lower())
        scores = self.bm25.get_scores(tokenized_q)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        lines = ["### Worked SQL Exemplars (Few-Shot Prompting):"]
        for idx in top_indices:
            if scores[idx] > 0.05:
                ex = self.exemplars[idx]
                lines.append(f"Question: \"{ex['question']}\"")
                lines.append(f"SQL: {ex['sql']}\n")

        return "\n".join(lines) if len(lines) > 1 else ""
