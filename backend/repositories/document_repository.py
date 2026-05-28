from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from backend.core.database import documents_collection


def serialize_document(document: dict | None) -> dict | None:
    if document is None:
        return None

    document["_id"] = str(document["_id"])
    return document


def create_document_record(
    document_name: str,
    original_file_path: str,
    nodes_json_path: str,
    total_nodes: int,
) -> str:
    document_data = {
        "document_name":      document_name,
        "original_file_path": original_file_path,
        "nodes_json_path":    nodes_json_path,
        "tree_json_path":     None,
        "total_nodes":        total_nodes,
        "status":             "NODES_READY",
        "uploaded_at":        datetime.now(timezone.utc),
    }

    result = documents_collection.insert_one(document_data)
    return str(result.inserted_id)


def update_document_tree(document_id: str, tree_json_path: str) -> bool:
    try:
        object_id = ObjectId(document_id)
    except InvalidId:
        return False

    result = documents_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "tree_json_path": tree_json_path,
                "status":         "READY",
                "indexed_at":     datetime.now(timezone.utc),
            }
        },
    )
    return result.modified_count > 0


def list_documents() -> list[dict]:
    documents: list[dict] = []

    for document in documents_collection.find():
        documents.append(serialize_document(document))

    return documents


def fetch_document_by_id(document_id: str) -> dict | None:
    try:
        object_id = ObjectId(document_id)
    except InvalidId:
        return None

    document = documents_collection.find_one({"_id": object_id})
    return serialize_document(document)


def fetch_document_by_nodes_path(nodes_json_path: str) -> dict | None:
    document = documents_collection.find_one({"nodes_json_path": nodes_json_path})
    return serialize_document(document)
