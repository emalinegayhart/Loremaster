import sys
import json
import random
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras
import anthropic
from config import ES_ENDPOINT, ES_API_KEY, ES_INDEX, NEON_CONNECTION_STRING, ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TARGETS = {
    "lore":            30,
    "quest":           20,
    "item":            20,
    "gameplay":        20,
    "long_tail":       10,
    "lore_short":      15,
    "quest_short":     10,
    "item_short":      10,
    "gameplay_short":  10,
    "long_tail_short":  5,
}

CATEGORY_FILTERS = {
    "lore":            "content ILIKE '%lore%' OR title ~* '(Arthas|Sylvanas|Illidan|Thrall|Jaina|Anduin|Garrosh|Kael|Malfurion|Tyrande|Varian)'",
    "quest":           "title ~* '^(A |The |An )?[A-Z]' AND content ILIKE '%quest%'",
    "item":            "content ILIKE '%item level%' OR content ILIKE '%binds when%' OR title ILIKE '%sword%' OR title ILIKE '%staff%' OR title ILIKE '%helm%'",
    "gameplay":        "content ILIKE '%mechanic%' OR content ILIKE '%ability%' OR content ILIKE '%talent%'",
    "long_tail":       "LENGTH(content) < 500 AND content IS NOT NULL",
    "lore_short":      "content ILIKE '%lore%' OR title ~* '(Arthas|Sylvanas|Illidan|Thrall|Jaina|Anduin|Garrosh|Kael|Malfurion|Tyrande|Varian)'",
    "quest_short":     "title ~* '^(A |The |An )?[A-Z]' AND content ILIKE '%quest%'",
    "item_short":      "content ILIKE '%item level%' OR content ILIKE '%binds when%' OR title ILIKE '%sword%' OR title ILIKE '%staff%' OR title ILIKE '%helm%'",
    "gameplay_short":  "content ILIKE '%mechanic%' OR content ILIKE '%ability%' OR content ILIKE '%talent%'",
    "long_tail_short": "LENGTH(content) < 500 AND content IS NOT NULL",
}

PROMPT_CONVERSATIONAL = """Given this World of Warcraft article, generate a realistic question a player might ask that this article would answer.
The question should sound natural and conversational, not like a search query.
Return only a JSON object with a single key "question". No other text.

Article title: {title}
Article summary: {summary}"""

PROMPT_SHORT = """Given this World of Warcraft article, generate a short direct query of 2-5 words that a player might search to find this article.
It should be concise and factual, not conversational. Like "Arthas death knight" or "Frostmourne sword lore".
Return only a JSON object with a single key "question". No other text.

Article title: {title}
Article summary: {summary}"""


def fetch_articles(category: str, limit: int) -> list[dict]:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT title, summary, content
        FROM pages
        WHERE {CATEGORY_FILTERS[category]}
        AND content IS NOT NULL
        AND LENGTH(content) > 100
        ORDER BY RANDOM()
        LIMIT {limit * 3}
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return random.sample(list(rows), min(limit, len(rows)))


def generate_question(title: str, summary: str, short: bool = False) -> str | None:
    prompt = PROMPT_SHORT if short else PROMPT_CONVERSATIONAL
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt.format(
                title=title,
                summary=(summary or "")[:500],
            )}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)["question"]
    except Exception as e:
        print(f"Skipped '{title}': {e}")
        return None


def run():
    existing = json.loads(Path(__file__).parent.parent.joinpath("data/benchmark.json").read_text())
    new_entries = []

    for category, target in TARGETS.items():
        existing_count = sum(1 for e in existing if e["category"] == category)
        needed = target - existing_count
        if needed <= 0:
            print(f"{category}: already at target ({existing_count}/{target})")
            continue

        print(f"\n{category}: generating {needed} questions...")
        articles = fetch_articles(category, needed)

        is_short = category.endswith("_short")
        base_category = category.replace("_short", "") if is_short else category

        for article in articles:
            question = generate_question(article["title"], article.get("summary", ""), short=is_short)
            if question:
                new_entries.append({
                    "query":    question,
                    "expected": article["title"],
                    "category": base_category,
                    "type":     "short" if is_short else "conversational",
                })
                print(f"  + {question[:80]}")

    all_entries = existing + new_entries
    Path(__file__).parent.parent.joinpath("data/benchmark.json").write_text(json.dumps(all_entries, indent=2))
    print(f"\nDone. {len(all_entries)} total entries in benchmark.json ({len(new_entries)} new)")


if __name__ == "__main__":
    run()
