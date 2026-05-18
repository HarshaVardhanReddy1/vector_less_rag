# import json
 
# import re
# from typing import List, Dict

# # =========================================================
# # CONFIG
# # =========================================================

# MODEL_NAME = "openai/gpt-oss-120b:free"

# INPUT_JSON = "pages.json"
# OUTPUT_JSON = "generated_toc.json"

# PAGES_PER_CHUNK = 3


# # =========================================================
# # LOAD PAGES
# # =========================================================

# def load_pages(json_path: str) -> List[Dict]:

#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     return data


# # =========================================================
# # CREATE PAGE MARKED TEXT
# # =========================================================

# def build_chunk_text(pages: List[Dict], start_index: int) -> str:

#     full_text = ""

#     for idx, page_data in enumerate(pages):

#         page_number = start_index + idx + 1

#         text = page_data.get("page_text", "").strip()

#         if not text:
#             continue

#         full_text += f"\n\n===== PAGE {page_number} =====\n\n"
#         full_text += text

#     return full_text


# # =========================================================
# # PROMPT
# # =========================================================

# def generate_prompt(document_text: str) -> str:

#     prompt = f"""
# You are an expert document structure extraction system.

# Your task is to extract:
# - headings
# - subheadings
# - hierarchy levels
# - summaries
# - physical page numbers

# IMPORTANT RULES:
# - Extract ONLY headings/subheadings
# - Ignore paragraph text
# - Use the PAGE markers
# - Return ONLY valid JSON
# - No explanations
# - No markdown
# - No comments
# - If nothing exists return []

# LEVEL RULES:
# - Main chapter = level 1
# - Section = level 2
# - Subsection = level 3

# JSON FORMAT:

# [
#   {{
#     "title": "Introduction",
#     "level": 1,
#     "page": 1,
#     "summary": "Overview of the section"
#   }}
# ]

# DOCUMENT:

# {document_text}
# """

#     return prompt


# # =========================================================
# # CALL LLM
# # =========================================================

# def call_llm(prompt: str):

#     response = ollama.chat(
#         model=MODEL_NAME,
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         options={
#             "temperature": 0
#         }
#     )

#     return response["message"]["content"]


# # =========================================================
# # EXTRACT JSON
# # =========================================================

# def extract_json(text: str):

#     text = text.strip()

#     print("\n================ LLM OUTPUT ================\n")
#     print(text)

#     # Remove markdown json blocks
#     text = re.sub(r"```json", "", text)
#     text = re.sub(r"```", "", text)

#     start = text.find("[")
#     end = text.rfind("]")

#     if start == -1 or end == -1:
#         raise ValueError("No valid JSON array found.")

#     json_text = text[start:end + 1]

#     return json.loads(json_text)


# # =========================================================
# # PROCESS DOCUMENT
# # =========================================================

# def process_document():

#     pages = load_pages(INPUT_JSON)

#     final_toc = []

#     total_pages = len(pages)

#     for i in range(0, total_pages, PAGES_PER_CHUNK):

#         chunk_pages = pages[i:i + PAGES_PER_CHUNK]

#         print(f"\nProcessing chunk starting at page {i + 1}")

#         chunk_text = build_chunk_text(chunk_pages, i)

#         if not chunk_text.strip():
#             print("Empty chunk skipped.")
#             continue

#         prompt = generate_prompt(chunk_text)

#         try:

#             llm_output = call_llm(prompt)

#             toc_data = extract_json(llm_output)

#             if isinstance(toc_data, list):

#                 final_toc.extend(toc_data)

#                 print(f"Added {len(toc_data)} nodes")

#         except Exception as e:

#             print(f"\nERROR: {e}")

#     return final_toc


# # =========================================================
# # REMOVE DUPLICATES
# # =========================================================

# def remove_duplicates(toc_data):

#     unique = []
#     seen = set()

#     for item in toc_data:

#         title = item.get("title", "").strip().lower()
#         page = item.get("page", 0)

#         key = (title, page)

#         if key not in seen:

#             seen.add(key)

#             unique.append(item)

#     return unique


# # =========================================================
# # SAVE OUTPUT
# # =========================================================

# def save_output(data, output_path):

#     with open(output_path, "w", encoding="utf-8") as f:

#         json.dump(data, f, indent=4, ensure_ascii=False)


# # =========================================================
# # MAIN
# # =========================================================

# if __name__ == "__main__":

#     toc = process_document()

#     toc = remove_duplicates(toc)

#     save_output(toc, OUTPUT_JSON)

#     print("\n===================================")
#     print("TOC generation completed.")
#     print(f"Total nodes: {len(toc)}")
#     print(f"Saved to: {OUTPUT_JSON}")