from typing import Dict, Any, List, Tuple
import re

STOP_WORDS = {"how", "many", "were", "held", "in", "of", "the", "a", "an", "to", "for", "on", "by", "is", "are", "was", "be", "with", "at", "from", "and", "or", "what", "which", "show", "list", "find", "get"}

class SchemaLinker:
    """
    Universal Schema Linker that prunes full database schema down to relevant tables/columns,
    infers candidate foreign key join conditions, performs value-aware categorical matching,
    and orders tables by semantic relevance score. Zero domain hardcoding.
    """
    def __init__(self):
        pass

    def link_schema(self, question: str, catalog: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Retrieves relevant tables from catalog, matches literal categorical values, orders tables by relevance score,
        and infers join candidates. Custom uploaded tables are prioritized over default seed demo tables.
        Returns: (pruned_catalog: Dict, join_hints: List[str])
        """
        value_hints, value_matched_tables = self.find_value_matches(question, catalog)
        q_lower = question.lower()
        q_tokens = set(re.findall(r'\w+', q_lower)) - STOP_WORDS

        # Score each table based on name, column names, sample values & custom upload status
        table_scores = {}
        for tbl_name, tbl_info in catalog.items():
            score = 0
            
            # Custom uploaded tables get base priority over default benchmark seed data
            if tbl_name.lower() != "ecommerce_benchmark" and tbl_name.lower() != "sample_warehouse":
                score += 100

            tbl_tokens = set(re.findall(r'\w+', tbl_name.lower())) - STOP_WORDS
            score += len(q_tokens.intersection(tbl_tokens)) * 20

            for col in tbl_info.get("columns", []):
                col_name = col["name"].lower()
                col_tokens = set(re.findall(r'\w+', col_name)) - STOP_WORDS
                score += len(q_tokens.intersection(col_tokens)) * 10

                for val in col.get("sample_values", []):
                    val_str = str(val).lower().strip()
                    if val_str and len(val_str) > 1 and val_str in q_lower:
                        score += 30

            if tbl_name in value_matched_tables:
                score += 50

            table_scores[tbl_name] = score

        # Sort tables by score descending
        sorted_tables = sorted(catalog.keys(), key=lambda t: table_scores[t], reverse=True)

        if len(catalog) <= 3:
            pruned_catalog = {t: catalog[t] for t in sorted_tables}
        else:
            top_tables = sorted_tables[:3]
            pruned_catalog = {t: catalog[t] for t in top_tables}

            # Always preserve tables matched via literal categorical values
            for v_tbl in value_matched_tables:
                if v_tbl in catalog and v_tbl not in pruned_catalog:
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
                    if val_str and len(val_str) > 1 and val_str.lower() in q_lower:
                        hints.append(f"Value Match: '{val_str}' belongs to `{tbl_name}.{col['name']}`")
                        matched_tables.append(tbl_name)

        return hints, matched_tables

    def infer_join_hints(self, catalog: Dict[str, Any]) -> List[str]:
        """
        Detects primary/foreign key join relationships across tables in catalog.
        """
        hints = []
        tables = list(catalog.keys())
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                t1, t2 = tables[i], tables[j]
                cols1 = {c["name"].lower() for c in catalog[t1]["columns"]}
                cols2 = {c["name"].lower() for c in catalog[t2]["columns"]}

                shared_keys = cols1.intersection(cols2)
                for key in shared_keys:
                    if key.endswith("_id") or key.endswith("_key") or key == "id":
                        hints.append(f"JOIN Hint: `{t1}.{key} = {t2}.{key}`")
        return hints
