import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.repositories.document_repository import (
    create_document_record,
    fetch_document_by_id,
    fetch_document_by_nodes_path,
    update_document_tree,
)
from backend.indexing.indexer import build_index
from backend.retrieval.answer_engine import answer_query
from backend.utils.json_utils import load_json_data
from backend.processing.pipeline import run_document_processing_pipeline


# ---------------------------------------------------------------------------
# Storage paths
# ---------------------------------------------------------------------------

# backend/services/ -> backend/ -> project_1/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR     = PROJECT_ROOT / "data"
DOCS_DIR     = DATA_DIR / "docs"
NODES_DIR    = DATA_DIR / "nodes"
TREES_DIR    = DATA_DIR / "trees"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify_document_name(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "document"


def build_document_paths(document_slug: str) -> dict[str, Path]:
    return {
        "pdf_path":   DOCS_DIR  / f"{document_slug}.pdf",
        "nodes_path": NODES_DIR / f"{document_slug}.json",
        "tree_path":  TREES_DIR / f"{document_slug}.json",
    }


def ensure_storage_directories() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    TREES_DIR.mkdir(parents=True, exist_ok=True)


def _run_pdf_processing(pdf_path: Path, nodes_path: Path) -> None:
    """Run the document processing pipeline to produce enriched nodes JSON."""
    nodes_dir = str(nodes_path.parent)
    run_document_processing_pipeline(str(pdf_path), nodes_dir)

    # pdf_processor names the JSON after the PDF stem; rename to nodes_path if different.
    generated = nodes_path.parent / f"{pdf_path.stem}.json"
    if generated.exists() and generated != nodes_path:
        generated.rename(nodes_path)


# ---------------------------------------------------------------------------
# Step 1 — Upload and process: PDF → enriched nodes JSON
# ---------------------------------------------------------------------------

async def process_and_save_document(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    document_slug  = slugify_document_name(file.filename)
    document_paths = build_document_paths(document_slug)
    ensure_storage_directories()

    try:
        # Already processed? Return existing record.
        if document_paths["nodes_path"].exists():
            saved = fetch_document_by_nodes_path(str(document_paths["nodes_path"]))
            if saved:
                # Build tree if it was never created for this record.
                if not document_paths["tree_path"].exists() or not saved.get("tree_json_path"):
                    build_index(
                        nodes_path=str(document_paths["nodes_path"]),
                        tree_path=str(document_paths["tree_path"]),
                    )
                    update_document_tree(saved["_id"], str(document_paths["tree_path"]))
                nodes_data = load_json_data(document_paths["nodes_path"])
                return {
                    "message":       "Document already processed.",
                    "document_id":   saved["_id"],
                    "document_name": saved["document_name"],
                    "total_nodes":   len(nodes_data),
                    "status":        "READY",
                    "paths": {
                        "pdf_path":   str(document_paths["pdf_path"]),
                        "nodes_path": str(document_paths["nodes_path"]),
                        "tree_path":  str(document_paths["tree_path"]),
                    },
                }

        # Save PDF, run pipeline → nodes JSON.
        file_bytes = await file.read()
        document_paths["pdf_path"].write_bytes(file_bytes)

        _run_pdf_processing(document_paths["pdf_path"], document_paths["nodes_path"])

        nodes_data  = load_json_data(document_paths["nodes_path"])
        document_id = create_document_record(
            document_name=file.filename,
            original_file_path=str(document_paths["pdf_path"]),
            nodes_json_path=str(document_paths["nodes_path"]),
            total_nodes=len(nodes_data),
        )

        # Build tree immediately after nodes are ready.
        build_index(
            nodes_path=str(document_paths["nodes_path"]),
            tree_path=str(document_paths["tree_path"]),
        )
        update_document_tree(document_id, str(document_paths["tree_path"]))

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {error}") from error
    finally:
        await file.close()

    return {
        "message":       "Document processed and indexed successfully.",
        "document_id":   document_id,
        "document_name": file.filename,
        "total_nodes":   len(nodes_data),
        "status":        "READY",
        "paths": {
            "pdf_path":   str(document_paths["pdf_path"]),
            "nodes_path": str(document_paths["nodes_path"]),
            "tree_path":  str(document_paths["tree_path"]),
        },
    }


# ---------------------------------------------------------------------------
# Step 2 — Index: nodes JSON → retrieval tree JSON
# ---------------------------------------------------------------------------

def build_document_index(document_id: str) -> dict:
    saved = fetch_document_by_id(document_id)
    if saved is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    nodes_path    = Path(saved["nodes_json_path"])
    document_slug = nodes_path.stem
    tree_path     = TREES_DIR / f"{document_slug}.json"

    try:
        # Already indexed? Return existing.
        if tree_path.exists() and saved.get("tree_json_path"):
            return {
                "message":              "Document already indexed.",
                "document_id":          document_id,
                "status":               "READY",
                "reused_existing_index": True,
                "paths": {
                    "nodes_path": str(nodes_path),
                    "tree_path":  str(tree_path),
                },
            }

        index_info = build_index(
            nodes_path=str(nodes_path),
            tree_path=str(tree_path),
        )
        update_document_tree(document_id, str(tree_path))

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Index build failed: {error}") from error

    return {
        "message":      "Retrieval tree built successfully.",
        "document_id":  document_id,
        "status":       "READY",
        "paths": {
            "nodes_path": str(nodes_path),
            "tree_path":  str(tree_path),
        },
        "index_info": index_info,
    }


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def answer_document_query(query: str, tree_path: str, nodes_path: str) -> dict:
    try:
        return answer_query(
            query=query,
            tree_path=tree_path,
            nodes_path=nodes_path,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Query failed: {error}") from error
