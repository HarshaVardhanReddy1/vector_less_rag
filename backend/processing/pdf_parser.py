"""PDF → enriched markdown.

Reads a PDF page by page, converts each page to markdown via pymupdf4llm,
replaces image placeholders with VLM-generated IMAGE_CONTEXT blocks, and
returns the combined markdown string along with a heading→page map.
"""

import os
import re

import fitz          # PyMuPDF
import pymupdf4llm

from backend.processing.image_summarizer import summarize_image


_HEADING_RE       = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
_IMAGE_CONTEXT_RE = re.compile(r"<IMAGE_CONTEXT[^>]*>.*?</IMAGE_CONTEXT>", re.DOTALL)


def _replace_images_with_context(raw_md: str) -> str:
    """Swap markdown image links with VLM-generated IMAGE_CONTEXT blocks."""
    referenced = re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", raw_md)

    summaries: dict[str, str] = {}
    for img_path in referenced:
        abs_path = os.path.abspath(img_path)
        key      = os.path.basename(abs_path)
        try:
            summaries[key] = summarize_image(abs_path)
        except Exception as exc:
            print(f"  Warning: could not summarize {key}: {exc}")

    def _replace(match: re.Match) -> str:
        full_path = match.group(2)
        key       = os.path.basename(full_path)
        if key in summaries:
            return (
                f"\n\n<IMAGE_CONTEXT src='{full_path}'>\n"
                f"{summaries[key]}\n"
                f"</IMAGE_CONTEXT>\n\n"
            )
        return match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _replace, raw_md)


def parse_pdf_to_markdown(
    pdf_path: str,
    image_output_dir: str,
) -> tuple[str, dict[str, int]]:
    """Convert a PDF to a single enriched markdown string.

    Returns:
        full_md          — complete markdown with IMAGE_CONTEXT blocks
        heading_page_map — {heading_text: first_page_number (1-indexed)}
    """
    pdf_doc     = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    pdf_doc.close()

    md_pages: list[str]              = []
    heading_page_map: dict[str, int] = {}

    for i in range(total_pages):
        page_num = i + 1
        print(f"Processing page {page_num}/{total_pages}...")

        raw_md   = pymupdf4llm.to_markdown(
            doc=pdf_path,
            pages=[i],
            write_images=True,
            image_path=image_output_dir,
            image_format="png",
        )
        enriched = _replace_images_with_context(raw_md)
        md_pages.append(enriched.strip())

        # Record first-seen page for each heading; mask IMAGE_CONTEXT blocks
        # first so VLM description lines that look like headings are not recorded.
        masked = _IMAGE_CONTEXT_RE.sub("", enriched)
        for hm in _HEADING_RE.finditer(masked):
            heading_text = re.sub(r"\*+", "", hm.group(2)).strip()
            if heading_text and heading_text not in heading_page_map:
                heading_page_map[heading_text] = page_num

    full_md = "\n\n".join(md_pages)
    return full_md, heading_page_map
