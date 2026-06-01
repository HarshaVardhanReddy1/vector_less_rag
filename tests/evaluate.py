"""Phase 2: Evaluate the RAG system against the generated Q&A dataset.

Requires tests/qa_dataset.json (run generate_qa.py first).
Outputs a timestamped results file to tests/results/ and prints an accuracy report.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from backend.core.llm import generate_response
from backend.retrieval.answer_engine import answer_query
from backend.utils.json_utils import ensure_valid_json, save_json_data

QA_DATASET_PATH = Path(__file__).parent / "test_data.json"
RESULTS_DIR = Path(__file__).parent / "results"
CORRECTNESS_THRESHOLD = 0.7
MAX_RETRIES = 3

DOCS = {
    "distributed-systems-rag-test": {
        "tree": str(ROOT / "data/trees/distributed-systems-rag-test.json"),
        "nodes": str(ROOT / "data/tocs/distributed-systems-rag-test.json"),
    },
    "earthmover": {
        "tree": str(ROOT / "data/trees/earthmover.json"),
        "nodes": str(ROOT / "data/tocs/earthmover.json"),
    },
    "final-major-project-research-paper": {
        "tree": str(ROOT / "data/trees/final-major-project-research-paper.json"),
        "nodes": str(ROOT / "data/tocs/final-major-project-research-paper.json"),
    },
    "final-pinnit-phase-feature-list-plan-v1-1-proposal-1": {
        "tree": str(ROOT / "data/trees/final-pinnit-phase-feature-list-plan-v1-1-proposal-1.json"),
        "nodes": str(ROOT / "data/tocs/final-pinnit-phase-feature-list-plan-v1-1-proposal-1.json"),
    },
    "ride-hailing-pricing-and-scaling-strategy-260521204826": {
        "tree": str(ROOT / "data/trees/ride-hailing-pricing-and-scaling-strategy-260521204826.json"),
        "nodes": str(ROOT / "data/tocs/ride-hailing-pricing-and-scaling-strategy-260521204826.json"),
    },
}


def _judge_correctness(question: str, expected_answer: str, actual_answer: str) -> dict:
    """Score how semantically correct the actual answer is against the expected answer."""
    prompt = (
        "You are evaluating a RAG system. Given a question, the expected answer, and "
        "the system's actual answer, score how semantically correct the actual answer is.\n\n"
        "Score 0.0–1.0:\n"
        "  1.0  = Fully correct, covers all key facts\n"
        "  0.7–0.9 = Mostly correct, minor omissions or different phrasing\n"
        "  0.4–0.6 = Partially correct, captures some facts but misses key details\n"
        "  0.1–0.3 = Mostly incorrect or largely irrelevant\n"
        "  0.0  = No answer or completely wrong\n\n"
        "Focus on semantic equivalence — exact wording doesn't matter, core facts do.\n\n"
        'Return strict JSON only, no markdown: {"correctness_score": 0.85, "reasoning": "one sentence"}\n\n'
        f"QUESTION: {question}\n"
        f"EXPECTED ANSWER: {expected_answer}\n"
        f"ACTUAL ANSWER: {actual_answer or '(no answer)'}"
    )

    def _validate(parsed):
        if not isinstance(parsed, dict):
            raise ValueError("expected object")
        score = parsed.get("correctness_score")
        if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
            raise ValueError("correctness_score must be a float 0.0–1.0")
        if not str(parsed.get("reasoning", "")).strip():
            raise ValueError("reasoning must be non-empty")
        parsed["correctness_score"] = round(float(score), 2)
        return parsed

    try:
        raw = generate_response(prompt)
        return ensure_valid_json(raw, max_retries=2, validator=_validate)
    except Exception as exc:
        print(f"    [WARN] Judge failed: {exc}")
        return {"correctness_score": 0.0, "reasoning": f"Judge error: {exc}"}


def _print_report(data: dict) -> None:
    w = 55
    print("\n" + "=" * 65)
    print("  RAG Evaluation Results")
    print("=" * 65)
    print(f"  Total questions       : {data['total_questions']}")
    print(f"  Correct (>= {data['correctness_threshold']:.0%}) : {data['correct']} / {data['total_questions']}")
    print(f"  Overall accuracy      : {data['accuracy'] * 100:.1f}%")
    print(f"  Avg correctness score : {data['average_correctness_score']:.2f}")
    print()
    print("  Per-document breakdown:")
    for doc, stats in data["per_document"].items():
        filled = int(stats["accuracy"] * 20)
        bar = "[" + "#" * filled + "-" * (20 - filled) + "]"
        print(f"    {doc[:w]:<{w}} {stats['correct']:>2}/{stats['total']}  {stats['accuracy']*100:5.1f}%  {bar}")
    print()
    print(f"  Router errors (failed after retries): {data['router_errors']}")
    print(f"  Results: {data['results_path']}")
    print("=" * 65)


def main():
    if not QA_DATASET_PATH.exists():
        print(f"ERROR: {QA_DATASET_PATH} not found.")
        print("Add your test_data.json to the tests/ folder.")
        sys.exit(1)

    with open(QA_DATASET_PATH, "r", encoding="utf-8") as f:
        qa_dataset = json.load(f)

    print(f"=== RAG Evaluation ===")
    print(f"Loaded {len(qa_dataset)} questions")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"results_{timestamp}.json"

    per_doc_stats: dict = {doc: {"total": 0, "correct": 0} for doc in DOCS}
    results = []
    router_errors = 0

    for i, item in enumerate(qa_dataset, start=1):
        doc = item["document"]
        question = item["question"]
        print(f"\n[{i:>3}/{len(qa_dataset)}] [{doc[:28]}] {question[:75]}...")

        if doc not in DOCS:
            print(f"  [WARN] Unknown document '{doc}', skipping.")
            continue

        doc_paths = DOCS[doc]

        # Query the RAG system with retries for transient OpenRouter errors
        actual_answer = ""
        selected_nodes = []
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                rag_result = answer_query(
                    query=question,
                    tree_path=doc_paths["tree"],
                    toc_path=doc_paths["nodes"],
                )
                actual_answer = rag_result.get("answer", "")
                selected_nodes = rag_result.get("selected_nodes", [])
                break
            except Exception as exc:
                if attempt < MAX_RETRIES:
                    print(f"  [RETRY {attempt}/{MAX_RETRIES}] {exc} — retrying...")
                else:
                    print(f"  [ERROR] RAG query failed after {MAX_RETRIES} attempts: {exc}")
                    router_errors += 1

        # Judge semantic correctness against expected answer
        judgment = _judge_correctness(question, item["expected_answer"], actual_answer)
        score = judgment["correctness_score"]
        is_correct = score >= CORRECTNESS_THRESHOLD
        verdict = "CORRECT  " if is_correct else "INCORRECT"
        print(f"  {verdict} score={score:.2f} | {judgment['reasoning'][:80]}")

        per_doc_stats[doc]["total"] += 1
        if is_correct:
            per_doc_stats[doc]["correct"] += 1

        results.append({
            "id": item.get("id", i),
            "document": doc,
            "node_id": item.get("node_id", ""),
            "question": question,
            "expected_answer": item["expected_answer"],
            "actual_answer": actual_answer,
            "is_correct": is_correct,
            "correctness_score": score,
            "correctness_reasoning": judgment["reasoning"],
            "selected_nodes": selected_nodes,
        })

    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])
    accuracy = correct / total if total > 0 else 0.0
    avg_score = sum(r["correctness_score"] for r in results) / total if total > 0 else 0.0

    per_document = {
        doc: {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        }
        for doc, stats in per_doc_stats.items()
        if stats["total"] > 0
    }

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "correctness_threshold": CORRECTNESS_THRESHOLD,
        "average_correctness_score": round(avg_score, 4),
        "per_document": per_document,
        "router_errors": router_errors,
        "results_path": str(results_path),
        "results": results,
    }

    save_json_data(output, results_path)
    _print_report(output)


if __name__ == "__main__":
    main()
