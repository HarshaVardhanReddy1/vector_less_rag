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
  "node_id"  — a dotted numeric id giving the section's place in the hierarchy.
               Extract explicit numbers from headings (e.g., "1. Title" → "1",
               "4.2 Subsection" → "4.2"). For unnumbered sections, nest them under
               the most recent numbered parent section. Maintain strict hierarchical
               depth — child sections must have exactly one more dot level than parent.

Rules:
- node_id: Extract numbers from heading format "N. Title" or "N.M. Title" exactly.
  For unnumbered sections appearing after a numbered parent, assign the next child
  number: if last parent was "7", next children are "7.1", "7.2", etc.
  Keep it dotted-numeric, unique, and with no skipped levels.
- summary: cover all of the content — every topic, table, and figure.
- keywords: extract key terms users might search for or ask questions about, including:
  * Abbreviations and acronyms (e.g., "API", "JSON", "REST")
  * Full forms / expanded terms (e.g., "Application Programming Interface")
  * Technical and domain-specific terms
  * Table headings and column names (e.g., "Table 1: Model Performance", "Accuracy", "F1-Score")
  * Image headings and captions (from <IMAGE_CONTEXT> blocks)
  * Equation labels and descriptions (keep equations in their original form, do not parse)
  * Proper nouns, product names, and frameworks
  * Words that appear emphasized or highlighted in content
  * Concepts that could be queried or asked about directly
  Do not include generic words. Draw keywords from the entire content, not just headings.
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
{{"heading", "node_id", "summary"}}. Use them to determine parent-child relationships
and the next available node_id numbering. Do not re-enrich or output them.
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
  "node_id"  — a dotted numeric id continuing the hierarchy from <PREVIOUS_CONTEXT>.
               Extract explicit numbers from headings (e.g., "7. Title" → "7",
               "7.2 Subsection" → "7.2"). For unnumbered sections, determine if they
               belong under the parent_node (continue child numbering) or start a new
               top-level section. Maintain strict hierarchical depth.

Rules:
- node_id: Extract numbers from heading format "N. Title" or "N.M. Title" exactly.
  For unnumbered sections: if they logically belong under parent_node (based on content
  and context), assign the next available child number. If they start a new top-level
  section, use the next available top-level number after the parent.
  Keep it dotted-numeric, unique, and with no skipped levels.
- summary: cover all of the content — every topic, table, and figure.
- keywords: extract key terms users might search for or ask questions about, including:
  * Abbreviations and acronyms (e.g., "API", "JSON", "REST")
  * Full forms / expanded terms (e.g., "Application Programming Interface")
  * Technical and domain-specific terms
  * Table headings and column names (e.g., "Table 1: Model Performance", "Accuracy", "F1-Score")
  * Image headings and captions (from <IMAGE_CONTEXT> blocks)
  * Equation labels and descriptions (keep equations in their original form, do not parse)
  * Proper nouns, product names, and frameworks
  * Words that appear emphasized or highlighted in content
  * Concepts that could be queried or asked about directly
  Do not include generic words. Draw keywords from the entire content, not just headings.
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
