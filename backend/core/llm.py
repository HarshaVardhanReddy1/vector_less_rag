import os
from typing import Iterator

from dotenv import load_dotenv
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI, OpenAI


def _load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPEN_ROUTER_API_KEY is not set. Add it to the environment or the project .env file."
        )
    return api_key


def get_client() -> OpenAI:
    client = OpenAI(
        api_key=_load_api_key(),
        base_url="https://openrouter.ai/api/v1",
    )
    return wrap_openai(client)


def get_async_client() -> AsyncOpenAI:
    """Return an async OpenAI-compatible client for use with await/asyncio.gather."""
    client = AsyncOpenAI(
        api_key=_load_api_key(),
        base_url="https://openrouter.ai/api/v1",
    )
    return wrap_openai(client)


@traceable(run_type="llm", name="LLM · generate_response")
def generate_response(prompt: str, model: str = "openai/gpt-oss-120b:free") -> str:
    try:
        client   = get_client()
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise RuntimeError("The LLM returned no choices.")

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("The LLM returned an empty message.")

        return content.strip()
    except Exception as error:
        preview = prompt[:200].replace("\n", " ")
        raise RuntimeError(
            f"LLM request failed for model '{model}'. Prompt preview: {preview}"
        ) from error


def generate_response_stream(
    prompt: str, model: str = "openai/gpt-oss-120b:free"
) -> Iterator[str]:
    """Yield response text tokens one at a time using the streaming API."""
    try:
        client = get_client()
        stream = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as error:
        preview = prompt[:200].replace("\n", " ")
        raise RuntimeError(
            f"LLM stream failed for model '{model}'. Prompt preview: {preview}"
        ) from error
