from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.publish_rdb import RULE_DATA_FILES, build_release_snapshot, contains_pending_review
from tools.validate_rdb import validate_rdb


def rule(file_name: str) -> dict:
    return {
        "id": f"{file_name[:-5]}.test",
        "type": "rule",
        "category": file_name[:-5],
        "subcategory": "test",
        "name": "Test",
        "raw_text": "Raw.",
        "summary": "Summary.",
        "costs": {},
        "requirements": [],
        "effects": [],
        "modifiers": {},
        "relationships": [],
        "tags": ["reviewed"],
        "source": {"book": "Book", "page_start": 1, "page_end": 1},
        "needs_manual_review": False,
    }


class TestPublishRdb(unittest.TestCase):
    def test_detects_nested_pending_review(self) -> None:
        self.assertTrue(contains_pending_review({"effects": [{"needs_manual_review": True}]}))

    def test_release_snapshot_is_mode_create_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = root / "promoted"
            promoted.mkdir()
            for file_name in RULE_DATA_FILES:
                (promoted / file_name).write_text(
                    json.dumps(
                        {
                            "category": file_name[:-5],
                            "file": file_name,
                            "complete": False,
                            "items": [rule(file_name)],
                        }
                    ),
                    encoding="utf-8",
                )
            output = root / "release"
            manifest = build_release_snapshot(
                promoted_data_dir=promoted,
                output_root=output,
                version="1.0.0",
                source_book="Book",
            )

            result = validate_rdb(output)

        self.assertTrue(manifest["mode_create_ready"])
        self.assertTrue(result.mode_create_ready)


if __name__ == "__main__":
    unittest.main()
