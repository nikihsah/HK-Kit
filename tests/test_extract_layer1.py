from __future__ import annotations

import unittest
from pathlib import Path

from tools.extract_layer1 import (
    build_candidates,
    default_output_path,
    guess_category,
    split_page_into_blocks,
)


class TestExtractLayer1(unittest.TestCase):
    def test_split_page_into_blocks_prefers_blank_lines(self) -> None:
        text = "First rule block.\n\nSecond rule block."
        self.assertEqual(split_page_into_blocks(text), ["First rule block.", "Second rule block."])

    def test_guess_category_is_conservative(self) -> None:
        self.assertEqual(guess_category("Эта черта дает необычную особенность."), "traits")
        self.assertEqual(guess_category("Completely unrelated text."), "unknown")

    def test_build_candidates_marks_layer1_as_maintainer_only(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {
                "pdf_name": "test.pdf",
                "pdf_sha256": "abc123",
            },
            "page_count": 1,
            "pages": [
                {
                    "page": 1,
                    "text": "Черта панциря.\n\nЭта черта помогает описать защиту персонажа.",
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["artifact"], "HK-RDB Layer 1")
        self.assertFalse(document["mode_create_allowed"])
        self.assertEqual(document["candidate_count"], 2)
        self.assertEqual(document["candidates"][0]["status"], "needs_review")
        self.assertEqual(document["candidates"][0]["source"]["page_start"], 1)
        self.assertEqual(document["candidates"][1]["category_hint"], "traits")

    def test_default_output_path_replaces_layer0_suffix(self) -> None:
        output = default_output_path(Path("book.layer0.json"), Path("sources/layer1"))
        self.assertEqual(output.as_posix(), "sources/layer1/book.layer1.json")


if __name__ == "__main__":
    unittest.main()
