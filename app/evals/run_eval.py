import argparse
import json
from pathlib import Path

from app.page_index_rebuilt.retriever import answer_query, retrieve_context_for_query


EVALS_DIR = Path(__file__).resolve().parent
SAMPLE_DOCUMENTS_DIR = EVALS_DIR / "sample_documents"
QUERY_SET_PATH = EVALS_DIR / "sample_queries.json"

DOCUMENT_PATHS = {
    "employee_handbook": {
        "pages_path": SAMPLE_DOCUMENTS_DIR / "employee_handbook_pages.json",
        "tree_path": SAMPLE_DOCUMENTS_DIR / "employee_handbook_tree.json",
        "toc_path": SAMPLE_DOCUMENTS_DIR / "employee_handbook_toc.json",
    },
    "ml_ops_digest": {
        "pages_path": SAMPLE_DOCUMENTS_DIR / "ml_ops_digest_pages.json",
        "tree_path": SAMPLE_DOCUMENTS_DIR / "ml_ops_digest_tree.json",
        "toc_path": SAMPLE_DOCUMENTS_DIR / "ml_ops_digest_toc.json",
    },
}


def load_query_set(path: Path = QUERY_SET_PATH) -> list[dict]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def text_contains_all_keywords(text: str, keywords: list[str]) -> bool:
    normalized_text = text.lower()
    return all(keyword.lower() in normalized_text for keyword in keywords)


def evaluate_case(case: dict, include_answer: bool = False) -> dict:
    doc_paths = DOCUMENT_PATHS[case["doc_id"]]
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
    }


def summarize_results(results: list[dict], include_answer: bool = False) -> dict:
    total = len(results)
    retrieval_hits = sum(1 for item in results if item["retrieval_hit"])
    title_hits = sum(1 for item in results if item["title_hit"])
    context_hits = sum(1 for item in results if item["context_keyword_hit"])

    summary = {
        "total_cases": total,
        "retrieval_accuracy": retrieval_hits / total if total else 0.0,
        "title_match_rate": title_hits / total if total else 0.0,
        "context_keyword_rate": context_hits / total if total else 0.0,
    }

    if include_answer:
        answer_hits = sum(1 for item in results if item["answer_keyword_hit"])
        summary["answer_keyword_rate"] = answer_hits / total if total else 0.0

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the sample retrieval evaluation set.")
    parser.add_argument(
        "--include-answer",
        action="store_true",
        help="Also generate answers and score expected answer keywords.",
    )
    args = parser.parse_args()

    query_set = load_query_set()
    results = [evaluate_case(case, include_answer=args.include_answer) for case in query_set]
    summary = summarize_results(results, include_answer=args.include_answer)

    print(json.dumps({"summary": summary, "results": results}, indent=2))


if __name__ == "__main__":
    main()
