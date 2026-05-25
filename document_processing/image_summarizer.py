from openai import OpenAI
import base64
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present


def _get_client() -> OpenAI:
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPEN_ROUTER_API_KEY environment variable is not set.")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def summarize_image(image_path: str) -> str:
    """Summarize scanned images, charts, diagrams, flowcharts, screenshots, and normal images."""
    base64_image = encode_image(image_path)
    client = _get_client()

    response = client.chat.completions.create(
        model="qwen/qwen2.5-vl-72b-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Look at this image and describe only what is actually present.\n\n"
                            "- If there is text, transcribe it.\n"
                            "- If there is a table, reproduce it in markdown.\n"
                            "- If there is a chart or graph, describe what it shows and its key values.\n"
                            "- If there is a diagram or flowchart, explain the flow.\n"
                            "- If there are other visual elements, describe them briefly.\n\n"
                            "Skip any category that does not appear in the image. "
                            "Do not mention or explain missing elements."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "sample_scan.png"
    summary = summarize_image(image_path)
    print("\n===== IMAGE SUMMARY =====\n")
    print(summary)