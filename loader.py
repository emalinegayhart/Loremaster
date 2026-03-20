import argparse
import json
import logging
from pathlib import Path

import psycopg2
import psycopg2.extras
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

from config import (
    NEON_CONNECTION_STRING,
    ES_ENDPOINT,
    ES_API_KEY,
    ES_INDEX,
    CLEAN_JSONL,
    PG_BATCH_SIZE,
    ES_BATCH_SIZE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def create_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id            SERIAL PRIMARY KEY,
                page_id       TEXT UNIQUE NOT NULL,
                title         TEXT NOT NULL,
                url           TEXT NOT NULL,
                summary       TEXT,
                content       TEXT,
                last_modified TIMESTAMPTZ,
                created_at    TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_pages_page_id ON pages(page_id);
            CREATE INDEX IF NOT EXISTS idx_pages_title   ON pages(title);
        """)
    conn.commit()
    log.info("Schema ready")


def load_postgres(jsonl_path: Path):
    log.info("Connecting to Neon...")
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    create_schema(conn)

    total = inserted = skipped = 0
    batch = []

    def flush(batch, conn):
        if not batch:
            return 0
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO pages (page_id, title, url, summary, content, last_modified)
                VALUES %s
                ON CONFLICT (page_id) DO UPDATE SET
                    title         = EXCLUDED.title,
                    url           = EXCLUDED.url,
                    summary       = EXCLUDED.summary,
                    content       = EXCLUDED.content,
                    last_modified = EXCLUDED.last_modified
                """,
                batch,
                template="(%s, %s, %s, %s, %s, %s)",
            )
        conn.commit()
        return len(batch)

    log.info("Loading into Postgres...")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Postgres", unit="pages"):
            line = line.strip()
            if not line:
                continue

            doc = json.loads(line)

            if not doc.get("content", "").strip():
                skipped += 1
                continue

            batch.append((
                doc["page_id"],
                doc["title"],
                doc["url"],
                doc.get("summary") or "",
                doc.get("content") or "",
                doc.get("last_modified"),
            ))
            total += 1

            if len(batch) >= PG_BATCH_SIZE:
                inserted += flush(batch, conn)
                batch = []

    inserted += flush(batch, conn)
    conn.close()

    log.info("━━━ Postgres done ━━━")
    log.info("  Inserted/updated : %d", inserted)
    log.info("  Skipped          : %d", skipped)


ES_MAPPING = {
    "mappings": {
        "properties": {
            "page_id":       {"type": "keyword"},
            "title":         {
                "type": "text",
                "analyzer": "english",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "url":           {"type": "keyword"},
            "summary":       {"type": "text", "analyzer": "english"},
            "content":       {"type": "text", "analyzer": "english"},
            "last_modified": {"type": "date"},
        }
    },
    "settings": {
        "analysis": {
            "analyzer": {
                "english": {"type": "english"}
            }
        }
    }
}


def get_es_client():
    return Elasticsearch(ES_ENDPOINT, api_key=ES_API_KEY)


def create_es_index(es: Elasticsearch):
    if es.indices.exists(index=ES_INDEX):
        log.info("ES index '%s' already exists", ES_INDEX)
        return
    es.indices.create(index=ES_INDEX, body=ES_MAPPING)
    log.info("Created ES index '%s'", ES_INDEX)


def load_elasticsearch_from_postgres():
    log.info("Connecting to Elasticsearch...")
    es = get_es_client()
    create_es_index(es)

    log.info("Connecting to Neon...")
    conn = psycopg2.connect(NEON_CONNECTION_STRING)

    def generate_docs(conn):
        with conn.cursor(name="es_cursor", cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.itersize = ES_BATCH_SIZE
            cur.execute("SELECT page_id, title, url, summary, content, last_modified FROM pages")
            for row in cur:
                yield {
                    "_index": ES_INDEX,
                    "_id":    row["page_id"],
                    "_source": {
                        "page_id":       row["page_id"],
                        "title":         row["title"],
                        "url":           row["url"],
                        "summary":       row["summary"],
                        "content":       row["content"],
                        "last_modified": row["last_modified"].isoformat() if row["last_modified"] else None,
                    }
                }

    log.info("Bulk indexing into Elasticsearch...")
    success, errors = helpers.bulk(
        es,
        generate_docs(conn),
        chunk_size=ES_BATCH_SIZE,
        raise_on_error=False,
    )

    conn.close()

    log.info("━━━ Elasticsearch done ━━━")
    log.info("  Indexed : %d", success)
    if errors:
        log.warning("  Errors  : %d", len(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-only", action="store_true")
    parser.add_argument("--es-only", action="store_true")
    parser.add_argument("--input", type=Path, default=Path(CLEAN_JSONL))
    args = parser.parse_args()

    if args.es_only:
        load_elasticsearch_from_postgres()
        return

    if args.pg_only:
        load_postgres(args.input)
        return

    load_postgres(args.input)
    load_elasticsearch_from_postgres()


if __name__ == "__main__":
    main()
