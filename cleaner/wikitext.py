"""
wikitext.py

Converts raw MediaWiki wikitext into clean plain text using mwparserfromhell.
Also extracts structured infobox data as a dictionary.
"""

import re
import mwparserfromhell


def clean_wikitext(raw: str) -> str:
    """
    Convert raw wikitext to clean plain text.

    Steps:
      1. Parse with mwparserfromhell (handles nested templates, links, etc.)
      2. Strip all template markup  {{...}}
      3. Convert [[Link|Display]] → Display text
      4. Remove section headers
      5. Collapse whitespace
    """
    if not raw:
        return ""

    try:
        wikicode = mwparserfromhell.parse(raw)
    except Exception:
        # Fallback to regex-based cleaning if the parser chokes on malformed wikitext
        return _regex_fallback(raw)

    # Strip all templates (infoboxes, navboxes, etc.)
    # We extract infobox data separately in extract_infobox()
    for template in wikicode.filter_templates():
        try:
            wikicode.remove(template)
        except Exception:
            pass

    # Get plain text — this handles [[links]], bold/italic markers, etc.
    text = wikicode.strip_code(
        normalize=True,
        collapse=True,
        keep_template_params=False,
    )

    # Clean up remaining artifacts
    text = _post_process(text)
    return text


def extract_infobox(raw: str) -> dict:
    """
    Extract key-value pairs from the first infobox template found in the wikitext.

    Returns a flat dict like:
      {"name": "Arthas Menethil", "race": "Human / Undead", "level": "??"}

    Returns an empty dict if no infobox is found.
    """
    if not raw:
        return {}

    try:
        wikicode = mwparserfromhell.parse(raw)
    except Exception:
        return {}

    for template in wikicode.filter_templates():
        name = template.name.strip().lower()
        # Infobox templates on Wowpedia have names like "npcbox", "itembox", "questbox", etc.
        if any(keyword in name for keyword in ("box", "infobox", "tooltip")):
            return _parse_template_params(template)

    return {}


def _parse_template_params(template) -> dict:
    """Convert a mwparserfromhell Template's params to a clean dict."""
    result = {}
    for param in template.params:
        key = str(param.name).strip()
        value = str(param.value).strip()

        # Recursively clean the value (it might contain nested wikitext)
        try:
            value_parsed = mwparserfromhell.parse(value)
            value = value_parsed.strip_code(normalize=True, collapse=True).strip()
        except Exception:
            pass

        # Skip empty values
        if key and value:
            result[key] = value

    return result


def _post_process(text: str) -> str:
    """Final cleanup of text after wikitext stripping."""

    # Remove section header markup (== Header ==)
    text = re.sub(r"={2,}[^=]+=={2,}", "", text)

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Remove <ref> citation tags and their contents
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/?>", "", text)

    # Remove any remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    text = (
        text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&nbsp;", " ")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
    )

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def _regex_fallback(raw: str) -> str:
    """
    Simple regex-based wikitext cleaner used when mwparserfromhell fails.
    Less accurate but better than returning raw wikitext.
    """
    text = raw
    # Remove templates
    text = re.sub(r"\{\{[^}]*\}\}", "", text, flags=re.DOTALL)
    # Convert links [[X|Y]] → Y, [[X]] → X
    text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)
    # Remove external links
    text = re.sub(r"\[https?://\S+ ([^\]]+)\]", r"\1", text)
    # Remove bold/italic markers
    text = re.sub(r"'{2,3}", "", text)
    return _post_process(text)
