
import json
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response


# -----------------------------------
# Load TOC Data
# -----------------------------------
with open("toc_data.json", "r", encoding="utf-8") as f:
    toc_data = json.load(f)


# -----------------------------------
# Load Pages Data
# -----------------------------------
with open("pages.json", "r", encoding="utf-8") as f:
    pages_data = json.load(f)


# -----------------------------------
# Extract Titles
# -----------------------------------
titles = [
    item["title"]
    for item in toc_data
]


# -----------------------------------
# Build Context From First 10 Pages
# -----------------------------------
def build_pages_context(pages, max_pages=10):

    context = ""

    for i, page in enumerate(pages[22:22+max_pages]):

        page_text = page.get("page_text", "").strip()

        if not page_text:
            continue

        context += (
            f"\n\n"
            f"========== PHYSICAL_PAGE_INDEX: {i+22} ==========\n"
            f"{page_text}\n"
        )

    return context


# -----------------------------------
# Build Prompt
# -----------------------------------
def build_prompt(titles, context):

    return f"""
You are an expert PDF document analyzer.

You are given:
1. A list of TOC titles
2. Document page content with physical page indexes

Your task:
Find which physical page index contains each title.

Rules:
- Match semantically, not exact text only
- Ignore OCR noise and spacing issues
- Ignore titles that are not present in the context
- Return ONLY valid JSON
- Do not explain anything
- Do not generate markdown

Return format:

[
    {{
        "title": "Overview",
        "physical_page_index": 5
    }},
    {{
        "title": "Financial Stability",
        "physical_page_index": 12
    }}
]

TOC TITLES:
----------------
{json.dumps(titles, indent=2)}

DOCUMENT CONTEXT:
----------------
{context[:10000]}
----------------
"""


# -----------------------------------
# Generate Context
# -----------------------------------
context = build_pages_context(
    pages_data,
    max_pages=10
)
 



# -----------------------------------
# Generate Prompt
# -----------------------------------
prompt = build_prompt(
    titles,
    context
)
print(prompt)

# -----------------------------------
# LLM Response
# -----------------------------------
response = generate_response(prompt)

print(response)


