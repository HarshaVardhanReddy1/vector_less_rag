def generate_tree_multi_node_selection_prompt(query: str, tree_text: str) -> str:
    return f"""
You are a document retrieval system.

Given a user query and a full document tree, identify ALL nodes that contain
information relevant to answering the query. Include both direct matches and
closely supporting context.

IMPORTANT RULES:
1. Select ALL relevant nodes — not just the single best match.
2. Use node_id, title, summary, and keywords to judge relevance.
3. Do NOT invent node IDs. Select ONLY from the tree below.
4. Prefer the most specific (deepest) matching node. If both a parent and its
   child are relevant, select the child — its content subsumes the parent.
5. If nothing is relevant, return an empty list.
6. Return ONLY valid JSON. No markdown, no explanations.

QUERY:
{query}

DOCUMENT TREE:
{tree_text}

OUTPUT FORMAT:
{{
  "selected_node_ids": ["1.2", "3.1.2"],
  "reason": "Short reason for selections."
}}
"""


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
