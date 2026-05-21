from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
JSON_DIR = PROJECT_ROOT / "json_files"

DEFAULT_QUERY_LOG_PATH = JSON_DIR /"json_responses"/"responses_log.json"

DEFAULT_CONTEXT_MAX_TOKENS = 20_000

