from fastapi import APIRouter, File, HTTPException, UploadFile

from app.repositories.document_repository import fetch_document_by_id, list_documents
from app.services.document_service import answer_document_query, upload_and_index_document


router = APIRouter()


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.post("/documents/upload")
async def upload_document_endpoint(file: UploadFile = File(...)):
    return await upload_and_index_document(file)


@router.get("/documents")
async def list_documents_endpoint():
    return {"documents": list_documents()}


@router.get("/documents/query")
async def query_document_endpoint(query: str, tree_path: str, pages_path: str):
    return answer_document_query(query=query, tree_path=tree_path, pages_path=pages_path)


@router.get("/documents/{document_id}")
async def fetch_document_endpoint(document_id: str):
    document = fetch_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document
