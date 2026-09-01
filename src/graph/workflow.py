from langgraph.graph import StateGraph, START, END
from src.graph.state import AgentState
from src.graph.nodes import Text2SQLGraphNodes
from src.knowledge.catalog import SchemaCatalog
import duckdb

class Text2SQLWorkflow:
    """
    LangGraph-powered stateful Text-to-SQL workflow engine.
    Orchestrates schema linking, SQL drafting, AST validation, sandbox execution,
    and self-correction loops.
    """
    def __init__(self, db_path: str = "data/sample_warehouse.db"):
        self.db_path = db_path
        self.nodes = Text2SQLGraphNodes(db_path=db_path)
        self.catalog_profiler = SchemaCatalog(db_path=db_path)
        self.app = self._build_graph()

    def _build_graph(self):
        """Constructs and compiles the LangGraph StateGraph pipeline."""
        graph = StateGraph(AgentState)

        # Graph Nodes
        graph.add_node("link_schema", self.nodes.link_schema_node)
        graph.add_node("generate_sql", self.nodes.generate_sql_node)
        graph.add_node("validate_and_execute", self.nodes.validate_and_execute_node)
        graph.add_node("self_correct", self.nodes.self_correct_node)
        graph.add_node("format_answer", self.nodes.format_answer_node)

        # Pipeline Edges
        graph.add_edge(START, "link_schema")
        graph.add_edge("link_schema", "generate_sql")
        graph.add_edge("generate_sql", "validate_and_execute")

        # Self-Correction Conditional Routing Edge
        graph.add_conditional_edges(
            "validate_and_execute",
            self._should_retry,
            {
                "self_correct": "self_correct",
                "format_answer": "format_answer"
            }
        )
        graph.add_edge("self_correct", "validate_and_execute")
        graph.add_edge("format_answer", END)

        return graph.compile()

    def _should_retry(self, state: AgentState) -> str:
        """Determines whether to attempt execution-guided self-correction."""
        if not state.execution_success and state.retry_count < state.max_retries:
            return "self_correct"
        return "format_answer"

    def run(self, question: str, connection: duckdb.DuckDBPyConnection = None) -> AgentState:
        """Executes the full Text-to-SQL workflow pipeline."""
        catalog = self.catalog_profiler.inspect_schema(connection=connection)
        state = AgentState(question=question, catalog=catalog)

        # Execute step sequence
        state = self.nodes.link_schema_node(state)
        state = self.nodes.generate_sql_node(state)
        state = self.nodes.validate_and_execute_node(state, connection=connection)

        while not state.execution_success and state.retry_count < state.max_retries:
            state = self.nodes.self_correct_node(state)
            state = self.nodes.validate_and_execute_node(state, connection=connection)

        state = self.nodes.format_answer_node(state)
        return state
