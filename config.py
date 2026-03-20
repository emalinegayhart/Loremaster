import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")
ES_ENDPOINT = os.getenv("ES_ENDPOINT")
ES_API_KEY  = os.getenv("ES_API_KEY")
ES_INDEX    = "wowpedia"
CLEAN_JSONL = "data/clean/pages.jsonl"
PG_BATCH_SIZE = 500
ES_BATCH_SIZE = 500
