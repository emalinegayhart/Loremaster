"""
Re-indexes all articles through the ELSER inference pipeline to populate
the content_sparse field for hybrid search.

Run after setup_elser.py has been executed. The job runs asynchronously
on Elasticsearch and progress is polled every 30 seconds.
"""
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from elasticsearch import Elasticsearch
from config import ES_ENDPOINT, ES_API_KEY, ES_INDEX

es = Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)

PIPELINE_ID = "elser-sparse-embedding"
POLL_INTERVAL = 30


def reindex():
    total = es.count(index=ES_INDEX)["count"]
    print(f"Total articles: {total}")
    print("Starting update_by_query with ELSER pipeline (runs async on ES)...")

    resp = es.update_by_query(
        index=ES_INDEX,
        pipeline=PIPELINE_ID,
        body={"query": {"bool": {"must_not": {"exists": {"field": "content_sparse"}}}}},
        wait_for_completion=False,
    )

    task_id = resp["task"]
    print(f"Task ID: {task_id}")
    print(f"Polling every {POLL_INTERVAL}s...\n")

    while True:
        task = es.tasks.get(task_id=task_id)
        status   = task["task"]["status"]
        updated  = status.get("updated", 0)
        failures = len(task.get("response", {}).get("failures", []))

        pct = (updated / total * 100) if total else 0
        print(f"Progress: {updated}/{total} ({pct:.1f}%) -- failures: {failures}")

        if task["completed"]:
            print(f"\nDone. {updated} articles re-indexed, {failures} failures.")
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    reindex()
