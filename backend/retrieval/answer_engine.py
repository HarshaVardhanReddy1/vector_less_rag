"""Answer generation — retrieves context, generates answer, evaluates, logs."""

import json
from typing import Iterator

from langsmith import traceable

from backend.config import DEFAULT_QUERY_LOG_PATH
from backend.core.llm import generate_response, generate_response_stream
from backend.evaluation.evaluator import evaluate_answer
from backend.prompts.answer import generate_context_grounded_answer_prompt
from backend.retrieval.context_retriever import retrieve_context_for_query
from backend.utils.node_utils import append_query_response, format_retrieved_context, normalize_title


def _build_answer_prompt(query: str, retrieved_context: dict) -> str:
    return generate_context_grounded_answer_prompt(
        query=query,
        retrieved_context_text=format_retrieved_context(retrieved_context),
    )


@traceable(run_type="chain", name="Pipeline · answer_query")
def answer_query(
    query: str,
    tree_path: str,
    nodes_path: str,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
    evaluate: bool = False,
) -> dict:
    """Generate an answer for the given query.

    Args:
        evaluate: When True, runs the LLM judge after answering and includes
                  reasoning, confidence, and metrics in the response.
                  Defaults to False to avoid the extra LLM call in production.
    """
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            nodes_path=nodes_path,
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
            "answer":      answer_text,
        }

        if evaluate:
            judgment = evaluate_answer(
                query=query,
                answer=answer_text,
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
            f"nodes '{nodes_path}'."
        ) from error


def stream_answer_query(
    query: str,
    tree_path: str,
    nodes_path: str,
    log_path: str = DEFAULT_QUERY_LOG_PATH,
) -> Iterator[str]:
    """Yield SSE-formatted lines: first a metadata event, then answer tokens.

    Event format:
        data: {"type": "meta", "selected_nodes": [...], "start_index": N}
        data: {"type": "token", "content": "..."}
        data: [DONE]
    """
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            nodes_path=nodes_path,
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

        yield "data: [DONE]\n\n"

        append_query_response(
            {"query": query, "selected_nodes": selected_nodes, "answer": full_answer},
            log_path,
        )

    except Exception as error:
        yield f"data: {json.dumps({'type': 'error', 'message': str(error)})}\n\n"
        yield "data: [DONE]\n\n"
