from langsmith import traceable

from .llm import generate_response
from .prompts import generate_llm_judge_prompt
from .utils import ensure_valid_json


_JUDGE_MODEL = "openai/gpt-4o-mini"

_JUDGE_VALIDATION_REQUIREMENTS = """
Return a JSON object with exactly these fields:
- faithfulness_score: float between 0.0 and 1.0
- relevance_score: float between 0.0 and 1.0
- context_precision_score: float between 0.0 and 1.0
- reasoning: non-empty string
"""


def _validate_judge_response(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Judge response must be a JSON object.")

    def _float_score(field: str) -> float:
        val = data.get(field)
        try:
            f = float(val)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            raise ValueError(f"Field '{field}' must be a number, got {val!r}.")
        if not (0.0 <= f <= 1.0):
            raise ValueError(f"Field '{field}' must be between 0.0 and 1.0, got {f}.")
        return round(f, 2)

    faithfulness      = _float_score("faithfulness_score")
    relevance         = _float_score("relevance_score")
    context_precision = _float_score("context_precision_score")

    reasoning = data.get("reasoning", "")
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ValueError("Field 'reasoning' must be a non-empty string.")

    return {
        "faithfulness_score":      faithfulness,
        "relevance_score":         relevance,
        "context_precision_score": context_precision,
        "reasoning":               reasoning.strip(),
    }


def _derive_confidence(avg: float) -> str:
    if avg >= 0.75:
        return "high"
    if avg >= 0.45:
        return "medium"
    return "low"


@traceable(run_type="chain", name="Evaluator · evaluate_answer")
def evaluate_answer(query: str, answer: str, context_text: str) -> dict:
    """
    Evaluate a generated answer using an LLM-as-Judge approach.

    Scores three metrics via a single structured LLM call:
      - faithfulness_score   (groundedness in retrieved context)
      - relevance_score      (how well the answer addresses the query)
      - context_precision_score (conciseness and precision of context use)

    Returns a dict with:
      - reasoning:  brief explanation from the judge
      - confidence: "high" | "medium" | "low" derived from the average of all three scores
      - metrics:    groundedness_score, relevance_score, accuracy_score (all 0-1 floats)
    """
    try:
        prompt = generate_llm_judge_prompt(query=query, answer=answer, context=context_text)
        raw    = generate_response(prompt, model=_JUDGE_MODEL)
        parsed = ensure_valid_json(
            raw,
            validator=_validate_judge_response,
            validation_requirements=_JUDGE_VALIDATION_REQUIREMENTS,
        )

        faithfulness      = parsed["faithfulness_score"]
        relevance         = parsed["relevance_score"]
        context_precision = parsed["context_precision_score"]
        accuracy          = round((faithfulness + relevance + context_precision) / 3, 2)

        return {
            "reasoning":  parsed["reasoning"],
            "confidence": _derive_confidence(accuracy),
            "metrics": {
                "groundedness_score": faithfulness,
                "relevance_score":    relevance,
                "accuracy_score":     accuracy,
            },
        }

    except Exception as exc:
        return {
            "reasoning":  f"Evaluation unavailable: {type(exc).__name__}",
            "confidence": "unknown",
            "metrics": {
                "groundedness_score": None,
                "relevance_score":    None,
                "accuracy_score":     None,
            },
        }
