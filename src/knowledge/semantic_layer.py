import os
import yaml
from typing import Dict, Any, List

class SemanticLayer:
    """
    Parses business definitions and metric formulas from semantic_layer.yaml.
    """
    def __init__(self, config_path: str = "config/semantic_layer.yaml"):
        self.config_path = config_path
        self.metrics = {}
        self.time_macros = {}
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = yaml.safe_load(f) or {}
                    self.metrics = data.get("metrics", {})
                    self.time_macros = data.get("time_macros", {})
            except Exception as e:
                print(f"Warning: Failed to load semantic layer config: {e}")

    def get_semantic_context(self, question: str) -> str:
        """
        Extracts relevant business metrics & time macros based on keyword matching in question.
        """
        lines = []
        q_lower = question.lower()

        matched_metrics = []
        for metric_name, m_info in self.metrics.items():
            aliases = m_info.get("alias", []) + [metric_name]
            if any(alias in q_lower for alias in aliases):
                matched_metrics.append(f"- **{metric_name}**: {m_info.get('description', '')} -> Formula: `{m_info.get('sql', '')}`")

        matched_macros = []
        for macro_name, macro_sql in self.time_macros.items():
            if macro_name.replace("_", " ") in q_lower or macro_name in q_lower:
                matched_macros.append(f"- **{macro_name}**: `{macro_sql}`")

        if matched_metrics or matched_macros:
            lines.append("### Business Semantic Definitions:")
            if matched_metrics:
                lines.append("Metrics:")
                lines.extend(matched_metrics)
            if matched_macros:
                lines.append("Time Filters:")
                lines.extend(matched_macros)
            lines.append("")

        return "\n".join(lines)
