import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.execution.validator import SQLValidator

def test_valid_select_query():
    validator = SQLValidator(dialect="duckdb")
    sql = "SELECT region, SUM(net_amount) AS rev FROM fact_sales GROUP BY region;"
    is_valid, clean_sql, err = validator.validate(sql)
    assert is_valid is True
    assert err == ""
    assert "fact_sales" in clean_sql

def test_block_drop_table():
    validator = SQLValidator(dialect="duckdb")
    sql = "DROP TABLE fact_sales;"
    is_valid, _, err = validator.validate(sql)
    assert is_valid is False
    assert "Security Guardrail Violation" in err

def test_block_multiple_statements():
    validator = SQLValidator(dialect="duckdb")
    sql = "SELECT * FROM fact_sales; DELETE FROM fact_sales;"
    is_valid, _, err = validator.validate(sql)
    assert is_valid is False
    assert "Multiple SQL statements" in err or "Security Guardrail Violation" in err
