from config import DEFAULT_CONTEXT_MAX_TOKENS, DEFAULT_PAGES_PATH, DEFAULT_TOC_PATH
from llm import generate_response
from prompts import generate_toc_from_context_prompt, generate_toc_merge_prompt
from utils import ensure_valid_json, load_json_data, save_json_data


def build_context_chunks(page_items: list[dict], max_tokens: int = DEFAULT_CONTEXT_MAX_TOKENS) -> list[str]:
    contexts: list[str] = []
    current_context: list[str] = []
    current_token_count = 0

    for item in page_items:
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
    prompt = generate_toc_from_context_prompt(context)
    result = generate_response(prompt)
    return ensure_valid_json(result)


def merge_tocs(existing_toc: list[dict], new_toc: list[dict]) -> list[dict]:
    prompt = generate_toc_merge_prompt(existing_toc, new_toc)
    result = generate_response(prompt)
    return ensure_valid_json(result)





def build_toc(contexts: list[str]) -> list[dict]:
    if not contexts:
        return []

    toc = generate_toc_from_context(contexts[0])

    for context in contexts[1:]:
        chunk_toc = generate_toc_from_context(context)
        toc = merge_tocs(toc, chunk_toc)

    return deduplicate_toc(toc)

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
    pages_path=DEFAULT_PAGES_PATH,
    output_path=DEFAULT_TOC_PATH,
    max_tokens: int = DEFAULT_CONTEXT_MAX_TOKENS,
) -> list[dict]:
    pages_data = load_json_data(pages_path)
    contexts = build_context_chunks(pages_data, max_tokens=max_tokens)
    toc = build_toc(contexts)
    save_json_data(toc, output_path)
    return toc

  
  