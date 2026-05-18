import json
import re
from pathlib import Path
from typing import Any, Callable

from .llm import generate_response
from .prompts import generate_json_fix_prompt


JSONValidator = Callable[[Any], Any]


NODE_ID_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")


def load_json_data(json_path: str | Path) -> Any:
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json_data(data: Any, output_path: str | Path) -> None:
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_pages_in_range(pages: list[dict], start_page: int, end_page: int) -> list[dict]:
    if (
        not isinstance(start_page, int)
        or not isinstance(end_page, int)
        or isinstance(start_page, bool)
        or isinstance(end_page, bool)
    ):
        raise ValueError("Page range bounds must be integers.")

    if start_page < 1 or end_page < start_page:
        raise ValueError(
            f"Invalid page range {start_page}-{end_page}. Expected 1-based inclusive bounds."
        )

    pages_by_number: dict[int, dict] = {}
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(f"Page entry at index {index} must be a JSON object.")

        page_number = page.get("page")
        if not isinstance(page_number, int) or isinstance(page_number, bool) or page_number < 1:
            raise ValueError(f"Page entry at index {index} must have an integer 'page' >= 1.")

        if page_number in pages_by_number:
            raise ValueError(f"Duplicate page number {page_number} found in pages JSON.")

        pages_by_number[page_number] = page

    selected_pages: list[dict] = []
    missing_pages: list[int] = []
    for page_number in range(start_page, end_page + 1):
        page = pages_by_number.get(page_number)
        if page is None:
            missing_pages.append(page_number)
            continue
        selected_pages.append(page)

    if missing_pages:
        missing_pages_text = ", ".join(str(page_number) for page_number in missing_pages)
        raise ValueError(
            f"Pages JSON is missing page numbers required for range {start_page}-{end_page}: "
            f"{missing_pages_text}"
        )

    return selected_pages


def _serialize_json_candidate(json_candidate: Any) -> str:
    if isinstance(json_candidate, str):
        return json_candidate
    return json.dumps(json_candidate, ensure_ascii=False, indent=2)


def ensure_valid_json(
    json_context: Any,
    max_retries: int = 3,
    validator: JSONValidator | None = None,
    validation_requirements: str = "",
) -> Any:
    current_response = json_context
    

    for _ in range(max_retries):
        try:
            parsed_response = (
                current_response
                if isinstance(current_response, (list, dict))
                else json.loads(current_response)
            )
            return validator(parsed_response) if validator is not None else parsed_response
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            repair_prompt = generate_json_fix_prompt(
                _serialize_json_candidate(current_response),
                str(error),
                validation_requirements=validation_requirements,
            )
            current_response = generate_response(repair_prompt)

    raise ValueError("Failed to parse and validate LLM response as valid JSON.")


def _validate_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Field '{field_name}' must be a string.")

    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"Field '{field_name}' must be a non-empty string.")

    return normalized_value


def _validate_node_id(value: Any, field_name: str = "node_id") -> str:
    node_id = _validate_non_empty_string(value, field_name)
    if not NODE_ID_PATTERN.fullmatch(node_id):
        raise ValueError(
            f"Field '{field_name}' must use dotted numeric notation like '1' or '1.2.3'."
        )
    return node_id


def validate_toc_nodes(json_data: Any) -> list[dict]:
    if not isinstance(json_data, list):
        raise ValueError("TOC output must be a JSON array.")

    validated_nodes: list[dict] = []
    seen_node_ids: set[str] = set()

    for index, item in enumerate(json_data):
        if not isinstance(item, dict):
            raise ValueError(f"TOC node at index {index} must be a JSON object.")

        title = _validate_non_empty_string(item.get("title"), f"title[{index}]")
        node_id = _validate_node_id(item.get("node_id"), f"node_id[{index}]")

        page_number = item.get("page_number")
        if not isinstance(page_number, int) or isinstance(page_number, bool) or page_number < 1:
            raise ValueError(f"Field 'page_number[{index}]' must be an integer >= 1.")

        summary = _validate_non_empty_string(item.get("summary"), f"summary[{index}]")

        if node_id in seen_node_ids:
            raise ValueError(f"Duplicate node_id '{node_id}' found in TOC output.")
        seen_node_ids.add(node_id)

        validated_nodes.append(
            {
                "title": title,
                "node_id": node_id,
                "page_number": page_number,
                "summary": summary,
            }
        )

    return validated_nodes


def validate_selection_response(
    json_data: Any,
    allowed_node_ids: set[str] | None = None,
) -> dict:
    if not isinstance(json_data, dict):
        raise ValueError("Selection output must be a JSON object.")

    selected_node_id = json_data.get("selected_node_id")
    reason = _validate_non_empty_string(json_data.get("reason"), "reason")

    if selected_node_id is None:
        return {"selected_node_id": None, "reason": reason}

    validated_node_id = _validate_node_id(selected_node_id, "selected_node_id")

    if allowed_node_ids is not None and validated_node_id not in allowed_node_ids:
        raise ValueError(
            f"Selected node_id '{validated_node_id}' is not present in the allowed candidates."
        )

    return {"selected_node_id": validated_node_id, "reason": reason}


def flatten_tree(nodes: list[dict]) -> list[dict]:
    flattened_nodes = []

    for node in nodes:
        flattened_nodes.append(node)
        flattened_nodes.extend(flatten_tree(node.get("sub_nodes", [])))

    return flattened_nodes


def find_node_by_id(nodes: list[dict], node_id: str) -> dict | None:
    for node in nodes:
        if node["node_id"] == node_id:
            return node

        found = find_node_by_id(node.get("sub_nodes", []), node_id)
        if found is not None:
            return found

    return None


def format_node(node: dict) -> str:
    return json.dumps(
        {
            "node_id": node["node_id"],
            "title": node["title"],
            "summary": node["summary"],
            "start_index": node["start_index"],
            "end_index": node["end_index"],
        },
        ensure_ascii=False,
    )


def format_candidate_nodes(nodes: list[dict]) -> str:
    return "\n".join(format_node(node) for node in nodes)


def format_retrieved_context(item: dict) -> str:
    return f"""NODE ID: {item['node_id']}
TITLE: {item['title']}
SUMMARY: {item['summary']}
PAGE RANGE: {item['start_index']} - {item['end_index']}
CONTEXT:
{item['context']}"""


def append_query_response(query_response: dict, log_path: str | Path) -> None:
    try:
        query_log = load_json_data(log_path)
    except FileNotFoundError:
        query_log = []

    if not isinstance(query_log, list):
        raise ValueError(f"{log_path} must contain a JSON array.")

    query_log.append(query_response)
    save_json_data(query_log, log_path)
