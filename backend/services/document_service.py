import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.config import DOCS_DIR, NODES_DIR, TOCS_DIR, TREES_DIR
from backend.repositories.document_repository import (
    create_pending_record,
    fetch_document_by_id,
    fetch_document_by_nodes_path,
    update_document_nodes,
    update_document_status,
    update_document_tree,
)
from backend.indexing.indexer import build_index
from backend.retrieval.answer_engine import answer_query
from backend.utils.json_utils import load_json_data
from backend.processing.pipeline import run_document_processing_pipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify_document_name(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "document"


def build_document_paths(document_slug: str) -> dict[str, Path]:
    return {
        "pdf_path": DOCS_DIR / f"{document_slug}.pdf",
        # The enriched/summarized nodes file is what gets queried at runtime.
        # It lives in tocs/; markdown + chunked intermediates stay in nodes/.
        "toc_path": TOCS_DIR / f"{document_slug}.json",
        "tree_path":  TREES_DIR / f"{document_slug}.json",
    }


def ensure_storage_directories() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    TOCS_DIR.mkdir(parents=True, exist_ok=True)
    TREES_DIR.mkdir(parents=True, exist_ok=True)


def _run_pdf_processing(pdf_path: Path, toc_path: Path) -> None:
    run_document_processing_pipeline(
        str(pdf_path),
        base_output_dir=str(NODES_DIR),
        toc_output_dir=str(toc_path.parent),
    )

    generated = toc_path.parent / f"{pdf_path.stem}.json"
    if generated.exists() and generated != toc_path:
        generated.rename(toc_path)


# ---------------------------------------------------------------------------
# Step 1a — Save file and register (fast, runs synchronously in request)
# ---------------------------------------------------------------------------

async def save_and_register_document(file: UploadFile) -> tuple[str, dict[str, Path], bool]:
    """Save the uploaded PDF and create a PENDING record. Returns (document_id, paths, is_new).

    If the document was already fully processed, returns is_new=False so the
    caller knows NOT to schedule a background task.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    document_slug  = slugify_document_name(file.filename)
    document_paths = build_document_paths(document_slug)
    ensure_storage_directories()

    try:
        # Already processed — return existing record, no background task needed.
        if document_paths["toc_path"].exists():
            saved = fetch_document_by_nodes_path(str(document_paths["toc_path"]))
            if saved:
                # Rebuild tree if missing (fast, pure Python, no LLM calls).
                if not document_paths["tree_path"].exists() or not saved.get("tree_json_path"):
                    build_index(
                        toc_path=str(document_paths["toc_path"]),
                        tree_path=str(document_paths["tree_path"]),
                    )
                    update_document_tree(saved["_id"], str(document_paths["tree_path"]))
                return saved["_id"], document_paths, False

        # New document — save PDF and create a PENDING record.
        file_bytes = await file.read()
        document_paths["pdf_path"].write_bytes(file_bytes)

        document_id = create_pending_record(
            document_name=file.filename,
            original_file_path=str(document_paths["pdf_path"]),
        )
        return document_id, document_paths, True

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to register document: {error}") from error
    finally:
        await file.close()


# ---------------------------------------------------------------------------
# Step 1b — Pipeline (slow, runs as a BackgroundTask)
# ---------------------------------------------------------------------------

def run_document_pipeline_background(
    document_id: str,
    pdf_path: Path,
    toc_path: Path,
    tree_path: Path,
) -> None:
    """Full processing pipeline: PDF → nodes → tree. Runs in a background task."""
    update_document_status(document_id, "PROCESSING")
    try:
        _run_pdf_processing(pdf_path, toc_path)
        nodes_data = load_json_data(toc_path)
        update_document_nodes(document_id, str(toc_path), len(nodes_data))

        build_index(toc_path=str(toc_path), tree_path=str(tree_path))
        update_document_tree(document_id, str(tree_path))

    except Exception as error:
        update_document_status(document_id, "FAILED", str(error))
        raise


# ---------------------------------------------------------------------------
# Step 2 — Index: nodes JSON → retrieval tree JSON
# ---------------------------------------------------------------------------

def build_document_index(document_id: str) -> dict:
    saved = fetch_document_by_id(document_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    toc_path    = Path(saved["nodes_json_path"])
    document_slug = toc_path.stem
    tree_path     = TREES_DIR / f"{document_slug}.json"

    try:
        if tree_path.exists() and saved.get("tree_json_path"):
            return {
                "message":               "Document already indexed.",
                "document_id":           document_id,
                "status":                "READY",
                "reused_existing_index": True,
                "paths": {
                    "toc_path": str(toc_path),
                    "tree_path":  str(tree_path),
                },
            }

        index_info = build_index(
            toc_path=str(toc_path),
            tree_path=str(tree_path),
        )
        update_document_tree(document_id, str(tree_path))

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Index build failed: {error}") from error

    return {
        "message":     "Retrieval tree built successfully.",
        "document_id": document_id,
        "status":      "READY",
        "paths": {
            "toc_path": str(toc_path),
            "tree_path":  str(tree_path),
        },
        "index_info": index_info,
    }


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def answer_document_query(query: str, document_id: str, evaluate: bool = True) -> dict:
    """Look up paths by document_id and answer the query."""
    saved = fetch_document_by_id(document_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    if saved.get("status") != "READY":
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready for querying (status: {saved.get('status', 'unknown')}).",
        )

    tree_path  = saved.get("tree_json_path")
    toc_path = saved.get("nodes_json_path")
    if not tree_path or not toc_path:
        raise HTTPException(status_code=409, detail="Document index is incomplete.")

    try:
        return answer_query(
            query=query,
            tree_path=tree_path,
            toc_path=toc_path,
            evaluate=evaluate,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Query failed: {error}") from error
