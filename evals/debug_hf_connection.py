import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def debug_hf():
    load_dotenv()
    print("=" * 60)
    print("🐞 DEBUGGING HUGGING FACE CONNECTIVITY & TOKENS")
    print("=" * 60)

    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    hf_repo = os.getenv("HF_MODEL_REPO", "Priyanka221105/text2sql-qwen2.5-duckdb")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    print(f"1. HF Token Present?  : {'YES (' + hf_token[:5] + '...)' if hf_token else '❌ NO (Missing in .env)'}")
    print(f"2. HF Model Repo      : {hf_repo}")
    print(f"3. Gemini Key Present?: {'YES (' + gemini_key[:5] + '...)' if gemini_key else '❌ NO'}")
    
    if not hf_token:
        print("\n⚠️ WARNING: HUGGINGFACEHUB_API_TOKEN is missing in your .env file!")
        print("Please add HUGGINGFACEHUB_API_TOKEN=hf_your_token to .env or Streamlit Secrets.")
        return

    print("\n------------------------------------------------------------")
    print("📡 Attempting Direct HuggingFaceEndpoint Connection:")
    print("------------------------------------------------------------")
    try:
        from langchain_huggingface import HuggingFaceEndpoint
        llm = HuggingFaceEndpoint(
            repo_id=hf_repo,
            huggingfacehub_api_token=hf_token,
            temperature=0.01,
            max_new_tokens=512
        )
        print(f"✅ SUCCESSFULLY INSTANTIATED HuggingFaceEndpoint({hf_repo})")
        print("Testing a test generation call...")
        res = llm.invoke("SELECT * FROM test")
        print(f"Response: {res}")
    except Exception as e:
        print(f"❌ FAILED TO CONNECT TO HUGGING FACE MODEL:")
        print(f"Error Details: {e}")
        print("\nPossible reasons:")
        print("1. Has Colab finished pushing your model to https://huggingface.co/Priyanka221105/text2sql-qwen2.5-duckdb ?")
        print("2. Is your HF token a WRITE token from https://huggingface.co/settings/tokens ?")

if __name__ == "__main__":
    debug_hf()
