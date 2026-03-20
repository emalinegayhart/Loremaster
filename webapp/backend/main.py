import sys
import json
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras
import anthropic
from elasticsearch import Elasticsearch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import (
    NEON_CONNECTION_STRING,
    ES_ENDPOINT,
    ES_API_KEY,
    ES_INDEX,
    ANTHROPIC_API_KEY,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

es     = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = FastAPI(title="Loremaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


def search_wowpedia(query: str, limit: int = 5) -> list[dict]:
    result = es.search(
        index=ES_INDEX,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^4", "summary^2", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            },
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 500,
                        "number_of_fragments": 1,
                    }
                }
            },
            "size": limit,
            "_source": ["title", "url", "summary"],
        }
    )

    pages = []
    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        highlight = hit.get("highlight", {}).get("content", [])
        snippet = highlight[0] if highlight else src.get("summary", "")
        pages.append({
            "title":   src.get("title", ""),
            "url":     src.get("url", ""),
            "snippet": snippet,
        })
    return pages


def build_system_prompt(context_pages: list[dict]) -> str:
    if not context_pages:
        context = "No specific pages found. Answer from general WoW knowledge."
    else:
        context = "\n\n---\n\n".join(
            f"**{p['title']}**\nSource: {p['url']}\n{p['snippet']}"
            for p in context_pages
        )

    return f"""You are an expert on World of Warcraft with deep knowledge of its lore, characters, gameplay, and history. Answer directly and confidently — never use filler phrases like "Based on the available information", "According to", "It appears that", or "Based on what we know". Just state the facts.
If the retrieved information is not relevant to the question, answer from your own general WoW knowledge instead. Always give a confident, helpful answer.

Format your response in two parts:

PART 1 — Write a conversational markdown summary that directly answers the question.
Use bold and natural prose. Keep it to 2-4 paragraphs.
When citing a source, use a markdown link with the text "source" like this: ([source](https://...))

PART 2 — After your summary, append exactly this delimiter on its own line:
[SECTIONS]
Then immediately output a JSON array of 2-5 sections for extra detail, like:
[{{"title":"Origins","content":"Detail here. ([source](https://...))"}},{{"title":"Powers","content":"..."}}]

No text after the JSON. No markdown in section content except for the source link format above.

Available information:
{context}"""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
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
