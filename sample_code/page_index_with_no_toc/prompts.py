import json


def generate_initial_tree_prompt(initial_tree_context):

    prompt = f"""
You are an expert document structure extraction system.

Your task is to analyze the provided document context and generate a hierarchical document tree in STRICT JSON format.

IMPORTANT OBJECTIVE:
Extract ONLY real document sections, headings, and sub-sections that are explicitly visible in the context.

STRICT RULES:

1. Extract only meaningful document sections.
2. Preserve hierarchy correctly.
3. Create nested sub_nodes only when true sub-sections exist.
4. Do NOT hallucinate headings.
5. Do NOT infer missing sections.
6. Do NOT create fake hierarchy.

NODE FORMAT:

Each node MUST contain exactly these fields:

- node_id
- title
- start_index
- end_index
- summary
- sub_nodes

NODE ID RULES:

1. node_id must always be a string.
2. Root nodes:
   "0001", "0002", "0003"
3. Child nodes:
   "0001.1", "0001.2"
4. Grandchild nodes:
   "0001.1.1"
5. Use hierarchical numbering only.
6. Never use "-" in node IDs.

PAGE RULES:

1. Use ONLY physical page indexes from:
   ================= PAGE X START =================

2. start_index:
   first page where section appears.

3. end_index:
   last page where section appears.

4. Always ensure:
   start_index <= end_index

5. Child page ranges must stay inside parent ranges.

SUMMARY RULES:

1. Summary must be concise.
2. Maximum 1-2 sentences.
3. Maximum 50 words.
4. Do NOT copy large text from context.
5. Summarize only the actual section content.

SUB NODE RULES:

1. Use [] if no children exist.
2. Never omit sub_nodes field.
3. Child nodes must be semantically related to parent.

OUTPUT RULES:

1. Return ONLY valid JSON.
2. Output must start with [ and end with ].
3. Do NOT include explanations.
4. Do NOT include markdown.
5. Do NOT wrap in ```json.
6. Do NOT include comments.
7. Do NOT include trailing commas.
8. Ensure all strings are properly escaped.
9. Ensure valid nested JSON structure.
10. Return compact JSON.

IMPORTANT:

1. Focus on structural accuracy over completeness.
2. Prefer fewer accurate nodes over many noisy nodes.
3. Ignore:
   - page headers
   - page footers
   - page numbers
   - repeated navigation text
   - copyright text
   - references unless they are actual sections

DOCUMENT CONTEXT:

{initial_tree_context}
"""

    return prompt


def generate_tree_prompt(existing_tree, context):

    prompt = f"""
You are an expert hierarchical document tree refinement system.

Your task is to extend the EXISTING DOCUMENT TREE using the NEW DOCUMENT CONTEXT.

IMPORTANT OBJECTIVE:
Add ONLY genuinely new sections found in the new context while preserving the entire existing hierarchy exactly.

STRICT RULES:

1. Preserve all existing nodes exactly.
2. Never remove existing nodes.
3. Never modify existing summaries unless clearly incorrect.
4. Add only new sections from the new context.
5. Avoid duplicate nodes.
6. Maintain proper hierarchy.

NODE FORMAT:

Every node MUST contain:

- node_id
- title
- start_index
- end_index
- summary
- sub_nodes

NODE ID RULES:

1. Continue numbering sequentially.
2. Use hierarchical numbering:
   "0001"
   "0001.1"
   "0001.1.1"

3. Never use:
   - "0014-1"
   - "1)"
   - "(a)"

4. Preserve existing node IDs.

PAGE RULES:

1. Use ONLY physical page indexes from:
   ================= PAGE X START =================

2. Ensure:
   start_index <= end_index

3. Child page ranges must remain inside parent ranges.

4. If a child exceeds parent range:
   update parent range accordingly.

5. Never create impossible page ranges.

SUMMARY RULES:

1. Keep summaries concise.
2. Maximum 50 words.
3. Do NOT generate long summaries.
4. Avoid repeating parent summaries.

DUPLICATE RULES:

1. Do NOT create duplicate sections.
2. Merge semantically identical sections.
3. Preserve the earliest valid node_id.

OUTPUT RULES:

1. Return the COMPLETE updated tree.
2. Include BOTH old and new nodes.
3. Return ONLY valid JSON.
4. Output must start with [ and end with ].
5. Do NOT include explanations.
6. Do NOT include markdown.
7. Do NOT wrap in ```json.
8. Do NOT include comments.
9. Do NOT include trailing commas.
10. Ensure properly escaped strings.

IMPORTANT:

1. Prefer structural correctness over excessive detail.
2. Ignore noisy administrative subsections unless clearly important.
3. Avoid generating deeply fragmented trees.
4. Preserve semantic consistency.

EXISTING TREE:

{existing_tree}

NEW DOCUMENT CONTEXT:

{context}
"""

    return prompt


def generate_json_fix_prompt(broken_json, error_message):

    prompt = f"""
You are an expert JSON repair system.

Your task is to repair the provided JSON text.

IMPORTANT RULES:

1. Fix ONLY JSON formatting issues.
2. Do NOT modify actual data content.
3. Do NOT remove nodes.
4. Do NOT add hallucinated content.
5. Preserve all values exactly.
6. Fix issues like:
   - unterminated strings
   - missing commas
   - trailing commas
   - invalid escape characters
   - extra text outside JSON
   - broken brackets
   - malformed quotes

7. Return ONLY valid JSON.
8. Do NOT add explanations.
9. Do NOT use markdown.
10. Do NOT wrap output in ```json.

JSON ERROR:

{error_message}

BROKEN JSON:

{broken_json}
"""

    return prompt


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


def generate_relevant_node(context, query):
    """
    Generate a prompt to retrieve the single most relevant node.

    Parameters:
        context (list): Tree JSON data
        query (str): User query

    Returns:
        str
    """

    prompt = f"""
You are an intelligent document retrieval system.

Your task is to analyze the user query and identify ONLY ONE most relevant node
from the provided document tree.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do NOT return explanations, markdown, or additional text.
3. Return ONLY a single JSON object.
4. Use both the node title and summary to determine relevance.
5. Select the BEST matching node only.
6. If multiple nodes are relevant, return the most specific and relevant node.
7. Include:
   - node_id
   - title
   - start_index
   - end_index
   - reason
8. If no relevant node exists, return an empty list:

[]

RESPONSE FORMAT:

{{
    "node_id": "0001",
    "title": "Overview",
    "start_index": 10,
    "end_index": 25,
    "reason": "This section is relevant because it discusses ..."
}}

DOCUMENT TREE:
{json.dumps(context, indent=2)}

USER QUERY:
{query}
"""

    return prompt


def generate_single_level_node_selection_prompt(
    query: str,
    candidate_nodes_text: str,
    parent_node_text: str = "",
) -> str:
    return f"""
You are a document retrieval router.

Your task is to select the single best matching node for the query
from the current candidate level only.

RULES:
1. Prefer the most semantically relevant node.
2. Use both title and summary.
3. Do not invent node IDs.
4. Choose only from the nodes listed under CANDIDATE NODES.
5. Ignore child nodes that are not explicitly listed as candidates.
6. Return exactly one node ID if a candidate is relevant.
7. If nothing is relevant, return `"selected_node_id": null`.
8. Return ONLY valid JSON.
9. Evaluate only the current level. Do not assume anything about hidden child nodes.
10. If the query is broad, choose the best parent-level match from the candidates shown.

QUERY:
{query}

{parent_node_text}

CANDIDATE NODES:
{candidate_nodes_text}

OUTPUT FORMAT:
{{
  "selected_node_id": "0001",
  "reason": "Short reason for the selection."
}}
"""


def generate_full_tree_node_selection_prompt(
    query: str,
    full_tree_candidates_text: str,
) -> str:
    return f"""
You are a document retrieval router.

The root-level selection did not find a relevant top-level node.
As a fallback, select the single best matching node from anywhere in the full document tree.

RULES:
1. Prefer the most semantically relevant node.
2. Use title, summary, and page range.
3. Do not invent node IDs.
4. Choose only from the nodes listed under FULL TREE CANDIDATES.
5. Return exactly one node ID if a node is relevant.
6. If nothing is relevant, return `"selected_node_id": null`.
7. Return ONLY valid JSON.
8. You may select a node from any depth level because the full tree is visible here.

QUERY:
{query}

FULL TREE CANDIDATES:
{full_tree_candidates_text}

OUTPUT FORMAT:
{{
  "selected_node_id": "0001.2",
  "reason": "Short reason for the selection."
}}
"""


def generate_context_grounded_answer_prompt(
    query: str,
    retrieved_contexts_text: str,
) -> str:
    return f"""
You are a question answering system.

Answer the query using ONLY the retrieved contexts below.
If the answer is not supported by the contexts, say so clearly.
Be concise but accurate.

QUERY:
{query}

RETRIEVED CONTEXTS:
{retrieved_contexts_text}
"""

def generate_answer_prompt(context, query):
    """
    Generate a prompt for answering the user query
    using the retrieved relevant context.

    Parameters:
        context (str): Relevant extracted document content
        query (str): User query

    Returns:
        str
    """

    prompt = f"""
You are an intelligent document question-answering system.

Your task is to answer the user query ONLY using the provided context.

IMPORTANT RULES:

1. Answer strictly based on the provided context.
2. Do NOT generate information outside the context.
3. If the answer is not available in the context, reply with:

"I could not find the answer in the provided document context."

4. Provide a clear and concise answer.
5. Do NOT mention phrases like:
   - "According to the context"
   - "Based on the document"
   - "The provided text says"

6. Keep the response natural and direct.

CONTEXT:
{context}

USER QUERY:
{query}

ANSWER:
"""

    return prompt
