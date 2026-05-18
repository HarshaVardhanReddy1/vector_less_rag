from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
JSON_DIR = PROJECT_ROOT / "json_files"

DEFAULT_PAGES_PATH = JSON_DIR / "pdf_pages1.json"
DEFAULT_TOC_PATH = JSON_DIR / "toc_titles.json"
DEFAULT_TREE_PATH = JSON_DIR / "tree_titles.json"
DEFAULT_QUERY_LOG_PATH = JSON_DIR / "query_response_log_titles.json"

DEFAULT_CONTEXT_MAX_TOKENS = 30_000

