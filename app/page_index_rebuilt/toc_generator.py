from .config import DEFAULT_CONTEXT_MAX_TOKENS 
from .llm import generate_response
from .prompts import generate_toc_from_context_prompt, generate_toc_merge_prompt
from .utils import (
    ensure_valid_json,
    load_json_data,
    save_json_data,
    validate_page_items,
    validate_toc_nodes,
)


TOC_VALIDATION_REQUIREMENTS = """
Return a JSON array of objects.
Each object must contain exactly these fields:
- title: non-empty string
- node_id: non-empty dotted numeric string like 1, 1.2, or 2.3.4
- page_number: integer >= 1
- summary: non-empty string
Do not return duplicate node_id values.
"""


def build_context_chunks(page_items: list[dict], max_tokens: int = DEFAULT_CONTEXT_MAX_TOKENS) -> list[str]:
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
        raise ValueError(f"max_tokens must be a positive integer, got {max_tokens!r}.")

    validated_page_items = validate_page_items(page_items)
    contexts: list[str] = []
    current_context: list[str] = []
    current_token_count = 0

    for item in validated_page_items:
        page_number = item["page"]
        page_text = item["page_text"]
        token_count = item["token_count"]

        formatted_text = f"""
================ PAGE {page_number} START ================

{page_text}

================ PAGE {page_number} END ================
"""

        if current_context and current_token_count + token_count > max_tokens:
            contexts.append("\n".join(current_context))
            current_context = []
            current_token_count = 0

        current_context.append(formatted_text)
        current_token_count += token_count

    if current_context:
        contexts.append("\n".join(current_context))

    return contexts


def generate_toc_from_context(context: str) -> list[dict]:
    try:
        prompt = generate_toc_from_context_prompt(context)
        result = generate_response(prompt)
        return ensure_valid_json(
            result,
            validator=validate_toc_nodes,
            validation_requirements=TOC_VALIDATION_REQUIREMENTS,
        )
    except Exception as error:
        raise RuntimeError("Failed to generate TOC from a context chunk.") from error


def merge_tocs(existing_toc: list[dict], new_toc: list[dict]) -> list[dict]:
    try:
        prompt = generate_toc_merge_prompt(existing_toc, new_toc)
        result = generate_response(prompt)
        return ensure_valid_json(
            result,
            validator=validate_toc_nodes,
            validation_requirements=TOC_VALIDATION_REQUIREMENTS,
        )
    except Exception as error:
        raise RuntimeError("Failed to merge partial TOCs.") from error





def build_toc(contexts: list[str]) -> list[dict]:
    if not contexts:
        return []

    try:
        toc = generate_toc_from_context(contexts[0])

        for context in contexts[1:]:
            chunk_toc = generate_toc_from_context(context)
            toc = merge_tocs(toc, chunk_toc)

        return deduplicate_toc(toc)
    except Exception as error:
        raise RuntimeError(f"Failed to build TOC from {len(contexts)} context chunk(s).") from error

def deduplicate_toc(toc: list[dict]) -> list[dict]:
    seen = set()
    deduped = []

    for node in toc:
        key = (node.get("title", "").strip().lower(), node.get("page_number"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(node)

    return deduped


def generate_toc(
    pages_path:str,
    output_path:str,
    max_tokens: int = DEFAULT_CONTEXT_MAX_TOKENS,
) -> list[dict]:
    try:
        pages_data = load_json_data(pages_path)
        contexts = build_context_chunks(pages_data, max_tokens=max_tokens)
        toc = build_toc(contexts)
        save_json_data(toc, output_path)
        return toc
    except Exception as error:
        raise RuntimeError(
            f"Failed to generate TOC from pages file '{pages_path}' into '{output_path}'."
        ) from error

  
  
