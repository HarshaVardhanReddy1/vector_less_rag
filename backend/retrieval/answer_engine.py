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


@traceable(run_type="chain", name="Pipeline · answer_query")
def answer_query(
    query: str,
    tree_path: str,
    toc_path: str,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
    evaluate: bool = True,
) -> dict:
    """Generate an answer for the given query.

    Args:
        evaluate: When True (the default), runs the LLM judge after answering
                  and includes reasoning, confidence, and metrics in the
                  response. Pass False to skip the extra LLM call.
    """
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            toc_path=toc_path,
        )

        if retrieved_context is None:
            result = {
                "query":          query,
                "selected_nodes": [],
                "answer":         "No relevant nodes were found for the query.",
            }
            append_query_response(result, log_path)
            return result

        answer_text = generate_response(_build_answer_prompt(query, retrieved_context))
        clean_answer = re.sub(r"<REFERENCED_IMAGES>[\s\S]*?</REFERENCED_IMAGES>", "", answer_text).rstrip()

        _start_indices = retrieved_context.get(
            "start_indices",
            [retrieved_context["start_index"]] * len(retrieved_context["node_ids"]),
        )
        result = {
            "query": query,
            "selected_nodes": [
                {"node_id": nid, "title": normalize_title(title), "page": page}
                for nid, title, page in zip(
                    retrieved_context["node_ids"],
                    retrieved_context["titles"],
                    _start_indices,
                )
            ],
            "start_index": retrieved_context["start_index"],
            "answer":      clean_answer,
        }

        if evaluate:
            judgment = evaluate_answer(
                query=query,
                answer=clean_answer,
                context_text=format_retrieved_context(retrieved_context),
            )
            result["reasoning"]  = judgment.get("reasoning", "")
            result["confidence"] = judgment.get("confidence", "")
            result["metrics"]    = judgment.get("metrics", {})

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
    """Yield SSE-formatted lines: first a metadata event, then answer tokens.

    Event format:
        data: {"type": "meta", "selected_nodes": [...], "start_index": N}
        data: {"type": "token", "content": "..."}
        data: {"type": "eval", "reasoning": "...", "confidence": "...", "metrics": {...}}
        data: [DONE]

    Args:
        evaluate: When True, runs the LLM judge after the answer finishes and
                  emits a final "eval" event with reasoning, confidence, and
                  metrics before "[DONE]".
    """
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            toc_path=toc_path,
        )

        if retrieved_context is None:
            yield f"data: {json.dumps({'type': 'meta', 'selected_nodes': [], 'start_index': 0})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'content': 'No relevant nodes were found for the query.'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        _start_indices = retrieved_context.get(
            "start_indices",
            [retrieved_context["start_index"]] * len(retrieved_context["node_ids"]),
        )
        selected_nodes = [
            {"node_id": nid, "title": normalize_title(title), "page": page}
            for nid, title, page in zip(
                retrieved_context["node_ids"],
                retrieved_context["titles"],
                _start_indices,
            )
        ]
        yield f"data: {json.dumps({'type': 'meta', 'selected_nodes': selected_nodes, 'start_index': retrieved_context['start_index']})}\n\n"

        prompt = _build_answer_prompt(query, retrieved_context)
        full_answer = ""
        for token in generate_response_stream(prompt):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Extract image refs from REFERENCED_IMAGES block
        image_refs = extract_image_refs_from_answer(full_answer)
        if image_refs:
            yield f"data: {json.dumps({'type': 'images', 'images': image_refs})}\n\n"

        # Strip image block from displayed answer
        clean_answer = re.sub(r"<REFERENCED_IMAGES>[\s\S]*?</REFERENCED_IMAGES>", "", full_answer).rstrip()
        result = {"query": query, "selected_nodes": selected_nodes, "answer": clean_answer}

        if evaluate:
            judgment = evaluate_answer(
                query=query,
                answer=clean_answer,
                context_text=format_retrieved_context(retrieved_context),
            )
            result["reasoning"]  = judgment.get("reasoning", "")
            result["confidence"] = judgment.get("confidence", "")
            result["metrics"]    = judgment.get("metrics", {})
            yield f"data: {json.dumps({'type': 'eval', 'reasoning': result['reasoning'], 'confidence': result['confidence'], 'metrics': result['metrics']})}\n\n"

        yield "data: [DONE]\n\n"

        append_query_response(result, log_path)

    except Exception as error:
        yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
        yield "data: [DONE]\n\n"
