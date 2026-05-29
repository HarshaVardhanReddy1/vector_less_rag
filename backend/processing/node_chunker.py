"""Paragraph-based node chunker — splits oversized nodes into smaller child nodes.

Large nodes hurt retrieval precision because the LLM must work with a blob of text.
This module splits any node whose token_count exceeds max_tokens into paragraph-based
chunks. The first chunk stays in the parent; subsequent chunks become children named
"{heading} -2", "{heading} -3", etc.
"""

from backend.utils.token_utils import count_tokens

_DEFAULT_MAX_TOKENS = 1000


def _split_into_chunks(content: str, max_tokens: int) -> list[str]:
    """Split content on paragraph boundaries, accumulating up to max_tokens per chunk."""
    paragraphs = [p for p in content.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)
        if current and current_tokens + para_tokens > max_tokens:
            chunks.append("\n\n".join(current))
            current = [para]
            current_tokens = para_tokens
        else:
            current.append(para)
            current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_nodes(nodes: list[dict], max_tokens: int = _DEFAULT_MAX_TOKENS) -> list[dict]:
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
