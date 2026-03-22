"""
Sets up the ELSER inference pipeline and updates the ES index mapping
to add a sparse_vector field for hybrid search.

Run once after upgrading to a paid Elastic Cloud tier with ELSER available.
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elasticsearch import Elasticsearch
from config import ES_ENDPOINT, ES_API_KEY, ES_INDEX

es = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

PIPELINE_ID = "elser-sparse-embedding"


def create_pipeline():
    print("Creating ELSER inference pipeline...")
    es.ingest.put_pipeline(
        id=PIPELINE_ID,
        body={
            "description": "ELSER sparse embedding pipeline for hybrid search",
            "processors": [
                {
                    "inference": {
                        "model_id": ".elser_model_2_linux-x86_64",
                        "input_output": [
                            {
                                "input_field": "content",
                                "output_field": "content_sparse",
                            }
                        ],
                    }
                }
            ],
        },
    )
    print(f"Pipeline '{PIPELINE_ID}' created.")


def update_mapping():
    print("Updating index mapping to add sparse_vector field...")
    es.indices.put_mapping(
        index=ES_INDEX,
        body={
            "properties": {
                "content_sparse": {
                    "type": "sparse_vector",
                }
            }
        },
    )
    print("Mapping updated.")


if __name__ == "__main__":
    create_pipeline()
    update_mapping()
    print("\nDone. Run scripts/reindex_elser.py to populate sparse vectors.")
