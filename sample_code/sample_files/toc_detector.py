import json
import re
from typing import List, Tuple, Dict
from sample_code.page_index_with_no_toc.open_ai_llm import generate_response

 
 

def extract_json_from_text(text: str) -> Dict:
    """
    Try to extract a JSON object from the model output.
    It finds the first {...} block and json.loads it.
    Raises ValueError if none found or parsing fails.
    """
    # Try to find a JSON code fence first
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    candidate = None
    if m:
        candidate = m.group(1)
    else:
        # Fallback: find the first {...} block
        m2 = re.search(r'(\{(?:.|\n)*\})', text)
        if m2:
            candidate = m2.group(1)
    if not candidate:
        raise ValueError(f"No JSON object found in model output: {text[:200]!r}")
    try:
        return json.loads(candidate)
    except Exception as e:
        # Try a more lenient approach: remove trailing commas, etc.
        cleaned = re.sub(r',\s*}', '}', candidate)
        cleaned = re.sub(r',\s*\]', ']', cleaned)
        return json.loads(cleaned)

TOC_DETECT_PROMPT = """
You are a strict Table of Contents detector.

Your task:
Determine whether the given page is an actual Table of Contents (TOC) page.

A TOC page usually contains:
- many section titles
- many page numbers
- dotted leader patterns like ....... 12
- very little paragraph content
- navigation-style formatting

A normal content page usually contains:
- long paragraphs
- explanations
- financial text
- continuous sentences
- detailed discussion

IMPORTANT:
- Do NOT classify a page as TOC just because it contains headings or numbers.
- Abstract, summary, notation list, figure list, table list, references, appendix, and financial tables are NOT TOC pages.
- Return "yes" ONLY if this page is clearly a real table of contents page.

Given page text:
----------------
{content}
----------------

Return ONLY valid JSON in this exact format:

{{
  "thinking": "short reason",
  "toc_detected": "yes or no"
}}
"""

def detect_toc_on_page(page_text: str, max_retries: int = 2) -> str:
    """
    Returns 'yes' or 'no' depending on whether the model detects a TOC on the page.
    Retries up to max_retries if parsing fails.
    """
    prompt = TOC_DETECT_PROMPT.format(content=page_text[:6000])  # truncate long pages for safety
    attempt = 0
    last_err = None
    while attempt <= max_retries:
        attempt += 1
        resp = generate_response(prompt)
        try:
            data = extract_json_from_text(resp)
            res = data.get("toc_detected")
            if isinstance(res, str):
                return res.strip().lower()
            # if not in expected format, raise
            raise ValueError("Missing 'toc_detected' key or unexpected type")
        except Exception as e:
            last_err = e
            # continue to retry
            continue
    raise last_err

def find_toc_pages(page_list: List[Tuple[str, int]], max_pages: int = 20) -> List[int]:
    """
    Scans up to max_pages pages from page_list (list of (text, token_count)).
    Returns the list of indices (0-based) that contain TOC pages.
    Heuristic: collect consecutive pages with 'yes'. If a 'no' follows a 'yes', stop scanning.
    """
    toc_pages = []
    last_page_is_yes = False
    limit = min(max_pages, len(page_list))
    for i in range(limit):
        text, _ = page_list[i]
        try:
            result = detect_toc_on_page(text)
        except Exception as e:
            # If detection fails for one page, treat it as 'no' and continue
            print(f"[warn] detection failed for page {i}: {e}")
            result = "no"
        if result == "yes":
            toc_pages.append(i)
            last_page_is_yes = True
            print(f"[info] page {i} -> TOC detected")
        elif result == "no" and last_page_is_yes:
            print(f"[info] TOC ended at page {i-1}")
            break
        else:
            print(f"[info] page {i} -> no TOC")
    if not toc_pages:
        print("[info] No TOC pages found in the scanned range.")
    return toc_pages

# Example helpers to load pages.json written by extract_pages.py
def load_pages_from_json(path: str) -> List[Tuple[str, int]]:
    with open(path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    return [(item.get("page_text",""), int(item.get("tokens",0))) for item in arr]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages_json", help="pages.json produced by extract_pages.py", required=True)
    parser.add_argument("--max_pages", type=int, default=20, help="How many pages to check for TOC")
    args = parser.parse_args()

    pages = load_pages_from_json(args.pages_json)
    toc_pages = find_toc_pages(pages, max_pages=args.max_pages)
    print("TOC page indices (0-based):", toc_pages)