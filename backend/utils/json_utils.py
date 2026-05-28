import json
from pathlib import Path
from typing import Any, Callable

from backend.core.llm import generate_response
from backend.prompts.repair import generate_json_fix_prompt


JSONValidator = Callable[[Any], Any]


def load_json_data(json_path: str | Path) -> Any:
    path = Path(json_path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"JSON file not found: {path.resolve()}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Failed to parse JSON file {path.resolve()} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    except OSError as error:
        raise OSError(f"Failed to read JSON file {path.resolve()}: {error}") from error


def save_json_data(data: Any, output_path: str | Path) -> None:
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except TypeError as error:
        raise ValueError(
            f"Failed to serialize data for JSON output {path.resolve()}: {error}"
        ) from error
    except OSError as error:
        raise OSError(f"Failed to write JSON file {path.resolve()}: {error}") from error


def _serialize_json_candidate(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _truncate_for_error(value: Any, limit: int = 300) -> str:
    text = _serialize_json_candidate(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


def ensure_valid_json(
    json_context: Any,
    max_retries: int = 3,
    validator: JSONValidator | None = None,
    validation_requirements: str = "",
) -> Any:
    current_response = json_context
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            parsed = (
                current_response
                if isinstance(current_response, (list, dict))
                else json.loads(current_response)
            )
            return validator(parsed) if validator is not None else parsed
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            last_error = error
            if attempt == max_retries:
                break
            repair_prompt  = generate_json_fix_prompt(
                _serialize_json_candidate(current_response),
                str(error),
                validation_requirements=validation_requirements,
            )
            current_response = generate_response(repair_prompt)

    raise ValueError(
        "Failed to parse and validate LLM response as valid JSON after "
        f"{max_retries} attempts. Last error: {last_error}. "
        f"Last response snippet: {_truncate_for_error(current_response)}"
    )
