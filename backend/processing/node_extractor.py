"""Markdown → flat heading nodes.

Splits enriched markdown into one node per heading section. Each node carries
the heading text, the page it first appeared on, the section content, and a
tiktoken token count of that content.
"""

import re

import tiktoken


_HEADING_RE       = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
_IMAGE_CONTEXT_RE = re.compile(r"<IMAGE_CONTEXT[^>]*>.*?</IMAGE_CONTEXT>", re.DOTALL)


def _get_encoder():
    try:
        return tiktoken.encoding_for_model("gpt-4o")
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def extract_heading_nodes(
    full_md: str,
    heading_page_map: dict[str, int],
) -> list[dict]:
    """Split enriched markdown into flat heading-based nodes.

    Each node:
        heading     — cleaned heading text (no ``#`` or ``**``)
        page        — PDF page where this heading first appeared (1-indexed)
        content     — text between this heading and the next
        token_count — tiktoken count of the content string

    Headings inside IMAGE_CONTEXT blocks are skipped — they belong to VLM
    descriptions, not to document section headings.
    """
    encoder = _get_encoder()

    image_block_ranges = [
        (m.start(), m.end()) for m in _IMAGE_CONTEXT_RE.finditer(full_md)
    ]

    def _inside_image_block(pos: int) -> bool:
        return any(start <= pos < end for start, end in image_block_ranges)

    heading_matches = [
        hm for hm in _HEADING_RE.finditer(full_md)
        if not _inside_image_block(hm.start())
    ]

    nodes: list[dict] = []
    for i, hm in enumerate(heading_matches):
        heading_text  = re.sub(r"\*+", "", hm.group(2))
        heading_text  = re.sub(r"(?<!\w)_+|_+(?!\w)", "", heading_text).strip()
        content_start = hm.end()
        content_end   = (
            heading_matches[i + 1].start()
            if i + 1 < len(heading_matches)
            else len(full_md)
        )
        content = full_md[content_start:content_end].strip()

        nodes.append({
            "heading":     heading_text,
            "page":        heading_page_map.get(heading_text, 1),
            "content":     content,
            "token_count": len(encoder.encode(content)),
        })

    return nodes
