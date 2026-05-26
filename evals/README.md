# Sample Evaluation Set

This directory contains a small curated evaluation set for measuring retrieval quality on
page-based documents.

## Contents

- `sample_documents/`: tiny handcrafted page JSON files plus reference TOC/tree artifacts
- `sample_queries.json`: benchmark queries and expected outcomes
- `run_eval.py`: simple runner that scores retrieval hits and optional answer keyword hits

## Metrics

The runner reports:

- retrieval accuracy: selected node matches `expected_node_id`
- title match rate: selected node title contains the expected title snippet
- context keyword rate: retrieved context contains all expected context keywords
- answer keyword rate: optional, only when `--include-answer` is enabled

## Usage

Retrieval-only evaluation:

```bash
python evals/run_eval.py
```

Full evaluation including answer generation:

```bash
python evals/run_eval.py --include-answer
```

The answer mode uses the configured LLM, so it requires `OPEN_ROUTER_API_KEY`.
