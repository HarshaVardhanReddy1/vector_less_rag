"""File I/O entry point for tree building.

generate_tree_from_nodes — loads nodes, builds tree, saves tree file
build_index              — callable from the service layer
"""

from langsmith import traceable

from backend.indexing.tree_builder import build_tree_from_nodes
from backend.utils.json_utils import load_json_data, save_json_data


def generate_tree_from_nodes(nodes_path: str, output_path: str) -> list[dict]:
    """Load enriched nodes JSON, build tree, save tree file."""
    try:
        nodes = load_json_data(nodes_path)
        tree  = build_tree_from_nodes(nodes)
        save_json_data(tree, output_path)
        return tree
    except Exception as error:
        raise RuntimeError(
            f"Failed to build tree from nodes '{nodes_path}' into '{output_path}'."
        ) from error


@traceable(run_type="chain", name="Pipeline · build_index")
def build_index(nodes_path: str, tree_path: str) -> dict:
    try:
        nodes = load_json_data(nodes_path)
        tree  = generate_tree_from_nodes(
            nodes_path=nodes_path,
            output_path=tree_path,
        )
        return {
            "tree_path":   str(tree_path),
            "root_nodes":  len(tree),
            "total_nodes": len(nodes),
        }
    except Exception as error:
        raise RuntimeError(
            f"Failed to build index from nodes '{nodes_path}' into tree '{tree_path}'."
        ) from error
