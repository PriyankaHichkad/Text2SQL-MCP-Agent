from typing import Dict, Any, List, Tuple
from rank_bm25 import BM25Okapi
import re

class SchemaLinker:
    """
    Hybrid Schema Linker that prunes full database schema down to relevant tables/columns
    and infers candidate foreign key join conditions across tables.
    """
    def __init__(self):
        pass

    def link_schema(self, question: str, catalog: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Retrieves relevant tables from catalog and infers join candidates.
        Returns: (pruned_catalog: Dict, join_hints: List[str])
        """
        if len(catalog) <= 3:
            # Small schema: pass all tables
            pruned_catalog = catalog
        else:
            # BM25 Sparse Keyword Ranking
            table_names = list(catalog.keys())
            corpus = []
            for tbl, info in catalog.items():
                col_str = " ".join([c["name"] for c in info["columns"]])
                corpus.append(f"{tbl} {col_str}".lower().split())

            tokenized_query = re.findall(r'\w+', question.lower())
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(tokenized_query)

            # Select top 3 scoring tables
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
            pruned_catalog = {table_names[i]: catalog[table_names[i]] for i in top_indices}

        # Infer Foreign Key Join Candidates across pruned tables
        join_hints = self.infer_join_hints(pruned_catalog)
        return pruned_catalog, join_hints

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
