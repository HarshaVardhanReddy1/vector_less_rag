import json
import ollama
import re

# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "openai/gpt-oss-120b:free"

SUMMARY_JSON = "page_summaries.json"
PAGES_JSON = "pages.json"


# =========================================================
# LOAD JSON
# =========================================================

def load_json(json_path):

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# BUILD SUMMARY CONTEXT
# =========================================================

def build_summary_context(summary_data):

    context = ""

    for item in summary_data:

        page = item.get("page", "")
        summary = item.get("summary", "")
        keywords = item.get("keywords", [])

        context += f"""
PAGE: {page}

SUMMARY:
{summary}

KEYWORDS:
{", ".join(keywords)}

==================================================
"""

    return context


# =========================================================
# RETRIEVAL PROMPT
# =========================================================

def generate_retrieval_prompt(user_query, context):

    prompt = f"""
You are a document retrieval assistant.

Your task:
- Analyze the user query
- Analyze the document summaries
- Find the most relevant pages
- Return reasons for selecting those pages

RULES:
- Return ONLY valid JSON
- Maximum 5 pages
- No explanations outside JSON
- If nothing relevant exists return []

OUTPUT FORMAT:

[
  {{
    "page": 10,
    "reason": "This page discusses monetary policy."
  }}
]

USER QUERY:
{user_query}

DOCUMENT DATA:
{context}
"""

    return prompt


# =========================================================
# ANSWER GENERATION PROMPT
# =========================================================

def generate_answer_prompt(user_query, retrieved_context):

    prompt = f"""
You are a helpful document question-answering assistant.

Answer the user's question ONLY using the provided document context.

RULES:
- Be accurate
- Do not hallucinate
- If answer is not found say:
  "The answer is not available in the document."
- Give concise answers

USER QUESTION:
{user_query}

DOCUMENT CONTEXT:

{retrieved_context}
"""

    return prompt


# =========================================================
# CALL LLM
# =========================================================

def call_llm(prompt):

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"]


# =========================================================
# EXTRACT JSON
# =========================================================

def extract_json(text):

    print("\n================ RAW LLM OUTPUT ================\n")
    print(text)

    text = text.strip()

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON array found.")

    json_text = text[start:end + 1]

    return json.loads(json_text)


# =========================================================
# RETRIEVE RELEVANT PAGES
# =========================================================

def retrieve_pages(user_query):

    summary_data = load_json(SUMMARY_JSON)

    context = build_summary_context(summary_data)

    prompt = generate_retrieval_prompt(user_query, context)

    llm_output = call_llm(prompt)

    results = extract_json(llm_output)

    return results


# =========================================================
# GET PAGE TEXTS
# =========================================================

def get_page_texts(retrieved_pages, pages_data):

    context = ""

    for item in retrieved_pages:

        page_number = item.get("page")

        # Convert to zero-based index
        page_index = page_number - 1

        if 0 <= page_index < len(pages_data):

            page_text = pages_data[page_index].get("page_text", "")

            context += f"""
================ PAGE {page_number} ================

{page_text}

"""

    return context


# =========================================================
# GENERATE FINAL ANSWER
# =========================================================

def generate_final_answer(user_query, context):

    prompt = generate_answer_prompt(user_query, context)

    answer = call_llm(prompt)

    return answer


# =========================================================
# MAIN PIPELINE
# =========================================================

def rag_pipeline(user_query):

    print("\nRetrieving relevant pages...")

    retrieved_pages = retrieve_pages(user_query)

    print("\nRetrieved Pages:\n")
    print(json.dumps(retrieved_pages, indent=4))

    pages_data = load_json(PAGES_JSON)

    print("\nBuilding document context...")

    retrieved_context = get_page_texts(
        retrieved_pages,
        pages_data
    )

    print("\nGenerating final answer...")

    final_answer = generate_final_answer(
        user_query,
        retrieved_context
    )

    return {
        "query": user_query,
        "retrieved_pages": retrieved_pages,
        "answer": final_answer
    }


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    query = input("\nEnter your query: ")

    try:

        result = rag_pipeline(query)

        print("\n================ FINAL RESULT ================\n")

        print(json.dumps(result, indent=4, ensure_ascii=False))

    except Exception as e:

        print(f"\nERROR: {e}")