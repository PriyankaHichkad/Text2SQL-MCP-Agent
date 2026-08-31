import os
import google.generativeai as genai
from typing import Optional

class LLMRouter:
    """
    Provider-agnostic router for LLM calls.
    Primary: Google Gemini API (Free Tier)
    Fallback: Local Ollama / LiteLLM / Rule-based
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                print(f"Warning: Failed to configure Gemini API: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Sends prompt to LLM and returns clean text response.
        """
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature
                    )
                )
                return response.text.strip()
            except Exception as e:
                print(f"Gemini API generation error: {e}")
        
        # Rule-based fallback if no API key is provided for demonstration
        return self._rule_based_fallback(prompt)

    def _rule_based_fallback(self, prompt: str) -> str:
        """
        Fallback generator when running in offline mode without an API key.
        Generates standard DuckDB SQL for common questions.
        """
        p_lower = prompt.lower()
        if "revenue" in p_lower or "sales" in p_lower:
            if "region" in p_lower:
                return "SELECT c.region, SUM(s.net_amount) AS total_revenue FROM fact_sales s JOIN dim_customers c ON s.customer_id = c.customer_id GROUP BY c.region ORDER BY total_revenue DESC;"
            elif "category" in p_lower or "product" in p_lower:
                return "SELECT p.category, SUM(s.net_amount) AS total_revenue FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id GROUP BY p.category ORDER BY total_revenue DESC LIMIT 5;"
            else:
                return "SELECT SUM(net_amount) AS total_revenue FROM fact_sales;"
        elif "customer" in p_lower:
            return "SELECT COUNT(DISTINCT customer_id) AS total_customers FROM dim_customers;"
        elif "count" in p_lower or "how many" in p_lower:
            return "SELECT COUNT(*) AS total_records FROM fact_sales;"
        
        return "SELECT * FROM fact_sales LIMIT 10;"
