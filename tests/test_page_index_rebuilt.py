import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.engine import retriever, toc_generator
from backend.engine import tree_builder


class ChunkingTests(unittest.TestCase):
    def test_build_context_chunks_splits_when_token_budget_is_exceeded(self) -> None:
        pages = [
            {"page": 1, "page_text": "alpha", "token_count": 4},
            {"page": 2, "page_text": "beta", "token_count": 5},
            {"page": 3, "page_text": "gamma", "token_count": 3},
        ]

        contexts = toc_generator.build_context_chunks(pages, max_tokens=8)

        self.assertEqual(len(contexts), 2)
        self.assertIn("PAGE 1 START", contexts[0])
        self.assertIn("PAGE 2 START", contexts[1])
        self.assertIn("PAGE 3 START", contexts[1])
        self.assertNotIn("PAGE 2 START", contexts[0])

    def test_build_context_chunks_rejects_invalid_page_payload(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate page number 1"):
            toc_generator.build_context_chunks(
                [
                    {"page": 1, "page_text": "a", "token_count": 1},
                    {"page": 1, "page_text": "b", "token_count": 1},
                ],
                max_tokens=10,
            )


class TocGenerationTests(unittest.TestCase):
    # validation llm output
    @patch("backend.engine.toc_generator.generate_response")
    def test_generate_toc_from_context_validates_llm_output(self, mock_generate_response) -> None:
        mock_generate_response.return_value = json.dumps(
            [
                {
                    "title": "Overview",
                    "node_id": "1",
                    "page_number": 1,
                    "summary": "Document overview",
                }
            ]
        )

        toc = toc_generator.generate_toc_from_context("sample context")

        self.assertEqual(
            toc,
            [
                {
                    "title": "Overview",
                    "node_id": "1",
                    "page_number": 1,
                    "summary": "Document overview",
                }
            ],
        )
        mock_generate_response.assert_called_once()

    @patch("backend.engine.toc_generator.merge_tocs")
    @patch("backend.engine.toc_generator.generate_toc_from_context")
    def test_build_toc_merges_all_chunks_and_deduplicates(
        self,
        mock_generate_toc_from_context,
        mock_merge_tocs,
    ) -> None:
        chunk_one_toc = [
            {"title": "Overview", "node_id": "1", "page_number": 1, "summary": "Overview"}
        ]
        chunk_two_toc = [
            {"title": "Section A", "node_id": "2", "page_number": 2, "summary": "Section A"},
            {"title": "Overview", "node_id": "99", "page_number": 1, "summary": "Duplicate"},
        ]
        merged_toc = chunk_one_toc + chunk_two_toc

        mock_generate_toc_from_context.side_effect = [chunk_one_toc, chunk_two_toc]
        mock_merge_tocs.return_value = merged_toc

        toc = toc_generator.build_toc(["chunk one", "chunk two"])

        self.assertEqual(
            toc,
            [
                {"title": "Overview", "node_id": "1", "page_number": 1, "summary": "Overview"},
                {"title": "Section A", "node_id": "2", "page_number": 2, "summary": "Section A"},
            ],
        )
        mock_merge_tocs.assert_called_once_with(chunk_one_toc, chunk_two_toc)

    @patch("backend.engine.toc_generator.generate_response")
    def test_merge_tocs_returns_validated_merged_toc(self, mock_generate_response) -> None:
        mock_generate_response.return_value = json.dumps(
            [
                {
                    "title": "Overview",
                    "node_id": "1",
                    "page_number": 1,
                    "summary": "Merged overview",
                },
                {
                    "title": "Details",
                    "node_id": "1.1",
                    "page_number": 2,
                    "summary": "Merged details",
                },
            ]
        )

        merged = toc_generator.merge_tocs(
            [{"title": "Overview", "node_id": "1", "page_number": 1, "summary": "Old"}],
            [{"title": "Details", "node_id": "2", "page_number": 2, "summary": "New"}],
        )

        self.assertEqual([node["node_id"] for node in merged], ["1", "1.1"])


class TreeConstructionTests(unittest.TestCase):
    def test_build_tree_from_toc_constructs_hierarchy_and_ranges(self) -> None:
        toc = [
            {"title": "Overview", "node_id": "1", "page_number": 1, "summary": "Overview"},
            {"title": "Section A", "node_id": "1.1", "page_number": 2, "summary": "Section A"},
            {"title": "Section B", "node_id": "1.2", "page_number": 4, "summary": "Section B"},
            {"title": "Appendix", "node_id": "2", "page_number": 6, "summary": "Appendix"},
        ]

        tree = tree_builder.build_tree_from_toc(toc, document_end_index=8)

        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]["node_id"], "0001")
        self.assertEqual(tree[0]["start_index"], 1)
        self.assertEqual(tree[0]["end_index"], 6)
        self.assertEqual([child["node_id"] for child in tree[0]["sub_nodes"]], ["0001.1", "0001.2"])
        self.assertEqual(tree[0]["sub_nodes"][0]["end_index"], 4)
        self.assertEqual(tree[0]["sub_nodes"][1]["end_index"], 6)
        self.assertEqual(tree[1]["node_id"], "0002")
        self.assertEqual(tree[1]["start_index"], 6)
        self.assertEqual(tree[1]["end_index"], 8)

    def test_get_document_end_index_falls_back_to_toc_when_pages_file_is_missing(self) -> None:
        toc = [
            {"title": "Overview", "node_id": "1", "page_number": 3, "summary": "Overview"},
            {"title": "Appendix", "node_id": "2", "page_number": 9, "summary": "Appendix"},
        ]

        end_index = tree_builder.get_document_end_index(
            toc,
            pages_path=Path("nonexistent-pages.json"),
        )

        self.assertEqual(end_index, 9)


class RetrievalTests(unittest.TestCase):
    def test_get_context_from_node_id_uses_explicit_page_numbers(self) -> None:
        tree = [
            {
                "node_id": "0001",
                "title": "Overview",
                "summary": "Overview summary",
                "start_index": 2,
                "end_index": 3,
                "sub_nodes": [],
            }
        ]
        pages = [
            {"page": 3, "page_text": "third page", "token_count": 1},
            {"page": 1, "page_text": "first page", "token_count": 1},
            {"page": 2, "page_text": "second page", "token_count": 1},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tree_path = temp_path / "tree.json"
            pages_path = temp_path / "pages.json"
            tree_path.write_text(json.dumps(tree), encoding="utf-8")
            pages_path.write_text(json.dumps(pages), encoding="utf-8")

            context = retriever.get_context_from_node_id(
                "0001",
                tree_path=tree_path,
                pages_path=pages_path,
            )

        self.assertEqual(context["start_index"], 2)
        self.assertIn("PAGE 2 START", context["context"])
        self.assertIn("second page", context["context"])
        self.assertIn("PAGE 3 START", context["context"])
        self.assertLess(
            context["context"].index("PAGE 2 START"),
            context["context"].index("PAGE 3 START"),
        )

    @patch("backend.engine.retriever.append_query_response")
    @patch("backend.engine.retriever.generate_response")
    @patch("backend.engine.retriever.retrieve_context_for_query")
    def test_answer_query_returns_grounded_answer(
        self,
        mock_retrieve_context_for_query,
        mock_generate_response,
        mock_append_query_response,
    ) -> None:
        mock_retrieve_context_for_query.return_value = {
            "node_id": "0001",
            "title": "Overview",
            "summary": "Overview summary",
            "start_index": 2,
            "end_index": 3,
            "context": "retrieved context",
        }
        mock_generate_response.return_value = "Grounded answer"

        result = retriever.answer_query(
            "What is covered?",
            tree_path="dummy_tree.json",
            pages_path="dummy_pages.json",
        )

        self.assertEqual(result["selected_node"]["node_id"], "0001")
        self.assertEqual(result["answer"], "Grounded answer")
        mock_append_query_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
