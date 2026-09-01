import duckdb
from src.graph.state import AgentState
from src.graph.intent import classify_intent
from src.knowledge.schema_linker import SchemaLinker
from src.knowledge.exemplars import ExemplarRetriever
from src.models.router import LLMRouter
from src.execution.validator import SQLValidator
from src.execution.sandbox import QuerySandbox

class Text2SQLGraphNodes:
    """
    Graph Execution Nodes for LangGraph Text-to-SQL Workflow Pipeline.
    """
    def __init__(self, db_path: str = "data/sample_warehouse.db", llm_router: LLMRouter = None):
        self.db_path = db_path
        self.linker = SchemaLinker()
        self.exemplar_retriever = ExemplarRetriever()
        self.llm = llm_router or LLMRouter()
        self.validator = SQLValidator()
        self.sandbox = QuerySandbox(db_path=db_path)

    def link_schema_node(self, state: AgentState) -> AgentState:
        """Node 1: Value-Aware Schema & Semantic Context Linking"""
        pruned_cat, join_hints = self.linker.link_schema(state.question, state.catalog)
        state.pruned_catalog = pruned_cat
        state.join_hints = join_hints
        
        semantic_ctx = self.linker.inject_semantic_context(state.question)
        state.semantic_context = f"\n\nSemantic Rules:\n{semantic_ctx}" if semantic_ctx else ""
        return state

    def generate_sql_node(self, state: AgentState) -> AgentState:
        """Node 2: Smart Intent-Based Dual Router: Zero-Shot Compiler vs LLM Engine"""
        intent = classify_intent(state.question, state.pruned_catalog or state.catalog)

        # Build prompt format for fallback generator or LLM
        catalog_str = "Database Schema & Sample Values:\n"
        for tbl_name, tbl_info in (state.pruned_catalog or state.catalog).items():
            catalog_str += f"Table `{tbl_name}`:\n"
            for col in tbl_info["columns"]:
                c_name = col.get("name") or col.get("column_name", "column")
                c_type = col.get("type") or col.get("data_type", "VARCHAR")
                c_samples = col.get("samples") or col.get("sample_values", [])
                samples_str = f" (Samples: {c_samples})" if c_samples else ""
                catalog_str += f"  - {c_name} ({c_type}){samples_str}\n"

        prompt_str = f"{catalog_str}\nQuestion: \"{state.question}\""

        if intent == "SIMPLE_DETERMINISTIC":
            state.generated_sql = self.llm._dynamic_fallback_generator(prompt_str)
            state.used_engine = "Zero-Shot Deterministic Engine (Sub-Millisecond)"
            return state

        # Complex Analytical Intent -> LLM Engine
        join_hints_str = ""
        if state.join_hints:
            join_hints_str = "Candidate Join Relationships:\n" + "\n".join([f"- {h}" for h in state.join_hints]) + "\n\n"

        exemplars_str = self.exemplar_retriever.retrieve_exemplars(state.question, top_k=2)

        prompt = f"""You are an expert SQL Data Analyst writing DuckDB SQL queries.
Given the natural language business question, write a SINGLE, read-only SELECT SQL query.

{catalog_str}
{join_hints_str}{state.semantic_context}
{exemplars_str}

Question: "{state.question}"

Rules:
1. Return ONLY the raw SQL query inside ```sql ... ``` code block.
2. Use valid DuckDB SQL syntax.
3. Do NOT include any DDL/DML statements (NO DROP, DELETE, UPDATE, INSERT, ALTER).
4. ALWAYS use explicit JOIN conditions with ON clauses.
"""
        state.generated_sql = self.llm.generate(prompt)
        state.used_engine = getattr(self.llm, "active_engine", "Gemini 3.6 Flash (LangChain)")
        return state

    def validate_and_execute_node(self, state: AgentState, connection: duckdb.DuckDBPyConnection = None) -> AgentState:
        """Node 3: Validate AST and execute in read-only sandbox"""
        success, df_res, clean_sql, exec_err = self.sandbox.execute_query(state.generated_sql, connection=connection)
        state.is_valid = success or (exec_err == "")
        state.clean_sql = clean_sql
        state.execution_success = success
        state.result_df = df_res
        state.execution_error = exec_err
        return state

    def self_correct_node(self, state: AgentState) -> AgentState:
        """Node 4: Execution-Guided AST Self-Correction Node"""
        state.retry_count += 1
        
        err_msg = state.validation_error if not state.is_valid else state.execution_error
        
        correction_prompt = f"""The SQL query you previously generated produced an error.
Original Question: "{state.question}"

Failed SQL Query:
{state.generated_sql}

Error Feedback:
{err_msg}

Please fix the error and return ONLY the corrected, valid DuckDB SQL query inside a ```sql ... ``` code block.
"""
        state.generated_sql = self.llm.generate(correction_prompt)
        return state

    def format_answer_node(self, state: AgentState) -> AgentState:
        """Node 5: Natural Language Answer Formatting Node"""
        if not state.execution_success:
            state.final_answer = f"⚠️ Query Execution Failure (Retries: {state.retry_count}):\n{state.execution_error}"
            state.confidence_score = 0.0
            return state

        df = state.result_df
        if df is None or df.empty:
            state.final_answer = "ℹ️ Query executed successfully, but returned 0 rows matching your criteria."
            state.confidence_score = 0.9
            return state

        row_count = len(df)
        cols = list(df.columns)
        
        # Concise answer summary
        if row_count == 1 and len(cols) == 1:
            val = df.iloc[0, 0]
            if isinstance(val, (int, float)):
                formatted_val = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
            else:
                formatted_val = str(val)
            state.final_answer = f"**{cols[0]}**: `{formatted_val}`"
        else:
            state.final_answer = f"Returned **{row_count}** result rows across columns `{', '.join(cols)}`."

        state.confidence_score = max(0.6, 1.0 - (state.retry_count * 0.15))
        return state
