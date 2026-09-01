# Text2SQL-MCP-Agent ⚡

> **A production-grade, zero-cost Text-to-SQL AI agent and Streamlit copilot with native MCP server integration, dynamic CSV schema linking, and read-only AST safety guardrails.**

---

## 🌟 Overview

**Text2SQL-MCP-Agent** bridges the gap between natural language business questions and enterprise data warehouses / CSV files. Built on state-of-the-art AI system design principles (Spider 2.0 research, RESDSQL, DIN-SQL), it converts natural language text into precise, AST-validated read-only SQL queries, executes them safely against DuckDB, and returns tabular insights alongside natural language answers.

### 🔑 Key Features
- **100% Free & Open-Source Stack**: Operates with zero paid API costs using Google Gemini Free Tier, local Ollama, DuckDB, and CPU SentenceTransformers.
- **Dynamic Multi-Table CSV Ingestion**: Drag-and-drop multiple CSV files via Streamlit or MCP; DuckDB automatically registers each file as a separate queryable table.
- **Automated Multi-Table JOIN Discovery**: Automatically detects shared Primary/Foreign Key relationships across tables (e.g. `orders.customer_id <-> customers.customer_id`, `orders.product_id <-> products.product_id`) and injects candidate join conditions into LLM prompt context.
- **Value-Aware Categorical Linking**: Matches literal text values (e.g. `'Consumer'`, `'Seattle'`) against sample categorical values across database columns.
- **Smart AI Chart Recommendation**: Automatically filters out non-trackable ID columns (`_id`, `_key`, `code`) from Y-axis metric aggregations.
- **One-Click Query & Data Exports**: Export clean `.sql` query files, `.csv` result tables, and standard `.json` MCP payloads directly from the Streamlit UI.
- **Automated Benchmark & Evals Suite (`evals/evaluate.py`)**: Includes a bundled <1MB benchmark dataset (`data/ecommerce_benchmark.csv`) and test harness evaluating Execution Accuracy (EX %) and latency.
- **AST Safety Guardrails (`SQLGlot`)**: Statically parses SQL syntax trees to enforce single read-only `SELECT` queries and prevent SQL injection or cartesian products.
- **Native Model Context Protocol (MCP)**: Exposes `@mcp.tool()` and `@mcp.resource()` endpoints so Claude Desktop, Antigravity IDE, Cursor, and AI agents can query the warehouse.
- **Streamlit Web UI (`src/app.py`)**: Interactive web dashboard featuring CSV drag-and-drop, dynamic schema inspector, chat bar, SQL query viewer, and Plotly visual charts.

---

## 🏗️ 5-Layer Spine System Design Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 MCP CLIENT HOST / STREAMLIT APP UI                       │
│        (Claude Desktop / Cursor / Antigravity IDE / Streamlit)           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      5-LAYER AGENT ARCHITECTURE                          │
│                                                                          │
│  LAYER 1: MODEL & ROUTER                                                 │
│    └─ Provider-agnostic LLMRouter (Gemini 2.5 / Ollama / Dynamic Zero-Shot) │
│                                                                          │
│  LAYER 2: WRAPPING (KNOWLEDGE, TOOLS & MEMORY)                           │
│    ├─ Knowledge : Dynamic PRAGMA catalog profiler & categorical samples  │
│    ├─ Schema Linker: Sparse BM25 + Value-Aware Categorical Matching      │
│    ├─ Semantic Layer: Governed metric definitions & time macro dictionary│
│    ├─ Few-Shot Retrieval: Dynamic worked question-to-SQL exemplars       │
│    └─ Self-Correction: Bounded execution error feedback retry loop       │
│                                                                          │
│  LAYER 3: EVALS & REAL-TIME GUARDRAILS                                   │
│    ├─ Static Guardrail: SQLGlot AST single read-only SELECT enforcement  │
│    ├─ Evals Harness   : Labeled benchmark suite (100% EX accuracy)       │
│    └─ Abstention Engine: Default safe handoff (confidence 0.0) on errors  │
│                                                                          │
│  LAYER 4 & 5: SAFETY & OPTIMIZATION                                      │
│    └─ DuckDB read-only session, statement timeouts, row caps & caching   │
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
│   ├── app.py                          # Streamlit Web Application
│   ├── mcp_server.py                   # FastMCP server exposing tools & resources
│   ├── graph/
│   │   ├── state.py                    # Agent state definition
│   │   ├── nodes.py                    # Pipeline execution nodes
│   │   └── workflow.py                 # State machine workflow coordinator
│   ├── knowledge/
│   │   ├── catalog.py                  # Dynamic schema profiler & sample extractor
│   │   ├── schema_linker.py            # Hybrid BM25 schema linker & join inferencer
│   │   └── semantic_layer.py           # Metric resolution & business dictionary
│   ├── execution/
│   │   ├── sandbox.py                  # DuckDB read-only sandbox executor
│   │   └── validator.py                # SQLGlot AST validator & security guardrails
│   └── models/
│       └── router.py                   # LLM provider router (Gemini Free / Fallback)
└── tests/
    ├── test_validator.py               # AST validator unit tests
    └── test_sandbox.py                 # Query sandbox unit tests
```

---

## 🧪 Evals & Verification

Run unit tests to verify AST security checks and execution sandbox safety:
```bash
pytest
```

---

## 🛠️ Tools & Technologies

- 🐍 [Python 3.10+](https://www.python.org/downloads/) — Core programming language
- 🦆 [DuckDB](https://duckdb.org/) — In-memory analytical database engine
- ⚡ [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — Open protocol for AI tools & context
- 🚀 [FastMCP](https://github.com/jlowin/fastmcp) — High-level Python MCP server framework
- 📊 [Streamlit](https://streamlit.io/) — Interactive web application interface
- 🛡️ [SQLGlot](https://github.com/tobymao/sqlglot) — SQL parser, AST validator & transpiler
- 🤖 [Google Gemini API](https://ai.google.dev/) — LLM reasoning & SQL query generation (Free Tier)
- 🧠 [SentenceTransformers](https://www.sbert.net/) — Local CPU vector embeddings & RAG

---

## 📚 References & State of the Art (SOTA) Inspiration

This project draws inspiration from leading Text-to-SQL research, benchmark surveys, and enterprise system designs:

- 📖 [HKUST NL2SQL Handbook (TKDE'25 / VLDB'24)](https://github.com/HKUSTDial/NL2SQL_Handbook) — A comprehensive survey of Text-to-SQL in the era of LLMs, 3-stage pipeline decomposition (Pre-processing, Translation, Post-processing), and execution accuracy evaluation frameworks.
- 🤖 [Wren AI (Canner)](https://github.com/Canner/WrenAI) — Open-source AI agent for data warehouses with governed semantic engines and dynamic database adapters.
- 🎓 [Text2SQL with LLMs](https://github.com/kavyabammidi/text2sql) — Few-shot exemplar retrieval, SQLGlot AST transpilation, and evaluation paradigms.
- 📊 [Awesome Generative AI Guide (Text-to-SQL Analytics)](https://github.com/aishwaryanr/awesome-generative-ai-guide/tree/main/interview_prep/system-design/text-to-sql-analytics) — 5-layer AI system design spine and Spider 2.0 evaluation benchmarks.


