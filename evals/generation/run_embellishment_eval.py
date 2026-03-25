import sys
import json
import anthropic
from datetime import datetime
from pathlib import Path
from elasticsearch import Elasticsearch

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import ANTHROPIC_API_KEY, ES_ENDPOINT, ES_API_KEY, ES_INDEX
from evals.generation.judge import score_narrative
from evals.generation.run_eval import search_with_snippets, generate

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
es     = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

BENCHMARK = Path(__file__).parent / "benchmark.json"
STRATEGY  = "rrf_elser"

PROMPT_VARIANTS = {
    "original":      "Write a conversational markdown summary that directly answers the question. Use bold and natural prose.",
    "clear_direct":  "Write a clear, direct markdown summary that directly answers the question.",
    "match_tone":    "Write a markdown summary that directly answers the question. Match the tone of the content provided.",
    "no_adjectives": "Write a markdown summary that directly answers the question.",
}


def run():
    benchmark  = json.loads(BENCHMARK.read_text())
    categories = sorted(set(b["category"] for b in benchmark))
    all_results = {}

    for variant_name, instruction in PROMPT_VARIANTS.items():
        print(f"\nRunning: {variant_name}")
        results = []

        for entry in benchmark:
            question = entry["question"]
            print(f"  {question[:60]}...")

            snippets = search_with_snippets(question, STRATEGY)
            response = generate(question, snippets, instruction)

            source_j   = score_narrative("\n---\n".join(snippets), client)
            response_j = score_narrative(response, client)

            results.append({
                **entry,
                "snippets":           snippets,
                "response":           response,
                "source_score":       source_j["narrative_score"],
                "response_score":     response_j["narrative_score"],
                "delta":              response_j["narrative_score"] - source_j["narrative_score"],
                "source_reasoning":   source_j["reasoning"],
                "response_reasoning": response_j["reasoning"],
            })

        all_results[variant_name] = results

    # Overall comparison table
    col = 14
    print(f"\n\n{'':18}", end="")
    for name in PROMPT_VARIANTS:
        print(f"  {name:>{col}}", end="")
    print()
    print("-" * (18 + (col + 2) * len(PROMPT_VARIANTS)))

    for field in ["source_score", "response_score", "delta"]:
        avgs = {n: sum(r[field] for r in all_results[n]) / len(all_results[n]) for n in PROMPT_VARIANTS}
        print(f"{field:<18}", end="")
        for name in PROMPT_VARIANTS:
            print(f"  {avgs[name]:>{col}.2f}", end="")
        print()

    # Per-category breakdown
    print(f"\nPer-category breakdown:")
    for category in categories:
        print(f"\n  {category}")
        for field in ["source_score", "response_score", "delta"]:
            print(f"    {field:<18}", end="")
            for name in PROMPT_VARIANTS:
                cat_results = [r for r in all_results[name] if r["category"] == category]
                avg = sum(r[field] for r in cat_results) / len(cat_results)
                print(f"  {avg:>12.2f}", end="")
            print()

    # High embellishment flags
    print(f"\nHigh embellishment flags (delta >= 2):")
    print("-" * 60)
    for name in PROMPT_VARIANTS:
        flagged = [r for r in all_results[name] if r["delta"] >= 2]
        print(f"\n  {name} — {len(flagged)} flagged")
        for r in flagged:
            print(f"    [{r['category']}] {r['question'][:55]}...")
            print(f"      source={r['source_score']}  response={r['response_score']}  delta={r['delta']:+d}")
            print(f"      {r['response_reasoning']}")

    timestamp   = datetime.now().strftime("%Y-%m-%d_%I-%M%p").lower()
    output_path = Path(__file__).parent / f"embellishment_results_{timestamp}.json"
    output_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    run()
