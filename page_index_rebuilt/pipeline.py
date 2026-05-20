from .config import DEFAULT_PAGES_PATH, DEFAULT_TOC_PATH, DEFAULT_TREE_PATH
from .retriever import answer_query
from .toc_generator import generate_toc
from .tree_builder import generate_tree_from_toc


def build_index(
    pages_path=DEFAULT_PAGES_PATH,
    toc_path=DEFAULT_TOC_PATH,
    tree_path=DEFAULT_TREE_PATH,
) -> dict:
    try:
        toc = generate_toc(pages_path=pages_path, output_path=toc_path)
        tree = generate_tree_from_toc(toc_path=toc_path, output_path=tree_path)
        return {
            "toc_path": str(toc_path),
            "tree_path": str(tree_path),
            "toc_nodes": len(toc),
            "root_nodes": len(tree),
        }
    except Exception as error:
        raise RuntimeError(
            f"Failed to build index from pages '{pages_path}' with TOC output '{toc_path}' "
            f"and tree output '{tree_path}'."
        ) from error


def answer_from_pages_json(
    query: str,
    pages_path=DEFAULT_PAGES_PATH,
    tree_path=DEFAULT_TREE_PATH,
) -> dict:
    try:
        return answer_query(query=query, tree_path=tree_path, pages_path=pages_path)
    except Exception as error:
        raise RuntimeError(
            f"Failed to answer query {query!r} from pages '{pages_path}' using tree '{tree_path}'."
        ) from error
