import json
import re
from pathlib import Path
from typing import Any

from backend.utils.json_utils import load_json_data, save_json_data


NODE_ID_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")

_MD_BOLD_RE   = re.compile(r"\*+")
_MD_ITALIC_RE = re.compile(r"(?<!\w)_+|_+(?!\w)")


def normalize_title(text: str) -> str:
    text = _MD_BOLD_RE.sub("", text)
    text = _MD_ITALIC_RE.sub("", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Field '{field_name}' must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"Field '{field_name}' must be a non-empty string.")
    return normalized


def _validate_node_id(value: Any, field_name: str = "node_id") -> str:
    node_id = _validate_non_empty_string(value, field_name)
    if not NODE_ID_PATTERN.fullmatch(node_id):
        raise ValueError(
            f"Field '{field_name}' must use dotted numeric notation like '1' or '1.2.3'."
        )
    return node_id


def validate_selection_response(
    json_data: Any,
    allowed_node_ids: set[str] | None = None,
) -> dict:
    if not isinstance(json_data, dict):
        raise ValueError("Selection output must be a JSON object.")

    selected_node_id = json_data.get("selected_node_id")
    reason           = _validate_non_empty_string(json_data.get("reason"), "reason")

    if selected_node_id is None:
        return {"selected_node_id": None, "reason": reason}

    validated_id = _validate_node_id(selected_node_id, "selected_node_id")

    if allowed_node_ids is not None and validated_id not in allowed_node_ids:
        raise ValueError(
            f"Selected node_id '{validated_id}' is not present in the allowed candidates."
        )

    return {"selected_node_id": validated_id, "reason": reason}


# ---------------------------------------------------------------------------
# Tree traversal
# ---------------------------------------------------------------------------

def flatten_tree(nodes: list[dict]) -> list[dict]:
    flat = []
    for node in nodes:
        flat.append(node)
        flat.extend(flatten_tree(node.get("sub_nodes", [])))
    return flat


def find_node_by_id(nodes: list[dict], node_id: str) -> dict | None:
    for node in nodes:
        if node["node_id"] == node_id:
            return node
        found = find_node_by_id(node.get("sub_nodes", []), node_id)
        if found is not None:
            return found
    return None


# ---------------------------------------------------------------------------
# Node formatting (for LLM prompts)
# ---------------------------------------------------------------------------

def format_node(node: dict) -> str:
    data: dict = {
        "node_id":     node["node_id"],
        "title":       node["title"],
        "summary":     node["summary"],
        "start_index": node["start_index"],
    }
    if node.get("keywords"):
        data["keywords"] = node["keywords"]
    return json.dumps(data, ensure_ascii=False)


def format_candidate_nodes(nodes: list[dict]) -> str:
    return "\n".join(format_node(node) for node in nodes)


def format_tree_for_prompt(nodes: list[dict], indent: int = 0) -> str:
    lines = []
    prefix = "  " * indent
    for node in nodes:
        lines.append(f"{prefix}[{node['node_id']}] {node['title']}")
        if node.get("summary"):
            lines.append(f"{prefix}  summary: {node['summary']}")
        if node.get("keywords"):
            lines.append(f"{prefix}  keywords: {', '.join(node['keywords'])}")
        sub_nodes = node.get("sub_nodes", [])
        if sub_nodes:
            lines.append(format_tree_for_prompt(sub_nodes, indent + 1))
    return "\n".join(lines)


def validate_multi_selection_response(
    json_data: Any,
    allowed_node_ids: set[str] | None = None,
) -> dict:
    if not isinstance(json_data, dict):
        raise ValueError("Selection output must be a JSON object.")

    selected_node_ids = json_data.get("selected_node_ids")
    reason = _validate_non_empty_string(json_data.get("reason"), "reason")

    if selected_node_ids is None or selected_node_ids == []:
        return {"selected_node_ids": [], "reason": reason}

    if not isinstance(selected_node_ids, list):
        raise ValueError("Field 'selected_node_ids' must be a JSON array.")

    validated_ids = []
    for nid in selected_node_ids:
        validated_id = _validate_node_id(nid, "selected_node_ids item")
        if allowed_node_ids is not None and validated_id not in allowed_node_ids:
            raise ValueError(
                f"Selected node_id '{validated_id}' is not present in the allowed candidates."
            )
        validated_ids.append(validated_id)

    return {"selected_node_ids": validated_ids, "reason": reason}


def format_retrieved_context(item: dict) -> str:
    if "node_ids" in item:
        node_ids_str = ", ".join(item["node_ids"])
        titles_str   = "; ".join(item["titles"])
        return (
            f"NODE IDs: {node_ids_str}\n"
            f"TITLES: {titles_str}\n"
            f"START PAGE: {item['start_index']}\n"
            f"CONTEXT:\n{item['context']}"
        )
    return (
        f"NODE ID: {item['node_id']}\n"
        f"TITLE: {item['title']}\n"
        f"SUMMARY: {item['summary']}\n"
        f"START PAGE: {item['start_index']}\n"
        f"CONTEXT:\n{item['context']}"
    )


# ---------------------------------------------------------------------------
# Query response logging
# ---------------------------------------------------------------------------

def append_query_response(query_response: dict, log_path: str | Path) -> None:
    try:
        query_log = load_json_data(log_path)
    except FileNotFoundError:
        query_log = []

    if not isinstance(query_log, list):
        raise ValueError(f"{log_path} must contain a JSON array.")

    query_log.append(query_response)
    save_json_data(query_log, log_path)
