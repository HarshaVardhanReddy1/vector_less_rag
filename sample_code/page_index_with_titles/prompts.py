def generate_toc_from_context_prompt(context, previous_toc):

    prompt = f"""
You are an expert document Table of Contents (TOC) extraction system.

Your task is to analyze the provided document context chunk and extend the existing TOC.

The document context contains explicit page markers in this format:

================ PAGE X START ================
...
================ PAGE X END ================

You must carefully extract ALL valid TOC/headings visible in the current context and continue the TOC sequentially.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Return a flat sequential list of TOC nodes.

Each node must contain ONLY:

1. title
2. node_id
3. page_number

Do NOT generate summaries.

--------------------------------------------------
CRITICAL REQUIREMENTS
--------------------------------------------------

1. Preserve ALL existing TOC entries EXACTLY as provided.
2. NEVER modify:
   - existing titles
   - existing node_ids
   - existing page_numbers
3. Append ONLY NEW entries discovered in the current context.
4. Maintain exact document order.
5. Do NOT duplicate existing entries.
6. Extract EVERY valid heading visible in the context.
7. Include:
   - sections
   - subsections
   - sub-subsections
   - appendices
   - statistical tables
   - officer lists
   - conference names
   - table entries if they appear as TOC entries
   - all numbered headings
8. Do NOT skip headings because they appear small or administrative.
9. Do NOT hallucinate:
   - titles
   - page_numbers
   - node_ids
10. Use ONLY information visible in the current context.
11. Return ONLY valid JSON.
12. Do NOT include explanations.
13. Do NOT wrap output inside markdown.
14. Preserve heading text as closely as possible.
15. Merge multiline headings into a single title when necessary.
16. Do NOT truncate titles.
17. Ignore:
   - paragraph text
   - page headers
   - page footers
   - repeated navigation text
   - random bold text
18. Extract ONLY real TOC/headings.
19. If a heading appears incomplete due to chunk boundaries, extract the visible portion only.
20. Do NOT invent missing continuation text.

--------------------------------------------------
NODE ID RULES
--------------------------------------------------

ALL node_ids MUST follow continuous hierarchical NUMERIC numbering.

Valid examples:

1
1.1
1.2
1.2.1
1.2.1.1
2
2.1
3

Rules:
- Use ONLY numeric hierarchy.
- NEVER use alphabetic node_ids such as:
    A
    A.1
    B
    G.1
- Appendices and supplementary sections must also use numeric numbering.
- Continue numbering from PREVIOUS TOC.
- Never restart numbering incorrectly.
- Never skip numbering levels.
- Never generate duplicate node_ids.
- Sibling sections must increment sequentially.
- Child numbering must belong to the nearest valid parent.
- Deep nesting is allowed:
    1.1.1
    1.1.1.1
- Maintain consistent hierarchy throughout the TOC.
- Infer hierarchy carefully from surrounding headings and ordering.
- If hierarchy is unclear, use the most reasonable continuation based on nearby headings.
- Never generate random numbering.

--------------------------------------------------
PAGE NUMBER RULES
--------------------------------------------------

1. Use ONLY visible page markers.
2. Assign the page where the heading FIRST appears.
3. Never guess page numbers.
4. Never reuse incorrect previous page numbers.
5. Page numbers must always be integers.

--------------------------------------------------
HEADING EXTRACTION RULES
--------------------------------------------------

1. Extract headings exactly as they appear.
2. Preserve ordering exactly.
3. Merge wrapped multiline headings correctly.
4. Include deeply nested headings if they are real TOC entries.
5. Include table names ONLY if they appear as TOC entries.
6. Include appendices ONLY if visible in the TOC.
7. Do NOT convert paragraph sentences into headings.
8. Do NOT omit headings because they appear repetitive.
9. Do NOT compress multiple headings into one.
10. Every extracted node must represent a real visible heading.

--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

[
    {{
        "title": "Overview",
        "node_id": "1",
        "page_number": 1
    }},
    {{
        "title": "Monetary Policy and Economic Developments",
        "node_id": "2",
        "page_number": 3
    }},
    {{
        "title": "Recent Economic Developments",
        "node_id": "2.1",
        "page_number": 4
    }}
]

--------------------------------------------------
PREVIOUS TOC
--------------------------------------------------

{previous_toc}

--------------------------------------------------
DOCUMENT CONTEXT
--------------------------------------------------

{context}

Return ONLY valid JSON array.
"""

    return prompt

def generate_json_fix_prompt(
    broken_json: str,
    error_message: str,
) -> str:

    return f"""
You are an expert JSON repair system.

Your task is to repair invalid JSON.

IMPORTANT RULES:

1. Fix ONLY JSON syntax/formatting issues.
2. Do NOT change the meaning of the content.
3. Do NOT remove valid fields.
4. Preserve all original data whenever possible.
5. Return ONLY valid JSON.
6. Do NOT add markdown or explanations.

JSON ERROR:
{error_message}

BROKEN JSON:
{broken_json}
"""