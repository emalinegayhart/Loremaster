"""
clean.py — Entry point for the cleaning pipeline.

Reads raw JSONL from the Go scraper, cleans each page, and writes
clean JSONL ready for Elasticsearch indexing.

Usage:
    python cleaner/clean.py
    python cleaner/clean.py --input data/raw/pages.jsonl --output data/clean/pages.jsonl
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from wikitext import clean_wikitext, extract_infobox
from normalizer import build_document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def clean_file(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = skipped = errors = 0

    with input_path.open("r", encoding="utf-8") as infile, \
         output_path.open("w", encoding="utf-8") as outfile:

        for line_num, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                continue

            # ── Parse raw JSON ──────────────────────────────────────────────
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("Line %d: invalid JSON — %s", line_num, e)
                errors += 1
                continue

            # ── Skip redirects — they have no real content ──────────────────
            if raw.get("is_redirect"):
                skipped += 1
                continue

            # ── Skip pages with no wikitext ─────────────────────────────────
            wikitext = raw.get("wikitext", "")
            if not wikitext:
                skipped += 1
                continue

            # ── Clean + extract ─────────────────────────────────────────────
            try:
                clean_text = clean_wikitext(wikitext)
                infobox    = extract_infobox(wikitext)
                document   = build_document(raw, clean_text, infobox)
            except Exception as e:
                log.warning(
                    "Line %d: failed to clean page '%s' — %s",
                    line_num, raw.get("title", "?"), e
                )
                errors += 1
                continue

            # ── Skip pages that are empty after cleaning ────────────────────
            if not document["content"].strip():
                skipped += 1
                continue

            # ── Write clean document ────────────────────────────────────────
            outfile.write(json.dumps(document, ensure_ascii=False) + "\n")
            total += 1

            if total % 500 == 0:
                log.info("Cleaned %d pages so far...", total)

    log.info("━━━ Done ━━━")
    log.info("  Cleaned : %d pages", total)
    log.info("  Skipped : %d pages (redirects / empty)", skipped)
    log.info("  Errors  : %d pages", errors)
    log.info("  Output  : %s", output_path)


def main():
    parser = argparse.ArgumentParser(description="Clean raw Wowpedia JSONL for Elasticsearch")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/pages.jsonl"),
        help="Path to raw JSONL file from Go scraper",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/clean/pages.jsonl"),
        help="Path to write clean JSONL output",
    )
    args = parser.parse_args()

    if not args.input.exists():
        log.error("Input file not found: %s", args.input)
        log.error("Run the Go scraper first: cd go-scraper && go run .")
        sys.exit(1)

    log.info("Input  → %s", args.input)
    log.info("Output → %s", args.output)

    clean_file(args.input, args.output)


if __name__ == "__main__":
    main()
