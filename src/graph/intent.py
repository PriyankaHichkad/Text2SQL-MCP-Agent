import re
from typing import Dict, Any

def classify_intent(question: str, catalog: Dict[str, Any]) -> str:
    """
    Classifies natural language business question intent into:
    - 'SIMPLE_DETERMINISTIC': Sub-millisecond execution via Zero-Shot Schema Engine (Aggregations, Group-By, Top-N, Percentages, Date Truncation)
    - 'COMPLEX_ANALYTICAL': LLM Engine (Multi-table joins, CTEs, Window functions, Subqueries)
    """
    q_lower = question.lower().strip()

    # Complex Keywords requiring LLM (CTEs, Window Functions, Subqueries, Joins)
    COMPLEX_PATTERNS = [
        r'\b(cte|with\s+cte|with\s+\w+\s+as)\b',
        r'\b(percentile|percentile_cont|within\s+group)\b',
        r'\b(lag|lead|over\s*\(|partition\s+by)\b',
        r'\b(second|2nd|third|3rd)\s+(highest|lowest|top|best)\b',
        r'\b(subquery|nested\s+query)\b',
        r'\b(left\s+join|right\s+join|inner\s+join|full\s+join|join)\b',
        r'\b(without\s+\w+|no\s+\w+\s+assigned|unassigned)\b',
        r'\b(more\s+than\s+their|higher\s+than\s+their|compared\s+to\s+their)\b'
    ]

    for pattern in COMPLEX_PATTERNS:
        if re.search(pattern, q_lower):
            return "COMPLEX_ANALYTICAL"

    # Multi-Table Detection
    num_tables = len(catalog.keys()) if catalog else 0
    if num_tables > 1:
        mentioned_tables = 0
        for tbl_name in catalog.keys():
            if tbl_name.lower() in q_lower:
                mentioned_tables += 1
        if mentioned_tables >= 2:
            return "COMPLEX_ANALYTICAL"

    return "SIMPLE_DETERMINISTIC"
