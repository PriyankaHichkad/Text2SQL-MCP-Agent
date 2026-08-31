import duckdb
from typing import Dict, Any, List

class SchemaCatalog:
    """
    Dynamic schema profiler that inspects table structure, data types,
    and pulls distinct categorical sample values at runtime.
    """
    def __init__(self, db_path: str = "data/sample_warehouse.db"):
        self.db_path = db_path

    def inspect_schema(self, connection: duckdb.DuckDBPyConnection = None) -> Dict[str, Any]:
        """
        Inspects all active tables, column types, and sample categorical values.
        Works with both persistent DuckDB database files and dynamic in-memory CSV connections.
        """
        con = connection
        close_con = False
        if con is None:
            con = duckdb.connect(self.db_path, read_only=True)
            close_con = True

        catalog = {}
        try:
            # Get list of user tables
            tables_df = con.execute("SHOW TABLES").fetchdf()
            table_names = tables_df["name"].tolist() if not tables_df.empty else []

            for tbl in table_names:
                # Column structure via PRAGMA
                info_df = con.execute(f"PRAGMA table_info('{tbl}')").fetchdf()
                columns_info = []

                for _, row in info_df.iterrows():
                    col_name = str(row["name"])
                    col_type = str(row["type"])
                    
                    # Extract sample values for string / categorical columns
                    sample_vals = []
                    if "VARCHAR" in col_type.upper() or "TEXT" in col_type.upper() or "STRING" in col_type.upper():
                        try:
                            sample_df = con.execute(
                                f"SELECT DISTINCT \"{col_name}\" FROM \"{tbl}\" WHERE \"{col_name}\" IS NOT NULL LIMIT 5"
                            ).fetchdf()
                            sample_vals = [str(v) for v in sample_df[col_name].tolist()]
                        except Exception:
                            sample_vals = []

                    columns_info.append({
                        "name": col_name,
                        "type": col_type,
                        "sample_values": sample_vals
                    })

                catalog[tbl] = {
                    "table_name": tbl,
                    "columns": columns_info
                }
        finally:
            if close_con:
                con.close()

        return catalog

    def format_catalog_for_prompt(self, catalog: Dict[str, Any]) -> str:
        """
        Formats catalog dictionary into a clean markdown string for LLM prompt context.
        """
        lines = []
        for tbl_name, tbl_info in catalog.items():
            lines.append(f"Table: `{tbl_name}`")
            for col in tbl_info["columns"]:
                samples_str = ""
                if col["sample_values"]:
                    samples_str = f" | Sample Values: {col['sample_values']}"
                lines.append(f"  - `{col['name']}` ({col['type']}){samples_str}")
            lines.append("")
        return "\n".join(lines)
