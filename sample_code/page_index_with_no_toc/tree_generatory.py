import json
from pathlib import Path


DEFAULT_TOC_PATH = "json_files/toc1.json"
DEFAULT_OUTPUT_PATH = "json_files/tree_from_toc1.json"
DEFAULT_PAGES_PATH = "json_files/pdf_pages1.json"


def load_json_data(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_data(data, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_document_end_index(toc_data, pages_path=DEFAULT_PAGES_PATH):
    pages_file = Path(pages_path)

    if pages_file.exists():
        pages_data = load_json_data(pages_file)
        if pages_data:
            return max(item["page"] for item in pages_data)

    if toc_data:
        return max(item["page_number"] for item in toc_data)

    return 0


def sort_toc_nodes(toc_data):
    return sorted(
        toc_data,
        key=lambda item: (
            item["page_number"],
            len(item["node_id"].split(".")),
            [int(part) for part in item["node_id"].split(".")],
        ),
    )


def build_tree_from_toc(toc_data, document_end_index=None):
    if not toc_data:
        return []

    sorted_toc = sort_toc_nodes(toc_data)

    if document_end_index is None:
        document_end_index = get_document_end_index(sorted_toc)

    root_nodes = []
    stack = []

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
            parent_node = stack[-1][1]
            parent_node["sub_nodes"].append(node)
        else:
            root_nodes.append(node)

        stack.append((level, node))

    assign_end_indexes(root_nodes, document_end_index)
    rebuild_node_ids(root_nodes)

    return root_nodes


def assign_end_indexes(nodes, parent_end_index):
    for index, node in enumerate(nodes):
        next_sibling_start = (
            nodes[index + 1]["start_index"]
            if index + 1 < len(nodes)
            else parent_end_index + 1
        )

        sibling_boundary = max(node["start_index"], next_sibling_start - 1)

        if node["sub_nodes"]:
            assign_end_indexes(node["sub_nodes"], sibling_boundary)
            node["end_index"] = max(
                node["start_index"],
                max(child["end_index"] for child in node["sub_nodes"]),
            )
        else:
            node["end_index"] = sibling_boundary


def rebuild_node_ids(nodes, parent_id=""):
    for index, node in enumerate(nodes, start=1):
        if parent_id:
            node["node_id"] = f"{parent_id}.{index}"
        else:
            node["node_id"] = f"{index:04d}"

        rebuild_node_ids(node["sub_nodes"], node["node_id"])


def generate_tree_from_toc(
    toc_path=DEFAULT_TOC_PATH,
    output_path=DEFAULT_OUTPUT_PATH,
    document_end_index=None,
):
    toc_data = load_json_data(toc_path)
    tree = build_tree_from_toc(toc_data, document_end_index=document_end_index)
    save_json_data(tree, output_path)
    return tree


if __name__ == "__main__":
    print("Generating tree from TOC...")
    tree = generate_tree_from_toc()
    print(f"Tree generated with {len(tree)} root nodes.")
    print(f"Saved to {DEFAULT_OUTPUT_PATH}")
