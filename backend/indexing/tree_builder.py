"""Pure tree logic — no file I/O.

build_tree_from_nodes — nests flat heading nodes into a tree using their node_id field
"""

from backend.utils.node_utils import normalize_title


def build_tree_from_nodes(nodes: list[dict]) -> list[dict]:
    """Build a nested retrieval tree from enriched heading nodes.

    Each node must have at minimum:
        heading, node_id (dotted string like "1" or "1.2.3"), page, summary, keywords

    Parent-child relationships are derived directly from the dotted node_id:
        "1.2.3" → parent is "1.2" → grandparent is "1"

    Returns a nested tree. node_ids are already assigned — no rebuild step needed.
    """
    if not nodes:
        return []

    root_nodes: list[dict]      = []
    id_to_node: dict[str, dict] = {}

    for node in nodes:
        node_id = node["node_id"]
        tree_node = {
            "node_id":     node_id,
            "title":       normalize_title(node["heading"]),
            "start_index": node["page"],
            "summary":     node.get("summary", ""),
            "keywords":    node.get("keywords", []),
            "sub_nodes":   [],
        }
        id_to_node[node_id] = tree_node

        dot_pos = node_id.rfind(".")
        if dot_pos == -1:
            root_nodes.append(tree_node)
        else:
            parent_id = node_id[:dot_pos]
            parent = id_to_node.get(parent_id)
            if parent is not None:
                parent["sub_nodes"].append(tree_node)
            else:
                print(f"  Warning: parent '{parent_id}' not found for '{node_id}'. Attaching to root.")
                root_nodes.append(tree_node)

    return root_nodes
