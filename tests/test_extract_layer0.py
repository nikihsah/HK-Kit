from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.extract_layer0 import build_layer0_document, default_output_path, normalize_text


class TestExtractLayer0(unittest.TestCase):
    def test_known_two_column_page_number_is_tracked(self) -> None:
        from tools.extract_layer0 import TWO_COLUMN_PAGE_NUMBERS

        self.assertIn(65, TWO_COLUMN_PAGE_NUMBERS)

    def test_normalize_text_preserves_content_but_cleans_spacing(self) -> None:
        text = "Line one  \r\n\r\n\r\nLine two\t\n"
        self.assertEqual(normalize_text(text), "Line one\n\nLine two")

    def test_build_layer0_document_marks_mode_create_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "rulebook.pdf"
            pdf.write_bytes(b"fake pdf bytes")

            document = build_layer0_document(
                source_pdf=pdf,
                book="Test Book",
                page_texts=["First page", ""],
                include_source_path=False,
            )

        self.assertEqual(document["artifact"], "HK-RDB Layer 0")
        self.assertFalse(document["mode_create_allowed"])
        self.assertEqual(document["book"], "Test Book")
        self.assertEqual(document["page_count"], 2)
        self.assertEqual(document["pages"][0]["page"], 1)
        self.assertEqual(document["pages"][0]["text"], "First page")
        self.assertEqual(document["pages"][1]["warnings"], ["empty_text"])
        self.assertNotIn("pdf_path", document["source"])
        self.assertIsNotNone(document["source"]["pdf_sha256"])

    def test_default_output_path_is_under_sources_layer0(self) -> None:
        output = default_output_path(Path("The Rulebook v1.8.pdf"), Path("sources/layer0"))
        self.assertEqual(output.as_posix(), "sources/layer0/The-Rulebook-v1.8.layer0.json")


if __name__ == "__main__":
    unittest.main()
