from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.repositories.document_repository import fetch_document_by_id, list_documents
from backend.services.document_service import (
    answer_document_query,
    build_document_index,
    process_and_save_document,
)


router = APIRouter()


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.post("/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    """Step 1 — PDF → enriched nodes JSON."""
    return await process_and_save_document(file)


@router.post("/documents/{document_id}/index")
def index_document_endpoint(document_id: str):
    """Step 2 — nodes JSON → retrieval tree JSON."""
    return build_document_index(document_id)


@router.get("/documents")
async def list_documents_endpoint():
    return {"documents": list_documents()}


@router.get("/documents/query")
async def query_document_endpoint(query: str, tree_path: str, nodes_path: str):
    return answer_document_query(query=query, tree_path=tree_path, nodes_path=nodes_path)


@router.get("/documents/{document_id}")
async def fetch_document_endpoint(document_id: str):
    document = fetch_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document
