from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.repositories.document_repository import fetch_document_by_id, list_documents
from backend.retrieval.answer_engine import stream_answer_query
from backend.services.document_service import (
    answer_document_query,
    build_document_index,
    run_document_pipeline_background,
    save_and_register_document,
)


router = APIRouter()


@router.get("/")
def read_root():
    return {"Hello": "World"}


@router.post("/documents/upload")
async def upload_document_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Save PDF and kick off processing in the background.

    Returns immediately with document_id and status=PROCESSING.
    Poll GET /documents/{document_id}/status to track progress.
    """
    document_id, document_paths, is_new = await save_and_register_document(file)

    if is_new:
        background_tasks.add_task(
            run_document_pipeline_background,
            document_id,
            document_paths["pdf_path"],
            document_paths["toc_path"],
            document_paths["tree_path"],
        )
        return {
            "message":     "Document upload received. Processing started in the background.",
            "document_id": document_id,
            "status":      "PROCESSING",
        }

    # Already processed — return the existing record info.
    saved = fetch_document_by_id(document_id)
    return {
        "message":       "Document already processed.",
        "document_id":   document_id,
        "document_name": saved["document_name"],
        "total_nodes":   saved["total_nodes"],
        "status":        "READY",
    }


@router.get("/documents/{document_id}/status")
async def document_status_endpoint(document_id: str):
    """Poll this endpoint to track processing progress after upload."""
    document = fetch_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "document_id":   document_id,
        "status":        document.get("status"),
        "error_message": document.get("error_message"),
        "total_nodes":   document.get("total_nodes", 0),
    }


@router.post("/documents/{document_id}/index")
def index_document_endpoint(document_id: str):
    """Rebuild the retrieval tree from existing nodes."""
    return build_document_index(document_id)


@router.get("/documents")
async def list_documents_endpoint():
    return {"documents": list_documents()}


@router.get("/documents/{document_id}/query/stream")
async def stream_query_endpoint(document_id: str, query: str, evaluate: bool = True):
    """Stream answer tokens via Server-Sent Events.

    Emits these event types:
      {"type": "meta", "selected_nodes": [...], "start_index": N}
      {"type": "token", "content": "..."}
      {"type": "eval", "reasoning": "...", "confidence": "...", "metrics": {...}}
      [DONE]

    Set evaluate=false to skip the LLM judge (no "eval" event is emitted).
    """
    document = fetch_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document.get("status") != "READY":
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready (status: {document.get('status', 'unknown')}).",
        )
    tree_path = document.get("tree_json_path")
    toc_path = document.get("nodes_json_path")
    if not tree_path or not toc_path:
        raise HTTPException(status_code=409, detail="Document index is incomplete.")

    return StreamingResponse(
        stream_answer_query(query=query, tree_path=tree_path, toc_path=toc_path, evaluate=evaluate),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/documents/{document_id}/query")
async def query_document_endpoint(
    document_id: str,
    query: str,
    evaluate: bool = True,
):
    """Query a document by its ID. Paths are looked up server-side.

    Set evaluate=true to include faithfulness / relevance metrics in the
    response (adds one extra LLM call per query).
    """
    return answer_document_query(query=query, document_id=document_id, evaluate=evaluate)


@router.get("/documents/{document_id}")
async def fetch_document_endpoint(document_id: str):
    document = fetch_document_by_id(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document
