from __future__ import annotations

import unittest

from tools.approve_review import approve_manifest, verification_errors
from tools.review_drafts import REVIEW_CHECKS


def item() -> dict:
    return {
        "id": "core-rules.test",
        "type": "core-rule",
        "category": "Core Rules",
        "subcategory": "test",
        "name": "Test",
        "raw_text": "Raw rule.",
        "summary": "Rule summary.",
        "costs": {},
        "requirements": [],
        "effects": [],
        "modifiers": {},
        "relationships": [],
        "tags": [],
        "source": {"book": "Book", "page_start": 1, "page_end": 1},
        "needs_manual_review": True,
    }


class TestApproveReview(unittest.TestCase):
    def test_clean_item_is_accepted_with_all_checks(self) -> None:
        draft = {("core-rules.json", "core-rules.test"): item()}
        manifest = {"entries": [{"file": "core-rules.json", "id": "core-rules.test", "issues": []}]}

        approved = approve_manifest(manifest, draft)
        entry = approved["entries"][0]

        self.assertEqual(entry["decision"], "accepted")
        self.assertEqual(set(entry["checks"]), set(REVIEW_CHECKS))
        self.assertTrue(all(entry["checks"].values()))
        self.assertEqual(approved["approval"]["rejected_count"], 0)

    def test_fallback_and_dangling_relationship_are_rejected(self) -> None:
        value = item()
        value["id"] = "equipment.rules.p001"
        value["relationships"] = [{"type": "uses", "target": "missing.id"}]

        errors = verification_errors(value, {value["id"]})

        self.assertIn("fallback_id", errors)
        self.assertIn("dangling_relationship:missing.id", errors)


if __name__ == "__main__":
    unittest.main()
