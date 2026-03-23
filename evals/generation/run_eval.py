import sys
import json
import requests
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

import anthropic
from config import ANTHROPIC_API_KEY
from evals.generation.judge import score

client     = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
API_URL    = "http://localhost:8080/api/chat"
BENCHMARK  = Path(__file__).parent / "benchmark.json"
DIMENSIONS = ["correctness", "faithfulness", "relevance"]


def call_loremaster(question: str) -> str:
    resp = requests.post(API_URL, json={"messages": [{"role": "user", "content": question}]}, stream=True)
    full_text = ""
    for chunk in resp.iter_content(chunk_size=None):
        text = chunk.decode("utf-8")
        if "[SECTIONS_JSON]" in text:
            full_text += text.split("[SECTIONS_JSON]")[0]
            break
        full_text += text
    return full_text.strip()


def run():
    benchmark  = json.loads(BENCHMARK.read_text())
    categories = sorted(set(b["category"] for b in benchmark))
    results    = []

    for entry in benchmark:
        print(f"  {entry['question'][:60]}...")
        response = call_loremaster(entry["question"])
        judgment = score(entry["question"], entry["reference"], response, client)
        results.append({**entry, "response": response, **judgment})

    print(f"\n{'Dimension':<15} {'Score':>6}")
    print("-" * 25)
    for dim in DIMENSIONS:
        avg = sum(r[dim] for r in results) / len(results)
        print(f"{dim:<15} {avg:>6.2f}/5")

    print(f"\nPer-category breakdown:")
    print("-" * 25)
    for category in categories:
        cat_results = [r for r in results if r["category"] == category]
        print(f"\n{category} ({len(cat_results)} questions)")
        for dim in DIMENSIONS:
            avg = sum(r[dim] for r in cat_results) / len(cat_results)
            print(f"  {dim:<15} {avg:.2f}/5")

    output_path = Path(__file__).parent / "results.json"
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    run()
