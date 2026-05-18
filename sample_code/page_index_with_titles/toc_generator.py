from sample_code.page_index_with_titles.config import DEFAULT_CONTEXT_MAX_TOKENS, DEFAULT_PAGES_PATH, DEFAULT_TOC_PATH
from sample_code.page_index_with_titles.llm import generate_response
from sample_code.page_index_with_titles.prompts import generate_toc_from_context_prompt
from sample_code.page_index_with_titles.utils import ensure_valid_json, load_json_data, save_json_data


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

def build_toc(contexts: list[str]) -> list[dict]:
    if not contexts:
        return []

    toc = generate_toc_from_context(contexts[0],[])

    for context in contexts[1:]:
        toc = generate_toc_from_context(context,toc)
      

    return deduplicate_toc(toc)

def generate_toc_from_context(context: str,toc) -> list[dict]:
    prompt = generate_toc_from_context_prompt(context,toc)
    result = generate_response(prompt)
    return ensure_valid_json(result)


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

generate_toc()