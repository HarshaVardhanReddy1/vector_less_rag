from pathlib import Path


# backend/ -> project_1/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"

DEFAULT_QUERY_LOG_PATH     = DATA_DIR / "responses" / "responses_log.json"
DEFAULT_CONTEXT_MAX_TOKENS = 20_000

# ---------------------------------------------------------------------------
# PDF enrichment settings
# ---------------------------------------------------------------------------

# On a free model the binding constraint is the NUMBER of requests (per-minute
# and per-day rate limits), not per-request cost — so larger batches (fewer
# LLM calls) are better. ENRICH_MAX_OUTPUT_TOKENS stays high enough that the
# bigger per-batch JSON output still fits without truncating.
ENRICH_MAX_BATCH_TOKENS  = 20000
ENRICH_CONTENT_MAX_CHARS = 1_500
ENRICH_MAX_OUTPUT_TOKENS = 16_000
ENRICH_MODEL             = "openai/gpt-oss-120b:free"

# ---------------------------------------------------------------------------
# Retrieval / answer-generation model (node selection + grounded answers)
# ---------------------------------------------------------------------------

RESPONSE_MODEL = "openai/gpt-oss-120b:free"
