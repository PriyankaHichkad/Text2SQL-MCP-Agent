import os
import json
import duckdb
from fastmcp import FastMCP
from src.graph.workflow import Text2SQLWorkflow
from src.knowledge.catalog import SchemaCatalog
from src.execution.validator import SQLValidator

# Initialize FastMCP Server
mcp = FastMCP("Text2SQL-MCP-Agent")

db_path = os.getenv("WAREHOUSE_DB_PATH", "data/sample_warehouse.db")
workflow = Text2SQLWorkflow(db_path=db_path)
catalog_profiler = SchemaCatalog(db_path=db_path)
validator = SQLValidator(dialect="duckdb")

@mcp.tool()
def query_analytics_db(question: str) -> str:
    """
    Executes natural language question against data warehouse.
    Returns JSON containing answer, SQL query, row count, tabular data, and execution metadata.
    """
    state = workflow.run(question)
    
    result = {
        "question": question,
        "answer": state.final_answer,
        "sql_query": state.clean_sql,
        "execution_success": state.execution_success,
        "confidence_score": state.confidence_score,
        "row_count": len(state.result_df) if state.result_df is not None else 0,
        "tabular_data": state.result_df.to_dict(orient="records") if state.result_df is not None else [],
        "error": state.execution_error or state.validation_error
    }
    return json.dumps(result, indent=2, default=str)

@mcp.tool()
def get_schema_catalog() -> str:
    """
    Returns active database schema catalog, tables, columns, data types, and sample categorical values.
    """
    cat = catalog_profiler.inspect_schema()
    return json.dumps(cat, indent=2)

@mcp.tool()
def load_csv_dataset(file_path: str, table_name: str) -> str:
    """
    Dynamically loads an external CSV file into DuckDB as a queryable table.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' does not exist."
    try:
        with duckdb.connect(db_path) as con:
            con.execute(f"CREATE OR REPLACE TABLE \"{table_name}\" AS SELECT * FROM read_csv_auto('{file_path}')")
        return f"Success: Loaded CSV '{file_path}' into table '{table_name}'."
    except Exception as e:
        return f"Error loading CSV: {str(e)}"

@mcp.tool()
def validate_sql_query(sql_query: str) -> str:
    """
    Statically validates SQL query AST for syntax correctness and single read-only SELECT safety.
    """
    is_valid, clean_sql, err = validator.validate(sql_query)
    res = {
        "is_valid": is_valid,
        "clean_sql": clean_sql,
        "error": err
    }
    return json.dumps(res, indent=2)

@mcp.resource("warehouse://schema/catalog")
def schema_resource() -> str:
    """Exposes database catalog as an MCP resource"""
    return json.dumps(catalog_profiler.inspect_schema(), indent=2)

if __name__ == "__main__":
    mcp.run()
