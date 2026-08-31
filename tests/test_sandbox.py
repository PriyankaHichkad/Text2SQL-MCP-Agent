import duckdb
import pytest
from src.execution.sandbox import QuerySandbox

def test_query_execution_in_memory():
    sandbox = QuerySandbox()
    con = duckdb.connect()
    con.execute("CREATE TABLE test_tbl (id INT, name VARCHAR);")
    con.execute("INSERT INTO test_tbl VALUES (1, 'Alice'), (2, 'Bob');")
    
    success, df, clean_sql, err = sandbox.execute_query("SELECT * FROM test_tbl;", connection=con)
    assert success is True
    assert len(df) == 2
    assert err == ""
