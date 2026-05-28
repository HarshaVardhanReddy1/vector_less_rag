"""Tree-walking node selection — finds the deepest node that matches a query."""

from langsmith import traceable

from backend.core.llm import generate_response
from backend.prompts.retrieval import (
    generate_full_tree_node_selection_prompt,
    generate_single_level_node_selection_prompt,
)
from backend.utils.json_utils import ensure_valid_json
from backend.utils.node_utils import (
    find_node_by_id,
    flatten_tree,
    format_candidate_nodes,
    format_node,
    validate_selection_response,
)


SELECTION_VALIDATION_REQUIREMENTS = """
Return a JSON object with:
- selected_node_id: either null or a dotted numeric string like 1 or 1.2 or 2.3.1
- reason: non-empty string
If selected_node_id is not null, it must be one of the provided candidate node IDs.
Do not invent node IDs.
"""


@traceable(run_type="retriever", name="Retriever · select_best_matching_node")
def select_best_matching_node(
    query: str,
    candidate_nodes: list[dict],
    parent_node: dict | None = None,
) -> dict | None:
    if not candidate_nodes:
        return None

    parent_context = ""
    if parent_node is not None:
        parent_context = f"\nPARENT NODE:\n{format_node(parent_node)}\n"

    prompt = generate_single_level_node_selection_prompt(
        query=query,
        candidate_nodes_text=format_candidate_nodes(candidate_nodes),
        parent_node_text=parent_context,
    )
    response        = generate_response(prompt)
    allowed_node_ids = {node["node_id"] for node in candidate_nodes}
    parsed          = ensure_valid_json(
        response,
        validator=lambda data: validate_selection_response(data, allowed_node_ids),
        validation_requirements=SELECTION_VALIDATION_REQUIREMENTS,
    )

    selected_id = parsed.get("selected_node_id")
    if not selected_id:
        return None

    for node in candidate_nodes:
        if node["node_id"] == selected_id:
            return node

    return None


@traceable(run_type="retriever", name="Retriever · find_deepest_matching_node")
def find_deepest_matching_node(
    query: str,
    candidate_nodes: list[dict],
    parent_node: dict | None = None,
) -> dict | None:
    selected = select_best_matching_node(
        query=query,
        candidate_nodes=candidate_nodes,
        parent_node=parent_node,
    )

    if selected is None:
        return None

    children = selected.get("sub_nodes", [])
    if not children:
        return selected

    deeper = find_deepest_matching_node(
        query=query,
        candidate_nodes=children,
        parent_node=selected,
    )
    return deeper if deeper is not None else selected


@traceable(run_type="retriever", name="Retriever · select_best_matching_node_from_full_tree")
def select_best_matching_node_from_full_tree(query: str, tree: list[dict]) -> dict | None:
    if not tree:
        return None

    prompt = generate_full_tree_node_selection_prompt(
        query=query,
        full_tree_candidates_text=format_candidate_nodes(flatten_tree(tree)),
    )
    response         = generate_response(prompt)
    allowed_node_ids = {node["node_id"] for node in flatten_tree(tree)}
    parsed           = ensure_valid_json(
        response,
        validator=lambda data: validate_selection_response(data, allowed_node_ids),
        validation_requirements=SELECTION_VALIDATION_REQUIREMENTS,
    )

    selected_id = parsed.get("selected_node_id")
    if not selected_id:
        return None

    return find_node_by_id(tree, selected_id)


def retrieve_relevant_node(query: str, tree_path: str) -> dict | None:
    from backend.utils.json_utils import load_json_data
    try:
        tree = load_json_data(tree_path)
    except Exception as error:
        raise RuntimeError(f"Failed to load retrieval tree from '{tree_path}'.") from error

    deepest = find_deepest_matching_node(query=query, candidate_nodes=tree)
    if deepest is not None:
        return deepest

    return select_best_matching_node_from_full_tree(query=query, tree=tree)
