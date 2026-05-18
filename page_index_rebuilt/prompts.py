import json


def generate_json_fix_prompt(
    broken_json: str,
    error_message: str,
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

BROKEN JSON:
{broken_json}
"""


 


def generate_toc_from_context_prompt(context: str) -> str:

    prompt = f"""
You are an expert document structure extraction system.

Your task is to analyze the provided document context chunk and extract a structured partial Table of Contents (TOC)
using only the headings and sections visible in that chunk.

The document context contains explicit page boundary markers like:

================ PAGE X START ================
...
================ PAGE X END ================

You must carefully analyze the content and identify:

- Main headings
- Subheadings
- Hierarchical structure
- Section relationships

IMPORTANT:
The goal is to produce a concise, useful partial TOC for this context chunk.
Prefer fewer, higher-value entries over exhaustive extraction.
Do not assume unseen pages before or after this chunk.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Extract a flat list of TOC nodes in sequential order for this chunk only.

Each node must contain:

1. title
2. node_id
3. page_number
4. summary

The TOC should include only major sections and clearly meaningful subsections.
Do NOT turn every small heading, table, office, district, or staff listing into its own TOC node.

--------------------------------------------------
NODE ID RULES
--------------------------------------------------

Generate hierarchical node IDs based on heading structure.

Examples:

1
1.1
1.1.1
2
2.1

Rules:
- Main sections -> 1, 2, 3...
- Child sections -> 1.1, 1.2...
- Nested child sections -> 1.1.1, 1.1.2...
- Maintain proper sequential numbering
- Never skip numbering levels
- Never generate duplicate node_ids

--------------------------------------------------
SUMMARY RULES
--------------------------------------------------

- Generate concise but meaningful summaries
- Parent node summaries should include the overall idea of their child sections
- Child node summaries should focus only on their own section content
- Do not hallucinate information not present in the document
- Keep summaries high-level
- Do not summarize line-by-line administrative detail
- Make summaries retrieval-friendly by clearly naming the main topic and scope
- Avoid vague summaries when a more specific summary is possible
- Keep each summary to 1-2 sentences

--------------------------------------------------
PAGE NUMBER RULES
--------------------------------------------------

- Use the page markers to determine page numbers
- Assign the page where the heading first appears
- Do not hallucinate page numbers
- Use only pages visible in this context chunk

--------------------------------------------------
IMPORTANT EXTRACTION RULES
--------------------------------------------------

1. Extract only real headings
2. Do not extract paragraph text as headings
3. Ignore page headers/footers
4. Ignore repeated navigation text
5. Ignore table/figure captions unless they are actual sections
6. Preserve document order
7. Maintain heading hierarchy correctly
8. Return ONLY valid JSON
9. Do not include explanations
10. Do not wrap JSON inside markdown
11. Prefer major document sections over low-level subsections
12. Skip repetitive administrative headings such as:
   - staff names and leadership rosters
   - district-by-district listings
   - branch-by-branch listings
   - individual tables, figures, appendices entries, or schedules
   - repeated policy/action items under the same parent unless they are clearly major sections
13. Include a child node only when it would be useful in a human-written TOC
14. If a section is mostly a directory, roster, or long list, keep only the parent section
15. Avoid exploding one parent into many tiny child entries
16. Do not invent earlier or later sections that are not visible in this chunk
17. If a parent section clearly begins in this chunk, include it even if the full document may continue beyond this chunk

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

[
    {{
        "title": "Introduction",
        "node_id": "1",
        "page_number": 1,
        "summary": "Provides an overview of the document."
    }},
    {{
        "title": "System Architecture",
        "node_id": "1.1",
        "page_number": 2,
        "summary": "Explains the frontend and backend architecture of the system."
    }}
]

--------------------------------------------------
DOCUMENT CONTEXT
--------------------------------------------------

{context}
"""

    return prompt


def generate_toc_merge_prompt(
    existing_toc: list,
    new_toc: list
) -> str:

    existing_toc_json = json.dumps(existing_toc, indent=2, ensure_ascii=False)
    new_toc_json = json.dumps(new_toc, indent=2, ensure_ascii=False)

    prompt = f"""
You are an expert document TOC merge system.

Your task is to merge two partial TOCs from different chunks of the same document.

You are given:
1. An EXISTING TOC from earlier pages
2. A NEW TOC from later pages

Your job is to:
- preserve all valid earlier nodes
- add genuinely new later nodes
- remove duplicates
- fix numbering only when necessary
- maintain hierarchy consistency
- keep summaries concise and retrieval-friendly

IMPORTANT:
Keep the TOC concise.
Do not expand the TOC with every minor heading from the later chunk.

==================================================
EXISTING TOC
==================================================

{existing_toc_json}

==================================================
NEW TOC
==================================================

{new_toc_json}

==================================================
OBJECTIVE
==================================================

Return the COMPLETE updated TOC for the full document.

The updated TOC must:
- preserve all previous nodes
- include newly discovered nodes
- maintain numbering consistency
- maintain hierarchy consistency
- remain concise and useful as a human TOC
- preserve the beginning sections of the document
- never drop valid early sections unless they are exact duplicates

==================================================
NODE STRUCTURE
==================================================

Each node must contain:

1. title
2. node_id
3. page_number
4. summary

==================================================
NODE ID RULES
==================================================

Generate hierarchical node IDs correctly in the final merged output.

Examples:

1
1.1
1.1.1
2
2.1
2.1.1

Rules:
- Main sections -> 1, 2, 3...
- Child sections -> 1.1, 1.2...
- Nested child sections -> 1.1.1...
- Never skip numbering levels
- Never generate duplicate node_ids
- Preserve previous numbering consistency where possible
- If duplicate or conflicting numbering exists, fix it so the final TOC is sequential and consistent

==================================================
SUMMARY RULES
==================================================

1. Generate concise and meaningful summaries.
2. Child summaries should describe only their own section content.
3. Parent summaries may contain high-level information about child sections.
4. Do not hallucinate information that does not exist in the document.
5. Do NOT rewrite all previous summaries.
6. Update a summary only if needed to reflect merged content more accurately.
7. Preserve good existing summaries whenever possible.
8. Do not modify unrelated summaries.
9. Keep summaries high-level and avoid low-value detail.
10. Make summaries retrieval-friendly by clearly naming the main topic, scope, and important concepts.
11. Avoid generic summaries when a more specific one is possible.

==================================================
MERGE RULES
==================================================

1. Preserve document order.
2. Preserve earlier sections before later sections.
3. Keep only one copy of duplicate entries.
4. If the same section appears in both TOCs, keep one merged version.
5. Prefer major sections and a limited number of meaningful subsections.
6. Do NOT add nodes for:
   - staff rosters
   - office/division personnel lists
   - district-by-district repeated entries
   - branch-by-branch repeated entries
   - individual tables or figure captions
   - long enumerations under appendixes unless they are clearly major sections
7. If multiple nearby headings are just components of the same administrative block, keep only the parent node.
8. When in doubt, omit low-importance headings instead of creating noisy TOC entries.
9. Do not remove valid early sections simply because later sections are more detailed.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY a valid JSON array.

Each node must follow this exact structure:

[
    {{
        "title": "Introduction",
        "node_id": "1",
        "page_number": 1,
        "summary": "Provides an overview of the document."
    }},
    {{
        "title": "System Architecture",
        "node_id": "1.1",
        "page_number": 2,
        "summary": "Explains the frontend and backend architecture of the system."
    }}
]

==================================================
OUTPUT RULES
==================================================

1. Return ONLY valid JSON
2. Do not add explanations
3. Do not add markdown
4. Do not wrap output inside ```json
5. Do not return text before or after JSON
6. Preserve sequential order
7. Preserve hierarchy using node_id structure
8. Every node must contain:
   - title
   - node_id
   - page_number
   - summary
9. Prefer fewer entries over exhaustive coverage
10. Do not duplicate an existing title/node unless it is genuinely a different section
11. The first entries of the final TOC should still represent the beginning of the document

==================================================
FINAL INSTRUCTION
==================================================

Return the COMPLETE updated TOC as a valid JSON array.
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

Your task is to answer the user query
ONLY using the retrieved context.

IMPORTANT RULES:

1. Use ONLY the provided context.
2. Do NOT invent information.
3. If the answer is not available in the context, reply with:
   "I could not find the answer in the provided context."
4. Keep the answer concise and accurate.
5. Do NOT mention phrases like:
   - "According to the context"
   - "Based on the retrieved text"
   - "The document says"
6. Return plain natural language only.

QUERY:
{query}

RETRIEVED CONTEXT:
{retrieved_context_text}

ANSWER:
"""