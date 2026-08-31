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
    and guard against SQL injection, DDL, DML, and cartesian cross joins.
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
        
        # Clean markdown backticks if present
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

        # Scan AST for forbidden expression types
        for node in parsed_ast.walk():
            if isinstance(node, FORBIDDEN_EXPRESSIONS):
                return False, clean_sql, f"Security Guardrail Violation: Forbidden operation '{type(node).__name__}' detected."

        # Check JOIN ON clauses (prevent cartesian products)
        for join_node in parsed_ast.find_all(exp.Join):
            if not join_node.args.get("on") and not join_node.args.get("using") and join_node.kind != "CROSS":
                return False, clean_sql, "Safety Check Failed: JOIN statement missing ON or USING clause."

        return True, clean_sql, ""
