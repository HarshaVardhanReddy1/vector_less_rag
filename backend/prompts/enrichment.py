def generate_enrichment_batch_prompt(batch_json: str, section_count: int) -> str:
    return f"""\
You are a document structure analyzer.

Each section in <INPUT> has a "seq_id" integer. For EACH section generate:

"seq_id"   — Copy the seq_id from the input exactly. Do NOT change or omit it.

"summary"  — Answer the question "What is this section about?" in 2–4 sentences.
             Write as a direct answer, not a description. Name the exact concepts, methods,
             results, or decisions covered. A reader must understand what this node contains
             without reading the original text.

"keywords" — 5–10 true keywords extracted from the content.
             Include: technical terms, abbreviations (e.g. "EMD", "SSP"), their full forms
             (e.g. "Earth Mover's Distance"), algorithm names, metric names, and domain-specific
             vocabulary. These must be words a user would type to search for this content.
             Do NOT include generic phrases like "key concepts" or "overview".

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

"summary"  — Answer the question "What is this section about?" in 2–4 sentences.
             Write as a direct answer, not a description. Name the exact concepts, methods,
             results, or decisions covered. A reader must understand what this node contains
             without reading the original text.

"keywords" — 5–10 true keywords extracted from the content.
             Include: technical terms, abbreviations (e.g. "EMD", "SSP"), their full forms
             (e.g. "Earth Mover's Distance"), algorithm names, metric names, and domain-specific
             vocabulary. These must be words a user would type to search for this content.

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