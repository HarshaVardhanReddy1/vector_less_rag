import json
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response


 
with open("pages.json", "r", encoding="utf-8") as f:
    data = json.load(f)


 
def generate_prompt(page_text: str) -> str:

    prompt = f"""
You are an expert PDF document structure analyzer.

Your task is to determine whether the given text represents a
Table of Contents (TOC) page.

A TOC page usually contains:
- section or chapter titles
- subsection titles
- page numbers
- dotted leaders (.....)
- structured list-style formatting
- appendix/index style entries
- many short lines instead of long paragraphs

A normal content page usually contains:
- long paragraphs
- explanations
- continuous prose
- descriptive text

Important Instructions:
- Focus on document structure, not topic meaning
- Ignore headers and footers
- Ignore standalone page numbers
- Abstract, summary, notation list, figure list, references, and table lists are NOT TOC pages
- Return ONLY one word
- Do not explain anything
- Do not generate markdown

Return ONLY:
yes

OR

no

Given Text:
----------------
{page_text[:4000]}
----------------
"""

    return prompt

def extract_json(text):
    response = text.replace("```json", "")
    response = response.replace("```", "")
    response = response.strip()

    data = json.loads(response)
    return data

 
def check_toc():

    toc_pages = []

    for i, page in enumerate(data[:20]):

        page_text = page.get("page_text", "").strip()

        # skip empty pages
        if not page_text:
            continue

        prompt = generate_prompt(page_text)

        result = generate_response(prompt)

        result = result.strip().lower()

        print(f"[PAGE {i}] -> {result}")

        if result == "yes":
            toc_pages.append(i)

    return toc_pages


# -----------------------------------
# Run
# -----------------------------------
if __name__ == "__main__":
    result = check_toc()

    print("\nDetected TOC Pages:")
    print(result)