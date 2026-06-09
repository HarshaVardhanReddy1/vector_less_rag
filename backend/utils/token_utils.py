"""Shared token-counting utility used across the processing pipeline."""

import tiktoken


def get_encoder() -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model("gpt-4o")
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(get_encoder().encode(text))
