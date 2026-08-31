from src.graph.state import AgentState
from src.graph.nodes import Text2SQLGraphNodes
from src.knowledge.catalog import SchemaCatalog
import duckdb

class Text2SQLWorkflow:
    """
    State machine workflow coordinator for the Text-to-SQL execution pipeline.
    """
    def __init__(self, db_path: str = "data/sample_warehouse.db"):
        self.db_path = db_path
        self.nodes = Text2SQLGraphNodes(db_path=db_path)
        self.catalog_profiler = SchemaCatalog(db_path=db_path)

    def run(self, question: str, connection: duckdb.DuckDBPyConnection = None) -> AgentState:
        """
        Executes full agent pipeline:
        Catalog -> Link Schema -> Generate -> Validate & Execute -> Self-Correct (if needed) -> Format Answer
        """
        # Step 0: Inspect Catalog
        catalog = self.catalog_profiler.inspect_schema(connection=connection)

        # Initialize State
        state = AgentState(question=question, catalog=catalog)

        # Step 1: Link Schema & Semantic Layer
        state = self.nodes.link_schema_node(state)

        # Step 2: Generate Initial SQL
        state = self.nodes.generate_sql_node(state)

        # Step 3: Validate & Execute
        state = self.nodes.validate_and_execute_node(state, connection=connection)

        # Step 4: Bounded Self-Correction Loop (Max 2 retries)
        while not state.execution_success and state.retry_count < state.max_retries:
            state = self.nodes.self_correct_node(state)
            state = self.nodes.validate_and_execute_node(state, connection=connection)

        # Step 5: Format Final Answer
        state = self.nodes.format_answer_node(state)

        return state
