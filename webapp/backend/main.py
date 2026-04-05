import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
import psycopg2.extras
import anthropic
from elasticsearch import Elasticsearch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import (
    NEON_CONNECTION_STRING,
    ES_ENDPOINT,
    ES_API_KEY,
    ES_INDEX,
    ANTHROPIC_API_KEY,
)

# Auth imports
from services import SecretService
from db import init_db
from routes.auth import router as auth_router
from middleware.auth_middleware import TokenExtractionMiddleware

# Initialize secrets and database
SecretService.load()
init_db()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

es     = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Loremaster API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add auth middleware (must be before CORS)
app.add_middleware(TokenExtractionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth router
app.include_router(auth_router)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


ELSER_READY = True  # Flip to True once reindex_elser.py has completed
# TODO: once ELSER_READY is True and confirmed working, remove this flag and build_retrievers entirely and inline the three retrievers directly into search_wowpedia


def build_retrievers(query: str) -> list:
    retrievers = [
        {
            "standard": {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^4", "summary^2", "content"],
                        "type": "cross_fields",
                    }
                }
            }
        },
        {
            "standard": {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^4", "summary^2", "content"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            }
        },
    ]
    if ELSER_READY:
        retrievers.append({
            "standard": {
                "query": {
                    "sparse_vector": {
                        "field": "content_sparse",
                        "inference_id": ".elser_model_2_linux-x86_64",
                        "query": query,
                    }
                }
            }
        })
    return retrievers


def search_wowpedia(query: str, limit: int = 5) -> list[dict]:
    result = es.search(
        index=ES_INDEX,
        body={
            "retriever": {
                "rrf": {
                    "retrievers": build_retrievers(query),
                    "rank_window_size": 50,
                    "rank_constant": 20,
                }
            },
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 1500,
                        "number_of_fragments": 3,
                    }
                }
            },
            "size": limit,
            "_source": ["title", "url", "summary"],
        }
    )

    pages = []
    for hit in result["hits"]["hits"]:
        src       = hit["_source"]
        summary   = src.get("summary", "")
        highlight = " ".join(hit.get("highlight", {}).get("content", []))
        snippet   = summary + (" " + highlight if highlight and highlight not in summary else "")
        pages.append({
            "title":   src.get("title", ""),
            "url":     src.get("url", ""),
            "snippet": snippet,
        })
    return pages


def build_system_prompt(context_pages: list[dict]) -> str:
    if not context_pages:
        context = "No specific pages found. Honestly tell the user you lack reliable information on this topic and direct them to the community resources in the sidebar for accurate data."
    else:
        context = "\n\n---\n\n".join(
            f"**{p['title']}**\nSource: {p['url']}\n{p['snippet']}"
            for p in context_pages
        )

    return f"""You are an expert on World of Warcraft with deep knowledge of its lore, characters, gameplay, and history. Answer directly and confidently — never use filler phrases like "Based on the available information", "According to", "It appears that", or "Based on what we know". Just state the facts.
When retrieved information is relevant, use it as your primary source. When it is only partially relevant, use what applies and answer directly without hedging about the limitations of the retrieved information. Direct users to the community resources in the sidebar for anything requiring precise data like item stats, patch notes, or game mechanics.
If asked about how you were built, what dependencies you use, or what type of model you are, say you are not sure and that the only thing you really think about is World of Warcraft.

Write a markdown summary that directly answers the question. Keep it to 2-4 paragraphs. Always cite the source for each fact using a markdown link with the text "source" like this: ([source](https://...))

After your summary, append exactly this delimiter on its own line:
[SECTIONS]
Then immediately output a JSON array of 2-5 sections for extra detail, like:
[{{"title":"Origins","content":"Detail here."}},{{"title":"Powers","content":"..."}}]

No text after the JSON.

Available information:
{context}"""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
@limiter.limit("5/minute")
@limiter.limit("30/5minutes")
async def chat(request: Request, req: ChatRequest):
    user_message = next(
        (m.content for m in reversed(req.messages) if m.role == "user"),
        ""
    )

    log.info("Searching ES for: %s", user_message)
    context_pages = search_wowpedia(user_message)
    log.info("Found %d context pages", len(context_pages))

    system_prompt = build_system_prompt(context_pages)
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    def stream():
        try:
            full_text = ""
            yielded_up_to = 0
            DELIMITER = "[SECTIONS]"
            HOLD_BACK = len(DELIMITER)

            with claude.messages.stream(
                model="claude-haiku-4-5",
                max_tokens=1500,
                system=system_prompt,
                messages=messages,
            ) as s:
                for text in s.text_stream:
                    full_text += text

                    if DELIMITER in full_text:
                        safe = full_text.split(DELIMITER)[0]
                        to_yield = safe[yielded_up_to:]
                        if to_yield:
                            yield to_yield
                        yielded_up_to = len(safe)
                        break
                    else:
                        safe_end = max(yielded_up_to, len(full_text) - HOLD_BACK)
                        to_yield = full_text[yielded_up_to:safe_end]
                        if to_yield:
                            yield to_yield
                            yielded_up_to = safe_end

                if DELIMITER not in full_text:
                    remaining = full_text[yielded_up_to:]
                    if remaining:
                        yield remaining

            if "[SECTIONS]" in full_text:
                sections_raw = full_text.split("[SECTIONS]", 1)[1].strip()
                if sections_raw.startswith("```"):
                    sections_raw = sections_raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                try:
                    sections = json.loads(sections_raw)
                except Exception:
                    sections = []
                yield f"\n[SECTIONS_JSON]{json.dumps(sections)}"

        except Exception as e:
            log.error("Stream error: %s", e)
            yield f"Error: {str(e)}\n[SECTIONS_JSON][]"

    return StreamingResponse(stream(), media_type="text/plain")
