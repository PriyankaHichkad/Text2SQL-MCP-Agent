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

FORBIDDEN_FUNCTIONS = {
    "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_blob",
    "scan_csv", "glob", "read_text", "sniff_csv", "sqlite_scan", "postgres_scan",
    "attach", "install", "load", "system", "system_execute", "copy"
}

class SQLValidator:
    """
    AST Static Validator using SQLGlot to enforce single read-only SELECT queries
    and guard against SQL injection, DDL, DML, multi-statement queries, and unauthorized file reading.
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

        # Check for unauthorized table functions or filesystem reading functions
        for func in parsed_ast.find_all((exp.Func, exp.Anonymous)):
            fn_name = func.name.lower() if func.name else ""
            if fn_name in FORBIDDEN_FUNCTIONS:
                return False, clean_sql, f"Security Guardrail Violation: Unauthorized filesystem or table function '{fn_name}' is forbidden."

        for table in parsed_ast.find_all(exp.Table):
            t_name = table.name.lower() if table.name else ""
            if t_name in FORBIDDEN_FUNCTIONS:
                return False, clean_sql, f"Security Guardrail Violation: Unauthorized filesystem or table function '{t_name}' is forbidden."

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
        Validates and executes SQL query safely with enforced row limit clamping.
        Returns: (success: bool, df_result: pd.DataFrame, clean_sql: str, error_message: str)
        """
        is_valid, clean_sql, val_error = self.validator.validate(sql_query)
        if not is_valid:
            return False, pd.DataFrame(), clean_sql, val_error

        # Strip trailing semicolons
        clean_sql_no_semi = clean_sql.strip()
        while clean_sql_no_semi.endswith(";"):
            clean_sql_no_semi = clean_sql_no_semi[:-1].strip()

        # Parse AST to inspect and clamp LIMIT if user specifies a limit exceeding max_rows
        try:
            parsed_ast = sqlglot.parse_one(clean_sql_no_semi, read=self.validator.dialect)
            limit_ast = parsed_ast.find(exp.Limit)
            if limit_ast and limit_ast.expression:
                try:
                    user_limit = int(limit_ast.expression.this)
                    if user_limit > self.max_rows:
                        limit_ast.set("expression", exp.Literal.number(self.max_rows))
                        clean_sql_no_semi = parsed_ast.sql(dialect=self.validator.dialect)
                except Exception:
                    pass
        except Exception:
            limit_ast = None

        sql_upper = clean_sql_no_semi.upper()
        is_scalar_agg = any(fn in sql_upper for fn in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("]) and "GROUP BY" not in sql_upper

        if not is_scalar_agg and not limit_ast and "LIMIT" not in sql_upper:
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
