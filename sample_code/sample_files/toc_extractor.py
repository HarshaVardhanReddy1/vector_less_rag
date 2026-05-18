from sample_code.sample_files.toc_detector2 import data, extract_json
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response
import json

def generate_toc_extraction_prompt(toc_text):

    return f"""
You are an expert PDF document structure analyzer.

Your task is to analyze the given text and determine whether it represents
a valid Table of Contents (TOC).

A valid TOC usually contains:
- section or chapter titles
- subsection titles
- page numbers
- dotted leaders
- structured list-style formatting
- appendix/index style entries
- hierarchical organization

If the given text is NOT a TOC:
Return ONLY:
NOT_TOC

If the given text IS a TOC:
Extract all TOC entries.

For each TOC entry extract:
- title
- level
- page

Rules:
- Preserve hierarchy levels
- Main sections should have smaller level numbers
- Subsections should have larger level numbers
- Ignore headers and footers
- Ignore empty lines
- Ignore decorative dots
- Ignore unrelated paragraphs
- Return ONLY valid JSON
- Do not explain anything
- Do not generate markdown

Return format if TOC is detected:

[
    {{
        "title": "Overview",
        "level": 1,
        "page": 1
    }},
    {{
        "title": "March 2024 Summary",
        "level": 2,
        "page": 3
    }}
]

TOC TEXT:
----------------
{toc_text}
----------------
"""
def generate_toc_list(lst):
    result=[]
    for page_num in lst:
        page_text = data[page_num].get("page_text", "").strip()

        if not page_text:
            continue
        prompt = generate_toc_extraction_prompt(page_text)
        response = generate_response(prompt)
        print(response)
        if response.strip() == "NOT_TOC":
            continue
        json_data = extract_json(response)
        result.extend(json_data)
    return result

result = generate_toc_list([0,2,3,6])
 
with open("toc_data.json","w",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=4)