import json
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response
from sample_code.page_index_with_no_toc.extract_pages import save_pages_to_json

from sample_code.page_index_with_no_toc.prompts import (
    generate_toc_from_context_prompt,
    generate_json_fix_prompt,
    generate_toc_merge_prompt,
)

output_path = "json_files/toc1.json"
def generate_toc(json_path):
    data = load_json_data(json_path)
    contexts = generate_context(data)
    toc = build_toc(contexts)
    save_pages_to_json(toc, output_path)
    return toc


def load_json_data(json_path):
    with open(json_path,"r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def generate_context(data, max_tokens=20000):
    contexts = []
    current_context = []
    current_token_count = 0

    for item in data:
        page_number = item["page"]
        page_text = item["page_text"]
        token_count = item["token_count"]

        # Add page markers for clear differentiation
        formatted_text = f"""
        ================ PAGE {page_number} START ================

        {page_text}

        ================ PAGE {page_number} END ================
        """

        # If adding this page exceeds limit,
        # save current context and start new one
        if current_token_count + token_count > max_tokens:
            if current_context:
                contexts.append("\n".join(current_context))

            current_context = []
            current_token_count = 0

        current_context.append(formatted_text)
        current_token_count += token_count

    # Add remaining context
    if current_context:
        contexts.append("\n".join(current_context))

    return contexts


# def generate_tree(contexts):
#     initial_tree_context = contexts[0]
#     initial_tree_prompt = generate_initial_tree_prompt(initial_tree_context)
#     tree_response = generate_response(initial_tree_prompt)
#     for context in contexts[1:]:
#         print(f"tree response: {tree_response}")
#         prompt = generate_tree_prompt(tree_response,context)
#         tree_response = generate_response(prompt)
#     return tree_response

def build_toc(contexts):
    if not contexts:
        return []

    toc = generate_toc_from_context(contexts[0])

    for context in contexts[1:]:
        chunk_toc = generate_toc_from_context(context)
        toc = merge_tocs(toc, chunk_toc)

    toc = deduplicate_toc(toc)
    return toc


def generate_toc_from_context(context):
    prompt = generate_toc_from_context_prompt(context)
    result = generate_response(prompt)
    toc = ensure_valid_json(result)
    return toc

def merge_tocs(existing_toc, new_toc):
    prompt = generate_toc_merge_prompt(existing_toc, new_toc)
    result = generate_response(prompt)
    merged_toc = ensure_valid_json(result)
    return merged_toc

def deduplicate_toc(toc):
    seen = set()
    deduped = []

    for node in toc:
        key = (
            node.get("title", "").strip().lower(),
            node.get("page_number"),
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(node)

    return deduped

def ensure_valid_json(json_context, max_retries=3):

    current_response = json_context

    for attempt in range(max_retries):

        if isinstance(current_response, (list, dict)):
            return current_response

        try:
            # Try converting directly
            parsed_json = json.loads(current_response)

            print("Valid JSON detected")

            return parsed_json

        except json.JSONDecodeError as e:

            print(f"JSON Error detected: {e}")

            # Save broken response for debugging
            with open(
                f"broken_json_attempt_{attempt + 1}.txt",
                "w",
                encoding="utf-8"
            ) as file:
                file.write(current_response)

            # Generate repair prompt
            repair_prompt = generate_json_fix_prompt(
                current_response,
                str(e)
            )

            # Ask LLM to repair JSON only
            current_response = generate_response(repair_prompt)

    raise Exception(
        "Failed to repair JSON after multiple attempts."
    )

if __name__ == "__main__":
    toc = generate_toc("json_files/pdf_pages1.json")
    
