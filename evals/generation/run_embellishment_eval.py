import sys
import json
import anthropic
from datetime import datetime
from pathlib import Path
from elasticsearch import Elasticsearch

sys.path.append(str(Path(__file__).parent.parent.parent))

from config import ANTHROPIC_API_KEY, ES_ENDPOINT, ES_API_KEY, ES_INDEX
from evals.retrieval.strategies import STRATEGIES
from evals.generation.judge import score_narrative
from evals.generation.run_eval import search_with_snippets, generate

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
es     = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

BENCHMARK          = Path(__file__).parent / "benchmark.json"
COMPARE_STRATEGIES = ["best_fields", "rrf_elser"]


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

            source_judgment   = score_narrative("\n---\n".join(snippets), client)
            response_judgment = score_narrative(response, client)

            source_score   = source_judgment["narrative_score"]
            response_score = response_judgment["narrative_score"]
            delta          = response_score - source_score

            results.append({
                **entry,
                "snippets":        snippets,
                "response":        response,
                "source_score":    source_score,
                "response_score":  response_score,
                "delta":           delta,
                "source_reasoning":   source_judgment["reasoning"],
                "response_reasoning": response_judgment["reasoning"],
            })
        all_results[strategy_name] = results

    # Overall summary
    col = 14
    print(f"\n\n{'':18}", end="")
    for name in COMPARE_STRATEGIES:
        print(f"  {name:>{col}}", end="")
    print()
    print("-" * (18 + (col + 2) * len(COMPARE_STRATEGIES)))

    for field in ["source_score", "response_score", "delta"]:
        avgs = {n: sum(r[field] for r in all_results[n]) / len(all_results[n]) for n in COMPARE_STRATEGIES}
        print(f"{field:<18}", end="")
        for name in COMPARE_STRATEGIES:
            print(f"  {avgs[name]:>{col}.2f}", end="")
        print()

    # Per-category breakdown
    print(f"\nPer-category breakdown:")
    for category in categories:
        print(f"\n  {category}")
        for field in ["source_score", "response_score", "delta"]:
            print(f"    {field:<18}", end="")
            for name in COMPARE_STRATEGIES:
                cat_results = [r for r in all_results[name] if r["category"] == category]
                avg = sum(r[field] for r in cat_results) / len(cat_results)
                print(f"  {avg:>12.2f}", end="")
            print()

    # Flag large positive deltas — model added narrative well beyond the source
    print(f"\nHigh embellishment flags (delta >= 2):")
    print("-" * 60)
    for name in COMPARE_STRATEGIES:
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
