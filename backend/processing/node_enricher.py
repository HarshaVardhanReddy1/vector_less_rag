"""LLM batch enrichment — adds summary, keywords, and node_id to heading nodes."""

import json

from backend.config import ENRICH_MAX_BATCH_TOKENS, ENRICH_MODEL
from backend.core.llm import get_client
from backend.prompts.enrichment import (
    generate_enrichment_batch_prompt,
    generate_enrichment_continuation_prompt,
)
from backend.utils.node_utils import NODE_ID_PATTERN


def _chunk_nodes_by_tokens(nodes: list[dict]) -> list[list[dict]]:
    """Group consecutive nodes until their combined token count reaches the limit."""
    chunks: list[list[dict]] = []
    current: list[dict]      = []
    total = 0

    for node in nodes:
        t = node["token_count"]
        if current and total + t > ENRICH_MAX_BATCH_TOKENS:
            chunks.append(current)
            current, total = [node], t
        else:
            current.append(node)
            total += t

    if current:
        chunks.append(current)

    return chunks


def _parse_node_id(raw, fallback: str) -> str:
    """Return raw if it's a valid dotted numeric ID, else return fallback."""
    value = str(raw).strip() if raw is not None else ""
    return value if NODE_ID_PATTERN.fullmatch(value) else fallback


def _enrich_chunk(
    chunk: list[dict],
    client,
    context_node: dict | None = None,
    seq_offset: int = 0,
) -> list[dict]:
    """One LLM call for a batch of nodes → [{summary, keywords, node_id}, …].

    Each input node carries a ``_seq_id`` integer sent as ``seq_id``. The LLM
    echoes it back so results are matched by ID rather than by position.
    """
    expected_ids = [n["_seq_id"] for n in chunk]

    batch_input = [
        {
            "seq_id":  n["_seq_id"],
            "heading": n["heading"],
            "content": n["content"],
        }
        for n in chunk
    ]
    batch_json = json.dumps(batch_input, ensure_ascii=False, indent=2)

    if context_node is not None:
        context_json = json.dumps(
            {
                "heading": context_node["heading"],
                "node_id": context_node["node_id"],
                "summary": context_node["summary"],
            },
            ensure_ascii=False,
        )
        prompt = generate_enrichment_continuation_prompt(batch_json, context_json, len(chunk))
    else:
        prompt = generate_enrichment_batch_prompt(batch_json, len(chunk))

    for attempt in range(1, 3):
        try:
            resp = client.chat.completions.create(
                model=ENRICH_MODEL,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            parsed = json.loads(resp.choices[0].message.content.strip())
            if not isinstance(parsed, list) or len(parsed) != len(chunk):
                raise ValueError(
                    f"Expected list of {len(chunk)}, got "
                    f"{type(parsed).__name__} of length "
                    f"{len(parsed) if isinstance(parsed, list) else '?'}"
                )
            returned_ids = [item.get("seq_id") for item in parsed]
            if returned_ids != expected_ids:
                raise ValueError(
                    f"seq_id mismatch — expected {expected_ids}, got {returned_ids}"
                )
            result_map = {item["seq_id"]: item for item in parsed}
            return [
                {
                    "summary":  (result_map[n["_seq_id"]].get("summary") or "").strip() or "No summary available.",
                    "keywords": [
                        k.strip()
                        for k in result_map[n["_seq_id"]].get("keywords", [])
                        if isinstance(k, str) and k.strip()
                    ],
                    "node_id": _parse_node_id(
                        result_map[n["_seq_id"]].get("node_id"),
                        fallback=str(seq_offset + i),
                    ),
                }
                for i, n in enumerate(chunk, start=1)
            ]
        except Exception as exc:
            print(f"  Warning: enrichment attempt {attempt} failed: {exc}")

    # Fallback — heading as summary, empty keywords, sequential flat IDs
    return [
        {
            "summary":  n["heading"],
            "keywords": [],
            "node_id":  str(seq_offset + i),
        }
        for i, n in enumerate(chunk, start=1)
    ]


def enrich_nodes(nodes: list[dict]) -> list[dict]:
    """Add summary, keywords, and node_id to every heading node via LLM.

    Stamps a sequential _seq_id (1-based) onto each node before batching so
    the LLM can echo IDs back and results are matched by ID, not by position.
    The temporary _seq_id field is removed before returning.
    """
    for i, node in enumerate(nodes, start=1):
        node["_seq_id"] = i

    client  = get_client()
    chunks  = _chunk_nodes_by_tokens(nodes)
    print(f"Enriching {len(nodes)} nodes in {len(chunks)} batch(es)...")

    enriched: list[dict]      = []
    context_node: dict | None = None
    processed = 0

    for i, chunk in enumerate(chunks, start=1):
        tok = sum(n["token_count"] for n in chunk)
        print(f"  Batch {i}/{len(chunks)}: {len(chunk)} nodes, {tok} tokens")

        results = _enrich_chunk(chunk, client, context_node=context_node, seq_offset=processed)
        enriched.extend(results)
        processed += len(chunk)

        context_node = {
            "heading": chunk[-1]["heading"],
            "node_id": results[-1]["node_id"],
            "summary": results[-1]["summary"],
        }

    for node, e in zip(nodes, enriched):
        node["node_id"] = e["node_id"]
        node["summary"]  = e["summary"]
        node["keywords"] = e["keywords"]
        node.pop("_seq_id", None)

    return nodes
