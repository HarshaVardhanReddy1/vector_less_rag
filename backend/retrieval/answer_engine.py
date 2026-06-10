"""Answer generation — retrieves context, generates answer, evaluates, logs."""

import json
import re
from typing import Iterator

from langsmith import traceable

from backend.config import DEFAULT_QUERY_LOG_PATH
from backend.core.llm import generate_response, generate_response_stream
from backend.evaluation.evaluator import evaluate_answer
from backend.prompts.answer import generate_context_grounded_answer_prompt
from backend.retrieval.context_retriever import retrieve_context_for_query
from backend.utils.node_utils import (
    append_query_response,
    extract_image_refs_from_answer,
    format_retrieved_context,
    normalize_title,
)


def _build_answer_prompt(query: str, retrieved_context: dict) -> str:
    return generate_context_grounded_answer_prompt(
        query=query,
        retrieved_context_text=format_retrieved_context(retrieved_context),
    )


def _build_selected_nodes(retrieved_context: dict) -> list[dict]:
    """Build selected nodes metadata from retrieved context."""
    start_indices = retrieved_context.get(
        "start_indices",
        [retrieved_context["start_index"]] * len(retrieved_context["node_ids"]),
    )
    return [
        {"node_id": nid, "title": normalize_title(title), "page": page}
        for nid, title, page in zip(
            retrieved_context["node_ids"],
            retrieved_context["titles"],
            start_indices,
        )
    ]


def _process_answer(full_answer: str) -> tuple[str, list[dict]]:
    """Extract images and clean answer text. Returns (clean_answer, image_refs)."""
    image_refs = extract_image_refs_from_answer(full_answer)
    clean_answer = re.sub(r"<REFERENCED_IMAGES>[\s\S]*?</REFERENCED_IMAGES>", "", full_answer).rstrip()
    return clean_answer, image_refs


def _build_result(query: str, selected_nodes: list[dict], clean_answer: str, context_text: str, evaluate: bool) -> dict:
    """Build result dict with optional evaluation."""
    result = {
        "query": query,
        "selected_nodes": selected_nodes,
        "answer": clean_answer,
    }

    if evaluate:
        judgment = evaluate_answer(query=query, answer=clean_answer, context_text=context_text)
        result["reasoning"] = judgment.get("reasoning", "")
        result["confidence"] = judgment.get("confidence", "")
        result["metrics"] = judgment.get("metrics", {})

    return result


@traceable(run_type="chain", name="Pipeline · answer_query")
def answer_query(
    query: str,
    tree_path: str,
    toc_path: str,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
    evaluate: bool = True,
) -> dict:
    """Generate an answer for the given query."""
    try:
        retrieved_context = retrieve_context_for_query(query, tree_path, toc_path)

        if retrieved_context is None:
            result = {
                "query": query,
                "selected_nodes": [],
                "answer": "No relevant nodes were found for the query.",
            }
            append_query_response(result, log_path)
            return result

        answer_text = generate_response(_build_answer_prompt(query, retrieved_context))
        clean_answer, _ = _process_answer(answer_text)
        selected_nodes = _build_selected_nodes(retrieved_context)

        result = _build_result(
            query=query,
            selected_nodes=selected_nodes,
            clean_answer=clean_answer,
            context_text=format_retrieved_context(retrieved_context),
            evaluate=evaluate,
        )
        result["start_index"] = retrieved_context["start_index"]

        append_query_response(result, log_path)
        return result

    except Exception as error:
        raise RuntimeError(
            f"Failed to answer query {query!r} using tree '{tree_path}' and "
            f"nodes '{toc_path}'."
        ) from error


@traceable(run_type="chain", name="Pipeline · stream_answer_query")
def stream_answer_query(
    query: str,
    tree_path: str,
    toc_path: str,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
    evaluate: bool = True,
) -> Iterator[str]:
    """Stream answer tokens via SSE with metadata, images, and optional evaluation."""
    try:
        retrieved_context = retrieve_context_for_query(query, tree_path, toc_path)

        if retrieved_context is None:
            yield f"data: {json.dumps({'type': 'meta', 'selected_nodes': [], 'start_index': 0})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'content': 'No relevant nodes were found for the query.'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        selected_nodes = _build_selected_nodes(retrieved_context)
        yield f"data: {json.dumps({'type': 'meta', 'selected_nodes': selected_nodes, 'start_index': retrieved_context['start_index']})}\n\n"

        full_answer = ""
        for token in generate_response_stream(_build_answer_prompt(query, retrieved_context)):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        clean_answer, image_refs = _process_answer(full_answer)

        if image_refs:
            yield f"data: {json.dumps({'type': 'images', 'images': image_refs})}\n\n"

        result = _build_result(
            query=query,
            selected_nodes=selected_nodes,
            clean_answer=clean_answer,
            context_text=format_retrieved_context(retrieved_context),
            evaluate=evaluate,
        )

        if evaluate:
            yield f"data: {json.dumps({'type': 'eval', 'reasoning': result['reasoning'], 'confidence': result['confidence'], 'metrics': result['metrics']})}\n\n"

        yield "data: [DONE]\n\n"
        append_query_response(result, log_path)

    except Exception as error:
        yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
        yield "data: [DONE]\n\n"
