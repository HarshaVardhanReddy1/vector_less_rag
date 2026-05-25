import os
import re
import sys

import pymupdf4llm

# Ensure this file's directory is on the path so image_summarizer can be imported
# regardless of the working directory the script is launched from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_summarizer import summarize_image


def run_document_processing_pipeline(pdf_path: str, base_output_dir: str) -> str:
    """Convert a PDF to enriched markdown with VLM-generated image descriptions.

    Returns the path to the final markdown file.
    """
    doc_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    # Use absolute paths so PyMuPDF always writes images to the right place
    # regardless of where the script is launched from.
    base_output_dir = os.path.abspath(base_output_dir)
    image_output_dir = os.path.join(base_output_dir, "extracted_images", doc_stem)
    os.makedirs(image_output_dir, exist_ok=True)

    print("Step 1: Extracting native layout text and asset images...")
    raw_markdown = pymupdf4llm.to_markdown(
        doc=pdf_path,
        write_images=True,
        image_path=image_output_dir,
        image_format="png",
    )

    print("Step 2: Cataloging extracted files and generating VLM summaries...")
    # Pull image paths directly from the markdown so we only summarize images
    # that belong to this document (not leftover files in the folder).
    referenced_images = re.findall(r"!\[[^\]]*\]\(([^)]+\.png)\)", raw_markdown)

    image_summaries: dict[str, str] = {}
    for img_path in referenced_images:
        # img_path may be relative; resolve against cwd for the actual file read
        abs_img_path = os.path.abspath(img_path)
        filename = os.path.basename(abs_img_path)
        try:
            image_summaries[filename] = summarize_image(abs_img_path)
        except Exception as exc:
            print(f"  Warning: could not summarize {filename}: {exc}")

    print("Step 3: Replacing markdown placeholders with VLM content blocks...")
    # Matches empty image tags produced by PyMuPDF: ![](path/to/file.png)
    placeholder_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

    def replace_placeholder(match: re.Match) -> str:
        full_placeholder_path = match.group(2)
        filename_key = os.path.basename(full_placeholder_path)

        if filename_key in image_summaries:
            summary = image_summaries[filename_key]
            return (
                f"\n\n<IMAGE_CONTEXT src='{full_placeholder_path}'>\n"
                f"{summary}\n"
                f"</IMAGE_CONTEXT>\n\n"
            )

        # Preserve the original tag if no summary was produced
        return match.group(0)

    final_markdown = re.sub(placeholder_pattern, replace_placeholder, raw_markdown)

    final_md_path = os.path.join(base_output_dir, f"{doc_stem}.md")
    with open(final_md_path, "w", encoding="utf-8") as f:
        f.write(final_markdown)

    print(f"\nPipeline complete. Output saved to: {final_md_path}")
    return final_md_path


if __name__ == "__main__":
    PDF_FILE_PATH = r"document_processing/docs/earthmover.pdf"
    OUTPUT_DIRECTORY = r"document_processing/docs/outputs"

    run_document_processing_pipeline(PDF_FILE_PATH, OUTPUT_DIRECTORY)