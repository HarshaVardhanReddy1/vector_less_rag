"""Document ingestion pipeline: PDF → markdown → nodes JSON.

Public entry point:
    run_document_processing_pipeline(pdf_path, base_output_dir)
        → (markdown_path, json_path)
"""

import json
import os

from backend.processing.pdf_parser import parse_pdf_to_markdown
from backend.processing.node_extractor import extract_heading_nodes
from backend.processing.node_enricher import enrich_nodes


def run_document_processing_pipeline(
    pdf_path: str,
    base_output_dir: str,
) -> tuple[str, str]:
    """Convert a PDF to an enriched markdown file and a heading-based JSON file.

    Args:
        pdf_path:        Absolute or relative path to the source PDF.
        base_output_dir: Directory where <stem>.md and <stem>.json are written.
                         Extracted images go into extracted_images/<stem>/.

    Returns:
        (markdown_path, json_path)
    """
    doc_stem         = os.path.splitext(os.path.basename(pdf_path))[0]
    base_output_dir  = os.path.abspath(base_output_dir)
    image_output_dir = os.path.join(base_output_dir, "extracted_images", doc_stem)
    os.makedirs(image_output_dir, exist_ok=True)

    # Stage 1 — PDF → enriched markdown
    full_md, heading_page_map = parse_pdf_to_markdown(pdf_path, image_output_dir)

    md_path = os.path.join(base_output_dir, f"{doc_stem}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    # Stage 2 — Markdown → flat heading nodes
    nodes = extract_heading_nodes(full_md, heading_page_map)

    # Stage 3 — LLM enrichment (summary, keywords, node_id)
    nodes = enrich_nodes(nodes)

    json_path = os.path.join(base_output_dir, f"{doc_stem}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=4, ensure_ascii=False)

    print(f"\nMarkdown : {md_path}")
    print(f"JSON     : {json_path}  ({len(nodes)} heading nodes)")
    return md_path, json_path
