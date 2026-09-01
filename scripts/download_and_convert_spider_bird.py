import os
import json
from datasets import load_dataset

def convert_spider_to_finetune(output_path: str = "data/finetune_dataset.jsonl", max_samples: int = 500):
    """
    Loads official Yale Spider benchmark dataset from Hugging Face,
    converts it into ChatML format, and merges it into data/finetune_dataset.jsonl.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print("📥 Loading official Yale Spider benchmark dataset via Hugging Face...")

    try:
        dataset = load_dataset("xlangai/spider", split="train")
    except Exception as e:
        print(f"⚠️ Notice loading Spider dataset: {e}")
        return

    system_prompt = (
        "You are an expert DuckDB SQL Data Analyst writing read-only SELECT queries. "
        "Use ONLY the tables and columns provided in the database schema context. "
        "Return ONLY the SQL query inside ```sql ... ``` code block."
    )

    spider_entries = []
    for i, row in enumerate(dataset):
        if i >= max_samples:
            break
        
        db_id = row.get("db_id", "analytics_db")
        question = row.get("question", "").strip()
        sql_query = row.get("query", "").strip()

        # Build schema description
        schema_text = f"Database `{db_id}`"
        query_toks = row.get("query_toks_no_value", [])
        if query_toks:
            tables = list({t for t in query_toks if t.isidentifier() and not t.isupper()})
            if tables:
                schema_text = "Tables available: " + ", ".join([f"`{t}`" for t in tables[:4]])

        user_msg = f"Database Schema:\n{schema_text}\n\nQuestion: \"{question}\""
        model_msg = f"```sql\n{sql_query}\n```"

        entry = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": model_msg}
            ]
        }
        spider_entries.append(entry)

    # Read existing custom project examples
    existing_entries = []
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        existing_entries.append(json.loads(line))
                    except Exception:
                        pass

    all_entries = spider_entries + existing_entries

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"✅ Successfully converted & saved {len(spider_entries)} Spider benchmark pairs + {len(existing_entries)} custom domain pairs into '{output_path}' (Total: {len(all_entries)} training examples).")

if __name__ == "__main__":
    convert_spider_to_finetune()
