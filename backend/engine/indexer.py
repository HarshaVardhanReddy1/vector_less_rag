from langsmith import traceable

from .toc_generator import generate_toc
from .tree_builder import generate_tree_from_toc
from .utils import load_json_data


@traceable(run_type="chain", name="Pipeline · build_index")
def build_index(
    pages_path: str,
    toc_path: str,
    tree_path: str,
) -> dict:
    try:
        toc = generate_toc(pages_path=pages_path, output_path=toc_path)
        pages_data = load_json_data(pages_path)
        document_end_index = len(pages_data)
        tree = generate_tree_from_toc(
            toc_path=toc_path,
            output_path=tree_path,
            document_end_index=document_end_index,
        )
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
