import os
from pathlib import Path


# ============================================================================
# DIRECTORY STRUCTURE
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))

# Storage subdirectories
DOCS_DIR = DATA_DIR / "docs"  # Uploaded PDFs
NODES_DIR = DATA_DIR / "nodes"  # Intermediate artifacts: markdown + chunked JSON
TOCS_DIR = DATA_DIR / "tocs"  # Enriched nodes JSON (queried at runtime)
TREES_DIR = DATA_DIR / "trees"  # Nested retrieval trees

DEFAULT_QUERY_LOG_PATH = DATA_DIR / "responses" / "responses_log.json"


# ============================================================================
# LLM MODELS
# ============================================================================

# Primary model for enrichment, answer generation, and general reasoning
PRIMARY_MODEL = "openai/gpt-oss-120b"

# Model for answer evaluation (judging faithfulness, relevance, precision)
JUDGE_MODEL = "openai/gpt-oss-120b"

# Vision-language model for image summarization and description
VLM_MODEL = "qwen/qwen2.5-vl-72b-instruct"

# Aliases for backward compatibility and clarity
ENRICH_MODEL = PRIMARY_MODEL
RESPONSE_MODEL = PRIMARY_MODEL


# ============================================================================
# TOKEN LIMITS & BUDGETS
# ============================================================================

# Node chunking: max tokens per chunk when splitting oversized nodes
CHUNK_MAX_TOKENS = 1000

# Enrichment batch: max tokens per enrichment batch (controls LLM call count)
# On a free model, the binding constraint is NUMBER of requests (rate limits),
# not per-request cost — so larger batches (fewer LLM calls) are better.
ENRICH_MAX_BATCH_TOKENS = 20000

# Enrichment output: max tokens in model response (budget for JSON output)
ENRICH_MAX_OUTPUT_TOKENS = 16_000

# Retrieval context: max tokens in the context window for answer generation
DEFAULT_CONTEXT_MAX_TOKENS = 20_000


# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================

# Enrichment retry budget (kept low to conserve free-tier quota)
# Failed requests still count against per-day limits
ENRICH_MAX_ATTEMPTS = 2

# Max duration for exponential backoff between enrichment retries
ENRICH_BACKOFF_MAX_SECONDS = 30


# ============================================================================
# LLM BEHAVIOR & PARAMETERS
# ============================================================================

# Temperature for LLM calls (0 = deterministic, higher = more creative)
# Enrichment uses 0 for consistency
LLM_TEMPERATURE_DETERMINISTIC = 0

# Reasoning effort for models that support it (e.g., gpt-oss)
LLM_REASONING_EFFORT = "low"  # low | medium | high

# Image summarization max tokens
VLM_MAX_TOKENS = 1000


# ============================================================================
# EVALUATION CONFIDENCE THRESHOLDS
# ============================================================================

# Confidence level thresholds based on average evaluation score
EVALUATION_CONFIDENCE_HIGH_THRESHOLD = 0.75
EVALUATION_CONFIDENCE_MEDIUM_THRESHOLD = 0.45


# ============================================================================
# STRUCTURED OUTPUT SCHEMAS
# ============================================================================

# JSON schema for node enrichment response (summary, keywords, node_id)
# Enforces valid JSON output, eliminating the need for repair
ENRICHMENT_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "node_enrichment",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "seq_id": {"type": "integer"},
                            "summary": {"type": "string"},
                            "keywords": {"type": "array", "items": {"type": "string"}},
                            "node_id": {"type": "string"},
                        },
                        "required": ["seq_id", "summary", "keywords", "node_id"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["sections"],
            "additionalProperties": False,
        },
    },
}
