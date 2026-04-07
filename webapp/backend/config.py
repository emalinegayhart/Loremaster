import os

NEON_CONNECTION_STRING = os.getenv(
    "NEON_CONNECTION_STRING",
    "postgresql://user:password@localhost/loremaster"
)

ES_ENDPOINT = os.getenv("ES_ENDPOINT", "http://localhost:9200")
ES_API_KEY = os.getenv("ES_API_KEY", "")
ES_INDEX = os.getenv("ES_INDEX", "wowpedia")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

ELSER_READY = os.getenv("ELSER_READY", "False").lower() == "true"
