"""Input validation utilities for consistent error handling and data validation."""

import re
from typing import Any, Callable, Optional

NODE_ID_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")


class ValidationError(ValueError):
    """Custom validation error for clearer error handling."""

    pass


def validate_non_empty_string(value: Any, field_name: str) -> str:
    """Validate that value is a non-empty string."""
    if not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string, got {type(value).__name__}.")
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"Field '{field_name}' must be a non-empty string.")
    return normalized


def validate_node_id(value: Any, field_name: str = "node_id") -> str:
    """Validate that value is a valid dotted numeric node ID (e.g., '1', '1.2.3')."""
    node_id = validate_non_empty_string(value, field_name)
    if not NODE_ID_PATTERN.fullmatch(node_id):
        raise ValidationError(
            f"Field '{field_name}' must use dotted numeric notation like '1' or '1.2.3', got '{node_id}'."
        )
    return node_id


def validate_float_in_range(
    value: Any,
    field_name: str,
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> float:
    """Validate that value is a float within the given range."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Field '{field_name}' must be a number, got {value!r}."
        )
    if not (min_val <= f <= max_val):
        raise ValidationError(
            f"Field '{field_name}' must be between {min_val} and {max_val}, got {f}."
        )
    return f


def validate_dict(value: Any, field_name: str = "object") -> dict:
    """Validate that value is a dictionary."""
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be a JSON object, got {type(value).__name__}.")
    return value


def validate_list(value: Any, field_name: str = "array") -> list:
    """Validate that value is a list."""
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a JSON array, got {type(value).__name__}.")
    return value


def validate_with_custom_validator(
    data: Any,
    validator: Callable[[Any], Any],
    validation_requirements: Optional[str] = None,
) -> Any:
    """Apply a custom validator function with error context."""
    try:
        return validator(data)
    except ValidationError:
        raise
    except Exception as e:
        context = f"\n{validation_requirements}" if validation_requirements else ""
        raise ValidationError(f"Validation failed: {e}{context}") from e


def validate_json_structure(data: dict, required_fields: list[str]) -> dict:
    """Validate that a dictionary contains all required fields."""
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    return data
