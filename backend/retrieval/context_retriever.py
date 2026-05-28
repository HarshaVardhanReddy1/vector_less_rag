"""Assembles the text context for a selected tree node."""

from backend.utils.json_utils import load_json_data
from backend.utils.node_utils import find_node_by_id
from backend.retrieval.node_selector import retrieve_relevant_node


def get_context_from_node_id(
    node_id: str,
    tree_path: str,
    nodes_path: str,
) -> dict:
    """Retrieve the text context for a given tree node.

    Context is assembled from all flat heading nodes whose node_id matches
    the selected tree node exactly or is a descendant (prefix match),
    concatenated in document order.
    """
    try:
        tree  = load_json_data(tree_path)
        nodes = load_json_data(nodes_path)
    except Exception as error:
        raise RuntimeError(
            f"Failed to load retrieval inputs for node '{node_id}'."
        ) from error

    node = find_node_by_id(tree, node_id)
    if node is None:
        raise ValueError(f"Node ID '{node_id}' not found in tree.")

    selected_nodes = [
        n for n in nodes
        if n.get("node_id") == node_id
        or n.get("node_id", "").startswith(node_id + ".")
    ]

    context = "\n\n".join(
        f"## {n['heading']}\n\n{n['content']}"
        for n in selected_nodes
    )

    return {
        "node_id":     node["node_id"],
        "title":       node["title"],
        "summary":     node["summary"],
        "start_index": node["start_index"],
        "context":     context,
    }


def retrieve_context_for_query(
    query: str,
    tree_path: str,
    nodes_path: str,
) -> dict | None:
    relevant_node = retrieve_relevant_node(query=query, tree_path=tree_path)
    if relevant_node is None:
        return None

    return get_context_from_node_id(
        node_id=relevant_node["node_id"],
        tree_path=tree_path,
        nodes_path=nodes_path,
    )
