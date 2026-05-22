import argparse
import json
import traceback
from pathlib import Path

from app.page_index_rebuilt.retriever import answer_query, retrieve_context_for_query


EVALS_DIR = Path(__file__).resolve().parent
SAMPLE_DOCUMENTS_DIR = EVALS_DIR / "sample_documents"
QUERY_SET_PATH = EVALS_DIR / "sample_queries.json"


def get_document_paths(doc_id: str) -> dict:
    return {
        "pages_path": SAMPLE_DOCUMENTS_DIR / f"{doc_id}_pages.json",
        "tree_path": SAMPLE_DOCUMENTS_DIR / f"{doc_id}_tree.json",
        "toc_path": SAMPLE_DOCUMENTS_DIR / f"{doc_id}_toc.json",
    }


def load_query_set(path: Path = QUERY_SET_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def text_contains_all_keywords(text: str, keywords: list[str]) -> bool:
    normalized_text = text.lower()
    return all(keyword.lower() in normalized_text for keyword in keywords)


def evaluate_case(case: dict, include_answer: bool = False) -> dict:
    try:
        doc_paths = get_document_paths(case["doc_id"])
        retrieved_context = retrieve_context_for_query(
            query=case["query"],
            tree_path=doc_paths["tree_path"],
            pages_path=doc_paths["pages_path"],
        )

        if retrieved_context is None:
            return {
                "doc_id": case["doc_id"],
                "query": case["query"],
                "retrieval_hit": False,
                "title_hit": False,
                "context_keyword_hit": False,
                "answer_keyword_hit": None,
                "selected_node_id": None,
                "selected_title": None,
                "answer": None,
                "error": None,
            }

        retrieval_hit = retrieved_context["node_id"] == case["expected_node_id"]
        title_hit = case["expected_title_contains"].lower() in retrieved_context["title"].lower()
        context_keyword_hit = text_contains_all_keywords(
            retrieved_context["context"],
            case.get("expected_context_keywords", []),
        )

        answer = None
        answer_keyword_hit = None
        if include_answer:
            result = answer_query(
                query=case["query"],
                tree_path=doc_paths["tree_path"],
                pages_path=doc_paths["pages_path"],
                log_path=EVALS_DIR / "eval_query_log.json",
            )
            answer = result["answer"]
            answer_keyword_hit = text_contains_all_keywords(
                answer,
                case.get("expected_answer_keywords", []),
            )

        return {
            "doc_id": case["doc_id"],
            "query": case["query"],
            "retrieval_hit": retrieval_hit,
            "title_hit": title_hit,
            "context_keyword_hit": context_keyword_hit,
            "answer_keyword_hit": answer_keyword_hit,
            "selected_node_id": retrieved_context["node_id"],
            "selected_title": retrieved_context["title"],
            "answer": answer,
            "error": None,
        }
    except Exception:
        return {
            "doc_id": case.get("doc_id"),
            "query": case.get("query"),
            "retrieval_hit": False,
            "title_hit": False,
            "context_keyword_hit": False,
            "answer_keyword_hit": None,
            "selected_node_id": None,
            "selected_title": None,
            "answer": None,
            "error": traceback.format_exc(),
        }


def summarize_results(results: list[dict], include_answer: bool = False) -> dict:
    total = len(results)
    errored = sum(1 for item in results if item["error"] is not None)
    scored = total - errored

    retrieval_hits = sum(1 for item in results if item["retrieval_hit"])
    title_hits = sum(1 for item in results if item["title_hit"])
    context_hits = sum(1 for item in results if item["context_keyword_hit"])

    summary = {
        "total_cases": total,
        "errored_cases": errored,
        "scored_cases": scored,
        "retrieval_accuracy": retrieval_hits / scored if scored else 0.0,
        "title_match_rate": title_hits / scored if scored else 0.0,
        "context_keyword_rate": context_hits / scored if scored else 0.0,
    }

    if include_answer:
        answer_hits = sum(1 for item in results if item["answer_keyword_hit"])
        summary["answer_keyword_rate"] = answer_hits / scored if scored else 0.0

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the sample retrieval evaluation set.")
    parser.add_argument(
        "--include-answer",
        action="store_true",
        help="Also generate answers and score expected answer keywords.",
    )
    parser.add_argument(
        "--doc-id",
        help="Only run eval cases for this document ID.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON results to this file instead of stdout.",
    )
    args = parser.parse_args()

    query_set = load_query_set()
    if args.doc_id:
        query_set = [case for case in query_set if case["doc_id"] == args.doc_id]

    results = [evaluate_case(case, include_answer=args.include_answer) for case in query_set]
    summary = summarize_results(results, include_answer=args.include_answer)

    output = json.dumps({"summary": summary, "results": results}, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Results written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
