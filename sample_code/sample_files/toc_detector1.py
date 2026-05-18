import json
import re
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response


# -----------------------------------
# Clean Page Text
# -----------------------------------
def clean_text(text):

    lines = text.splitlines()

    cleaned = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # remove extra spaces
        line = re.sub(r"\s+", " ", line)

        cleaned.append(line)

    return "\n".join(cleaned)


# -----------------------------------
# Build Prompt
# -----------------------------------
def build_toc_prompt(page_text):

    return f"""
You are an expert PDF document analyzer.

Determine whether the following page is a
Table of Contents (TOC) page.

A TOC page usually contains:
- section titles
- subsection titles
- page numbers
- dotted leaders
- structured list entries
- appendix/index style entries

Rules:
- Ignore headers and footers
- Ignore normal paragraphs
- Focus on page structure
- Return ONLY valid JSON
- Do not explain anything
- Do not generate markdown

Return format:

{{
    "is_toc": true,
    "confidence": 95
}}

OR

{{
    "is_toc": false,
    "confidence": 20
}}

PAGE TEXT:
----------------
{page_text[:4000]}
"""


# -----------------------------------
# Parse Response
# -----------------------------------
def parse_response(response):

    try:

        match = re.search(r"\{[\s\S]*?\}", response)

        if not match:
            return False, 0

        data = json.loads(match.group())

        is_toc = bool(data.get("is_toc", False))
        confidence = int(data.get("confidence", 0))

        return is_toc, confidence

    except Exception:
        return False, 0


# -----------------------------------
# Detect TOC Pages
# -----------------------------------
def detect_toc_pages(json_path, max_pages=20):

    with open(json_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    toc_pages = []

    for i in range(min(max_pages, len(pages))):

        current_text = clean_text(
            pages[i].get("page_text", "")
        )

        # skip empty pages
        if not current_text.strip():
            continue

        prompt = build_toc_prompt(current_text)

        try:

            response = generate_response(prompt)

            is_toc, confidence = parse_response(response)

            print(
                f"[PAGE {i}] "
                f"TOC={is_toc} "
                f"CONFIDENCE={confidence}"
            )

            if is_toc and confidence >= 70:
                toc_pages.append(i)

        except Exception as e:
            print(f"[ERROR] Page {i}: {e}")

    return toc_pages


# -----------------------------------
# Run
# -----------------------------------
toc_pages = detect_toc_pages("pages.json")

print("\nDetected TOC Pages:")
print(toc_pages)