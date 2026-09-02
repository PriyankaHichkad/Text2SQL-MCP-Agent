# Text2SQL-MCP-Agent ⚡

> **A production-grade, zero-cost Text-to-SQL AI agent and Streamlit copilot powered by LangGraph, LangChain, native MCP server integration, dynamic CSV schema linking, and read-only AST safety guardrails.**

👉 🌐 **Live Web App**: [text2sql-mcp-agent.streamlit.app](https://text2sql-mcp-agent-jxzsy3qnkeqmyfeas6ekkz.streamlit.app)

---

## 🌟 Overview

**Text2SQL-MCP-Agent** bridges the gap between natural language business questions and enterprise data warehouses / dynamic CSV files. Built on state-of-the-art AI system design principles (Spider 2.0 research, RESDSQL, DIN-SQL) and orchestrated via **LangGraph StateGraph** and **LangChain LCEL Runnables**, it converts natural language text into precise, AST-validated read-only SQL queries, executes them safely against DuckDB, and returns tabular insights alongside natural language answers.

### 🔑 Key Features
- **LangGraph & LangChain Engine**: Stateful graph orchestration (`StateGraph`) with nodes for schema linking, SQL drafting, LLM Judge constraint evaluation, AST validation, execution, self-correction, and answer formatting.
- **3-Tier Routing Architecture**: Automatically routes easy deterministic queries to a **sub-millisecond Zero-Shot Engine**, complex analytical queries to your **Hugging Face Fine-Tuned Model (`Priyanka221105/text2sql-qwen2.5-duckdb` / `Qwen/Qwen2.5-Coder-32B-Instruct`)**, and uses **Gemini 3.6 Flash** as an online backup.
- **LLM Judge Constraint Evaluator**: Evaluates generated SQL against the user's natural language question for semantic completeness (catching date boundaries like "last day of month", complex filters, or ranks) and triggers self-correction handoff to the fine-tuned model if constraints are missed.
- **Multi-Dialect SQL Transpilation (MySQL Default)**: Automatically formats and transpiles executed queries into **MySQL Dialect** (with on-the-fly toggling between MySQL, DuckDB, PostgreSQL, and Snowflake via `sqlglot`).
- **Consolidated Clean Codebase**: Streamlined down to 4 self-contained Python modules (`src/agent.py`, `src/engine.py`, `src/sandbox.py`, `src/app.py`) for maximum human readability and zero UI clutter.
- **Dynamic Multi-Table CSV Ingestion**: Drag-and-drop multiple CSV files via Streamlit or MCP; DuckDB automatically registers each file as a separate queryable table.
- **Automated Multi-Table JOIN Discovery**: Automatically detects shared Primary/Foreign Key relationships across tables (e.g. `orders.customer_id <-> customers.customer_id`) and injects candidate join conditions into prompt context.
- **Value-Aware Categorical Linking**: Matches literal text values (e.g. `'Consumer'`, `'Seattle'`) against sample categorical values across database columns.
- **AST Safety Guardrails (`SQLGlot`)**: Statically parses SQL syntax trees to enforce single read-only `SELECT` queries and prevent SQL injection or DDL/DML mutation statements.
- **Native Model Context Protocol (MCP)**: Exposes `@mcp.tool()` and `@mcp.resource()` endpoints so Claude Desktop, Antigravity IDE, Cursor, and AI agents can query the warehouse.
- **Streamlit Web UI (`src/app.py`)**: Interactive web dashboard featuring CSV drag-and-drop, dynamic schema inspector, chat bar, multi-dialect SQL query viewer, active engine badge, and Plotly visual charts.

---

## 🏗️ System Design Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 MCP CLIENT HOST / STREAMLIT APP UI                       │
│        (Claude Desktop / Cursor / Antigravity IDE / Streamlit)           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│               LANGGRAPH & LANGCHAIN 3-TIER ROUTING AGENT                 │
│                                                                          │
│  INTENT CLASSIFIER & ROUTER                                              │
│    ├─ Tier 1: Simple Aggregations & Summary ➔ Zero-Shot Engine (0ms, $0)  │
│    ├─ Tier 2: Complex Joins, CTEs, MoM ➔ Hugging Face Fine-Tuned LLM     │
│    └─ Tier 3: Online LLM Backup ➔ Gemini 3.6 Flash (LangChain)           │
│                                                                          │
│  LANGGRAPH STATEGRAPH NODES                                              │
│    ├─ Node 1: Value-Aware Schema & Semantic Context Linking              │
│    ├─ Node 2: SQL Drafting & Exemplars Injection                         │
│    ├─ Node 3: Read-Only DuckDB Sandbox Execution                         │
│    ├─ Node 4: LLM Judge Constraint Alignment Evaluator                   │
│    ├─ Node 5: Bounded Self-Correction Retry Loop (Max 2 retries)         │
│    └─ Node 6: Multi-Dialect Transpilation (MySQL) & NL Formatting        │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                 DUCKDB READ-ONLY EXECUTION SANDBOX                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Quickstart Guide

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/PriyankaHichkad/Text2SQL-MCP-Agent.git
cd Text2SQL-MCP-Agent
pip install -r requirements.txt
```

### 2. Seed Sample Database
Generate the sample e-commerce star schema (`data/sample_warehouse.db`) and `data/superstore.csv`:
```bash
python scripts/seed_db.py
```

### 3. Launch Streamlit Web App
Run the interactive copilot dashboard:
```bash
streamlit run src/app.py
```

### 4. Launch MCP Server
Run the Model Context Protocol server for Claude Desktop / IDEs:
```bash
python -m src.mcp_server
```

#### Claude Desktop Integration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "text2sql-agent": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/Text2SQL-MCP-Agent"
    }
  }
}
```

---

## 📁 Repository Structure

```
Text2SQL-MCP-Agent/
├── README.md                           # System overview & setup guide
├── pyproject.toml                      # Project metadata & dependencies
├── requirements.txt                    # Pip dependencies
├── config/
│   ├── semantic_layer.yaml             # Business metrics & macro definitions
│   └── warehouse_config.yaml           # Database configuration & security guardrails
├── scripts/
│   └── seed_db.py                      # Data seed script for DuckDB sample database
├── src/
│   ├── __init__.py
│   ├── app.py                          # Streamlit Web Application entrypoint
│   ├── agent.py                        # LangGraph StateGraph, Intent Router & Runnable Nodes
│   ├── engine.py                       # Schema Catalog, Linker, Exemplars & LangChain LLM Router
│   ├── sandbox.py                      # SQLGlot AST Validator & Read-Only DuckDB Sandbox
│   └── mcp_server.py                   # FastMCP server exposing tools & resources
└── tests/
    ├── test_edge_cases.py              # Edge-case evaluation test suite
    ├── test_validator.py               # AST validator unit tests
    └── test_sandbox.py                 # Query sandbox unit tests
```

---

## 🧪 Evals & Verification

Run the automated test suite to verify AST security guardrails, dual-intent routing, and execution sandbox safety:
```bash
pytest
```
*Current benchmark result: **11/11 tests passing in 3.95 seconds (100% success)**.*

---

## 🛠️ Tools & Technologies

- 🐍 [Python 3.10+](https://www.python.org/downloads/) — Core programming language
- 🦜🔗 [LangChain](https://www.langchain.com/) & [LangGraph](https://www.langchain.com/langgraph) — Stateful agent graph orchestration & LCEL Runnables
- 🦆 [DuckDB](https://duckdb.org/) — In-memory analytical database engine
- ⚡ [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — Open protocol for AI tools & context
- 🚀 [FastMCP](https://github.com/jlowin/fastmcp) — High-level Python MCP server framework
- 📊 [Streamlit](https://streamlit.io/) — Interactive web application interface
- 🛡️ [SQLGlot](https://github.com/tobymao/sqlglot) — SQL parser, AST validator & transpiler
- 🤖 [Google Gemini API](https://ai.google.dev/) — LLM reasoning & SQL query generation (Free Tier)


