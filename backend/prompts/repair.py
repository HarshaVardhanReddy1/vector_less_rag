def generate_json_fix_prompt(
    broken_json: str,
    error_message: str,
    validation_requirements: str = "",
) -> str:
    return f"""
You are an expert JSON repair system.

Your task is to repair invalid JSON.

IMPORTANT RULES:

1. Fix ONLY JSON syntax/formatting issues.
2. Do NOT change the meaning of the content.
3. Do NOT remove valid fields.
4. Preserve all original data whenever possible.
5. Return ONLY valid JSON.
6. Do NOT add markdown or explanations.

JSON ERROR:
{error_message}

VALIDATION REQUIREMENTS:
{validation_requirements or "The JSON only needs to be valid and preserve the original meaning."}

BROKEN JSON:
{broken_json}
"""
