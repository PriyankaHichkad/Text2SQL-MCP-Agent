---
base_model: Qwen/Qwen2.5-Coder-7B-Instruct
library_name: peft
tags:
- text-to-sql
- code
- sql
- duckdb
- qwen2.5
- qlora
- unsloth
license: apache-2.0
language:
- en
pipeline_tag: text-generation
---

# Text2SQL Qwen-2.5-Coder DuckDB (Fine-Tuned)

A specialized Text-to-SQL Large Language Model fine-tuned on **Qwen/Qwen2.5-Coder-7B-Instruct** using **QLoRA (Quantized Low-Rank Adaptation)**. It is specifically optimized to translate natural language business analytics questions into executable, read-only analytical **DuckDB SQL** queries (including multi-table JOINs, Common Table Expressions (CTEs), Window Functions, and relative date arithmetic).

- **Developed by:** Priyanka221105
- **Base Model:** [Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
- **Target Dialect:** DuckDB Analytical SQL (ANSI SQL compliant)
- **Fine-Tuning Method:** QLoRA (4-bit NF4 Quantization) via Unsloth & PEFT
- **Live Agent Deployment:** [text2sql-mcp-agent.streamlit.app](https://text2sql-mcp-agent-jxzsy3qnkeqmyfeas6ekkz.streamlit.app)
- **GitHub Repository:** [Text2SQL-MCP-Agent](https://github.com/PriyankaHichkad/Text2SQL-MCP-Agent)

---

## 🎯 Model Capabilities

- **Analytical Aggregations:** Computes single and multi-column aggregations (`SUM`, `AVG`, `COUNT(DISTINCT)`).
- **Relational Joins:** Resolves star-schema foreign key relationships (`INNER JOIN`, `LEFT JOIN`) with explicit `ON` clauses.
- **Window Functions:** Generates analytical partitions and rankings (`RANK() OVER (PARTITION BY ... ORDER BY ...)`).
- **Common Table Expressions (CTEs):** Synthesizes multi-stage CTEs (`WITH sub AS (...) SELECT ...`) for complex business logic.
- **DuckDB Date Arithmetic:** Natively applies DuckDB temporal functions (`LAST_DAY()`, `DATE_TRUNC()`, `DATEDIFF()`).
- **Read-Only Safety:** Strictly structured to produce read-only `SELECT` statements without destructive DDL/DML mutations.

---

## 📊 Training Dataset & Curation

- **Dataset Size:** 847 domain-specific natural language to SQL pairs.
- **Format:** ChatML prompt structure (`<|im_start|>system...<|im_end|>`).
- **Domain Coverage:**
  - E-commerce sales, customer transactions, inventory, returns, and time-series analytics.
  - Multi-table star schemas with foreign-key joins.
  - Complex boundary conditions: N-th ordinal ranks (e.g. "second highest"), relative month/year boundaries (e.g. "last day of July"), and percentage calculations.

---

## ⚙️ Training Hyperparameters (QLoRA)

The model was fine-tuned in 4-bit precision on a single Google Colab T4 GPU (16GB VRAM) using Unsloth and Hugging Face TRL's `SFTTrainer`:

| Hyperparameter | Value | Description |
| :--- | :--- | :--- |
| **Quantization** | 4-bit NormalFloat (NF4) | `bitsandbytes` double quantization with bfloat16 compute |
| **LoRA Rank ($r$)** | 16 | Rank of the low-rank adaptation decomposition matrices |
| **LoRA Alpha ($\alpha$)** | 32 | Scaling factor for adapter updates ($\alpha / r = 2.0$) |
| **LoRA Dropout** | 0.0 | Optimized for Unsloth kernel acceleration |
| **Target Modules** | All Linear Projections | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| **Optimizer** | `adamw_8bit` | 8-bit quantized AdamW to minimize optimizer state VRAM |
| **Learning Rate** | $2 \times 10^{-4}$ | Linear decay schedule with warmup |
| **Batch Size** | 2 per device | Gradient Accumulation Steps = 4 (Effective Batch Size = 8) |
| **Max Sequence Length** | 2,048 tokens | Context window covering table schemas, foreign keys, and exemplars |
| **Loss Function** | Cross-Entropy Loss | Masked on user prompt, computed only on assistant SQL response |

---

## 💬 Prompt Template (ChatML)

```text
<|im_start|>system
You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Use ONLY the tables and columns provided in the database schema context. Return ONLY the SQL query inside ```sql ... ``` code block.<|im_end|>
<|im_start|>user
Database Schema:
Table `orders`: order_id (INT), customer_id (INT), category (VARCHAR), net_amount (DECIMAL), order_date (DATE)

Question: "What is the total revenue for Furniture in 2024?"<|im_end|>
<|im_start|>assistant
```sql
SELECT SUM(net_amount) AS total_revenue
FROM orders
WHERE category = 'Furniture' AND YEAR(CAST(order_date AS DATE)) = 2024;
```<|im_end|>
```

---

## 🚀 How to Run Locally

### Using Transformers & PEFT:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Priyanka221105/text2sql-qwen2.5-duckdb"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

prompt = """<|im_start|>system
You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. Return ONLY the SQL query inside ```sql ... ``` code block.<|im_end|>
<|im_start|>user
Database Schema:
Table `orders`: order_id (INT), net_amount (DECIMAL), category (VARCHAR)

Question: "Top 3 categories by total sales"<|im_end|>
<|im_start|>assistant
"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.01)
print(tokenizer.decode(outputs[0], skip_special_tokens=False))
```

---

## ⚠️ Limitations & Guardrails

1. **Dialect Specificity:** The model is optimized for **DuckDB** dialect. While DuckDB is standard ANSI SQL compliant, queries with temporal functions (e.g. `LAST_DAY`, `DATE_TRUNC`) may require transpilation (via SQLGlot) when executed on MySQL or PostgreSQL.
2. **Security Sandboxing:** In production, generated queries should always be validated by an AST parser (like `SQLGlot`) to ensure single-statement read-only execution and prevent unintentional mutations.
