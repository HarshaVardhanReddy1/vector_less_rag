
from .retriever import answer_query
from .toc_generator import generate_toc
from .tree_builder import generate_tree_from_toc
from .utils import load_json_data


def build_index(
    pages_path:str,
    toc_path:str,
    tree_path:str,
) -> dict:
    try:
        toc = generate_toc(pages_path=pages_path, output_path=toc_path)
        pages_data = load_json_data(pages_path)
        document_end_index = len(pages_data)
        print(document_end_index)
        tree = generate_tree_from_toc(toc_path=toc_path,output_path=tree_path,document_end_index=document_end_index)
        print("failed to build index")
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
    pages_path:str,
    tree_path:str,
) -> dict:
    try:
        return answer_query(query=query, tree_path=tree_path, pages_path=pages_path)
    except Exception as error:
        raise RuntimeError(
            f"Failed to answer query {query!r} from pages '{pages_path}' using tree '{tree_path}'."
        ) from error
