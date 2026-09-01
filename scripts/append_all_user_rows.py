import os
import json

def append_raw_jsonl_from_user():
    dataset_path = "data/finetune_dataset.jsonl"
    
    # We will read all user JSON lines directly
    raw_lines = [
        '{"messages": [{"role": "system", "content": "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Use ONLY the tables and columns provided in the database schema context. Return ONLY the SQL query inside ```sql ... ``` code block."}, {"role": "user", "content": "Database Schema:\\nTable `orders`: order_id (INT), customer_id (INT), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DECIMAL), discount_amount (DECIMAL), quantity (INT), order_status (VARCHAR), payment_method (VARCHAR), order_date (DATE), ship_date (DATE)\\n\\nQuestion: \\"What is the total net revenue from completed orders?\\""}, {"role": "assistant", "content": "```sql\\nSELECT SUM(net_amount) AS total_revenue FROM orders WHERE order_status = \'completed\';\\n```"}]}',
        '{"messages": [{"role": "system", "content": "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Use ONLY the tables and columns provided in the database schema context. Return ONLY the SQL query inside ```sql ... ``` code block."}, {"role": "user", "content": "Database Schema:\\nTable `orders`: order_id (INT), customer_id (INT), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DECIMAL), discount_amount (DECIMAL), quantity (INT), order_status (VARCHAR), payment_method (VARCHAR), order_date (DATE), ship_date (DATE)\\n\\nQuestion: \\"Show the top 5 categories by total revenue.\\""}, {"role": "assistant", "content": "```sql\\nSELECT category, SUM(net_amount) AS total_revenue FROM orders GROUP BY category ORDER BY total_revenue DESC LIMIT 5;\\n```"}]}',
        '{"messages": [{"role": "system", "content": "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Use ONLY the tables and columns provided in the database schema context. Return ONLY the SQL query inside ```sql ... ``` code block."}, {"role": "user", "content": "Database Schema:\\nTable `orders`: order_id (INT), customer_id (INT), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DECIMAL), discount_amount (DECIMAL), quantity (INT), order_status (VARCHAR), payment_method (VARCHAR), order_date (DATE), ship_date (DATE)\\n\\nQuestion: \\"What percentage of orders were returned?\\""}, {"role": "assistant", "content": "```sql\\nSELECT ROUND(100.0 * SUM(CASE WHEN order_status = \'returned\' THEN 1 ELSE 0 END) / COUNT(*), 2) AS return_pct FROM orders;\\n```"}]}',
        '{"messages": [{"role": "system", "content": "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Use ONLY the tables and columns provided in the database schema context. Return ONLY the SQL query inside ```sql ... ``` code block."}, {"role": "user", "content": "Database Schema:\\nTable `orders`: order_id (INT), customer_id (INT), region (VARCHAR), category (VARCHAR), subcategory (VARCHAR), net_amount (DECIMAL), discount_amount (DECIMAL), quantity (INT), order_status (VARCHAR), payment_method (VARCHAR), order_date (DATE), ship_date (DATE)\\n\\nQuestion: \\"List distinct payment methods used.\\""}, {"role": "assistant", "content": "```sql\\nSELECT DISTINCT payment_method FROM orders;\\n```"}]}'
    ]
    
    with open(dataset_path, "a", encoding="utf-8") as f:
        for line in raw_lines:
            f.write(line + "\n")
            
    print(f"✅ Appended user rows to '{dataset_path}'.")

if __name__ == "__main__":
    append_raw_jsonl_from_user()
