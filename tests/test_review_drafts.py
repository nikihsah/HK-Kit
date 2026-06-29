from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.review_drafts import (
    REVIEW_CHECKS,
    build_review_entry,
    build_review_manifest,
    default_output_path,
    write_review_manifest,
)


def sample_item() -> dict:
    return {
        "id": "traits.p001.b001.entry",
        "type": "traits",
        "category": "Traits",
        "subcategory": "",
        "name": "Draft trait",
        "raw_text": "Draft raw text",
        "summary": "Draft summary",
        "costs": {},
        "requirements": [],
        "effects": [],
        "modifiers": {},
        "relationships": [],
        "tags": ["layer2-draft", "needs-review"],
        "source": {
            "book": "Test Book",
            "page_start": 1,
            "page_end": 1,
        },
        "needs_manual_review": True,
    }


class TestReviewDrafts(unittest.TestCase):
    def test_build_review_entry_starts_pending(self) -> None:
        entry = build_review_entry("traits.json", sample_item())

        self.assertEqual(entry["decision"], "pending")
        self.assertEqual(entry["recommended_next_action"], "review_against_source_text")
        self.assertEqual(entry["file"], "traits.json")
        self.assertEqual(set(entry["checks"]), set(REVIEW_CHECKS))
        self.assertTrue(all(value is False for value in entry["checks"].values()))

    def test_build_review_manifest_counts_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft_root = Path(tmp) / "book.rdb-draft"
            data_dir = draft_root / "data"
            data_dir.mkdir(parents=True)
            (data_dir / "traits.json").write_text(
                json.dumps(
                    {
                        "category": "Traits",
                        "file": "traits.json",
                        "complete": False,
                        "items": [sample_item()],
                    }
                ),
                encoding="utf-8",
            )

            manifest = build_review_manifest(draft_root)

        self.assertFalse(manifest["mode_create_allowed"])
        self.assertFalse(manifest["review_policy"]["final_hk_rdb_write_allowed"])
        self.assertEqual(manifest["summary"]["entry_count"], 1)
        self.assertEqual(manifest["summary"]["file_counts"]["traits.json"], 1)
        self.assertEqual(manifest["entries"][0]["decision"], "pending")

    def test_default_output_path_uses_review_suffix(self) -> None:
        output = default_output_path(Path("book.rdb-draft"), Path("sources/reviews"))
        self.assertEqual(output.as_posix(), "sources/reviews/book.review.json")

    def test_write_review_manifest_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested" / "review.json"
            write_review_manifest({"artifact": "test"}, output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
