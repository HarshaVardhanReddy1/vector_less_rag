from .config import  DEFAULT_QUERY_LOG_PATH 
from .llm import generate_response
from .prompts import (
    generate_context_grounded_answer_prompt,
    generate_full_tree_node_selection_prompt,
    generate_single_level_node_selection_prompt,
)
from .utils import (
    append_query_response,
    ensure_valid_json,
    find_node_by_id,
    flatten_tree,
    format_candidate_nodes,
    format_node,
    format_retrieved_context,
    get_pages_in_range,
    load_json_data,
    validate_selection_response,
)


SELECTION_VALIDATION_REQUIREMENTS = """
Return a JSON object with:
- selected_node_id: either null or a dotted numeric string like 0001 or 0001.2
- reason: non-empty string
If selected_node_id is not null, it must be one of the provided candidate node IDs.
Do not invent node IDs.
"""


def select_best_matching_node(
    query: str,
    candidate_nodes: list[dict],
    parent_node: dict | None = None,
) -> dict | None:
    if not candidate_nodes:
        return None

    parent_context = ""
    if parent_node is not None:
        parent_context = f"""
PARENT NODE:
{format_node(parent_node)}
"""

    prompt = generate_single_level_node_selection_prompt(
        query=query,
        candidate_nodes_text=format_candidate_nodes(candidate_nodes),
        parent_node_text=parent_context,
    )
    response = generate_response(prompt)
    allowed_node_ids = {node["node_id"] for node in candidate_nodes}
    parsed = ensure_valid_json(
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


def find_deepest_matching_node(
    query: str,
    candidate_nodes: list[dict],
    parent_node: dict | None = None,
) -> dict | None:
    selected_node = select_best_matching_node(
        query=query,
        candidate_nodes=candidate_nodes,
        parent_node=parent_node,
    )

    if selected_node is None:
        return None

    children = selected_node.get("sub_nodes", [])
    if not children:
        return selected_node

    deeper_match = find_deepest_matching_node(
        query=query,
        candidate_nodes=children,
        parent_node=selected_node,
    )

    return deeper_match if deeper_match is not None else selected_node


def select_best_matching_node_from_full_tree(query: str, tree: list[dict]) -> dict | None:
    if not tree:
        return None

    prompt = generate_full_tree_node_selection_prompt(
        query=query,
        full_tree_candidates_text=format_candidate_nodes(flatten_tree(tree)),
    )
    response = generate_response(prompt)
    allowed_node_ids = {node["node_id"] for node in flatten_tree(tree)}
    parsed = ensure_valid_json(
        response,
        validator=lambda data: validate_selection_response(data, allowed_node_ids),
        validation_requirements=SELECTION_VALIDATION_REQUIREMENTS,
    )

    selected_id = parsed.get("selected_node_id")
    if not selected_id:
        return None

    return find_node_by_id(tree, selected_id)


def retrieve_relevant_node(query: str, tree_path:str) -> dict | None:
    try:
        tree = load_json_data(tree_path)
    except Exception as error:
        raise RuntimeError(f"Failed to load retrieval tree from '{tree_path}'.") from error

    deepest_node = find_deepest_matching_node(query=query, candidate_nodes=tree)
    if deepest_node is not None:
        return deepest_node

    return select_best_matching_node_from_full_tree(query=query, tree=tree)


def get_context_from_node_id(
    node_id: str,
    tree_path:str,
    pages_path:str,
) -> dict:
    try:
        tree = load_json_data(tree_path)
        pages = load_json_data(pages_path)
    except Exception as error:
        raise RuntimeError(
            f"Failed to load retrieval inputs for node '{node_id}' from '{tree_path}' and "
            f"'{pages_path}'."
        ) from error

    node = find_node_by_id(tree, node_id)
    if node is None:
        raise ValueError(f"Node ID '{node_id}' not found in tree.")

    selected_pages = get_pages_in_range(
        pages=pages,
        start_page=node["start_index"],
        end_page=node["end_index"],
    )
    context = "\n\n".join(
        f"=============== PAGE {page['page']} START ===============\n"
        f"{page['page_text']}\n"
        f"=============== PAGE {page['page']} END ==============="
        for page in selected_pages
    )

    return {
        "node_id": node["node_id"],
        "title": node["title"],
        "summary": node["summary"],
        "start_index": node["start_index"],
        "end_index": node["end_index"],
        "context": context,
    }


def retrieve_context_for_query(
    query: str,
    tree_path:str,
    pages_path:str,
) -> dict | None:
    relevant_node = retrieve_relevant_node(query=query, tree_path=tree_path)
    if relevant_node is None:
        return None

    return get_context_from_node_id(
        node_id=relevant_node["node_id"],
        tree_path=tree_path,
        pages_path=pages_path,
    )


def generate_answer_prompt(query: str, retrieved_context: dict) -> str:
    return generate_context_grounded_answer_prompt(
        query=query,
        retrieved_context_text=format_retrieved_context(retrieved_context),
    )


def answer_query(
    query: str,
    tree_path:str,
    pages_path:str,
    log_path:str = DEFAULT_QUERY_LOG_PATH,
) -> dict:
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            pages_path=pages_path,
        )

        if retrieved_context is None:
            result = {
                "query": query,
                "selected_node": None,
                "answer": "No relevant nodes were found for the query.",
            }
            append_query_response(result, log_path)
            return result

        answer_prompt = generate_answer_prompt(query, retrieved_context)
        answer = generate_response(answer_prompt)

        result = {
            "query": query,
            "selected_node": {
                "node_id": retrieved_context["node_id"],
                "title": retrieved_context["title"],
                "start_index": retrieved_context["start_index"],
                "end_index": retrieved_context["end_index"],
            },
            "answer": answer,
        }
        append_query_response(result, log_path)
        return result
    except Exception as error:
        raise RuntimeError(
            f"Failed to answer query {query!r} using tree '{tree_path}' and pages '{pages_path}'."
        ) from error
