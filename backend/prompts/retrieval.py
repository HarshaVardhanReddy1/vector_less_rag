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
  "selected_node_id": "1",
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
  "selected_node_id": "1.2",
  "reason": "Short reason."
}}
"""
