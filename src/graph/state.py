from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import pandas as pd

@dataclass
class AgentState:
    """
    LangGraph Agent State definition tracking Text-to-SQL context, queries, engine, and execution feedback.
    """
    question: str
    catalog: Dict[str, Any] = field(default_factory=dict)
    pruned_catalog: Dict[str, Any] = field(default_factory=dict)
    join_hints: List[str] = field(default_factory=list)
    semantic_context: str = ""
    
    generated_sql: str = ""
    clean_sql: str = ""
    is_valid: bool = False
    validation_error: str = ""
    
    execution_success: bool = False
    result_df: Optional[pd.DataFrame] = None
    execution_error: str = ""
    
    retry_count: int = 0
    max_retries: int = 2
    
    final_answer: str = ""
    confidence_score: float = 1.0
    used_engine: str = "Gemini 2.5 Flash (LangChain)"
