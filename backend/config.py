from pathlib import Path


# backend/ -> project_1/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"

DEFAULT_QUERY_LOG_PATH     = DATA_DIR / "responses" / "responses_log.json"
DEFAULT_CONTEXT_MAX_TOKENS = 20_000

# ---------------------------------------------------------------------------
# PDF enrichment settings
# ---------------------------------------------------------------------------

ENRICH_MAX_BATCH_TOKENS  = 20_000
ENRICH_CONTENT_MAX_CHARS = 1_500
ENRICH_MODEL             = "gpt-oss-120b:free"
