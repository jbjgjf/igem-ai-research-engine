import os
from dotenv import load_dotenv

load_dotenv()

# LLM Backend settings
LLM_BACKEND = os.getenv("LLM_BACKEND", "mlx").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MLX_MODEL_ID = os.getenv("MLX_MODEL_ID", "mlx-community/Qwen2.5-7B-Instruct-4bit")
MLX_MAX_TOKENS = int(os.getenv("MLX_MAX_TOKENS", "2048"))
MLX_TEMPERATURE = float(os.getenv("MLX_TEMPERATURE", "0.7"))

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_LITERATURE_DB = os.getenv("NOTION_LITERATURE_DB")
NOTION_HYPOTHESIS_DB = os.getenv("NOTION_HYPOTHESIS_DB")
NOTION_IDEA_DB = os.getenv("NOTION_IDEA_DB")
NOTION_EXPERIMENT_DB = os.getenv("NOTION_EXPERIMENT_DB")
# Optional (not yet wired)
NOTION_AGING_MECHANISM_DB = os.getenv("NOTION_AGING_MECHANISM_DB")

# Project settings
PAPERS_TO_FETCH = 5
SEARCH_QUERY = '(aging OR "cellular senescence") AND ("synthetic biology" OR "genetic circuit")'

def validate_required_env():
    missing = []
    
    if LLM_BACKEND == "openai" and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    elif LLM_BACKEND == "mlx" and not MLX_MODEL_ID:
        missing.append("MLX_MODEL_ID")
        
    if not NOTION_TOKEN:
        missing.append("NOTION_TOKEN")
    if not NOTION_LITERATURE_DB:
        missing.append("NOTION_LITERATURE_DB")
    if not NOTION_HYPOTHESIS_DB:
        missing.append("NOTION_HYPOTHESIS_DB")
    if not NOTION_EXPERIMENT_DB:
        missing.append("NOTION_EXPERIMENT_DB")

    if missing:
        raise RuntimeError(f"Missing required environment variables for {LLM_BACKEND} backend: {', '.join(missing)}")
