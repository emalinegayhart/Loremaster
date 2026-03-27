import sys
import json
import anthropic
from datetime import datetime
from pathlib import Path
from elasticsearch import Elasticsearch

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import ANTHROPIC_API_KEY, ES_ENDPOINT, ES_API_KEY, ES_INDEX
from evals.retrieval.strategies import STRATEGIES
from evals.generation.judge import score

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
es     = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

BENCHMARK          = Path(__file__).parent / "benchmark.json"
DIMENSIONS         = ["correctness", "faithfulness", "relevance"]
COMPARE_STRATEGIES = ["best_fields", "rrf_elser"]

BASE_SYSTEM_PROMPT = """You are an expert on World of Warcraft with deep knowledge of its lore, characters, gameplay, and history. Answer directly and confidently — never use filler phrases like "Based on the available information", "According to", "It appears that", or "Based on what we know". Just state the facts.
When retrieved information is relevant, use it as your primary source. When it is only partially relevant, use what applies and acknowledge the limits of what you know.

{instruction} Keep it to 2-4 paragraphs.

Available information:
{context}"""

DEFAULT_INSTRUCTION = "Write a markdown summary that directly answers the question."


def search_with_snippets(question: str, strategy_name: str) -> list[str]:
    body = {
        **STRATEGIES[strategy_name]["query"](question),
        "size": 5,
        "_source": ["title", "url", "summary"],
        "highlight": {
            "fields": {
                "content": {"fragment_size": 1500, "number_of_fragments": 3}
            }
        },
    }
    result = es.search(index=ES_INDEX, body=body)
    snippets = []
    for hit in result["hits"]["hits"]:
        src       = hit["_source"]
        highlight = hit.get("highlight", {}).get("content", [])
        snippet   = highlight[0] if highlight else src.get("summary", "")
        snippets.append(f"{src.get('title', '')}: {snippet}")
    return snippets


def generate(question: str, snippets: list[str], instruction: str = DEFAULT_INSTRUCTION) -> str:
    context = "\n\n---\n\n".join(snippets) if snippets else "No relevant information found."
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        system=BASE_SYSTEM_PROMPT.format(instruction=instruction, context=context),
        messages=[{"role": "user", "content": question}],
    )
    return resp.content[0].text.strip()


def run():
    benchmark   = json.loads(BENCHMARK.read_text())
    categories  = sorted(set(b["category"] for b in benchmark))
    all_results = {}

    for strategy_name in COMPARE_STRATEGIES:
        print(f"\nRunning: {strategy_name}")
        results = []
        for entry in benchmark:
            print(f"  {entry['question'][:60]}...")
            snippets = search_with_snippets(entry["question"], strategy_name)
            response = generate(entry["question"], snippets)
            judgment = score(entry["question"], entry["reference"], snippets, response, client)
            results.append({**entry, "response": response, "snippets": snippets, **judgment})
        all_results[strategy_name] = results

    # Overall comparison table
    col = 14
    print(f"\n\n{'Dimension':<15}", end="")
    for name in COMPARE_STRATEGIES:
        print(f"  {name:>{col}}", end="")
    print(f"  {'delta':>8}")
    print("-" * (15 + (col + 2) * len(COMPARE_STRATEGIES) + 10))

    for dim in DIMENSIONS:
        avgs  = {n: sum(r[dim] for r in all_results[n]) / len(all_results[n]) for n in COMPARE_STRATEGIES}
        delta = avgs[COMPARE_STRATEGIES[-1]] - avgs[COMPARE_STRATEGIES[0]]
        print(f"{dim:<15}", end="")
        for name in COMPARE_STRATEGIES:
            print(f"  {avgs[name]:>{col}.2f}", end="")
        print(f"  {delta:>+8.2f}")

    # Per-category breakdown
    print(f"\nPer-category breakdown:")
    for category in categories:
        print(f"\n  {category}")
        for dim in DIMENSIONS:
            avgs = []
            print(f"    {dim:<15}", end="")
            for name in COMPARE_STRATEGIES:
                cat_results = [r for r in all_results[name] if r["category"] == category]
                avg = sum(r[dim] for r in cat_results) / len(cat_results)
                avgs.append(avg)
                print(f"  {avg:>12.2f}", end="")
            print(f"  {avgs[-1] - avgs[0]:>+8.2f}")

    timestamp   = datetime.now().strftime("%Y-%m-%d_%I-%M%p").lower()
    output_path = Path(__file__).parent / f"results_{timestamp}.json"
    output_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    run()
