import os

from dotenv import load_dotenv
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI


def get_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPEN_ROUTER_API_KEY is not set. Add it to the environment or the project .env file."
        )
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    return wrap_openai(client)


@traceable(run_type="llm", name="LLM · generate_response")
def generate_response(prompt: str, model: str = "openai/gpt-oss-120b:free") -> str:
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise RuntimeError("The LLM returned no choices.")

        message_content = response.choices[0].message.content
        if not isinstance(message_content, str) or not message_content.strip():
            raise RuntimeError("The LLM returned an empty message.")

        return message_content.strip()
    except Exception as error:
        prompt_preview = prompt[:200].replace("\n", " ")
        raise RuntimeError(
            f"LLM request failed for model '{model}'. Prompt preview: {prompt_preview}"
        ) from error
