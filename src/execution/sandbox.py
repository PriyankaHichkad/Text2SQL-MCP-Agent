import duckdb
import pandas as pd
from typing import Dict, Any, Tuple
from src.execution.validator import SQLValidator

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

        # Ensure LIMIT clause exists to prevent overwhelming memory
        clean_sql_no_semi = clean_sql.rstrip(";").strip()
        if "LIMIT" not in clean_sql_no_semi.upper():
            sql_to_run = f"{clean_sql_no_semi} LIMIT {self.max_rows}"
        else:
            sql_to_run = clean_sql_no_semi

        try:
            if connection is not None:
                # Use provided in-memory / uploaded DuckDB connection
                df = connection.execute(sql_to_run).fetchdf()
            else:
                # Open read-only connection to db_path
                with duckdb.connect(self.db_path, read_only=True) as con:
                    df = con.execute(sql_to_run).fetchdf()
            
            return True, df, clean_sql, ""
        except Exception as e:
            return False, pd.DataFrame(), clean_sql, f"Database Execution Error: {str(e)}"
