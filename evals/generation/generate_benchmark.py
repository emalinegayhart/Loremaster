import sys
import json
import random
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras
import anthropic
from config import NEON_CONNECTION_STRING, ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

TARGETS = {
    "lore":     20,
    "gameplay": 20,
    "item":     20,
}

CATEGORY_FILTERS = {
    "lore":     "title ~* '(Arthas|Sylvanas|Illidan|Thrall|Jaina|Anduin|Garrosh|Kael|Malfurion|Tyrande|Varian|Lich King|Deathwing|Uther|Medivh|Gul.dan|Ner.zhul|Vol.jin|Cairne|Bolvar)' OR content ILIKE '%lore%'",
    "gameplay": "content ILIKE '%mechanic%' OR content ILIKE '%ability%' OR content ILIKE '%talent%' OR content ILIKE '%pvp%' OR content ILIKE '%dungeon%'",
    "item":     "content ILIKE '%item level%' OR content ILIKE '%binds when%' OR content ILIKE '%equip:%' OR title ILIKE '%sword%' OR title ILIKE '%staff%' OR title ILIKE '%helm%' OR title ILIKE '%blade%'",
}

QUESTION_PROMPT = """Given this World of Warcraft article, generate a realistic question a player might ask that this article would answer.
The question should sound natural and conversational.
Return only a JSON object with a single key "question". No other text.

Article title: {title}
Article content: {content}"""

REFERENCE_PROMPT = """Given this World of Warcraft article, write a concise and accurate reference answer to the following question. 
Use only information from the article. Keep it to 2-4 sentences.
Return only a JSON object with a single key "answer". No other text.

Question: {question}
Article title: {title}
Article content: {content}"""


def fetch_articles(category: str, limit: int) -> list[dict]:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"""
        SELECT title, summary, content
        FROM pages
        WHERE {CATEGORY_FILTERS[category]}
        AND content IS NOT NULL
        AND LENGTH(content) > 300
        ORDER BY RANDOM()
        LIMIT {limit * 3}
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return random.sample(list(rows), min(limit, len(rows)))


def generate_question(title: str, content: str) -> str | None:
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            messages=[{"role": "user", "content": QUESTION_PROMPT.format(
                title=title,
                content=content[:1500],
            )}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)["question"]
    except Exception as e:
        print(f"  Skipped question for '{title}': {e}")
        return None


def generate_reference(question: str, title: str, content: str) -> str | None:
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": REFERENCE_PROMPT.format(
                question=question,
                title=title,
                content=content[:1500],
            )}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)["answer"]
    except Exception as e:
        print(f"  Skipped reference for '{title}': {e}")
        return None


def run():
    benchmark_path = Path(__file__).parent / "benchmark.json"
    existing       = json.loads(benchmark_path.read_text())
    new_entries    = []

    for category, target in TARGETS.items():
        existing_count = sum(1 for e in existing if e["category"] == category)
        needed         = target - existing_count

        if needed <= 0:
            print(f"{category}: already at target ({existing_count}/{target})")
            continue

        print(f"\n{category}: generating {needed} entries...")
        articles = fetch_articles(category, needed)

        for article in articles:
            title   = article["title"]
            content = article.get("content") or article.get("summary") or ""

            question = generate_question(title, content)
            if not question:
                continue

            reference = generate_reference(question, title, content)
            if not reference:
                continue

            new_entries.append({
                "question":  question,
                "reference": reference,
                "category":  category,
            })
            print(f"  + [{category}] {question[:80]}")

    all_entries = existing + new_entries
    benchmark_path.write_text(json.dumps(all_entries, indent=2))
    print(f"\nDone. {len(all_entries)} total entries ({len(new_entries)} new)")

    counts = {}
    for e in all_entries:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    for cat, count in sorted(counts.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    run()
