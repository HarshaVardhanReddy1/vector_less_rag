"""VLM-based image description using the shared OpenRouter client."""

import base64

from backend.core.llm import get_async_client, get_client


_VLM_MODEL = "qwen/qwen2.5-vl-72b-instruct"

_IMAGE_SUMMARY_PROMPT = """\
Describe this image in a way that is optimized for search and question answering.

Your first line MUST be exactly:
TYPE: <one of: equation, chart, table, diagram, text, figure>

Then write the description following these rules:
- equation : Transcribe it exactly in LaTeX notation wrapped in $$...$$. Output only the LaTeX.
- table    : Reproduce it as a full markdown table. Include every cell value.
- chart    : State what the chart shows, then list all axis labels, legend entries, and key numeric values.
- diagram  : Name every node/box/step and describe every arrow or connection between them.
- text     : Transcribe the text exactly as it appears.
- figure   : Describe with specific detail — include all labels, variable names, algorithm names, numeric values, and spatial relationships.

Include domain-specific terms, entity names, and numeric values explicitly so the description matches user search queries.
Do not add a preamble like "The image shows..." — start directly with TYPE: on the first line."""


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _parse_vlm_response(raw: str) -> dict:
    """Parse 'TYPE: ...' first line + remaining content into a structured dict."""
    lines = raw.strip().splitlines()
    image_type = "figure"
    desc_start = 0

    if lines and lines[0].upper().startswith("TYPE:"):
        image_type = lines[0].split(":", 1)[1].strip().lower()
        desc_start = 1

    description = "\n".join(lines[desc_start:]).strip()
    return {"type": image_type, "description": description}


def summarize_image(image_path: str, context: str = "") -> dict:
    """Return {"type": str, "description": str} for the given image.

    context: optional surrounding document text (heading + nearby prose) that
             helps the VLM produce a more accurate, domain-aware description.
    """
    base64_image = encode_image(image_path)
    client = get_client()

    context_hint = f"Document context:\n{context}\n\n" if context.strip() else ""
    full_prompt = context_hint + _IMAGE_SUMMARY_PROMPT

    response = client.chat.completions.create(
        model=_VLM_MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )
    raw = response.choices[0].message.content
    return _parse_vlm_response(raw)


async def summarize_image_async(image_path: str, context: str = "") -> dict:
    """Async version of summarize_image — use with asyncio.gather for concurrency."""
    base64_image = encode_image(image_path)
    client = get_async_client()

    context_hint = f"Document context:\n{context}\n\n" if context.strip() else ""
    full_prompt = context_hint + _IMAGE_SUMMARY_PROMPT

    response = await client.chat.completions.create(
        model=_VLM_MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )
    raw = response.choices[0].message.content
    return _parse_vlm_response(raw)
