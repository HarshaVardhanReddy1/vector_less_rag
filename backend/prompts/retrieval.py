# def generate_tree_multi_node_selection_prompt(query: str, tree_text: str) -> str:
#     return f"""
# You are a precise document retrieval system. Your ONLY job is to select nodes
# that contain information to answer the user's query. Prioritize recall (finding
# all relevant nodes) while avoiding false positives (selecting irrelevant nodes).

# CORE PRINCIPLES:
# 1. SEMANTIC MATCHING: Match nodes based on MEANING, not keywords.
#    - Query "project timeline" should retrieve nodes about schedules, milestones,
#      phases — NOT nodes mentioning "timeline" in other contexts.
#    - Use node title, summary, AND keywords together to assess relevance.

# 2. AVOID FALSE POSITIVES: If a node title/keywords match but content is unrelated
#    to the query's intent, DO NOT select it.
#    - Example: Query "What is the algorithm?" should NOT select a node titled
#      "Algorithm Phases" if it discusses implementation phases, not the algorithm itself.

# 3. COMPLETE CONTEXT: Select enough nodes to provide a complete answer.
#    - Include parent nodes when they provide essential overview/context.
#    - Include child nodes when they provide specific details the query needs.
#    - DO NOT exclude context nodes thinking the query can understand standalone content.

# 4. TRUST NODE METADATA: Title and summary are most reliable; keywords are hints.
#    - If title/summary clearly state relevance → select the node.
#    - If only keywords match but title/summary don't indicate relevance → reject.

# 5. WHEN IN DOUBT: Prefer NO selection over incorrect selection.
#    - A missing relevant node is better than including an irrelevant one that
#      introduces confusion or hallucination risk.

# SELECTION RULES:
# - Select nodes that DIRECTLY answer the query or are essential for understanding.
# - Do NOT select nodes that only partially or tangentially relate (keyword coincidence).
# - Do NOT select nodes from unrelated topics (e.g., code algorithms when query is about
#   project phases).
# - Do NOT invent node IDs — use ONLY IDs from the tree below.
# - If nothing is relevant, return an empty list.

# QUERY:
# {query}

# DOCUMENT TREE:
# {tree_text}

# OUTPUT FORMAT (ONLY valid JSON, no markdown or explanations):
# {{
#   "selected_node_ids": ["1.2", "3.1.2"],
#   "reason": "Nodes X and Y directly answer the query about [topic]. Node Z excluded because [reason]."
# }}

# If no nodes are relevant:
# {{
#   "selected_node_ids": [],
#   "reason": "No nodes contain information relevant to this query."
# }}
# """


def generate_tree_multi_node_selection_prompt(query: str, tree_text: str) -> str:
    return f"""
You are an expert hierarchical retrieval engine.

Your task is to identify all nodes that may contain information useful for answering the user's query.

TREE STRUCTURE:
Each node contains:
- node_id
- title
- summary
- keywords
- sub_nodes

RETRIEVAL RULES:

1. Understand the semantic meaning of the query.
2. Match against node titles, summaries, and keywords.
3. Do NOT rely only on exact keyword matching.
4. Include nodes containing:
   - Direct answers
   - Supporting context
   - Related concepts required to generate a complete answer
5. Consider parent-child relationships.
6. A node may be relevant even if it uses different wording than the query.
7. Exclude clearly unrelated nodes.
8. Return all potentially useful nodes ranked by relevance.

OUTPUT RULES:
- Return ONLY valid JSON.
- No explanations outside JSON.
- Do not generate the final answer.
- Only identify relevant nodes.

Output Format:

{{
    "query": "{query}",
    "selected_nodes": [
        {{
            "node_id": "node_id",
            "relevance_score": 95,
            "reason": "short reason"
        }}
    ]
}}

USER QUERY:
{query}

TREE:
{tree_text}
"""