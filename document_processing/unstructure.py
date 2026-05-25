"""
unstructure.py
--------------
Send a document to the Unstructured.io API and save the parsed result as a
Markdown file.

Usage (stand-alone):
    python document_processing/unstructure.py

Environment variable required:
    UNSTRUCTURED_API_KEY  – your Unstructured.io API key

The function `run_unstructured_pipeline` can also be imported and called from
other modules in this package.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# ---------------------------------------------------------------------------
# API settings
# ---------------------------------------------------------------------------
UNSTRUCTURED_API_URL = "https://api.unstructuredapp.io/general/v0/general"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _elements_to_markdown(elements: list[dict]) -> str:
    """Convert a list of Unstructured element dicts to a Markdown string."""
    lines: list[str] = []

    for el in elements:
        el_type = el.get("type", "")
        text = el.get("text", "").strip()

        if not text:
            continue

        if el_type == "Title":
            lines.append(f"\n## {text}\n")
        elif el_type == "Header":
            lines.append(f"\n# {text}\n")
        elif el_type in ("NarrativeText", "FigureCaption"):
            lines.append(f"\n{text}\n")
        elif el_type == "ListItem":
            lines.append(f"- {text}")
        elif el_type == "Table":
            # Unstructured may return tables as plain text; wrap in a code block
            lines.append(f"\n```\n{text}\n```\n")
        elif el_type in ("PageBreak",):
            lines.append("\n---\n")
        else:
            # UncategorizedText, Image descriptions, etc.
            lines.append(f"\n{text}\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_unstructured_pipeline(
    doc_path: str,
    output_dir: str,
    *,
    strategy: str = "hi_res",
    output_filename: str | None = None,
) -> str:
    """Send *doc_path* to Unstructured.io and write the result as Markdown.

    Parameters
    ----------
    doc_path:
        Absolute or relative path to the source document (PDF, DOCX, …).
    output_dir:
        Directory where the output Markdown file will be saved (created if
        it does not exist).
    strategy:
        Unstructured partitioning strategy.  ``"hi_res"`` gives the best
        layout accuracy but is slower; ``"fast"`` skips OCR.
    output_filename:
        Override the default output filename
        (``<source_stem>_unstructured.md``).

    Returns
    -------
    str
        Path to the saved Markdown file.
    """
    api_key = os.environ.get("UNSTRUCTURED_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "UNSTRUCTURED_API_KEY is not set. "
            "Export it before running this script:\n"
            "  $env:UNSTRUCTURED_API_KEY = 'your-key-here'  (PowerShell)\n"
            "  export UNSTRUCTURED_API_KEY='your-key-here'  (bash)"
        )

    doc_path = os.path.abspath(doc_path)
    if not os.path.isfile(doc_path):
        raise FileNotFoundError(f"Document not found: {doc_path}")

    os.makedirs(output_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # Step 1 – upload and partition
    # -----------------------------------------------------------------------
    print(f"Step 1: Uploading '{os.path.basename(doc_path)}' to Unstructured.io …")

    with open(doc_path, "rb") as fh:
        response = requests.post(
            UNSTRUCTURED_API_URL,
            headers={"unstructured-api-key": api_key},
            files={"files": (os.path.basename(doc_path), fh, "application/octet-stream")},
            data={"strategy": strategy},
            timeout=300,  # large documents can take a while
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Unstructured API returned HTTP {response.status_code}:\n{response.text}"
        )

    elements: list[dict] = response.json()
    print(f"  → Received {len(elements)} element(s) from the API.")

    # -----------------------------------------------------------------------
    # Step 2 – save raw JSON response (optional, useful for debugging)
    # -----------------------------------------------------------------------
    stem = os.path.splitext(os.path.basename(doc_path))[0]
    json_path = os.path.join(output_dir, f"{stem}_unstructured.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(elements, jf, indent=2, ensure_ascii=False)
    print(f"Step 2: Raw JSON saved → {json_path}")

    # -----------------------------------------------------------------------
    # Step 3 – convert elements to Markdown and save
    # -----------------------------------------------------------------------
    print("Step 3: Converting elements to Markdown …")
    markdown = _elements_to_markdown(elements)

    md_filename = output_filename or f"{stem}_unstructured.md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(markdown)

    print(f"\nPipeline complete. Markdown saved → {md_path}")
    return md_path


# ---------------------------------------------------------------------------
# Stand-alone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Edit these two paths to point at the document you want to process.
    PDF_FILE_PATH = r"document_processing/docs/earthmover.pdf"
    OUTPUT_DIRECTORY = r"document_processing/docs/outputs"

    run_unstructured_pipeline(PDF_FILE_PATH, OUTPUT_DIRECTORY)
