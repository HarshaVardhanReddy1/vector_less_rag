

def finalize_tree(tree):

    tree = remove_duplicates(tree)

    tree = sort_nodes(tree)

    tree = fix_page_ranges(tree)

    tree = rebuild_node_ids(tree)

    return tree

def remove_duplicates(nodes):

    seen = set()

    unique_nodes = []

    for node in nodes:

        key = (
            node["title"],
            node["start_index"],
            node["end_index"]
        )

        if key not in seen:

            seen.add(key)

            node["sub_nodes"] = remove_duplicates(
                node.get("sub_nodes", [])
            )

            unique_nodes.append(node)

    return unique_nodes

def sort_nodes(nodes):

    nodes.sort(
        key=lambda x: (
            x["start_index"],
            x["end_index"]
        )
    )

    for node in nodes:
        sort_nodes(node.get("sub_nodes", []))

    return nodes

def fix_page_ranges(nodes):

    for node in nodes:

        children = node.get("sub_nodes", [])

        if children:

            fix_page_ranges(children)

            child_start = min(
                child["start_index"]
                for child in children
            )

            child_end = max(
                child["end_index"]
                for child in children
            )

            node["start_index"] = min(
                node["start_index"],
                child_start
            )

            node["end_index"] = max(
                node["end_index"],
                child_end
            )

    return nodes

def rebuild_node_ids(nodes, parent_id=""):

    for index, node in enumerate(nodes, start=1):

        if parent_id:
            node_id = f"{parent_id}.{index}"
        else:
            node_id = f"{index:04d}"

        node["node_id"] = node_id

        rebuild_node_ids(
            node.get("sub_nodes", []),
            node_id
        )

    return nodes