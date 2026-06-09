"""Node chunker — splits oversized nodes into smaller child nodes.

Large nodes hurt retrieval precision. This module splits any node whose token_count
exceeds max_tokens into chunks at safe boundaries:

  - Markdown tables (lines starting with '|') are treated as atomic units.
  - IMAGE_CONTEXT blocks are treated as atomic units.
  - Everything else is split at paragraph boundaries (\n\n).

The first chunk stays in the parent node; subsequent chunks become children named
"{heading} -2", "{heading} -3", etc.
"""

import re

from backend.config import CHUNK_MAX_TOKENS
from backend.utils.token_utils import count_tokens

# Matches a full IMAGE_CONTEXT block including its content (capturing group so
# re.split preserves the block in the result list at odd indices).
_IMAGE_CONTEXT_RE = re.compile(
    r"(<IMAGE_CONTEXT[^>]*>.*?</IMAGE_CONTEXT>)",
    re.DOTALL,
)

# A line that is part of a markdown table starts with optional whitespace then '|'.
_TABLE_LINE_RE = re.compile(r"^[ \t]*\|", re.MULTILINE)


def _extract_table_segments(text: str) -> list[tuple[str, bool]]:
    """Split plain text into (segment_text, is_table) pairs.

    Consecutive lines that start with '|' form one atomic table segment.
    All other lines form prose segments that can later be split into paragraphs.
    """
    lines = text.splitlines(keepends=True)
    segments: list[tuple[str, bool]] = []
    current: list[str] = []
    in_table: bool | None = None

    for line in lines:
        is_tl = bool(_TABLE_LINE_RE.match(line))
        if in_table is None:
            in_table = is_tl
            current = [line]
        elif is_tl == in_table:
            current.append(line)
        else:
            seg = "".join(current)
            if seg.strip():
                segments.append((seg, in_table))
            current = [line]
            in_table = is_tl

    if current:
        seg = "".join(current)
        if seg.strip():
            segments.append((seg, in_table or False))

    return segments


def _content_to_atoms(content: str) -> list[str]:
    """Break content into the smallest indivisible units for chunk accumulation.

    Processing order:
      1. IMAGE_CONTEXT blocks  → kept whole
      2. Markdown table rows   → kept whole
      3. Prose paragraphs      → split on blank lines
    """
    atoms: list[str] = []

    # re.split with a capturing group → odd-indexed parts are the captured blocks
    parts = _IMAGE_CONTEXT_RE.split(content)
    for i, part in enumerate(parts):
        if not part.strip():
            continue
        if i % 2 == 1:
            # Captured IMAGE_CONTEXT block — atomic
            atoms.append(part.strip())
        else:
            # Plain text — detect tables, then split prose into paragraphs
            for seg_text, is_table in _extract_table_segments(part):
                if is_table:
                    atoms.append(seg_text.strip())
                else:
                    for para in seg_text.split("\n\n"):
                        para = para.strip()
                        if para:
                            atoms.append(para)

    return atoms


def _split_into_chunks(content: str, max_tokens: int) -> list[str]:
    """Split content into chunks of up to max_tokens.

    Atomic units (tables, IMAGE_CONTEXT blocks) are never broken. If a single
    atomic unit exceeds max_tokens it forms its own oversized chunk — it cannot
    be split further without losing meaning.
    """
    atoms = _content_to_atoms(content)
    if not atoms:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for atom in atoms:
        atom_tokens = count_tokens(atom)
        if current and current_tokens + atom_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            current = [atom]
            current_tokens = atom_tokens
        else:
            current.append(atom)
            current_tokens += atom_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_nodes(nodes: list[dict], max_tokens: int = CHUNK_MAX_TOKENS) -> list[dict]:
    """Return a flat list where every node exceeding max_tokens is split into chunks.

    The parent node keeps the first chunk as its content.
    Remaining chunks are inserted immediately after as sibling nodes named
    "{original heading} -2", "{original heading} -3", ...

    Nodes at or under max_tokens are passed through unchanged.
    """
    result: list[dict] = []

    for node in nodes:
        if node["token_count"] <= max_tokens:
            result.append(node)
            continue

        chunks = _split_into_chunks(node["content"], max_tokens)

        if len(chunks) <= 1:
            result.append(node)
            continue

        # First chunk → parent keeps it
        parent = dict(node)
        parent["content"] = chunks[0]
        parent["token_count"] = count_tokens(chunks[0])
        result.append(parent)

        # Remaining chunks → child nodes
        for i, chunk_text in enumerate(chunks[1:], start=2):
            result.append({
                "heading":     f"{node['heading']} -{i}",
                "page":        node["page"],
                "content":     chunk_text,
                "token_count": count_tokens(chunk_text),
            })

    return result
