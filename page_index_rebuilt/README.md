# Page Index Rebuilt

`page_index_rebuilt` is a compact document-indexing pipeline for page-based JSON input.
It uses an LLM to build a table of contents, converts that TOC into a hierarchical page-range tree, and retrieves the most relevant section to answer a user query with grounded context.

## Pipeline Overview

The package works in three main stages:

1. Read a pages JSON file where each item includes page text and token metadata.
2. Build a merged TOC from page chunks, then convert that TOC into a tree with page ranges.
3. Retrieve the best matching node for a query and generate an answer from the pages covered by that node.

## Expected Input

The pipeline expects a JSON file shaped like:

```json
[
    {
        "page": 1,
        "page_text": "Document text for page 1",
        "token_count": 512
    }
]
```

By default, the package reads from:

- `../json_files/pdf_pages1.json`

## Generated Output

By default, the package writes:

- `../json_files/toc_rebuilt.json`: merged TOC nodes
- `../json_files/tree_rebuilt.json`: hierarchical tree with `start_index` and `end_index`
- `../json_files/query_response_log_rebuilt.json`: saved query/response history

## Module Guide

- `config.py`: default file paths and token budget
- `llm.py`: OpenRouter-backed LLM client wrapper
- `prompts.py`: prompt builders for TOC generation, node selection, and answer generation
- `utils.py`: JSON helpers, tree utilities, formatting helpers, and query logging
- `toc_generator.py`: page chunking, partial TOC generation, TOC merge, and deduplication
- `tree_builder.py`: TOC sorting, tree construction, and page-range assignment
- `retriever.py`: node selection, context extraction, and grounded answer generation
- `pipeline.py`: high-level entrypoints for index building and answering

## Setup

Install the required dependencies in your environment:

```bash
pip install openai python-dotenv
```

Add an `.env` file at the project root with:

```env
OPEN_ROUTER_API_KEY=your_api_key_here
```

The current LLM client is configured to call OpenRouter at:

- `https://openrouter.ai/api/v1`

The default model in `llm.py` is:

- `openai/gpt-oss-120b:free`

## Usage

Build the TOC and tree:

```python
from page_index_rebuilt.pipeline import build_index

result = build_index()
print(result)
```

Answer a question using an existing tree:

```python
from page_index_rebuilt.pipeline import answer_from_pages_json

result = answer_from_pages_json(
    "What does the supervision section cover?"
)
print(result["selected_node"])
print(result["answer"])
```

Call the lower-level retriever directly if you already have a tree file:

```python
from page_index_rebuilt.retriever import answer_query

result = answer_query("Explain capital planning and stress testing.")
print(result)
```

## Returned Shapes

`build_index()` returns a summary dictionary like:

```python
{
    "toc_path": ".../toc_rebuilt.json",
    "tree_path": ".../tree_rebuilt.json",
    "toc_nodes": 12,
    "root_nodes": 4
}
```

`answer_query()` and `answer_from_pages_json()` return:

```python
{
    "query": "...",
    "selected_node": {
        "node_id": "0001.1",
        "title": "...",
        "start_index": 10,
        "end_index": 15
    },
    "answer": "..."
}
```

## Retrieval Behavior

Retrieval is hierarchical by default:

1. Choose the best node among the current level.
2. Descend into its children until no better child is found.
3. Fall back to a full-tree selection pass if the hierarchical pass fails.

The final answer is generated only from the page range covered by the selected node.

## Notes

- `page_index` values are treated as 1-based page numbers.
- `token_count` is used only for chunking during TOC generation.
- Query results are appended to `query_response_log_rebuilt.json`.
- `pipeline.py` currently contains example code at module level, so importing it may trigger an immediate query unless that example is removed or guarded.
