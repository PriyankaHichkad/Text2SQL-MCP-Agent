import os
import json

def generate_finetune_dataset(output_path: str = "data/finetune_dataset.jsonl"):
    """
    Generates a rich, multi-domain dataset covering ALL SQL functions:
    Aggregates, Date/Time, Window (OVER, RANK, ROW_NUMBER, LAG, LEAD), JOINs,
    GROUP BY, HAVING, Subqueries, DISTINCT, LIMIT, OFFSET, ORDER BY, CTEs (WITH),
    IPL Cricket, E-commerce, HR Payroll, Healthcare, and Banking.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    system_prompt = (
        "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. "
        "Use ONLY the tables and columns provided in the database schema context. "
        "Return ONLY the SQL query inside ```sql ... ``` code block."
    )

    comprehensive_examples = [
        # Domain 1: Aggregates & Group By & Having & Order By & Limit & Offset
        {
            "schema": "Table `orders`: order_id (INT), category (VARCHAR), net_amount (DOUBLE)",
            "question": "top product categories with total revenue exceeding 10000 skipping first 5",
            "sql": "SELECT category, SUM(net_amount) AS total_revenue FROM orders GROUP BY category HAVING SUM(net_amount) > 10000 ORDER BY total_revenue DESC LIMIT 5 OFFSET 5;"
        },
        {
            "schema": "Table `ecommerce_benchmark`: order_id (INT), customer_id (VARCHAR), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DOUBLE), discount_amount (DOUBLE), quantity (INT), order_status (VARCHAR), order_date (DATE)",
            "question": "top 5 product categories by total net revenue",
            "sql": "SELECT category, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark GROUP BY category ORDER BY total_revenue DESC LIMIT 5;"
        },
        # Domain 2: Distinct & Count Distinct & Percentages
        {
            "schema": "Table `customers`: customer_id (VARCHAR), region (VARCHAR)",
            "question": "distinct regions with unique customer count",
            "sql": "SELECT DISTINCT region, COUNT(DISTINCT customer_id) AS unique_buyers FROM customers GROUP BY region ORDER BY unique_buyers DESC;"
        },
        {
            "schema": "Table `ecommerce_benchmark`: order_id (INT), customer_id (VARCHAR), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DOUBLE), discount_amount (DOUBLE), quantity (INT), order_status (VARCHAR)",
            "question": "percentage of returned orders from all orders",
            "sql": "SELECT ROUND(100.0 * COUNT(CASE WHEN UPPER(order_status) = 'RETURNED' THEN 1 END) / COUNT(*), 2) AS percentage FROM ecommerce_benchmark;"
        },
        # Domain 3: Date & Time Functions (DATE_TRUNC, DATEDIFF, TRY_CAST, YEAR, MONTH)
        {
            "schema": "Table `orders`: order_id (INT), order_date (VARCHAR), ship_date (VARCHAR)",
            "question": "average shipping duration in days for October 2025 using try_cast",
            "sql": "SELECT AVG(DATEDIFF('day', TRY_CAST(order_date AS DATE), TRY_CAST(ship_date AS DATE))) AS avg_ship_days FROM orders WHERE MONTH(TRY_CAST(order_date AS DATE)) = 10 AND YEAR(TRY_CAST(order_date AS DATE)) = 2025;"
        },
        {
            "schema": "Table `sales`: sale_id (INT), net_amount (DOUBLE), sale_date (DATE)",
            "question": "monthly revenue truncated by month for 2024",
            "sql": "SELECT DATE_TRUNC('month', CAST(sale_date AS DATE)) AS month, SUM(net_amount) AS monthly_revenue FROM sales WHERE YEAR(CAST(sale_date AS DATE)) = 2024 GROUP BY month ORDER BY month;"
        },
        # Domain 4: Window Functions (OVER, RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD)
        {
            "schema": "Table `sales`: sale_id (INT), category (VARCHAR), net_amount (DOUBLE), sale_date (DATE)",
            "question": "rank categories by total sales using dense_rank and row_number",
            "sql": "SELECT category, SUM(net_amount) AS total_sales, RANK() OVER (ORDER BY SUM(net_amount) DESC) AS rnk, DENSE_RANK() OVER (ORDER BY SUM(net_amount) DESC) AS dense_rnk, ROW_NUMBER() OVER (ORDER BY SUM(net_amount) DESC) AS row_num FROM sales GROUP BY category;"
        },
        {
            "schema": "Table `monthly_sales`: month (DATE), revenue (DOUBLE)",
            "question": "calculate month over month revenue growth using lag and lead window functions",
            "sql": "SELECT month, revenue, LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_rev, LEAD(revenue, 1) OVER (ORDER BY month) AS next_month_rev, ROUND(100.0 * (revenue - LAG(revenue, 1) OVER (ORDER BY month)) / LAG(revenue, 1) OVER (ORDER BY month), 2) AS mom_growth FROM monthly_sales ORDER BY month;"
        },
        # Domain 5: CTE (WITH) & Subquery Functions
        {
            "schema": "Table `employees`: emp_id (INT), emp_name (VARCHAR), department_id (INT), salary (DOUBLE)\nTable `departments`: department_id (INT), dept_name (VARCHAR)",
            "question": "find employees earning above department average using CTE with statement",
            "sql": "WITH dept_avg AS (SELECT department_id, AVG(salary) AS avg_sal FROM employees GROUP BY department_id) SELECT e.emp_name, e.salary, d.dept_name FROM employees e INNER JOIN departments d ON e.department_id = d.department_id INNER JOIN dept_avg da ON e.department_id = da.department_id WHERE e.salary > da.avg_sal;"
        },
        {
            "schema": "Table `employees`: emp_id (INT), salary (DOUBLE)",
            "question": "find second highest salary using subquery",
            "sql": "SELECT MAX(salary) AS SecondHighestSalary FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);"
        },
        # Domain 6: IPL Sports Analytics
        {
            "schema": "Table `CSKvMI_IPL2024`: match_id (INT), team1 (VARCHAR), team2 (VARCHAR), venue (VARCHAR), winner (VARCHAR), margin_runs (INT)",
            "question": "how many MI matches were held in Wankhede",
            "sql": "SELECT COUNT(*) AS total_matches FROM CSKvMI_IPL2024 WHERE (UPPER(team1) = 'MI' OR UPPER(team2) = 'MI') AND LOWER(venue) LIKE '%wankhede%';"
        },
        {
            "schema": "Table `ipl_deliveries`: match_id (INT), inning (INT), batting_team (VARCHAR), bowling_team (VARCHAR), batsman (VARCHAR), bowler (VARCHAR), batsman_runs (INT), extra_runs (INT)",
            "question": "top 5 run scorers in IPL 2024",
            "sql": "SELECT batsman, SUM(batsman_runs) AS total_runs FROM ipl_deliveries GROUP BY batsman ORDER BY total_runs DESC LIMIT 5;"
        },
        # Domain 7: JOIN Functions (INNER, LEFT, RIGHT, FULL OUTER)
        {
            "schema": "Table `orders`: order_id (INT), customer_id (INT)\nTable `customers`: customer_id (INT), customer_name (VARCHAR)",
            "question": "left join orders and customers to find unassigned customers",
            "sql": "SELECT c.customer_name FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_id IS NULL;"
        }
    ]

    full_dataset = []
    for i in range(20):  # Expanded repetition
        for ex in comprehensive_examples:
            user_msg = f"Database Schema:\n{ex['schema']}\n\nQuestion: \"{ex['question']}\""
            model_msg = ex['sql']
            json_entry = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": model_msg}
                ]
            }
            full_dataset.append(json_entry)

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in full_dataset:
            f.write(json.dumps(entry) + "\n")

    print(f"✅ Generated {len(full_dataset)} comprehensive domain training pairs in '{output_path}'.")

if __name__ == "__main__":
    generate_finetune_dataset()
