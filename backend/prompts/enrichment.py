def generate_enrichment_batch_prompt(batch_json: str, section_count: int) -> str:
    return f"""\
You are a document structure analyzer.

Each section in <INPUT> has a "seq_id" integer. For EACH section generate:

"seq_id"   — Copy the seq_id from the input exactly. Do NOT change or omit it.

"summary"  — Complete summary of ALL content. Include every topic, feature, and detail present.
             Do NOT omit anything. If the section spans multiple topics, cover all of them.

"keywords" — 5–10 short phrases drawn from the FULL content (not just the heading).
             Every distinct concept, feature, or topic in the content must appear in keywords.

"node_id"  — Hierarchical dotted ID reflecting this section's position in the document structure.

  Examples:
    1         → first top-level section
    1.1       → first child of section 1
    1.1.1     → first child of section 1.1
    2         → second top-level section
    2.1       → first child of section 2

  Rules:
  • Main sections        → 1, 2, 3 ...
  • Child sections       → 1.1, 1.2, 1.3 ...
  • Nested child sections → 1.1.1, 1.1.2 ...
  • Maintain proper sequential numbering — siblings are numbered 1, 2, 3 in order.
  • Never skip levels — 1.1.1 requires 1.1 to exist.
  • Never generate duplicate node_ids — every section must have a unique ID.
  • Parallel headings (same depth, same pattern) get sibling IDs at the same level.
  • A heading that is a sub-topic of the one before it gets a child ID (one dot deeper).
  • Paragraph chunk nodes: a heading ending with ' -2', ' -3', ' -4', … is a continuation
    chunk of the immediately preceding node whose heading is the same text without the suffix.
    The parent holds chunk 1 (no suffix). Assign chunk nodes as numerical children of that parent.
    Example: parent "Background" → node_id "2"; "Background -2" → "2.1"; "Background -3" → "2.2".

━━━ FORMAT RULES ━━━

- <INPUT> below contains exactly {section_count} sections.
- Output MUST be a JSON array of exactly {section_count} objects — one per section, in input order.
- Each object: "seq_id" (integer, copied from input), "summary" (non-empty string), "keywords" (non-empty list), "node_id" (dotted numeric string like "1" or "2.3.1").
- Return ONLY valid JSON — no markdown fences, no extra text.

<INPUT>
{batch_json}
</INPUT>

Output:
[
  {{"seq_id": 1, "summary": "...", "keywords": ["...", "..."], "node_id": "1"}},
  ...
]
"""


def generate_enrichment_continuation_prompt(
    batch_json: str,
    context_node_json: str,
    section_count: int,
) -> str:
    return f"""\
You are a document structure analyzer.

<PREVIOUS_BATCH_CONTEXT>
The section below was the LAST one processed in the previous batch.
Do NOT enrich it — use its heading and node_id to continue numbering for <INPUT>.
{context_node_json}
</PREVIOUS_BATCH_CONTEXT>

Each section in <INPUT> has a "seq_id" integer. For EACH section generate:

"seq_id"   — Copy the seq_id from the input exactly. Do NOT change or omit it.

"summary"  — Complete summary of ALL content. Include every topic, feature, and detail present.
             Do NOT omit anything. If the section spans multiple topics, cover all of them.

"keywords" — 5–10 short phrases drawn from the FULL content (not just the heading).
             Every distinct concept, feature, or topic in the content must appear in keywords.

"node_id"  — Hierarchical dotted ID continuing from the context node above.

  Examples:
    1         → first top-level section
    1.1       → first child of section 1
    1.1.1     → first child of section 1.1
    2         → second top-level section
    2.1       → first child of section 2

  Rules:
  • Continue numbering from where the previous batch ended — do NOT restart from 1.
  • Main sections        → 1, 2, 3 ...
  • Child sections       → 1.1, 1.2, 1.3 ...
  • Nested child sections → 1.1.1, 1.1.2 ...
  • Never skip levels — 1.1.1 requires 1.1 to exist.
  • Never generate duplicate node_ids.
  • Parallel headings get sibling IDs; sub-topics get child IDs (one dot deeper).
  • Paragraph chunk nodes: a heading ending with ' -2', ' -3', ' -4', … is a continuation
    chunk of the immediately preceding node whose heading is the same text without the suffix.
    The parent holds chunk 1 (no suffix). Assign chunk nodes as numerical children of that parent.
    Example: parent "Background" → node_id "2"; "Background -2" → "2.1"; "Background -3" → "2.2".

━━━ FORMAT RULES ━━━

- <INPUT> below contains exactly {section_count} sections.
- Output MUST be a JSON array of exactly {section_count} objects — one per section, in input order.
- Output covers <INPUT> sections ONLY — do NOT include the context node.
- Each object: "seq_id" (integer, copied from input), "summary" (non-empty string), "keywords" (non-empty list), "node_id" (dotted numeric string like "1" or "2.3.1").
- Return ONLY valid JSON — no markdown fences, no extra text.

<INPUT>
{batch_json}
</INPUT>

Output:
[
  {{"seq_id": 1, "summary": "...", "keywords": ["...", "..."], "node_id": "2.1"}},
  ...
]
"""
