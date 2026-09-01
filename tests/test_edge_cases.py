import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graph.workflow import Text2SQLWorkflow
import duckdb

@pytest.fixture
def db_conn():
    con = duckdb.connect()
    benchmark_csv = "data/ecommerce_benchmark.csv"
    if os.path.exists(benchmark_csv):
        con.execute(f"CREATE TABLE ecommerce_benchmark AS SELECT * FROM read_csv_auto('{benchmark_csv}')")
    return con

def test_edge_case_percentage(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("percentage of electronics sold from all the orders", connection=db_conn)
    assert res.execution_success
    assert "%" in res.final_answer or "percentage" in res.clean_sql.lower()

def test_edge_case_product_quantity(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("how many shirts were bought in europe", connection=db_conn)
    assert res.execution_success
    assert "SUM(quantity)" in res.clean_sql or "total_quantity" in res.clean_sql

def test_edge_case_revenue_2025(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("net amount that europe got from furniture in 2025", connection=db_conn)
    assert res.execution_success
    assert "SUM(net_amount)" in res.clean_sql or "total_net_amount" in res.clean_sql
    assert "2025" in res.clean_sql

def test_edge_case_top_categories(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("top 5 product categories by total net revenue", connection=db_conn)
    assert res.execution_success
    assert "GROUP BY category" in res.clean_sql
    assert "LIMIT 5" in res.clean_sql

def test_edge_case_discount_north_america(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("total discount amount given in North America", connection=db_conn)
    assert res.execution_success
    assert "SUM(discount_amount)" in res.clean_sql

def test_edge_case_october_revenue(db_conn):
    wf = Text2SQLWorkflow()
    res = wf.run("total amout of revenue in october", connection=db_conn)
    assert res.execution_success
    assert "SUM(net_amount)" in res.clean_sql or "total_net_amount" in res.clean_sql
    assert "10" in res.clean_sql or "october" in res.clean_sql.lower()
