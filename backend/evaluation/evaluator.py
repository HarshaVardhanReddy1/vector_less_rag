from langsmith import traceable

from backend.config import (
    EVALUATION_CONFIDENCE_MEDIUM_THRESHOLD,
    EVALUATION_CONFIDENCE_HIGH_THRESHOLD,
    JUDGE_MODEL,
)
from backend.core.llm import generate_response
from backend.prompts.judge import generate_llm_judge_prompt
from backend.utils.json_utils import ensure_valid_json
from backend.utils.validation import (
    validate_dict,
    validate_float_in_range,
    validate_non_empty_string,
)

JUDGE_VALIDATION_REQUIREMENTS = """
Return a JSON object with exactly these fields:
- faithfulness_score: float between 0.0 and 1.0
- relevance_score: float between 0.0 and 1.0
- context_precision_score: float between 0.0 and 1.0
- reasoning: non-empty string
"""


def _validate_judge_response(data: object) -> dict:
    """Validate the judge model's response structure and values."""
    data_dict = validate_dict(data, "Judge response")

    faithfulness = validate_float_in_range(
        data_dict.get("faithfulness_score"),
        "faithfulness_score",
    )
    relevance = validate_float_in_range(
        data_dict.get("relevance_score"),
        "relevance_score",
    )
    context_precision = validate_float_in_range(
        data_dict.get("context_precision_score"),
        "context_precision_score",
    )
    reasoning = validate_non_empty_string(data_dict.get("reasoning"), "reasoning")

    return {
        "faithfulness_score": round(faithfulness, 2),
        "relevance_score": round(relevance, 2),
        "context_precision_score": round(context_precision, 2),
        "reasoning": reasoning,
    }


def _derive_confidence(avg: float) -> str:
    """Determine confidence level based on average evaluation score."""
    if avg >= EVALUATION_CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    if avg >= EVALUATION_CONFIDENCE_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


@traceable(run_type="chain", name="Evaluator · evaluate_answer")
def evaluate_answer(query: str, answer: str, context_text: str) -> dict:
    try:
        prompt = generate_llm_judge_prompt(query=query, answer=answer, context=context_text)
        raw = generate_response(prompt, model=JUDGE_MODEL)
        parsed = ensure_valid_json(
            raw,
            validator=_validate_judge_response,
            validation_requirements=JUDGE_VALIDATION_REQUIREMENTS,
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
