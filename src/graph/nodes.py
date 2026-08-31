from src.graph.state import AgentState
from src.knowledge.schema_linker import SchemaLinker
from src.knowledge.semantic_layer import SemanticLayer
from src.execution.validator import SQLValidator
from src.execution.sandbox import QuerySandbox
from src.models.router import LLMRouter
import duckdb

class Text2SQLGraphNodes:
    def __init__(self, db_path: str = "data/sample_warehouse.db", llm_router: LLMRouter = None):
        self.db_path = db_path
        self.linker = SchemaLinker()
        self.semantic_layer = SemanticLayer()
        self.validator = SQLValidator(dialect="duckdb")
        self.sandbox = QuerySandbox(db_path=db_path)
        self.llm = llm_router or LLMRouter()

    def link_schema_node(self, state: AgentState) -> AgentState:
        """Node 1: Link schema & inject semantic metrics"""
        state.pruned_catalog, state.join_hints = self.linker.link_schema(state.question, state.catalog)
        state.semantic_context = self.semantic_layer.get_semantic_context(state.question)
        return state

    def generate_sql_node(self, state: AgentState) -> AgentState:
        """Node 2: Draft SQL query using LLM"""
        catalog_str = ""
        for tbl_name, tbl_info in state.pruned_catalog.items():
            catalog_str += f"Table `{tbl_name}`:\n"
            for col in tbl_info["columns"]:
                samples = f" (Samples: {col['sample_values']})" if col["sample_values"] else ""
                catalog_str += f"  - {col['name']} ({col['type']}){samples}\n"

        join_hints_str = ""
        if state.join_hints:
            join_hints_str = "Candidate Join Relationships:\n" + "\n".join([f"- {h}" for h in state.join_hints]) + "\n\n"

        prompt = f"""You are an expert SQL Data Analyst writing DuckDB SQL queries.
Given the natural language business question, write a SINGLE, read-only SELECT SQL query.

{catalog_str}
{join_hints_str}{state.semantic_context}
Question: "{state.question}"

Rules:
1. Return ONLY the raw SQL query inside ```sql ... ``` code block.
2. Use valid DuckDB SQL syntax.
3. Do NOT include any DDL/DML statements (NO DROP, DELETE, UPDATE, INSERT, ALTER).
4. ALWAYS use explicit JOIN conditions with ON clauses.
"""
        state.generated_sql = self.llm.generate(prompt)
        return state

    def validate_and_execute_node(self, state: AgentState, connection: duckdb.DuckDBPyConnection = None) -> AgentState:
        """Node 3: Validate AST and execute in read-only sandbox"""
        is_valid, clean_sql, val_err = self.validator.validate(state.generated_sql)
        state.is_valid = is_valid
        state.clean_sql = clean_sql
        state.validation_error = val_err

        if not is_valid:
            state.execution_success = False
            state.execution_error = val_err
            return state

        # Execute in sandbox
        success, df_result, _, exec_err = self.sandbox.execute_query(clean_sql, connection=connection)
        state.execution_success = success
        state.result_df = df_result
        state.execution_error = exec_err

        return state

    def self_correct_node(self, state: AgentState) -> AgentState:
        """Node 4: Bounded self-correction loop when query fails"""
        state.retry_count += 1
        
        err_msg = state.validation_error or state.execution_error
        prompt = f"""Your previous SQL query failed to run. Please fix the error and rewrite a valid DuckDB SELECT query.

Original Question: "{state.question}"
Previous Generated Query:
{state.generated_sql}

Error Message:
{err_msg}

Return ONLY the repaired raw SQL query inside ```sql ... ``` code block.
"""
        state.generated_sql = self.llm.generate(prompt)
        return state

    def format_answer_node(self, state: AgentState) -> AgentState:
        """Node 5: Synthesize final answer and tabular results"""
        if not state.execution_success:
            state.final_answer = f"⚠️ I am unable to answer this question with confidence. Error: {state.execution_error or state.validation_error}"
            state.confidence_score = 0.0
            return state

        df = state.result_df
        if df is None or df.empty:
            state.final_answer = "The query executed successfully, but returned 0 matching records."
            state.confidence_score = 0.9
            return state

        # Create quick natural language summary
        row_count = len(df)
        cols_str = ", ".join(df.columns.tolist())
        first_row_str = str(df.iloc[0].to_dict())

        state.final_answer = f"Retrieved {row_count} rows. Key columns: `{cols_str}`. Top result: {first_row_str}."
        state.confidence_score = 1.0
        return state
