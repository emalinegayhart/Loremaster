import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest
from elasticsearch import Elasticsearch
from config import ES_ENDPOINT, ES_API_KEY, ES_INDEX

es = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

TOP_K = 5

RETRIEVAL_CASES = [
    ("Who is Arthas?",                                     "Arthas Menethil"),
    ("What is Frostmourne?",                               "Frostmourne"),
    ("What happened to Sylvanas?",                         "Sylvanas"),
    ("Who is Illidan Stormrage?",                          "Illidan Stormrage"),
    ("Tell me about the Wrathgate event",                  "Wrathgate"),
    ("how do i do this quest A Call to Ardenweald Kyrian", "A Call to Ardenweald (Kyrian)"),
    ("what is the quest Lament of the Highborne",          "Lament of the Highborne"),
    ("What is Thunderfury Blessed Blade of the Windseeker","Thunderfury"),
    ("What drops from Onyxia",                             "Onyxia"),
    ("What is twinking in wow",                            "Sunscale Helmet"),
    ("What is the difference between horde and alliance",  "Alliance"),
]


def search(query: str) -> list[str]:
    result = es.search(
        index=ES_INDEX,
        body={
            "retriever": {
                "rrf": {
                    "retrievers": [
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
                        {
                            "standard": {
                                "query": {
                                    "sparse_vector": {
                                        "field": "content_sparse",
                                        "inference_id": ".elser_model_2_linux-x86_64",
                                        "query": query,
                                    }
                                }
                            }
                        },
                    ],
                    "rank_window_size": 50,
                    "rank_constant": 20,
                }
            },
            "size": TOP_K,
            "_source": ["title"],
        },
    )
    return [h["_source"]["title"] for h in result["hits"]["hits"]]


@pytest.mark.parametrize("query,expected", RETRIEVAL_CASES)
def test_retrieval(query, expected):
    titles = search(query)
    assert any(expected.lower() in t.lower() for t in titles), (
        f"Expected '{expected}' in top {TOP_K} results for query '{query}'\n"
        f"Got: {titles}"
    )
