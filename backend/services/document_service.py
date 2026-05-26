import re
from pathlib import Path

import pdfplumber
import tiktoken
from fastapi import HTTPException, UploadFile

from backend.repositories.document_repository import create_document_record, fetch_document_by_tree_path
from backend.engine.indexer import build_index
from backend.engine.retriever import answer_query
from backend.engine.utils import load_json_data, save_json_data


# backend/services/ -> backend/ -> project_1/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
PAGES_DIR = DATA_DIR / "pages"
TOCS_DIR = DATA_DIR / "tocs"
TREES_DIR = DATA_DIR / "trees"

MODEL_NAME = "openai/gpt-oss-120b:free"


def slugify_document_name(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return slug or "document"


def build_document_paths(document_slug: str) -> dict[str, Path]:
    return {
        "pdf_path": DOCS_DIR / f"{document_slug}.pdf",
        "pages_path": PAGES_DIR / f"{document_slug}.json",
        "toc_path": TOCS_DIR / f"{document_slug}.json",
        "tree_path": TREES_DIR / f"{document_slug}.json",
    }


def ensure_storage_directories() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    TOCS_DIR.mkdir(parents=True, exist_ok=True)
    TREES_DIR.mkdir(parents=True, exist_ok=True)


def get_token_encoder(model_name: str = MODEL_NAME):
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def extract_pages_from_pdf(pdf_path: Path) -> list[dict]:
    encoder = get_token_encoder()
    pages_data: list[dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            token_count = len(encoder.encode(page_text))
            pages_data.append(
                {
                    "page": page.page_number,
                    "page_text": page_text,
                    "token_count": token_count,
                }
            )

    return pages_data


async def upload_and_index_document(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    document_slug = slugify_document_name(file.filename)
    document_paths = build_document_paths(document_slug)
    ensure_storage_directories()

    try:
        if document_paths["tree_path"].exists():
            if not document_paths["pages_path"].exists():
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Tree file already exists for '{document_slug}', but pages JSON is missing: "
                        f"{document_paths['pages_path']}"
                    ),
                )

            pages_data = load_json_data(document_paths["pages_path"])
            saved_document = fetch_document_by_tree_path(str(document_paths["tree_path"]))

            if saved_document is None:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Tree file already exists for '{document_slug}', but no saved document record "
                        f"was found for: {document_paths['tree_path']}"
                    ),
                )

            index_info = {
                "toc_path": str(document_paths["toc_path"]),
                "tree_path": str(document_paths["tree_path"]),
                "reused_existing_index": True,
            }
            return {
                "message": "Document already indexed. Returning saved document details.",
                "document_id": saved_document["_id"],
                "document_name": saved_document["document_name"],
                "total_pages": saved_document["total_pages"],
                "paths": {
                    "pdf_path": saved_document["original_file_path"],
                    "pages_path": saved_document["pages_json_path"],
                    "toc_path": saved_document["toc_json_path"],
                    "tree_path": saved_document["tree_json_path"],
                },
                "index_info": index_info,
                "document": saved_document,
            }
        else:
            file_bytes = await file.read()
            document_paths["pdf_path"].write_bytes(file_bytes)

            pages_data = extract_pages_from_pdf(document_paths["pdf_path"])
            save_json_data(pages_data, document_paths["pages_path"])

            index_info = build_index(
                pages_path=document_paths["pages_path"],
                toc_path=document_paths["toc_path"],
                tree_path=document_paths["tree_path"],
            )

            document_id = create_document_record(
                document_name=file.filename,
                original_file_path=str(document_paths["pdf_path"]),
                pages_json_path=str(document_paths["pages_json_path"]),
                toc_json_path=str(document_paths["toc_path"]),
                tree_json_path=str(document_paths["tree_path"]),
                total_pages=len(pages_data),
            )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {error}") from error
    finally:
        await file.close()

    return {
        "message": "Document uploaded and indexed successfully.",
        "document_id": document_id,
        "document_name": file.filename,
        "total_pages": len(pages_data),
        "paths": {key: str(path) for key, path in document_paths.items()},
        "index_info": index_info,
    }


def answer_document_query(query: str, tree_path: str, pages_path: str) -> dict:
    try:
        return answer_query(
            query=query,
            tree_path=tree_path,
            pages_path=pages_path,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Query failed: {error}") from error
