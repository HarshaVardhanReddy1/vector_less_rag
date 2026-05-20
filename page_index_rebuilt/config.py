from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
JSON_DIR = PROJECT_ROOT / "json_files"

DEFAULT_PAGES_PATH = JSON_DIR / "json_pages" / "earthmover.json"
DEFAULT_TOC_PATH = JSON_DIR / "json_tocs" / "earthmover.json"
DEFAULT_TREE_PATH = JSON_DIR /"json_trees" /"earthmover.json"
DEFAULT_QUERY_LOG_PATH = JSON_DIR /"json_responses"/"earthmover.json"

DEFAULT_CONTEXT_MAX_TOKENS = 20_000

