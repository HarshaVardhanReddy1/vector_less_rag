def generate_enrichment_batch_prompt(batch_json: str, section_count: int) -> str:
    return f"""\
You are a document structure analyzer.

Each section in <INPUT> has a "seq_id" integer. For EACH section generate:

"seq_id"   — Copy the seq_id from the input exactly. Do NOT change or omit it.

"summary"  — Answer the question "What does this section cover and what does it say?"
             Write 2–4 sentences. Be specific: name the exact methods, models, algorithms,
             results, or concepts discussed. A reader must be able to judge from the summary
             alone whether this section answers their question.
             Rules:
             • State what the section IS about, not that it "discusses" or "covers" something.
             • Mention concrete details — numbers, names, comparisons, conclusions.
             • If the section contains a table or figure, state what it shows.
             • Never write "This section introduces…" or "This part covers…" — start directly
               with the subject matter.

"keywords" — 5–10 specific terms extracted directly from the content.
             Include: technical terms, named methods/algorithms, model names, metric names,
             proper nouns, and domain-specific vocabulary that appear in the text.
             Each keyword must be 1–3 words.
             Rules:
             • Use terms a user would actually type when searching for this content.
             • Do NOT include generic phrases like "key concepts", "performance comparison",
               or "model overview" — only concrete terms from the content.
             • Examples of good keywords: "ReLU", "batch normalization", "ResNet-50",
               "attention mechanism", "F1 score", "gradient descent".

"node_id"  — Hierarchical dotted ID reflecting the semantic position of this section.

  How to determine CHILD vs SIBLING:
  • A section is a CHILD of the one before it when its heading:
      - Narrows, details, or specialises the preceding topic
        (e.g. "Neural Networks" → children: "Convolutional Layers", "Activation Functions")
      - Is noticeably more specific or focused than the preceding heading
  • A section is a SIBLING when its heading:
      - Introduces a parallel or independent topic at the same level of abstraction
      - Starts a clearly new theme unrelated to the immediately preceding section
  • A section RISES to a higher level when it is broader in scope than the current depth
    (e.g. after several sub-sections, a heading matching the scope of a top-level topic)

  Numbering rules:
  • Top-level sections  → 1, 2, 3 …
  • Children            → 1.1, 1.2, 2.1 …
  • Deeper children     → 1.1.1, 1.1.2 …
  • Never skip levels — 1.1.1 requires 1.1 to exist first.
  • Never generate duplicate node_ids — every section must have a unique ID.
  • If a heading starts with a numeric prefix (e.g. "3.1 Methods"), treat it as authoritative.

  Chunk continuation nodes (heading ends with ' -2', ' -3', …):
  • Overflow chunks of the parent (same heading without the suffix).
  • Assign as children of that parent regardless of content.
  • After all chunks, resume sibling numbering at the parent's level.
  Examples:
    "Background" → "2";  "Background -2" → "2.1";  "Background -3" → "2.2";  next section → "3"
    parent "4.1 Overview" → "4.1";  "4.1 Overview -2" → "4.1.1";  next sibling → "4.2"

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
  {{"seq_id": 1, "summary": "ReLU and its variants (Leaky ReLU, ELU, GELU) address vanishing gradients by providing non-zero gradients for positive inputs, enabling training of deep networks. GELU is preferred in Transformers due to its smooth probabilistic gating.", "keywords": ["ReLU", "Leaky ReLU", "GELU", "vanishing gradient", "activation function", "backpropagation"], "node_id": "1"}},
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

"summary"  — Answer the question "What does this section cover and what does it say?"
             Write 2–4 sentences. Be specific: name the exact methods, models, algorithms,
             results, or concepts discussed. A reader must be able to judge from the summary
             alone whether this section answers their question.
             Rules:
             • State what the section IS about, not that it "discusses" or "covers" something.
             • Mention concrete details — numbers, names, comparisons, conclusions.
             • If the section contains a table or figure, state what it shows.
             • Never write "This section introduces…" or "This part covers…" — start directly
               with the subject matter.

"keywords" — 5–10 specific terms extracted directly from the content.
             Include: technical terms, named methods/algorithms, model names, metric names,
             proper nouns, and domain-specific vocabulary that appear in the text.
             Each keyword must be 1–3 words.
             Rules:
             • Use terms a user would actually type when searching for this content.
             • Do NOT include generic phrases like "key concepts", "performance comparison",
               or "model overview" — only concrete terms from the content.
             • Examples of good keywords: "ReLU", "batch normalization", "ResNet-50",
               "attention mechanism", "F1 score", "gradient descent".

"node_id"  — Hierarchical dotted ID continuing from the context node above.

  How to determine CHILD vs SIBLING:
  • A section is a CHILD of the one before it when its heading:
      - Narrows, details, or specialises the preceding topic
        (e.g. "Neural Networks" → children: "Convolutional Layers", "Activation Functions")
      - Is noticeably more specific or focused than the preceding heading
  • A section is a SIBLING when its heading:
      - Introduces a parallel or independent topic at the same level of abstraction
      - Starts a clearly new theme unrelated to the immediately preceding section
  • A section RISES to a higher level when it is broader in scope than the current depth
    (e.g. after several sub-sections, a heading matching the scope of a top-level topic)

  Numbering rules:
  • Continue numbering from where the previous batch ended — do NOT restart from 1.
  • Top-level sections  → 1, 2, 3 …
  • Children            → 1.1, 1.2, 2.1 …
  • Deeper children     → 1.1.1, 1.1.2 …
  • Never skip levels — 1.1.1 requires 1.1 to exist first.
  • Never generate duplicate node_ids.
  • If a heading starts with a numeric prefix (e.g. "3.1 Methods"), treat it as authoritative.

  Chunk continuation nodes (heading ends with ' -2', ' -3', …):
  • Overflow chunks of the parent (same heading without the suffix).
  • Assign as children of that parent regardless of content.
  • After all chunks, resume sibling numbering at the parent's level.
  Examples:
    "Background" → "2";  "Background -2" → "2.1";  "Background -3" → "2.2";  next section → "3"
    parent "4.1 Overview" → "4.1";  "4.1 Overview -2" → "4.1.1";  next sibling → "4.2"

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
  {{"seq_id": 1, "summary": "ResNet-50 achieves 76.1% Top-1 accuracy on ImageNet using residual connections that let gradients bypass layers via identity shortcuts, enabling 50-layer training without vanishing gradients.", "keywords": ["ResNet-50", "residual connections", "skip connections", "ImageNet", "Top-1 accuracy", "identity shortcut"], "node_id": "2.1"}},
  ...
]
"""
