import json


def generate_json_fix_prompt(
    broken_json: str,
    error_message: str,
    validation_requirements: str = "",
) -> str:

    return f"""
You are an expert JSON repair system.

Your task is to repair invalid JSON.

IMPORTANT RULES:

1. Fix ONLY JSON syntax/formatting issues.
2. Do NOT change the meaning of the content.
3. Do NOT remove valid fields.
4. Preserve all original data whenever possible.
5. Return ONLY valid JSON.
6. Do NOT add markdown or explanations.

JSON ERROR:
{error_message}

VALIDATION REQUIREMENTS:
{validation_requirements or "The JSON only needs to be valid and preserve the original meaning."}

BROKEN JSON:
{broken_json}
"""


def generate_toc_from_context_prompt(context: str) -> str:
    return f"""
You are an expert document structure analyzer.

Your task is to analyze the given document context and generate a hierarchical Table of Contents (TOC).

The context contains one or more pages in the following format:

================ PAGE <page_number> START ================

<page content>

================ PAGE <page_number> END ================

Instructions:
1. Read all pages carefully.
2. Identify important sections, headings, and subheadings from the content.
3. Generate a structured TOC in hierarchical format.
4. Use hierarchical node IDs:
   - Main section: "1"
   - Subsection: "1.1"
   - Nested subsection: "1.1.1"
5. Each TOC item must contain:
   - "title" → section title
   - "node_id" → hierarchical section id
   - "page_number" → page where the section starts
   - "summary" → short meaningful summary of the section
6. Return ONLY valid JSON.
7. Do NOT include explanations, markdown, comments, or extra text.
8. Preserve logical hierarchy and ordering.
9. If no clear headings exist, infer meaningful section titles from the content.

Expected Output Format:
[
    {{
        "title": "Introduction",
        "node_id": "1",
        "page_number": 1,
        "summary": "Provides an overview of the document and its objectives."
    }},
    {{
        "title": "System Architecture",
        "node_id": "1.1",
        "page_number": 2,
        "summary": "Explains the system architecture and major components."
    }},
    {{
        "title": "API Layer",
        "node_id": "1.1.1",
        "page_number": 3,
        "summary": "Describes the API layer and request handling process."
    }}
]

Document Context:
{context}
"""


def generate_toc_merge_prompt(
    existing_toc: list,
    new_toc: list
) -> str:

    existing_toc_json = json.dumps(existing_toc, indent=2, ensure_ascii=False)
    new_toc_json = json.dumps(new_toc, indent=2, ensure_ascii=False)

    prompt = f"""
You are an expert hierarchical TOC merge system.

Your task is to merge two partial TOCs extracted from different chunks of the SAME document.

The output will be used in a production-grade hierarchical retrieval system.

Structural consistency and hierarchy preservation are CRITICALLY IMPORTANT.

==================================================
INPUTS
==================================================

1. EXISTING TOC
- extracted from earlier pages

2. NEW TOC
- extracted from later pages

==================================================
EXISTING TOC
==================================================

{existing_toc_json}

==================================================
NEW TOC
==================================================

{new_toc_json}

==================================================
PRIMARY OBJECTIVE
==================================================

Merge the TOCs into ONE complete hierarchical TOC while preserving:

- all valid headings
- all valid subheadings
- exact hierarchy
- exact document order
- correct parent-child relationships
- correct page numbers

Never lose hierarchy information during merging.

Missing a valid heading is considered a major failure.

==================================================
MERGE REQUIREMENTS
==================================================

You MUST:

- preserve all valid earlier nodes
- add all genuinely new nodes
- preserve hierarchy depth
- preserve document order
- preserve parent-child relationships
- preserve page numbers
- remove only TRUE duplicates

Do NOT simplify hierarchy for conciseness.

Do NOT collapse child sections into parents.

Do NOT flatten nested structures.

==================================================
DUPLICATE RULES
==================================================

Treat nodes as duplicates ONLY if:

- title is semantically identical
AND
- hierarchy position is equivalent
AND
- page relationship strongly indicates same section

If uncertain, KEEP BOTH.

Prefer preserving structure instead of aggressive deduplication.

==================================================
HIERARCHY RULES
==================================================

Preserve exact hierarchy depth.

Examples:

1
1.1
1.1.1
1.1.1.1

Never skip hierarchy levels.

Never move child sections under incorrect parents.

Never merge unrelated branches.

Never flatten deep hierarchies.

If a subsection exists, its parent MUST exist.

==================================================
NODE ID RULES
==================================================

Generate consistent hierarchical node IDs.

Rules:

- Main sections -> 1, 2, 3...
- Child sections -> 1.1, 1.2...
- Nested sections -> 1.1.1...
- Never skip numbering levels
- Never generate duplicate node_ids
- Preserve numbering consistency where possible
- Fix numbering only when necessary

==================================================
PAGE NUMBER RULES
==================================================

Preserve the original page_number for each heading.

The page_number MUST represent the page where the heading FIRST appears.

Do not modify correct earlier page numbers.

Do not infer missing page numbers.

==================================================
SUMMARY RULES
==================================================

Preserve good summaries whenever possible.

Update summaries ONLY when necessary.

Rules:

- keep summaries concise
- keep summaries retrieval-friendly
- do not hallucinate
- do not rewrite unrelated summaries
- preserve semantic specificity

==================================================
DOCUMENT ORDER RULES
==================================================

Preserve exact document order.

Earlier sections MUST remain before later sections.

Never reorder unrelated sections.

==================================================
IMPORTANT MERGE RULES
==================================================

1. Preserve ALL valid headings
2. Preserve ALL valid subheadings
3. Preserve ALL valid nested hierarchy
4. Never flatten hierarchy
5. Never collapse children into parents
6. Never remove valid early sections
7. Never lose parent-child relationships
8. Remove only true duplicates
9. Preserve document order
10. Preserve page number accuracy
11. Preserve hierarchy depth
12. Return ONLY valid JSON
13. Do not add explanations
14. Do not add markdown
15. Do not output text before or after JSON
16. Structural fidelity is MORE IMPORTANT than conciseness

==================================================
OUTPUT FORMAT
==================================================

[
    {{
        "title": "Introduction",
        "node_id": "1",
        "page_number": 1,
        "summary": "Provides an overview of the document."
    }},
    {{
        "title": "Architecture",
        "node_id": "1.1",
        "page_number": 2,
        "summary": "Explains the system architecture."
    }},
    {{
        "title": "API Layer",
        "node_id": "1.1.1",
        "page_number": 3,
        "summary": "Describes the API request handling layer."
    }}
]

==================================================
FINAL OUTPUT RULES
==================================================

Return ONLY a valid JSON array.

Do NOT:
- add markdown
- add explanations
- add comments
- add extra text
- add trailing commas

==================================================
FINAL INSTRUCTION
==================================================

Return the COMPLETE merged hierarchical TOC as valid JSON.
"""

    return prompt


def generate_single_level_node_selection_prompt(
    query: str,
    candidate_nodes_text: str,
    parent_node_text: str = "",
) -> str:

    return f"""
You are a document retrieval router.

Your task is to select the SINGLE BEST matching node
from the CURRENT candidate level only.

IMPORTANT RULES:

1. Prefer the most semantically relevant node.
2. Use both title and summary.
3. Do NOT invent node IDs.
4. Select ONLY from CANDIDATE NODES.
5. Ignore nodes not explicitly listed.
6. Return EXACTLY one node if relevant.
7. If nothing is relevant, return:
   {{
      "selected_node_id": null,
      "reason": "No relevant node found."
   }}
8. Return ONLY valid JSON.
9. Do NOT add markdown or explanations.

QUERY:
{query}

{parent_node_text}

CANDIDATE NODES:
{candidate_nodes_text}

OUTPUT FORMAT:
{{
  "selected_node_id": "0001",
  "reason": "Short reason."
}}
"""


def generate_full_tree_node_selection_prompt(
    query: str,
    full_tree_candidates_text: str,
) -> str:

    return f"""
You are a document retrieval router.

The root-level selection did not find a relevant node.

Your task is to search across the FULL TREE
and select the SINGLE BEST matching node.

IMPORTANT RULES:

1. Prefer the most semantically relevant node.
2. Use title, summary, and page range.
3. Do NOT invent node IDs.
4. Select ONLY from FULL TREE CANDIDATES.
5. Return EXACTLY one node if relevant.
6. If nothing is relevant, return:
   {{
      "selected_node_id": null,
      "reason": "No relevant node found."
   }}
7. Return ONLY valid JSON.
8. Do NOT add markdown or explanations.

QUERY:
{query}

FULL TREE CANDIDATES:
{full_tree_candidates_text}

OUTPUT FORMAT:
{{
  "selected_node_id": "0001.2",
  "reason": "Short reason."
}}
"""


def generate_context_grounded_answer_prompt(
    query: str,
    retrieved_context_text: str,
) -> str:

    return f"""
You are a context-grounded question answering system.

Answer the user query using ONLY the provided retrieved context.

RULES:

1. Use ONLY information explicitly present in the retrieved context.
2. Do NOT use external knowledge.
3. Do NOT infer, assume, or speculate.
4. If the answer is not fully supported by the context, say:
   "I could not find the answer in the provided context."
5. Keep the answer precise, complete, and grounded.
6. Do NOT mention phrases like "According to the context" or "The document says".
7. Preserve structure, lists, tables, and formatting whenever relevant.
8. Return plain natural language only — no JSON, no extra explanation.

QUERY:
{query}

RETRIEVED CONTEXT:
{retrieved_context_text}

ANSWER:
"""


def generate_llm_judge_prompt(query: str, answer: str, context: str) -> str:
    return f"""You are an impartial answer quality judge.

You will evaluate a generated answer against a user query and the retrieved context.

Score three metrics on a scale of 0.0 to 1.0:

METRIC DEFINITIONS:

1. faithfulness_score — Groundedness
   How well is the answer grounded in the retrieved context?
   1.0 = every claim in the answer is directly supported by the context.
   0.5 = some claims are supported, others are inferred or partially present.
   0.0 = the answer makes claims not supported by the context (hallucination).

2. relevance_score — Answer Relevancy
   How directly and completely does the answer address the user's query?
   1.0 = fully answers what was asked, nothing important left out.
   0.5 = partially answers the query or drifts from what was asked.
   0.0 = does not address the query at all.

3. context_precision_score — Context Precision
   Is the answer concise and uses only relevant parts of the context?
   1.0 = precise, uses only context information relevant to the query.
   0.5 = uses mostly relevant context but includes some irrelevant content.
   0.0 = verbose, padded with irrelevant context content, or highly redundant.

SCORING RULES:
- Scores must be floats between 0.0 and 1.0 (inclusive), rounded to two decimal places.
- Do not give uniformly high scores — score each dimension independently and critically.
- A good answer can still score low on faithfulness if it includes claims beyond the context.
- reasoning must be a single brief sentence (max 25 words) summarising key strengths or weaknesses.
- Return ONLY valid JSON. No markdown, no code fences, no extra text.

OUTPUT FORMAT:
{{
  "faithfulness_score": 0.00,
  "relevance_score": 0.00,
  "context_precision_score": 0.00,
  "reasoning": "Brief explanation here."
}}

QUERY:
{query}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}"""
