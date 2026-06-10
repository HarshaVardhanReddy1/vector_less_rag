"""Migration: Convert absolute paths to relative paths in MongoDB.

This script finds all documents with full file paths and converts them
to relative paths (just the filename).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")


def get_relative_path(full_path: str | None) -> str | None:
    """Extract just the filename from a full path."""
    if full_path is None:
        return None
    return Path(full_path).name


def migrate_documents():
    """Convert absolute paths to relative paths in MongoDB."""
    client = MongoClient(MONGO_URI)
    database = client[DB_NAME]
    documents_collection = database["documents_data"]

    # Find all documents that have full paths
    documents = documents_collection.find({
        "$or": [
            {"original_file_path": {"$ne": None}},
            {"nodes_json_path": {"$ne": None}},
            {"tree_json_path": {"$ne": None}},
        ]
    })

    updated_count = 0
    for doc in documents:
        doc_id = doc["_id"]
        original_path = doc.get("original_file_path")
        nodes_path = doc.get("nodes_json_path")
        tree_path = doc.get("tree_json_path")

        # Check if paths are already relative (just filename, no separators)
        is_original_relative = original_path is None or "/" not in original_path and "\\" not in original_path
        is_nodes_relative = nodes_path is None or "/" not in nodes_path and "\\" not in nodes_path
        is_tree_relative = tree_path is None or "/" not in tree_path and "\\" not in tree_path

        if is_original_relative and is_nodes_relative and is_tree_relative:
            print(f"  [{doc_id}] Already relative — skipping")
            continue

        # Convert to relative paths
        relative_original_path = get_relative_path(original_path) if not is_original_relative else original_path
        relative_nodes_path = get_relative_path(nodes_path) if not is_nodes_relative else nodes_path
        relative_tree_path = get_relative_path(tree_path) if not is_tree_relative else tree_path

        print(f"  [{doc_id}] Updating:")
        if not is_original_relative:
            print(f"    original_file_path: {original_path} -> {relative_original_path}")
        if not is_nodes_relative:
            print(f"    nodes_json_path: {nodes_path} -> {relative_nodes_path}")
        if not is_tree_relative:
            print(f"    tree_json_path: {tree_path} -> {relative_tree_path}")

        # Update document
        update_dict = {}
        if not is_original_relative:
            update_dict["original_file_path"] = relative_original_path
        if not is_nodes_relative:
            update_dict["nodes_json_path"] = relative_nodes_path
        if not is_tree_relative:
            update_dict["tree_json_path"] = relative_tree_path

        if update_dict:
            documents_collection.update_one(
                {"_id": doc_id},
                {"$set": update_dict},
            )
            updated_count += 1

    print(f"\nMigration complete. Updated {updated_count} documents.")
    client.close()


if __name__ == "__main__":
    print("Starting migration: absolute paths -> relative paths\n")
    migrate_documents()
