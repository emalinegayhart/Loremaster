"""
normalizer.py

Takes a raw page dict and the cleaned wikitext, and produces a
final normalized document ready for Elasticsearch indexing.
"""

import re
from datetime import datetime, timezone


# Maps category keywords to page types.
# Order matters — first match wins.
PAGE_TYPE_RULES = [
    (["npc", "mob", "creature", "boss"],            "npc"),
    (["item", "weapon", "armor", "equipment"],       "item"),
    (["quest"],                                      "quest"),
    (["spell", "ability", "talent"],                 "spell"),
    (["zone", "area", "dungeon", "raid", "region"],  "zone"),
    (["character", "person", "hero", "villain"],     "character"),
    (["race"],                                       "race"),
    (["class"],                                      "class"),
    (["faction"],                                    "faction"),
    (["lore", "history", "novel", "comic"],          "lore"),
]


def detect_page_type(title: str, categories: list[str]) -> str:
    """
    Infer the page type from its categories (and title as a fallback).
    Returns a lowercase string like "npc", "item", "quest", etc.
    """
    # Combine categories and title into one blob of text to check against
    haystack = " ".join(categories + [title]).lower()

    for keywords, page_type in PAGE_TYPE_RULES:
        if any(kw in haystack for kw in keywords):
            return page_type

    return "general"


def build_summary(text: str, max_chars: int = 500) -> str:
    """
    Extract the first paragraph of cleaned text as a summary.
    Strips to the nearest sentence boundary within max_chars.
    """
    if not text:
        return ""

    # Take the first non-empty paragraph
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return ""

    summary = paragraphs[0]

    if len(summary) <= max_chars:
        return summary

    # Truncate to the nearest sentence end within max_chars
    truncated = summary[:max_chars]
    last_period = truncated.rfind(".")
    if last_period > max_chars // 2:
        return truncated[: last_period + 1]

    return truncated.rstrip() + "…"


def normalize_categories(categories: list[str]) -> list[str]:
    """Lowercase and deduplicate categories."""
    seen = set()
    result = []
    for cat in categories:
        normalized = cat.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def count_words(text: str) -> int:
    """Simple word count."""
    return len(text.split()) if text else 0


def parse_timestamp(ts: str) -> str | None:
    """
    Parse a MediaWiki timestamp (ISO 8601) and return it in a format
    Elasticsearch accepts. Returns None if parsing fails.
    """
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def build_document(raw: dict, clean_text: str, infobox: dict) -> dict:
    """
    Combine the raw scraped data, cleaned text, and extracted infobox
    into a final document ready for Elasticsearch.

    Args:
        raw:        The raw page dict as scraped by the Go scraper
        clean_text: Plain text produced by wikitext.clean_wikitext()
        infobox:    Key-value dict from wikitext.extract_infobox()

    Returns:
        A flat dict matching the Elasticsearch index mapping
    """
    categories = normalize_categories(raw.get("categories", []))
    title = raw.get("title", "")

    return {
        "page_id":       str(raw.get("page_id", "")),
        "title":         title,
        "url":           raw.get("url", ""),
        "page_type":     detect_page_type(title, categories),
        "categories":    categories,
        "content":       clean_text,
        "summary":       build_summary(clean_text),
        "infobox":       infobox,
        "last_modified": parse_timestamp(raw.get("last_modified")),
        "word_count":    count_words(clean_text),
        "links":         raw.get("links", []),
        "is_redirect":   raw.get("is_redirect", False),
    }
