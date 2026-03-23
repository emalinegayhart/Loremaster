import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from elasticsearch import Elasticsearch
from config import ES_ENDPOINT, ES_API_KEY, ES_INDEX
from evals.retrieval.strategies import STRATEGIES
from evals.retrieval.metrics import hit_rate, mrr

es = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)
TOP_K = 5


def search(query_body: dict) -> list[str]:
    result = es.search(index=ES_INDEX, body={**query_body, "size": TOP_K, "_source": ["title"]})
    return [h["_source"]["title"] for h in result["hits"]["hits"]]


def print_table(label: str, indices: list[int], cached: dict, queries: list, expected: list):
    print(f"\n{label}")
    for name in STRATEGIES:
        results = [cached[name][i] for i in indices]
        exp     = [expected[i] for i in indices]
        hr      = hit_rate(results, exp, k=TOP_K)
        mrr_score = mrr(results, exp, k=TOP_K)
        print(f"  {name:<20} {hr:>8.2%}   MRR {mrr_score:.3f}")


def run():
    benchmark  = json.loads(Path(__file__).parent.parent.joinpath("data/benchmark.json").read_text())
    queries    = [b["query"]    for b in benchmark]
    expected   = [b["expected"] for b in benchmark]
    categories = [b["category"] for b in benchmark]
    types      = [b.get("type", "conversational") for b in benchmark]

    print("Running all strategies against benchmark...")
    cached = {}
    for name, strategy in STRATEGIES.items():
        print(f"  {name}...")
        cached[name] = [search(strategy["query"](q)) for q in queries]

    print(f"\n{'Strategy':<20} {'Hit@5':>8}   {'MRR':>8}")
    print("-" * 45)
    for name in STRATEGIES:
        hr        = hit_rate(cached[name], expected, k=TOP_K)
        mrr_score = mrr(cached[name], expected, k=TOP_K)
        print(f"{name:<20} {hr:>8.2%}   {mrr_score:>8.3f}")

    print("\n\nPer-category breakdown (Hit@5):")
    print("-" * 45)
    for category in sorted(set(categories)):
        indices = [i for i, c in enumerate(categories) if c == category]
        print_table(f"{category} ({len(indices)} queries)", indices, cached, queries, expected)

    print("\n\nBy query type:")
    print("-" * 45)
    for qtype in sorted(set(types)):
        indices = [i for i, t in enumerate(types) if t == qtype]
        print_table(f"{qtype} ({len(indices)} queries)", indices, cached, queries, expected)


if __name__ == "__main__":
    run()
