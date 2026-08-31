import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import os

from src.graph.workflow import Text2SQLWorkflow
from src.knowledge.catalog import SchemaCatalog

st.set_page_config(
    page_title="Text2SQL-MCP-Agent",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E88E5; }
    .sub-title { font-size: 1.1rem; color: #555555; margin-bottom: 20px; }
    .stCodeBlock { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ Text2SQL-MCP-Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Text-to-SQL Analytics Agent over Data Warehouses & Dynamic CSVs</div>', unsafe_allow_html=True)

# Initialize Session State
if "con" not in st.session_state:
    st.session_state.con = duckdb.connect()
    # Load default seed data if available
    seed_db = "data/sample_warehouse.db"
    if os.path.exists(seed_db):
        try:
            st.session_state.con.execute(f"ATTACH '{seed_db}' AS seed_db (READ_ONLY)")
            # Copy tables locally to in-memory con
            tables_df = st.session_state.con.execute("SHOW TABLES FROM seed_db").fetchdf()
            for tbl in tables_df["name"].tolist():
                st.session_state.con.execute(f"CREATE TABLE \"{tbl}\" AS SELECT * FROM seed_db.\"{tbl}\"")
        except Exception:
            pass

# Sidebar: CSV File Upload & Dataset Selection
with st.sidebar:
    st.header("📂 Data Ingestion")
    
    # Preset Real Dataset Loader
    preset_data = st.selectbox("Sample Datasets", ["Default Star Schema (E-Commerce)", "Upload Custom CSVs"])
    
    # Custom File Uploader
    uploaded_files = st.file_uploader(
        "Upload CSV File(s)", 
        type=["csv"], 
        accept_multiple_files=True,
        help="Upload single or multiple CSVs to query dynamically!"
    )
    
    if uploaded_files:
        for file in uploaded_files:
            tbl_name = os.path.splitext(file.name)[0].replace("-", "_").replace(" ", "_")
            df_upload = pd.read_csv(file)
            st.session_state.con.execute(f"CREATE OR REPLACE TABLE \"{tbl_name}\" AS SELECT * FROM df_upload")
            st.sidebar.success(f"Loaded `{tbl_name}` ({len(df_upload)} rows)")

    st.markdown("---")
    st.header("🔍 Schema Inspector")
    catalog_profiler = SchemaCatalog()
    cat = catalog_profiler.inspect_schema(connection=st.session_state.con)
    
    for tbl_name, tbl_info in cat.items():
        with st.expander(f"Table: `{tbl_name}`"):
            cols_df = pd.DataFrame(tbl_info["columns"])
            st.dataframe(cols_df, use_container_width=True)

# Main Chat & Query Interface
question = st.text_input(
    "💬 Ask a natural language business question:",
    placeholder="e.g., What was total revenue by region last quarter? OR Show top 5 products by quantity sold."
)

if question:
    with st.spinner("🤖 Agent analyzing schema, drafting SQL, and executing safely..."):
        workflow = Text2SQLWorkflow()
        state = workflow.run(question, connection=st.session_state.con)

    st.markdown("### 📊 Agent Results")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Natural Language Answer")
        if state.execution_success:
            st.success(state.final_answer)
        else:
            st.error(state.final_answer)
            
        st.markdown("#### Validated SQL Query")
        st.code(state.clean_sql or state.generated_sql, language="sql")
        
        st.caption(f"Confidence Score: `{state.confidence_score}` | Retries: `{state.retry_count}`")

    with col2:
        st.markdown("#### Tabular Query Results")
        if state.execution_success and state.result_df is not None and not state.result_df.empty:
            df = state.result_df
            st.dataframe(df, use_container_width=True)
            
            # Interactive Chart Auto-Generation
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
            
            if numeric_cols and categorical_cols:
                st.markdown("#### 📈 Visual Insight")
                fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title=f"{numeric_cols[0]} by {categorical_cols[0]}")
                st.plotly_chart(fig, use_container_width=True)
        elif state.execution_success:
            st.info("Query returned 0 rows.")
