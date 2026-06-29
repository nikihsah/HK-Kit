from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.promote_reviewed import (
    build_promoted_snapshot,
    entry_is_promotable,
    promoted_item,
    write_promoted_snapshot,
)
from tools.review_drafts import REVIEW_CHECKS


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


def sample_entry(decision: str = "accepted", checks: bool = True, issues: list | None = None) -> dict:
    return {
        "id": "traits.p001.b001.entry",
        "file": "traits.json",
        "decision": decision,
        "checks": {check: checks for check in REVIEW_CHECKS},
        "issues": issues or [],
    }


def write_draft_root(tmp: str) -> Path:
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
    return draft_root


class TestPromoteReviewed(unittest.TestCase):
    def test_entry_is_promotable_requires_accepted_and_checks(self) -> None:
        self.assertEqual(entry_is_promotable(sample_entry()), (True, "accepted"))
        self.assertEqual(
            entry_is_promotable(sample_entry(decision="pending")),
            (False, "decision_not_accepted"),
        )
        self.assertEqual(
            entry_is_promotable(sample_entry(checks=False)),
            (False, "required_checks_incomplete"),
        )
        self.assertEqual(
            entry_is_promotable(sample_entry(issues=["bad source"])),
            (False, "entry_has_issues"),
        )

    def test_promoted_item_removes_draft_flags(self) -> None:
        item = promoted_item(sample_item())
        self.assertFalse(item["needs_manual_review"])
        self.assertNotIn("layer2-draft", item["tags"])
        self.assertNotIn("needs-review", item["tags"])
        self.assertIn("reviewed", item["tags"])
        self.assertIn("promoted-candidate", item["tags"])

    def test_build_promoted_snapshot_promotes_only_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft_root = write_draft_root(tmp)
            review_manifest = {
                "entries": [
                    sample_entry(),
                    {
                        **sample_entry(decision="pending"),
                        "id": "traits.p999.b999.other",
                    },
                ]
            }
            containers, skipped = build_promoted_snapshot(
                draft_root=draft_root,
                review_manifest=review_manifest,
            )

        self.assertEqual(len(containers["traits.json"]["items"]), 1)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["reason"], "decision_not_accepted")

    def test_write_promoted_snapshot_creates_hk_rdb_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft_root = write_draft_root(tmp)
            containers, skipped = build_promoted_snapshot(
                draft_root=draft_root,
                review_manifest={"entries": [sample_entry()]},
            )
            output_root = Path(tmp) / "promotion"
            manifest = write_promoted_snapshot(
                output_root=output_root,
                containers=containers,
                skipped=skipped,
                draft_root=draft_root,
                review_path=Path("review.json"),
            )

            self.assertEqual(manifest["promoted_count"], 1)
            self.assertFalse(manifest["final_hk_rdb_write_allowed"])
            self.assertTrue((output_root / "HK-RDB" / "data" / "index.json").exists())
            self.assertTrue((output_root / "HK-RDB" / "data" / "traits.json").exists())


if __name__ == "__main__":
    unittest.main()
