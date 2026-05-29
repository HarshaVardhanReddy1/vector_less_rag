"""PDF → enriched markdown.

Reads a PDF page by page, converts each page to markdown via pymupdf4llm,
replaces image placeholders with VLM-generated IMAGE_CONTEXT blocks (carrying
a type= attribute and optional caption=), strips redundant raw picture-text
blocks, and returns the combined markdown string along with a heading→page map.
"""

import os
import re

import fitz          # PyMuPDF
import pymupdf4llm

from backend.processing.image_summarizer import summarize_image


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
_IMAGE_CONTEXT_RE = re.compile(r"<IMAGE_CONTEXT[^>]*>.*?</IMAGE_CONTEXT>", re.DOTALL)

# Matches pymupdf4llm's raw picture-text fallback blocks.
_PICTURE_TEXT_RE = re.compile(
    r"\*+[-\s]*Start of picture text[-\s]*\*+.*?\*+[-\s]*End of picture text[-\s]*\*+",
    re.DOTALL | re.IGNORECASE,
)

# Matches a bold figure/table caption that appears within a few blank lines
# after a closing IMAGE_CONTEXT tag.
_CAPTION_RE = re.compile(
    r"(</IMAGE_CONTEXT>)"
    r"((?:\s*\n){1,5}\s*)"
    r"(\*\*(?:Figure|Table|Fig\.?)\s[^*\n][^*]*\*\*)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_last_heading(md: str) -> str:
    """Return the most recent heading text found in md."""
    matches = _HEADING_RE.findall(md)
    if matches:
        _, text = matches[-1]
        return re.sub(r"\*+", "", text).strip()
    return ""


def _build_doc_context(accumulated_md: str, current_raw_md: str) -> str:
    """Build a context string from the last heading + recent plain text.

    Strips IMAGE_CONTEXT blocks and image refs so only prose reaches the VLM.
    Uses up to 600 characters of recent text to stay within prompt budgets.
    """
    last_heading = _get_last_heading(accumulated_md + "\n\n" + current_raw_md)

    plain = _IMAGE_CONTEXT_RE.sub("", accumulated_md)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", plain)
    plain = re.sub(r"\n{3,}", "\n\n", plain).strip()
    recent_text = plain[-600:]

    parts = []
    if last_heading:
        parts.append(f"Section: {last_heading}")
    if recent_text:
        parts.append(recent_text)
    return "\n".join(parts)


def _replace_images_with_context(raw_md: str, doc_context: str = "") -> str:
    """Swap markdown image links with VLM-generated IMAGE_CONTEXT blocks."""
    referenced = re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", raw_md)

    summaries: dict[str, dict] = {}
    for img_path in referenced:
        abs_path = os.path.abspath(img_path)
        key = os.path.basename(abs_path)
        try:
            summaries[key] = summarize_image(abs_path, context=doc_context)
        except Exception as exc:
            print(f"  Warning: could not summarize {key}: {exc}")

    def _replace(match: re.Match) -> str:
        full_path = match.group(2)
        key = os.path.basename(full_path)
        if key not in summaries:
            return match.group(0)
        result = summaries[key]
        img_type = result.get("type", "figure")
        description = result.get("description", "")
        return (
            f"\n\n<IMAGE_CONTEXT src='{full_path}' type='{img_type}'>\n"
            f"{description}\n"
            f"</IMAGE_CONTEXT>\n\n"
        )

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _replace, raw_md)


def _strip_picture_text(md: str) -> str:
    """Remove redundant raw picture-text blocks injected by pymupdf4llm."""
    return _PICTURE_TEXT_RE.sub("", md)


def _attach_captions(md: str) -> str:
    """Embed figure/table captions that immediately follow IMAGE_CONTEXT blocks.

    Moves the caption inside the block so it becomes part of the searchable
    image context and is indexed together with the VLM description.
    """
    def _embed(m: re.Match) -> str:
        caption_text = m.group(3).strip("*").strip()
        return f"\n\n**Caption:** {caption_text}\n</IMAGE_CONTEXT>"

    return _CAPTION_RE.sub(_embed, md)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf_to_markdown(
    pdf_path: str,
    image_output_dir: str,
) -> tuple[str, dict[str, int]]:
    """Convert a PDF to a single enriched markdown string.

    Returns:
        full_md          — complete markdown with IMAGE_CONTEXT blocks
        heading_page_map — {heading_text: first_page_number (1-indexed)}
    """
    pdf_doc = fitz.open(pdf_path)
    total_pages = len(pdf_doc)
    pdf_doc.close()

    md_pages: list[str] = []
    heading_page_map: dict[str, int] = {}
    accumulated_md = ""

    for i in range(total_pages):
        page_num = i + 1
        print(f"Processing page {page_num}/{total_pages}...")

        raw_md = pymupdf4llm.to_markdown(
            doc=pdf_path,
            pages=[i],
            write_images=True,
            image_path=image_output_dir,
            image_format="png",
        )

        doc_context = _build_doc_context(accumulated_md, raw_md)
        enriched = _replace_images_with_context(raw_md, doc_context=doc_context)
        enriched = _strip_picture_text(enriched)
        enriched = _attach_captions(enriched)
        enriched = enriched.strip()

        md_pages.append(enriched)
        accumulated_md += "\n\n" + enriched

        # Record first-seen page for each heading; mask IMAGE_CONTEXT blocks
        # so VLM description lines that look like headings are not recorded.
        masked = _IMAGE_CONTEXT_RE.sub("", enriched)
        for hm in _HEADING_RE.finditer(masked):
            heading_text = re.sub(r"\*+", "", hm.group(2)).strip()
            if heading_text and heading_text not in heading_page_map:
                heading_page_map[heading_text] = page_num

    full_md = "\n\n".join(md_pages)
    return full_md, heading_page_map
