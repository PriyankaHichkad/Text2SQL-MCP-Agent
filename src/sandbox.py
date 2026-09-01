import duckdb
import pandas as pd
import sqlglot
from sqlglot import exp
from typing import Tuple, Dict, Any, List

FORBIDDEN_EXPRESSIONS = (
    exp.Drop,
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.Create,
    exp.Alter,
    exp.Command,
)

class SQLValidator:
    """
    AST Static Validator using SQLGlot to enforce single read-only SELECT queries
    and guard against SQL injection, DDL, DML, and multi-statement queries.
    """
    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def validate(self, sql_query: str) -> Tuple[bool, str, str]:
        """
        Validates SQL string.
        Returns: (is_valid: bool, cleaned_sql: str, error_message: str)
        """
        if not sql_query or not sql_query.strip():
            return False, "", "Empty SQL query string provided."
        
        # Clean markdown code blocks if present
        clean_sql = sql_query.strip()
        if clean_sql.startswith("```sql"):
            clean_sql = clean_sql[6:]
        elif clean_sql.startswith("```"):
            clean_sql = clean_sql[3:]
        if clean_sql.endswith("```"):
            clean_sql = clean_sql[:-3]
        clean_sql = clean_sql.strip()

        # Remove trailing semicolons
        while clean_sql.endswith(";"):
            clean_sql = clean_sql[:-1].strip()

        try:
            parsed_expressions = sqlglot.parse(clean_sql, read=self.dialect)
        except Exception as e:
            return False, clean_sql, f"SQL Syntax Error: Unable to parse query. Details: {str(e)}"

        if not parsed_expressions:
            return False, clean_sql, "No valid SQL expressions found in query."

        if len(parsed_expressions) > 1:
            return False, clean_sql, "Security Guardrail Violation: Multiple SQL statements in a single query are strictly forbidden."

        parsed_ast = parsed_expressions[0]

        if not isinstance(parsed_ast, exp.Select):
            return False, clean_sql, f"Security Guardrail Violation: Only SELECT queries are permitted. Detected statement type: {type(parsed_ast).__name__}."

        for forbidden_cls in FORBIDDEN_EXPRESSIONS:
            if parsed_ast.find(forbidden_cls):
                return False, clean_sql, f"Security Guardrail Violation: Forbidden operation '{forbidden_cls.__name__}' detected."

        return True, parsed_ast.sql(dialect=self.dialect, pretty=True), ""


class QuerySandbox:
    """
    Executes AST-validated read-only SELECT queries against DuckDB in a safe sandbox environment.
    """
    def __init__(self, db_path: str = "data/sample_warehouse.db", max_rows: int = 1000):
        self.db_path = db_path
        self.max_rows = max_rows
        self.validator = SQLValidator(dialect="duckdb")

    def execute_query(self, sql_query: str, connection: duckdb.DuckDBPyConnection = None) -> Tuple[bool, pd.DataFrame, str, str]:
        """
        Validates and executes SQL query safely.
        Returns: (success: bool, df_result: pd.DataFrame, clean_sql: str, error_message: str)
        """
        is_valid, clean_sql, val_error = self.validator.validate(sql_query)
        if not is_valid:
            return False, pd.DataFrame(), clean_sql, val_error

        # Strip trailing semicolons
        clean_sql_no_semi = clean_sql.strip()
        while clean_sql_no_semi.endswith(";"):
            clean_sql_no_semi = clean_sql_no_semi[:-1].strip()

        # Check if scalar aggregate without GROUP BY
        sql_upper = clean_sql_no_semi.upper()
        is_scalar_agg = any(fn in sql_upper for fn in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("]) and "GROUP BY" not in sql_upper

        if not is_scalar_agg and "LIMIT" not in sql_upper:
            sql_to_run = f"{clean_sql_no_semi} LIMIT {self.max_rows}"
        else:
            sql_to_run = clean_sql_no_semi

        try:
            if connection is not None:
                df = connection.execute(sql_to_run).fetchdf()
            else:
                with duckdb.connect(self.db_path, read_only=True) as con:
                    df = con.execute(sql_to_run).fetchdf()
            
            return True, df, clean_sql_no_semi, ""
        except Exception as e:
            return False, pd.DataFrame(), clean_sql_no_semi, f"Database Execution Error: {str(e)}"

    def execute(self, sql_query: str, connection: duckdb.DuckDBPyConnection = None) -> Tuple[bool, pd.DataFrame, str]:
        """Alias for compatibility"""
        success, df, clean_sql, err = self.execute_query(sql_query, connection=connection)
        return success, df, err


# Alias for backward compatibility
SQLExecutionSandbox = QuerySandbox
