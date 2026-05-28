"""Single-call node selection — sends the whole tree to the LLM and retrieves all relevant nodes."""

from langsmith import traceable

from backend.core.llm import generate_response
from backend.prompts.retrieval import generate_tree_multi_node_selection_prompt
from backend.utils.json_utils import ensure_valid_json
from backend.utils.node_utils import (
    find_node_by_id,
    flatten_tree,
    format_tree_for_prompt,
    validate_multi_selection_response,
)


MULTI_SELECTION_VALIDATION_REQUIREMENTS = """
Return a JSON object with:
- selected_node_ids: a JSON array of dotted numeric strings like ["1", "1.2", "2.3.1"]. Can be empty [].
- reason: non-empty string
All IDs in selected_node_ids must come from the provided tree. Do not invent IDs.
"""


@traceable(run_type="retriever", name="Retriever · select_relevant_nodes_from_tree")
def select_relevant_nodes_from_tree(query: str, tree: list[dict]) -> list[dict]:
    if not tree:
        return []

    tree_text        = format_tree_for_prompt(tree)
    prompt           = generate_tree_multi_node_selection_prompt(query=query, tree_text=tree_text)
    response         = generate_response(prompt)
    allowed_node_ids = {node["node_id"] for node in flatten_tree(tree)}

    parsed = ensure_valid_json(
        response,
        validator=lambda data: validate_multi_selection_response(data, allowed_node_ids),
        validation_requirements=MULTI_SELECTION_VALIDATION_REQUIREMENTS,
    )

    selected_ids = parsed.get("selected_node_ids", [])
    return [
        node
        for nid in selected_ids
        if (node := find_node_by_id(tree, nid)) is not None
    ]


def retrieve_relevant_nodes(query: str, tree_path: str) -> list[dict]:
    from backend.utils.json_utils import load_json_data
    try:
        tree = load_json_data(tree_path)
    except Exception as error:
        raise RuntimeError(f"Failed to load retrieval tree from '{tree_path}'.") from error

    return select_relevant_nodes_from_tree(query=query, tree=tree)
