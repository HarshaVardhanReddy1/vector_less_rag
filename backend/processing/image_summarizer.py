"""VLM-based image description using the shared OpenRouter client."""

import base64

from backend.core.llm import get_client


_VLM_MODEL = "qwen/qwen2.5-vl-72b-instruct"

_IMAGE_SUMMARY_PROMPT = (
    "Look at this image and describe only what is actually present.\n\n"
    "- If there is text, transcribe it.\n"
    "- If there is a table, reproduce it in markdown.\n"
    "- If there is a chart or graph, describe what it shows and its key values.\n"
    "- If there is a diagram or flowchart, explain the flow.\n"
    "- If there are other visual elements, describe them briefly.\n\n"
    "Skip any category that does not appear in the image. "
    "Do not mention or explain missing elements."
)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def summarize_image(image_path: str) -> str:
    base64_image = encode_image(image_path)
    client       = get_client()

    response = client.chat.completions.create(
        model=_VLM_MODEL,
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _IMAGE_SUMMARY_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content
