from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_rdb import (
    build_draft_containers,
    candidate_to_rule_object,
    stable_rule_id,
    write_drafts,
)


def sample_candidate(category_hint: str = "traits") -> dict:
    return {
        "id": "l1.p001.b001.traits",
        "status": "needs_review",
        "category_hint": category_hint,
        "title_hint": "Черта панциря",
        "raw_text": "Черта панциря. Текст правила для проверки черновика.",
        "source": {
            "book": "Test Book",
            "pdf_name": "test.pdf",
            "pdf_sha256": "abc123",
            "page_start": 1,
            "page_end": 1,
            "layer0_page": 1,
            "layer0_block": 1,
        },
        "review_notes": [],
    }


class TestBuildRdb(unittest.TestCase):
    def test_candidate_to_rule_object_is_review_draft(self) -> None:
        item = candidate_to_rule_object(sample_candidate())

        self.assertTrue(item["needs_manual_review"])
        self.assertEqual(item["category"], "Traits")
        self.assertEqual(item["type"], "traits")
        self.assertIn("layer2-draft", item["tags"])
        self.assertEqual(item["source"]["page_start"], 1)
        self.assertEqual(item["requirements"], [])
        self.assertEqual(item["effects"], [])

    def test_stable_rule_id_uses_source_position(self) -> None:
        item_id = stable_rule_id("traits", sample_candidate())
        self.assertTrue(item_id.startswith("traits.p001.b001."))

    def test_build_draft_containers_skips_unknown(self) -> None:
        layer1 = {
            "candidates": [
                sample_candidate("traits"),
                sample_candidate("unknown"),
            ]
        }

        containers, skipped = build_draft_containers(layer1)

        self.assertEqual(len(containers["traits.json"]["items"]), 1)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["reason"], "unknown_or_unsupported_category_hint")

    def test_write_drafts_creates_manifest_and_data_files(self) -> None:
        layer1 = {"candidates": [sample_candidate("traits")]}
        containers, skipped = build_draft_containers(layer1)

        with tempfile.TemporaryDirectory() as tmp:
            manifest = write_drafts(
                layer1_path=Path("book.layer1.json"),
                containers=containers,
                skipped=skipped,
                output_dir=Path(tmp),
            )

            self.assertFalse(manifest["mode_create_allowed"])
            self.assertTrue((Path(tmp) / "book.rdb-draft" / "manifest.json").exists())
            self.assertTrue((Path(tmp) / "book.rdb-draft" / "data" / "traits.json").exists())


if __name__ == "__main__":
    unittest.main()
