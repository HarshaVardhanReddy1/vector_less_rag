import json
from typing import Any

from sample_code.page_index_with_no_toc.open_ai_llm import generate_response
from sample_code.page_index_with_no_toc.prompts import generate_json_fix_prompt


def load_json_data(json_path: str) -> Any:
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_valid_json(json_context: Any, max_retries: int = 3) -> Any:
    current_response = json_context

    for _ in range(max_retries):
        if isinstance(current_response, (list, dict)):
            return current_response

        try:
            return json.loads(current_response)
        except json.JSONDecodeError as error:
            repair_prompt = generate_json_fix_prompt(current_response, str(error))
            current_response = generate_response(repair_prompt)

    raise ValueError("Failed to parse LLM response as valid JSON.")


def flatten_tree(nodes: list[dict]) -> list[dict]:
    flattened_nodes = []

    for parent in nodes:
        flattened_nodes.append(parent)
        child_nodes = flatten_tree(parent.get("sub_nodes", []))
        flattened_nodes.extend(child_nodes)

    return flattened_nodes


def find_node_by_id(nodes: list[dict], node_id: str) -> dict | None:
    for node in nodes:
        if node["node_id"] == node_id:
            return node

        found = find_node_by_id(node.get("sub_nodes", []), node_id)
        if found:
            return found

    return None


def append_query_response(query_response: dict, log_path: str) -> None:
    try:
        query_log = load_json_data(log_path)
    except FileNotFoundError:
        query_log = []

    if not isinstance(query_log, list):
        raise ValueError(f"{log_path} must contain a JSON array.")

    query_log.append(query_response)

    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(query_log, file, indent=4, ensure_ascii=False)


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

