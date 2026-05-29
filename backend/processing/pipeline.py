"""Document ingestion pipeline: PDF → markdown → nodes JSON.

Public entry point:
    run_document_processing_pipeline(pdf_path, base_output_dir)
        → (markdown_path, json_path)
"""

import asyncio
import json
import os

from backend.processing.pdf_parser import parse_pdf_to_markdown
from backend.processing.node_extractor import extract_heading_nodes
from backend.processing.node_chunker import chunk_nodes
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
    full_md, heading_page_map = asyncio.run(parse_pdf_to_markdown(pdf_path, image_output_dir))

    md_path = os.path.join(base_output_dir, f"{doc_stem}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    # Stage 2 — Markdown → raw flat nodes (no LLM)
    nodes = extract_heading_nodes(full_md, heading_page_map)

    raw_json_path = os.path.join(base_output_dir, f"{doc_stem}_raw.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=4, ensure_ascii=False)
    print(f"Raw nodes: {raw_json_path}  ({len(nodes)} nodes)")

    # Stage 3 — Paragraph chunking (no LLM)
    nodes = chunk_nodes(nodes)

    chunked_json_path = os.path.join(base_output_dir, f"{doc_stem}_chunked.json")
    with open(chunked_json_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=4, ensure_ascii=False)
    print(f"Chunked  : {chunked_json_path}  ({len(nodes)} nodes after chunking)")

    # Stage 4 — LLM enrichment (node_id, summary, keywords)
    nodes = enrich_nodes(nodes)

    json_path = os.path.join(base_output_dir, f"{doc_stem}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=4, ensure_ascii=False)

    print(f"Enriched : {json_path}  ({len(nodes)} nodes)")
    return md_path, json_path
