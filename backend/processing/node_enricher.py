"""LLM batch enrichment — adds summary, keywords, and node_id to heading nodes."""

import json
import time

from langsmith import traceable

from backend.config import (
    ENRICH_BACKOFF_MAX_SECONDS,
    ENRICH_MAX_ATTEMPTS,
    ENRICH_MAX_BATCH_TOKENS,
    ENRICH_MAX_OUTPUT_TOKENS,
    ENRICH_MODEL,
    ENRICHMENT_RESPONSE_FORMAT,
    LLM_REASONING_EFFORT,
    LLM_TEMPERATURE_DETERMINISTIC,
)
from backend.core.llm import get_client
from backend.prompts.enrichment import (
    generate_enrichment_batch_prompt,
    generate_enrichment_continuation_prompt,
)
from backend.utils.node_utils import NODE_ID_PATTERN


def _chunk_nodes_by_tokens(nodes: list[dict]) -> list[list[dict]]:
    """Group consecutive nodes until their combined token count reaches the limit."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
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


def _parent_node_id(node_id: str) -> str | None:
    """Parent of a dotted id — "4.2.1" -> "4.2", "4" -> None."""
    dot = node_id.rfind(".")
    return node_id[:dot] if dot != -1 else None


def _enrich_chunk(
    chunk: list[dict],
    client,
    context_node: dict | None = None,
    parent_node: dict | None = None,
) -> list[dict]:
    """One LLM call for a batch of nodes → [{summary, keywords, node_id}, …].

    Each input section carries its seq_id; the model echoes it back, and results
    are matched to nodes by seq_id (not list position), so a dropped or reordered
    item never shifts the enrichment of the rest. The returned list is aligned to
    the input chunk order.

    context_node / parent_node give the previous batch's last node and that node's
    parent, so the model can continue the node_id hierarchy accurately.
    """
    # Fall back to the local index if a node predates seq_id (legacy node files).
    seq_ids = [n.get("seq_id", idx) for idx, n in enumerate(chunk)]
    # Send sections as delimited blocks rather than a JSON array: the large
    # markdown content stays verbatim (no escaping), which is cheaper in tokens
    # and easier for the model to read. Output is still JSON (schema-enforced).
    sections_text = "\n\n".join(
        f"=== SECTION seq_id={sid} ===\n"
        f"HEADING: {n['heading']}\n"
        f"CONTENT:\n{n['content']}"
        for sid, n in zip(seq_ids, chunk)
    )

    if context_node is not None:
        previous_context: dict = {"last_node": context_node}
        if parent_node is not None:
            previous_context["parent_node"] = parent_node
        context_json = json.dumps(previous_context, ensure_ascii=False)
        prompt = generate_enrichment_continuation_prompt(sections_text, context_json, len(chunk))
    else:
        prompt = generate_enrichment_batch_prompt(sections_text, len(chunk))

    for attempt in range(1, ENRICH_MAX_ATTEMPTS + 1):
        try:
            kwargs = dict(
                model=ENRICH_MODEL,
                temperature=LLM_TEMPERATURE_DETERMINISTIC,
                max_tokens=ENRICH_MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                # gpt-oss requires reasoning (it can't be disabled), so keep it
                # at low effort — minimal thinking tokens leave the output budget
                # for the JSON answer.
                extra_body={"reasoning": {"effort": LLM_REASONING_EFFORT}},
            )
            # Attempt 1 enforces the JSON schema; later attempts drop it as a
            # fallback in case the route rejects response_format.
            if attempt == 1:
                kwargs["response_format"] = ENRICHMENT_RESPONSE_FORMAT

            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("Model returned no answer content.")
            parsed = json.loads(content.strip())
            # Schema wraps the list under "sections"; tolerate a bare list too.
            items = parsed.get("sections") if isinstance(parsed, dict) else parsed
            if not isinstance(items, list):
                raise ValueError(f"Expected a JSON array, got {type(items).__name__}.")

            # Match each result back to its node by seq_id (coerce to int so a
            # stringified "3" still matches the integer 3).
            by_seq: dict[int, dict] = {}
            for item in items:
                if isinstance(item, dict) and "seq_id" in item:
                    try:
                        by_seq[int(item["seq_id"])] = item
                    except (TypeError, ValueError):
                        continue

            missing = [sid for sid in seq_ids if sid not in by_seq]
            if missing:
                raise ValueError(f"Response is missing seq_ids {missing}")

            return [
                {
                    "summary":  (by_seq[sid].get("summary") or "").strip() or "No summary available.",
                    "keywords": [
                        k.strip()
                        for k in by_seq[sid].get("keywords", [])
                        if isinstance(k, str) and k.strip()
                    ],
                    "node_id": _parse_node_id(
                        by_seq[sid].get("node_id"),
                        fallback=str(sid),
                    ),
                }
                for sid in seq_ids
            ]
        except Exception as exc:
            print(f"  Warning: enrichment attempt {attempt} failed: {exc}")
            # The daily free quota is exhausted — retrying today is pointless,
            # so bail straight to the fallback instead of burning attempts.
            if "per-day" in str(exc):
                break
            # Per-minute / transient 429s clear quickly — back off and retry.
            if attempt < ENRICH_MAX_ATTEMPTS:
                time.sleep(min(5 * attempt, ENRICH_BACKOFF_MAX_SECONDS))

    # Fallback — heading as summary, empty keywords, seq_id as a flat node_id
    return [
        {
            "summary":  n["heading"],
            "keywords": [],
            "node_id":  str(sid),
        }
        for sid, n in zip(seq_ids, chunk)
    ]


@traceable(run_type="chain", name="Pipeline · enrich_nodes")
def enrich_nodes(nodes: list[dict]) -> list[dict]:
    """Add summary, keywords, and node_id to every heading node via LLM."""
    client  = get_client()
    chunks  = _chunk_nodes_by_tokens(nodes)
    print(f"Enriching {len(nodes)} nodes in {len(chunks)} batch(es)...")

    enriched: list[dict]      = []
    context_node: dict | None = None
    parent_node: dict | None  = None
    # node_id -> {heading, node_id, summary} for every node enriched so far,
    # used to look up the last node's parent for continuation context.
    id_to_context: dict[str, dict] = {}

    for i, chunk in enumerate(chunks, start=1):
        tok = sum(n["token_count"] for n in chunk)
        print(f"  Batch {i}/{len(chunks)}: {len(chunk)} nodes, {tok} tokens")

        results = _enrich_chunk(chunk, client, context_node=context_node, parent_node=parent_node)
        enriched.extend(results)

        for node, e in zip(chunk, results):
            id_to_context[e["node_id"]] = {
                "heading": node["heading"],
                "node_id": e["node_id"],
                "summary": e["summary"],
            }

        context_node = {
            "heading": chunk[-1]["heading"],
            "node_id": results[-1]["node_id"],
            "summary": results[-1]["summary"],
        }
        parent_id   = _parent_node_id(context_node["node_id"])
        parent_node = id_to_context.get(parent_id) if parent_id else None

    for node, e in zip(nodes, enriched):
        node["node_id"] = e["node_id"]
        node["summary"]  = e["summary"]
        node["keywords"] = e["keywords"]

    return nodes
