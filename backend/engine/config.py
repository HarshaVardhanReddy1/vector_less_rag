from pathlib import Path


# backend/engine/ -> backend/ -> project_1/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_QUERY_LOG_PATH = DATA_DIR / "responses" / "responses_log.json"
DEFAULT_CONTEXT_MAX_TOKENS = 20_000
