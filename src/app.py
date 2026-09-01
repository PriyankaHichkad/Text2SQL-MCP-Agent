import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add root directory to sys.path for Streamlit Cloud & local module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import re
import sqlglot

from src.graph.workflow import Text2SQLWorkflow
from src.knowledge.catalog import SchemaCatalog

st.set_page_config(
    page_title="Text2SQL-MCP-Agent",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS styling for full-width code blocks & pre-wrap wrapping
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E88E5; }
    .sub-title { font-size: 1.1rem; color: #555555; margin-bottom: 20px; }
    .stCodeBlock { border-radius: 8px; width: 100% !important; }
    .stCodeBlock code { white-space: pre-wrap !important; word-break: break-word !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚡ Text2SQL-MCP-Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Text-to-SQL Analytics Agent over Data Warehouses & Dynamic CSVs</div>', unsafe_allow_html=True)

# Helper function to format SQL into broad multi-line formatted string
def format_pretty_sql(sql_str: str) -> str:
    if not sql_str:
        return ""
    try:
        return sqlglot.transpile(sql_str, read="duckdb", write="duckdb", pretty=True)[0]
    except Exception:
        res = sql_str
        for kw in ["FROM", "LEFT JOIN", "INNER JOIN", "JOIN", "WHERE", "GROUP BY", "ORDER BY", "LIMIT"]:
            res = re.sub(rf'\b({kw})\b', r'\n\1', res, flags=re.IGNORECASE)
        return res.strip()

# Helper function to detect ID columns
def is_id_column(col_name: str) -> bool:
    c = col_name.lower().strip()
    return bool(re.search(r'(_id|_key|^id$|code|number)$', c))

# Initialize Session State
if "con" not in st.session_state:
    st.session_state.con = duckdb.connect()
    # Load default benchmark / seed data if available
    benchmark_csv = "data/ecommerce_benchmark.csv"
    if os.path.exists(benchmark_csv):
        try:
            st.session_state.con.execute(f"CREATE TABLE ecommerce_benchmark AS SELECT * FROM read_csv_auto('{benchmark_csv}')")
        except Exception:
            pass

# Sidebar: CSV File Upload & Dataset Selection
with st.sidebar:
    st.header("📂 Data Ingestion")
    
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
    placeholder="e.g., Show top 5 product categories by net revenue OR What is net amount that europe got from furniture?"
)

if question:
    with st.spinner("🤖 Agent analyzing schema, value-aware linking, drafting SQL, and executing safely..."):
        workflow = Text2SQLWorkflow()
        state = workflow.run(question, connection=st.session_state.con)

    st.markdown("### 📊 Agent Results")
    
    # 1. Natural Language Answer (Full Width)
    if state.execution_success:
        st.success(state.final_answer)
    else:
        st.error(state.final_answer)

    # 2. Broad Full-Width Validated SQL Query Block
    st.markdown("#### 📜 Validated SQL Query")
    raw_sql = state.clean_sql or state.generated_sql
    formatted_sql = format_pretty_sql(raw_sql)
    st.code(formatted_sql, language="sql")
    st.caption(f"Confidence Score: `{state.confidence_score}` | Retries: `{state.retry_count}`")

    st.markdown("---")

    # 3. Two-Column Layout for Exports and Data Results
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📥 One-Click Exports")
        exp_c1, exp_c2, exp_c3 = st.columns(3)
        
        # SQL Query Export (.sql file)
        exp_c1.download_button(
            label="📄 Export Query (.sql)",
            data=formatted_sql,
            file_name="executed_query.sql",
            mime="text/plain",
            help="Exports the clean, formatted SQL query as an .sql file"
        )

        # Tabular Data Export (.csv file)
        if state.execution_success and state.result_df is not None and not state.result_df.empty:
            exp_c2.download_button(
                label="📊 Export Data (.csv)",
                data=state.result_df.to_csv(index=False),
                file_name="query_results.csv",
                mime="text/csv",
                help="Exports the executed result table as a .csv file"
            )

            # MCP JSON Payload Export (.json file)
            mcp_payload = {
                "question": question,
                "answer": state.final_answer,
                "sql_query": formatted_sql,
                "execution_success": state.execution_success,
                "confidence_score": state.confidence_score,
                "rows_returned": len(state.result_df),
                "data": state.result_df.to_dict(orient="records")
            }
            exp_c3.download_button(
                label="📋 Export MCP (.json)",
                data=json.dumps(mcp_payload, indent=2, default=str),
                file_name="mcp_response.json",
                mime="application/json",
                help="Exports full MCP standard payload as a .json file"
            )

    with col2:
        st.markdown("#### 📋 Tabular Query Results")
        if state.execution_success and state.result_df is not None and not state.result_df.empty:
            df = state.result_df
            st.dataframe(df, use_container_width=True)
            
            # Smart Chart Auto-Generation (Filtering out ID columns for Y-axis metrics)
            all_numerics = df.select_dtypes(include=['number']).columns.tolist()
            metric_cols = [c for c in all_numerics if not is_id_column(c)]
            categorical_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
            
            if metric_cols and categorical_cols:
                st.markdown("#### 📈 Smart Visual Insight")
                y_col = metric_cols[0]
                x_col = categorical_cols[0]
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", color=x_col)
                st.plotly_chart(fig, use_container_width=True)
            elif len(metric_cols) >= 2:
                st.markdown("#### 📈 Smart Visual Insight")
                fig = px.scatter(df, x=metric_cols[0], y=metric_cols[1], title=f"{metric_cols[1]} vs {metric_cols[0]}")
                st.plotly_chart(fig, use_container_width=True)
        elif state.execution_success:
            st.info("Query returned 0 rows.")
