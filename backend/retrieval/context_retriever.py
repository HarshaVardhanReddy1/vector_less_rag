"""Assembles text context from all selected tree nodes."""

from backend.utils.json_utils import load_json_data
from backend.utils.node_utils import find_node_by_id
from backend.retrieval.node_selector import retrieve_relevant_nodes


def get_context_from_node_ids(
    node_ids: list[str],
    tree_path: str,
    nodes_path: str,
) -> dict | None:
    """Assemble combined context for a list of selected node IDs.

    For each ID, collects all flat heading nodes that match or are descendants
    (prefix match). Nodes are deduplicated and kept in document order.
    """
    if not node_ids:
        return None

    try:
        tree  = load_json_data(tree_path)
        nodes = load_json_data(nodes_path)
    except Exception as error:
        raise RuntimeError(
            f"Failed to load retrieval inputs for nodes {node_ids!r}."
        ) from error

    tree_nodes = [
        node
        for nid in node_ids
        if (node := find_node_by_id(tree, nid)) is not None
    ]
    if not tree_nodes:
        return None

    node_ids_set = {n["node_id"] for n in tree_nodes}

    seen: set[str] = set()
    selected_flat: list[dict] = []
    for flat_node in nodes:
        flat_nid = flat_node.get("node_id", "")
        if flat_nid in seen:
            continue
        for nid in node_ids_set:
            if flat_nid == nid or flat_nid.startswith(nid + "."):
                seen.add(flat_nid)
                selected_flat.append(flat_node)
                break

    context = "\n\n".join(
        f"## {n['heading']}\n\n{n['content']}"
        for n in selected_flat
    )

    return {
        "node_ids":      [n["node_id"] for n in tree_nodes],
        "titles":        [n["title"] for n in tree_nodes],
        "start_indices": [n["start_index"] for n in tree_nodes],
        "start_index":   min(n["start_index"] for n in tree_nodes),
        "context":       context,
    }


def retrieve_context_for_query(
    query: str,
    tree_path: str,
    nodes_path: str,
) -> dict | None:
    relevant_nodes = retrieve_relevant_nodes(query=query, tree_path=tree_path)
    if not relevant_nodes:
        return None

    return get_context_from_node_ids(
        node_ids=[n["node_id"] for n in relevant_nodes],
        tree_path=tree_path,
        nodes_path=nodes_path,
    )
