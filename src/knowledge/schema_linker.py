from typing import Dict, Any, List, Tuple
from rank_bm25 import BM25Okapi
import re

class SchemaLinker:
    """
    Hybrid Schema Linker that prunes full database schema down to relevant tables/columns,
    infers candidate foreign key join conditions, and performs value-aware categorical matching.
    """
    def __init__(self):
        pass

    def link_schema(self, question: str, catalog: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Retrieves relevant tables from catalog, matches literal categorical values, and infers join candidates.
        Returns: (pruned_catalog: Dict, join_hints: List[str])
        """
        value_hints, value_matched_tables = self.find_value_matches(question, catalog)

        if len(catalog) <= 3:
            pruned_catalog = catalog
        else:
            table_names = list(catalog.keys())
            corpus = []
            for tbl, info in catalog.items():
                col_str = " ".join([c["name"] for c in info["columns"]])
                corpus.append(f"{tbl} {col_str}".lower().split())

            tokenized_query = re.findall(r'\w+', question.lower())
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(tokenized_query)

            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
            pruned_catalog = {table_names[i]: catalog[table_names[i]] for i in top_indices}

            # Always preserve tables matched via literal categorical values
            for v_tbl in value_matched_tables:
                if v_tbl in catalog:
                    pruned_catalog[v_tbl] = catalog[v_tbl]

        join_hints = self.infer_join_hints(pruned_catalog) + value_hints
        return pruned_catalog, join_hints

    def find_value_matches(self, question: str, catalog: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Value-Aware Indexer: Compares words in question against categorical sample values across all tables.
        Returns: (value_hints: List[str], matched_tables: List[str])
        """
        hints = []
        matched_tables = []
        q_lower = question.lower()

        for tbl_name, tbl_info in catalog.items():
            for col in tbl_info.get("columns", []):
                for val in col.get("sample_values", []):
                    val_str = str(val).strip()
                    if val_str and len(val_str) > 2 and val_str.lower() in q_lower:
                        hints.append(f"Value Match: '{val_str}' belongs to `{tbl_name}.{col['name']}`")
                        matched_tables.append(tbl_name)

        return list(set(hints)), list(set(matched_tables))

    def infer_join_hints(self, catalog: Dict[str, Any]) -> List[str]:
        """
        Scans tables for matching column names or ID patterns (e.g. customer_id across tables).
        """
        hints = []
        table_cols = {}
        for tbl_name, tbl_info in catalog.items():
            table_cols[tbl_name] = [c["name"] for c in tbl_info["columns"]]

        tables = list(table_cols.keys())
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                t1, t2 = tables[i], tables[j]
                common_cols = set(table_cols[t1]).intersection(set(table_cols[t2]))
                for col in common_cols:
                    if col.endswith("_id") or col.endswith("_key") or col == "id":
                        hints.append(f"`{t1}.{col}` <-> `{t2}.{col}`")
        return hints
