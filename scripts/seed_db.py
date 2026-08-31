import os
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data():
    os.makedirs("data", exist_ok=True)
    db_path = os.path.join("data", "sample_warehouse.db")
    
    # Connect to DuckDB
    con = duckdb.connect(db_path)
    
    # 1. Dim Customers
    customers_data = {
        "customer_id": list(range(101, 126)),
        "customer_name": [
            "Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright",
            "Fiona Gallagher", "George Clark", "Hannah Abbott", "Ian Malcolm", "Julia Roberts",
            "Kevin Spacey", "Laura Croft", "Michael Scott", "Nina Williams", "Oscar Martinez",
            "Pam Beesly", "Quentin Tarantino", "Rachel Green", "Steve Rogers", "Tony Stark",
            "Uma Thurman", "Victor Vance", "Wanda Maximoff", "Xavier Charles", "Yolanda Adams"
        ],
        "email": [f"user{i}@example.com" for i in range(101, 126)],
        "segment": np.random.choice(["Consumer", "Corporate", "Small Business"], 25),
        "region": np.random.choice(["North America", "Europe", "Asia Pacific", "Latin America"], 25),
        "country": np.random.choice(["USA", "Canada", "UK", "Germany", "Japan", "Australia"], 25),
        "signup_date": [(datetime(2023, 1, 1) + timedelta(days=int(i*12))).strftime("%Y-%m-%d") for i in range(25)]
    }
    df_customers = pd.DataFrame(customers_data)
    con.execute("CREATE OR REPLACE TABLE dim_customers AS SELECT * FROM df_customers")
    
    # 2. Dim Products
    products_data = {
        "product_id": list(range(501, 516)),
        "product_name": [
            "Pro Laptop 15-inch", "Ergonomic Office Chair", "Wireless Noise-Canceling Headphones",
            "Standing Desk Dual Motor", "Mechanical Keyboard RGB", "4K Ultra HD Monitor 27-inch",
            "USB-C Docking Station", "Smart Ergonomic Mouse", "High-Speed SSD 1TB", "HD Webcam 1080p",
            "Leather Executive Chair", "Aluminum Laptop Stand", "Power Strip Surge Protector",
            "Bluetooth Conference Speaker", "Cat6 Ethernet Cable 50ft"
        ],
        "category": [
            "Electronics", "Furniture", "Electronics", "Furniture", "Electronics", "Electronics",
            "Electronics", "Electronics", "Electronics", "Electronics", "Furniture", "Office Supplies",
            "Office Supplies", "Electronics", "Office Supplies"
        ],
        "subcategory": [
            "Laptops", "Chairs", "Headphones", "Desks", "Keyboards", "Monitors",
            "Accessories", "Mice", "Storage", "Webcams", "Chairs", "Accessories",
            "Accessories", "Speakers", "Cables"
        ],
        "unit_cost": [800.0, 150.0, 120.0, 300.0, 60.0, 220.0, 80.0, 35.0, 70.0, 45.0, 200.0, 25.0, 12.0, 90.0, 8.0],
        "list_price": [1200.0, 250.0, 200.0, 450.0, 100.0, 350.0, 130.0, 60.0, 110.0, 75.0, 320.0, 40.0, 22.0, 140.0, 15.0]
    }
    df_products = pd.DataFrame(products_data)
    con.execute("CREATE OR REPLACE TABLE dim_products AS SELECT * FROM df_products")
    
    # 3. Dim Stores
    stores_data = {
        "store_id": [1, 2, 3, 4],
        "store_name": ["Online Web Store", "Mobile Shopping App", "New York Flagship", "London Retail Branch"],
        "channel": ["Online Website", "Mobile App", "Retail Store", "Retail Store"],
        "city": ["Seattle", "San Francisco", "New York", "London"],
        "region": ["North America", "North America", "North America", "Europe"]
    }
    df_stores = pd.DataFrame(stores_data)
    con.execute("CREATE OR REPLACE TABLE dim_stores AS SELECT * FROM df_stores")
    
    # 4. Fact Sales (150 Transactions)
    np.random.seed(42)
    num_sales = 150
    start_date = datetime(2024, 1, 1)
    
    sales_data = {
        "sale_id": list(range(1001, 1001 + num_sales)),
        "customer_id": np.random.choice(customers_data["customer_id"], num_sales),
        "product_id": np.random.choice(products_data["product_id"], num_sales),
        "store_id": np.random.choice(stores_data["store_id"], num_sales),
        "order_date": [(start_date + timedelta(days=int(i * 3.5))).strftime("%Y-%m-%d") for i in range(num_sales)],
        "quantity": np.random.randint(1, 6, num_sales),
        "order_status": np.random.choice(["completed", "shipped", "returned", "pending", "cancelled"], num_sales, p=[0.7, 0.15, 0.05, 0.05, 0.05])
    }
    
    df_sales = pd.DataFrame(sales_data)
    # Join unit_price from products
    df_sales = df_sales.merge(df_products[["product_id", "list_price"]], on="product_id")
    df_sales.rename(columns={"list_price": "unit_price"}, inplace=True)
    df_sales["discount_amount"] = np.round(df_sales["unit_price"] * df_sales["quantity"] * np.random.choice([0.0, 0.05, 0.10, 0.15], num_sales), 2)
    df_sales["net_amount"] = np.round((df_sales["quantity"] * df_sales["unit_price"]) - df_sales["discount_amount"], 2)
    
    con.execute("CREATE OR REPLACE TABLE fact_sales AS SELECT * FROM df_sales")
    
    # Export sample CSV for standalone testing
    df_sales.to_csv("data/superstore.csv", index=False)
    
    con.close()
    print("Database data/sample_warehouse.db and data/superstore.csv seeded successfully!")

if __name__ == "__main__":
    generate_sample_data()
