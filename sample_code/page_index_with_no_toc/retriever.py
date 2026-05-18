from sample_code.page_index_with_no_toc.open_ai_llm import generate_response
from sample_code.page_index_with_no_toc.prompts import (
    generate_context_grounded_answer_prompt,
    generate_full_tree_node_selection_prompt,
    generate_single_level_node_selection_prompt,
)
from sample_code.page_index_with_no_toc.utils import (
    append_query_response,
    ensure_valid_json,
    find_node_by_id,
    format_candidate_nodes,
    format_node,
    format_retrieved_context,
    flatten_tree,
    load_json_data,
)


DEFAULT_TREE_PATH = "json_files/tree_from_toc1.json"
DEFAULT_PAGES_PATH = "json_files/pdf_pages1.json"
DEFAULT_QUERY_LOG_PATH = "json_files/query_response_log.json"


def answer_query(
    query: str,
    tree_path: str = DEFAULT_TREE_PATH,
    pages_path: str = DEFAULT_PAGES_PATH,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
) -> dict:
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
        append_query_response(result, log_path=log_path)
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
    append_query_response(result, log_path=log_path)
    return result


def retrieve_context_for_query(
    query: str,
    tree_path: str = DEFAULT_TREE_PATH,
    pages_path: str = DEFAULT_PAGES_PATH,
) -> dict | None:
    relevant_node = retrieve_relevant_node(
        query=query,
        tree_path=tree_path,
    )

    if relevant_node is None:
        return None

    return get_context_from_node_id(
        node_id=relevant_node["node_id"],
        tree_path=tree_path,
        pages_path=pages_path,
    )


def retrieve_relevant_node(
    query: str,
    tree_path: str = DEFAULT_TREE_PATH,
) -> dict | None:
    tree = load_json_data(tree_path)

    deepest_node = find_deepest_matching_node(
        query=query,
        candidate_nodes=tree,
        parent_node=None,
    )

    if deepest_node is not None:
        return deepest_node

    fallback_node = select_best_matching_node_from_full_tree(
        query=query,
        tree=tree,
    )

    return fallback_node


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

    if deeper_match is not None:
        return deeper_match

    return selected_node


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
    parsed = ensure_valid_json(response)

    selected_id = parsed.get("selected_node_id")
    if selected_id is None:
        selected_ids = parsed.get("selected_node_ids", [])
        if selected_ids:
            selected_id = selected_ids[0]

    if not selected_id:
        return None

    for node in candidate_nodes:
        if node["node_id"] == selected_id:
            return node

    return None


def select_best_matching_node_from_full_tree(
    query: str,
    tree: list[dict],
) -> dict | None:
    if not tree:
        return None

    prompt = generate_full_tree_node_selection_prompt(
        query=query,
        full_tree_candidates_text=format_candidate_nodes(flatten_tree(tree)),
    )
    response = generate_response(prompt)
    parsed = ensure_valid_json(response)

    selected_id = parsed.get("selected_node_id")
    if selected_id is None:
        selected_ids = parsed.get("selected_node_ids", [])
        if selected_ids:
            selected_id = selected_ids[0]

    if not selected_id:
        return None

    return find_node_by_id(tree, selected_id)


def get_context_from_node_id(
    node_id: str,
    tree_path: str = DEFAULT_TREE_PATH,
    pages_path: str = DEFAULT_PAGES_PATH,
) -> dict:
    tree = load_json_data(tree_path)
    pages = load_json_data(pages_path)

    node = find_node_by_id(tree, node_id)
    if node is None:
        raise ValueError(f"Node ID '{node_id}' not found in tree.")

    selected_pages = []
    for i in range(node["start_index"] - 1, node["end_index"]):
        selected_pages.append(pages[i])

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


def generate_answer_prompt(query: str, retrieved_context: dict) -> str:
    return generate_context_grounded_answer_prompt(
        query=query,
        retrieved_contexts_text=format_retrieved_context(retrieved_context),
    )

if __name__ == "__main__":
    query = input("Enter your query: ")
    response = answer_query(query)
    print(response)
