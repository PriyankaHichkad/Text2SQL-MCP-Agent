import sys
import os
import pytest
import duckdb
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import Text2SQLWorkflow, AgentState
from src.engine import LLMRouter

@pytest.fixture
def db_conn():
    con = duckdb.connect()
    con.execute("CREATE TABLE ecommerce_benchmark (category VARCHAR, region VARCHAR, net_amount DOUBLE, quantity INT, order_date VARCHAR);")
    con.execute("INSERT INTO ecommerce_benchmark VALUES ('Furniture', 'Europe', 500.0, 10, '2025-07-31'), ('Technology', 'North America', 1200.0, 5, '2025-08-01');")
    return con

def test_hermetic_heuristic_engine_execution(db_conn):
    """
    Hermetic Test: Verifies Tier-1 Heuristic Engine execution without network calls.
    """
    wf = Text2SQLWorkflow()
    # Simple query routes to heuristic engine (no LLM call)
    res = wf.run("total net_amount in Europe", connection=db_conn)
    assert res.execution_success is True
    assert "EUROPE" in res.clean_sql.upper()
    assert res.used_engine == "Zero-Shot Deterministic Engine (Sub-Millisecond)"

@patch.object(LLMRouter, "generate")
def test_hermetic_llm_complex_workflow(mock_generate, db_conn):
    """
    Hermetic Test: Mocks external LLM calls to verify complex workflow orchestration,
    AST validation, execution, and answer formatting offline in <0.1s.
    """
    mock_generate.return_value = "```sql\nSELECT category, SUM(net_amount) AS total_revenue FROM ecommerce_benchmark GROUP BY category ORDER BY total_revenue DESC;\n```"
    
    wf = Text2SQLWorkflow()
    # Query with 'cte' intent pattern routes to LLM
    res = wf.run("use a cte to calculate category total revenue", connection=db_conn)
    
    assert mock_generate.called
    assert res.execution_success is True
    assert "total_revenue" in res.clean_sql
    assert res.retry_count == 0

@patch.object(LLMRouter, "generate")
def test_hermetic_self_correction_loop(mock_generate, db_conn):
    """
    Hermetic Test: Mocks a failed initial SQL draft followed by a corrected draft to verify
    the state machine's self-correction loop offline.
    """
    # 1st call returns invalid column, 2nd call returns valid SQL
    mock_generate.side_effect = [
        "```sql\nSELECT non_existent_column FROM ecommerce_benchmark;\n```",
        "```sql\nSELECT category FROM ecommerce_benchmark;\n```"
    ]
    
    wf = Text2SQLWorkflow()
    res = wf.run("use a cte to fetch category", connection=db_conn)
    
    assert mock_generate.call_count == 2
    assert res.execution_success is True
    assert res.retry_count == 1

@patch.object(LLMRouter, "generate")
def test_hermetic_retry_exhaustion(mock_generate, db_conn):
    """
    Hermetic Test: Verifies that after reaching max_retries (2 retries),
    the workflow cleanly terminates with execution_success=False and zero confidence.
    """
    mock_generate.return_value = "```sql\nSELECT broken_syntax_col FROM non_existent_tbl;\n```"
    
    wf = Text2SQLWorkflow()
    res = wf.run("use a cte to trigger max retries", connection=db_conn)
    
    assert res.execution_success is False
    assert res.retry_count == 2
    assert res.confidence_score == 0.0
    assert "Query Execution Failure" in res.final_answer

def test_hermetic_max_rows_truncation_enforcement(db_conn):
    """
    Hermetic Test: Verifies that QuerySandbox automatically applies max_rows safety
    limits on unbounded SELECT queries.
    """
    from src.sandbox import QuerySandbox
    sandbox = QuerySandbox(max_rows=1)
    
    # Query without LIMIT gets truncated by sandbox execution to max_rows
    success, df, clean_sql, err = sandbox.execute_query(
        "SELECT * FROM ecommerce_benchmark", connection=db_conn
    )
    assert success is True
    assert len(df) == 1
    assert err == ""

def test_hermetic_ast_rejects_forbidden_ddl():
    """
    Hermetic Test: Verifies that SQLValidator AST blocks forbidden DDL/DML expressions.
    """
    from src.sandbox import SQLValidator
    validator = SQLValidator(dialect="duckdb")
    
    malicious_queries = [
        "ALTER TABLE ecommerce_benchmark ADD COLUMN hacked INT;",
        "CREATE TABLE backdoor (id INT);",
        "INSERT INTO ecommerce_benchmark VALUES ('Fake', 'Nowhere', 0, 0, '2025-01-01');"
    ]
    for q in malicious_queries:
        is_valid, _, err = validator.validate(q)
        assert is_valid is False
        assert "Security Guardrail Violation" in err

