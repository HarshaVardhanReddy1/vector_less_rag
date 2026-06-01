def generate_enrichment_batch_prompt(sections_text: str, section_count: int) -> str:
    return f"""\
You are a document structure analyzer.

<INPUT> contains {section_count} document sections in document order. Each
section is a block that begins with a line "=== SECTION seq_id=N ===", followed
by a "HEADING:" line and a "CONTENT:" block (the content is raw markdown and may
include tables and <IMAGE_CONTEXT> blocks describing figures or equations).

For each section, return one object with:
  "seq_id"   — the section's seq_id, copied exactly (used to match results back).
  "summary"  — a concise summary covering all of the section's content.
  "keywords" — the key terms and concepts found in the content.
  "node_id"  — a dotted numeric id giving the section's place in the document
               hierarchy. When the heading already carries a section number, use
               it; otherwise nest the section under its parent.

Rules:
- node_id: prefer the heading's own number; keep it dotted-numeric, unique, and
  with no skipped levels.
- summary: cover all of the content — every topic, table, and figure.
- keywords: draw them from the content, not just the heading.
- seq_id: copy it from the input unchanged.

Return ONLY a JSON object {{"sections": [...]}} with exactly {section_count}
objects, one per input section, each carrying its seq_id. No prose, no fences.

<INPUT>
{sections_text}
</INPUT>

Output format:
{{"sections": [
  {{"seq_id": 0, "summary": "...", "keywords": ["...", "..."], "node_id": "1"}},
  {{"seq_id": 1, "summary": "...", "keywords": ["...", "..."], "node_id": "1.1"}}
]}}
"""


def generate_enrichment_continuation_prompt(
    sections_text: str,
    context_node_json: str,
    section_count: int,
) -> str:
    return f"""\
You are a document structure analyzer.

<PREVIOUS_CONTEXT> shows where the previous batch left off, to help you continue
the node_id hierarchy. It has "last_node" (the final section enriched) and, when
it exists, "parent_node" (that section's parent) — each as
{{"heading", "node_id", "summary"}}. Use them only for numbering; do not
re-enrich or output them.
<PREVIOUS_CONTEXT>
{context_node_json}
</PREVIOUS_CONTEXT>

<INPUT> contains {section_count} document sections in document order. Each
section is a block that begins with a line "=== SECTION seq_id=N ===", followed
by a "HEADING:" line and a "CONTENT:" block (the content is raw markdown and may
include tables and <IMAGE_CONTEXT> blocks describing figures or equations).

For each section, return one object with:
  "seq_id"   — the section's seq_id, copied exactly (used to match results back).
  "summary"  — a concise summary covering all of the section's content.
  "keywords" — the key terms and concepts found in the content.
  "node_id"  — a dotted numeric id giving the section's place in the hierarchy,
               continuing from <PREVIOUS_CONTEXT>. When the heading already
               carries a section number, use it; otherwise nest it under its parent.

Rules:
- node_id: prefer the heading's own number; keep it dotted-numeric, unique, and
  with no skipped levels. Continue from <PREVIOUS_CONTEXT> — do not restart at 1.
- summary: cover all of the content — every topic, table, and figure.
- keywords: draw them from the content, not just the heading.
- seq_id: copy it from the input unchanged.

Return ONLY a JSON object {{"sections": [...]}} with exactly {section_count}
objects, one per input section, each carrying its seq_id. No prose, no fences.

<INPUT>
{sections_text}
</INPUT>

Output format:
{{"sections": [
  {{"seq_id": 12, "summary": "...", "keywords": ["...", "..."], "node_id": "2.1"}}
]}}
"""
