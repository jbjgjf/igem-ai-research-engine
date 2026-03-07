import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_LITERATURE_DB = os.getenv("NOTION_LITERATURE_DB")
NOTION_HYPOTHESIS_DB = os.getenv("NOTION_HYPOTHESIS_DB")
NOTION_IDEA_DB = os.getenv("NOTION_IDEA_DB")

# Project settings
PAPERS_TO_FETCH = 5
SEARCH_QUERY = 'aging cellular noise OR aging signaling OR "cellular senescence" "synthetic biology"'
