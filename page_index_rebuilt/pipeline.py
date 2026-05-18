from .config import DEFAULT_PAGES_PATH, DEFAULT_TOC_PATH, DEFAULT_TREE_PATH
from .retriever import answer_query
from .toc_generator import generate_toc
from .tree_builder import generate_tree_from_toc


def build_index(
    pages_path=DEFAULT_PAGES_PATH,
    toc_path=DEFAULT_TOC_PATH,
    tree_path=DEFAULT_TREE_PATH,
) -> dict:
    toc = generate_toc(pages_path=pages_path, output_path=toc_path)
    tree = generate_tree_from_toc(toc_path=toc_path, output_path=tree_path)
    return {
        "toc_path": str(toc_path),
        "tree_path": str(tree_path),
        "toc_nodes": len(toc),
        "root_nodes": len(tree),
    }


def answer_from_pages_json(
    query: str,
    pages_path=DEFAULT_PAGES_PATH,
    tree_path=DEFAULT_TREE_PATH,
) -> dict:
    return answer_query(query=query, tree_path=tree_path, pages_path=pages_path)
