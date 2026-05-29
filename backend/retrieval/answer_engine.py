"""Answer generation — retrieves context, generates answer, evaluates, logs."""

from langsmith import traceable

from backend.config import DEFAULT_QUERY_LOG_PATH
from backend.core.llm import generate_response
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
) -> dict:
    try:
        retrieved_context = retrieve_context_for_query(
            query=query,
            tree_path=tree_path,
            nodes_path=nodes_path,
        )

        if retrieved_context is None:
            result = {
                "query":query,
                "selected_nodes": [],
                "answer":"No relevant nodes were found for the query.",
            }
            append_query_response(result, log_path)
            return result

        answer_text   = generate_response(_build_answer_prompt(query, retrieved_context))
        context_text  = format_retrieved_context(retrieved_context)
        judgment      = evaluate_answer(
            query=query,
            answer=answer_text,
            context_text=context_text,
        )

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
            "reasoning":   judgment.get("reasoning", ""),
            "confidence":  judgment.get("confidence", ""),
            "metrics":     judgment.get("metrics", {}),
        }
        append_query_response(result, log_path)
        return result

    except Exception as error:
        raise RuntimeError(
            f"Failed to answer query {query!r} using tree '{tree_path}' and "
            f"nodes '{nodes_path}'."
        ) from error
