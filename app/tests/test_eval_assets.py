import json
import unittest
from pathlib import Path

from app.page_index_rebuilt.utils import find_node_by_id, load_json_data


EVALS_DIR = Path(__file__).resolve().parent.parent / "evals"
DOCUMENTS_DIR = EVALS_DIR / "sample_documents"
QUERY_SET_PATH = EVALS_DIR / "sample_queries.json"


class EvalAssetTests(unittest.TestCase):
    def test_query_set_references_existing_documents_and_nodes(self) -> None:
        with open(QUERY_SET_PATH, "r", encoding="utf-8") as file:
            query_set = json.load(file)

        self.assertGreater(len(query_set), 0)

        cached_trees: dict[str, list[dict]] = {}
        for case in query_set:
            doc_id = case["doc_id"]
            tree_path = DOCUMENTS_DIR / f"{doc_id}_tree.json"
            pages_path = DOCUMENTS_DIR / f"{doc_id}_pages.json"
            toc_path = DOCUMENTS_DIR / f"{doc_id}_toc.json"

            self.assertTrue(tree_path.exists(), f"Missing tree for {doc_id}")
            self.assertTrue(pages_path.exists(), f"Missing pages for {doc_id}")
            self.assertTrue(toc_path.exists(), f"Missing toc for {doc_id}")

            tree = cached_trees.setdefault(doc_id, load_json_data(tree_path))
            matched_node = find_node_by_id(tree, case["expected_node_id"])
            self.assertIsNotNone(matched_node, f"Missing node {case['expected_node_id']} for {doc_id}")
            self.assertIn("expected_title_contains", case)
            self.assertIn("expected_context_keywords", case)

    def test_sample_documents_have_matching_page_ranges(self) -> None:
        for pages_path in DOCUMENTS_DIR.glob("*_pages.json"):
            doc_id = pages_path.name.removesuffix("_pages.json")
            pages = load_json_data(pages_path)
            tree = load_json_data(DOCUMENTS_DIR / f"{doc_id}_tree.json")

            page_numbers = {item["page"] for item in pages}
            for node in tree:
                expected_range = set(range(node["start_index"], node["end_index"] + 1))
                self.assertTrue(
                    expected_range.issubset(page_numbers),
                    f"Node {node['node_id']} in {doc_id} points outside available pages.",
                )


if __name__ == "__main__":
    unittest.main()
