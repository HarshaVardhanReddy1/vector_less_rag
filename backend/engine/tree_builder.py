from pathlib import Path

 
from .utils import load_json_data, save_json_data, validate_page_items, validate_toc_nodes


def get_document_end_index(toc_data: list[dict], pages_path: str|None=None) -> int:
    pages_file = Path(pages_path)

    if pages_file.exists():
        pages_data = validate_page_items(load_json_data(pages_file))
        if pages_data:
            return max(item["page"] for item in pages_data)

    if toc_data:
        return max(item["page_number"] for item in toc_data)

    return 0


def sort_toc_nodes(toc_data: list[dict]) -> list[dict]:
    return sorted(
        toc_data,
        key=lambda item: [int(part) for part in item["node_id"].split(".")],
    )


def assign_end_indexes(nodes: list[dict], parent_end_index: int) -> None:
    for index, node in enumerate(nodes):
        if index + 1 < len(nodes):
            # Keep the next sibling's start page in range so we do not miss
            # section text that continues onto the same page where the next
            # heading appears.
            sibling_boundary = max(node["start_index"], nodes[index + 1]["start_index"])
        else:
            sibling_boundary = max(node["start_index"], parent_end_index)

        if node["sub_nodes"]:
            assign_end_indexes(node["sub_nodes"], sibling_boundary)
            node["end_index"] = max(
                node["start_index"],
                max(child["end_index"] for child in node["sub_nodes"]),
            )
        else:
            node["end_index"] = sibling_boundary


def rebuild_node_ids(nodes: list[dict], parent_id: str = "") -> None:
    for index, node in enumerate(nodes, start=1):
        node["node_id"] = f"{parent_id}.{index}" if parent_id else f"{index:04d}"
        rebuild_node_ids(node["sub_nodes"], node["node_id"])


def build_tree_from_toc(toc_data: list[dict], document_end_index: int | None = None) -> list[dict]:
    if not toc_data:
        return []
    sorted_toc = sort_toc_nodes(validate_toc_nodes(toc_data))
    if document_end_index is None:
        document_end_index = get_document_end_index(sorted_toc)
    root_nodes: list[dict] = []
    stack: list[tuple[int, dict]] = []

    for item in sorted_toc:
        node = {
            "node_id": item["node_id"],
            "title": item["title"],
            "start_index": item["page_number"],
            "end_index": item["page_number"],
            "summary": item["summary"],
            "sub_nodes": [],
        }

        level = len(item["node_id"].split("."))

        while stack and stack[-1][0] >= level:
            stack.pop()

        if stack:
            stack[-1][1]["sub_nodes"].append(node)
        else:
            root_nodes.append(node)

        stack.append((level, node))

    assign_end_indexes(root_nodes, document_end_index)
    rebuild_node_ids(root_nodes)
    return root_nodes


def generate_tree_from_toc(
    toc_path:str,
    output_path:str,
    document_end_index: int | None = None,
) -> list[dict]:
    try:
    
        toc_data = load_json_data(toc_path)
        tree = build_tree_from_toc(toc_data, document_end_index=document_end_index)
        save_json_data(tree, output_path)
        return tree
    except Exception as error:
        raise RuntimeError(
            f"Failed to generate tree from TOC file '{toc_path}' into '{output_path}'."
        ) from error
