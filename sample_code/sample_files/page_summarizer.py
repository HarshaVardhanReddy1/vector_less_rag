import json
import ollama
import re
from typing import List, Dict

# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "openai/gpt-oss-120b:free"

INPUT_JSON = "pages.json"
OUTPUT_JSON = "page_summaries.json"


# =========================================================
# LOAD JSON
# =========================================================

def load_pages(json_path: str) -> List[Dict]:

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# =========================================================
# GENERATE PROMPT
# =========================================================

def generate_prompt(page_number: int, page_text: str) -> str:

    prompt = f"""
You are an expert document analysis assistant.

Analyze the following page text.

Your task:
1. Generate a concise summary of the page
2. Extract important keywords from the page

RULES:
- Return ONLY valid JSON
- No explanations
- No markdown
- Keep summary short
- Keywords should be meaningful
- If page is empty return:
{{
  "page": {page_number},
  "summary": "",
  "keywords": []
}}

OUTPUT FORMAT:

{{
  "page": {page_number},
  "summary": "Short summary",
  "keywords": [
    "keyword1",
    "keyword2"
  ]
}}

PAGE TEXT:

{page_text}
"""

    return prompt


# =========================================================
# CALL OLLAMA
# =========================================================

def call_llm(prompt: str) -> str:

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
# CLEAN + PARSE JSON
# =========================================================

def extract_json(text: str) -> Dict:

    text = text.strip()

    print("\n================ LLM OUTPUT ================\n")
    print(text)

    # Remove markdown blocks
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON found.")

    json_text = text[start:end + 1]

    return json.loads(json_text)


# =========================================================
# PROCESS ALL PAGES
# =========================================================

def process_pages():

    pages = load_pages(INPUT_JSON)

    final_results = []

    for idx, page_data in enumerate(pages[4:22]):

        page_number = idx + 5

        page_text = page_data.get("page_text", "").strip()

        print(f"\nProcessing page {page_number}")

        if not page_text:

            print("Empty page skipped.")

            final_results.append({
                "page": page_number,
                "summary": "",
                "keywords": []
            })

            continue

        prompt = generate_prompt(page_number, page_text)

        try:

            llm_output = call_llm(prompt)

            parsed_data = extract_json(llm_output)

            final_results.append(parsed_data)

            print(f"Page {page_number} processed successfully.")

        except Exception as e:

            print(f"Error on page {page_number}: {e}")

            final_results.append({
                "page": page_number,
                "summary": "ERROR",
                "keywords": []
            })

    return final_results


# =========================================================
# SAVE OUTPUT
# =========================================================

def save_output(data, output_path):

    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    results = process_pages()

    save_output(results, OUTPUT_JSON)

    print("\n===================================")
    print("Processing completed.")
    print(f"Saved to: {OUTPUT_JSON}")