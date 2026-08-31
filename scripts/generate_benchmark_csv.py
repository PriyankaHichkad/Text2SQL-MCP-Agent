import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_benchmark_csv():
    os.makedirs("data", exist_ok=True)
    out_file = os.path.join("data", "ecommerce_benchmark.csv")
    
    np.random.seed(42)
    n = 5000
    
    start_date = datetime(2024, 1, 1)
    
    segments = ["Consumer", "Corporate", "Home Office", "Small Business"]
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    categories = ["Electronics", "Furniture", "Office Supplies", "Apparel"]
    
    subcategories = {
        "Electronics": ["Laptops", "Smartphones", "Headphones", "Monitors", "Keyboards"],
        "Furniture": ["Chairs", "Desks", "Bookcases", "Tables"],
        "Office Supplies": ["Paper", "Binders", "Storage", "Fasteners", "Supplies"],
        "Apparel": ["Jackets", "Shirts", "Footwear", "Accessories"]
    }
    
    statuses = ["completed", "shipped", "returned", "pending", "cancelled"]
    
    data = []
    for i in range(1, n + 1):
        cat = np.random.choice(categories)
        subcat = np.random.choice(subcategories[cat])
        qty = int(np.random.randint(1, 10))
        unit_p = round(float(np.random.uniform(15.0, 1200.0)), 2)
        disc = round(float(qty * unit_p * np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20])), 2)
        net = round((qty * unit_p) - disc, 2)
        
        ord_date = (start_date + timedelta(days=int(np.random.randint(0, 600)))).strftime("%Y-%m-%d")
        
        data.append({
            "order_id": f"ORD-{10000 + i}",
            "order_date": ord_date,
            "customer_id": f"CUST-{np.random.randint(100, 500)}",
            "customer_name": f"Customer_{np.random.randint(100, 500)}",
            "segment": np.random.choice(segments, p=[0.5, 0.25, 0.15, 0.10]),
            "region": np.random.choice(regions, p=[0.4, 0.3, 0.2, 0.1]),
            "category": cat,
            "subcategory": subcat,
            "product_id": f"PROD-{np.random.randint(500, 800)}",
            "product_name": f"{subcat} Model-{np.random.randint(1, 50)}",
            "quantity": qty,
            "unit_price": unit_p,
            "discount_amount": disc,
            "net_amount": net,
            "order_status": np.random.choice(statuses, p=[0.75, 0.12, 0.05, 0.05, 0.03])
        })
        
    df = pd.DataFrame(data)
    df.to_csv(out_file, index=False)
    
    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"Generated {out_file} ({len(df)} rows, {size_mb:.2f} MB)")

if __name__ == "__main__":
    create_benchmark_csv()
