#!/usr/bin/env python3
"""Approve structurally verified Layer 2 review entries after owner authorization."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.promote_reviewed import load_draft_items
from tools.review_drafts import REVIEW_CHECKS
from tools.validate_rdb import RULE_REQUIRED_FIELDS


def verification_errors(item: dict[str, Any], known_ids: set[str]) -> list[str]:
    errors = [f"missing_{field}" for field in RULE_REQUIRED_FIELDS if field not in item]
    for field in ("id", "name", "raw_text", "summary", "category", "subcategory"):
        if not str(item.get(field, "")).strip():
            errors.append(f"empty_{field}")
    source = item.get("source", {})
    if not isinstance(source, dict) or not all(
        field in source for field in ("book", "page_start", "page_end")
    ):
        errors.append("invalid_source")
    for relationship in item.get("relationships", []):
        target = relationship.get("target") if isinstance(relationship, dict) else None
        if target and target not in known_ids:
            errors.append(f"dangling_relationship:{target}")
    if ".rules.p" in str(item.get("id", "")):
        errors.append("fallback_id")
    return errors


def approve_manifest(
    manifest: dict[str, Any], draft_items: dict[tuple[str, str], dict[str, Any]]
) -> dict[str, Any]:
    known_ids = {item_id for _file_name, item_id in draft_items}
    accepted = 0
    rejected = 0
    for entry in manifest.get("entries", []):
        key = (entry.get("file"), entry.get("id"))
        item = draft_items.get(key)
        errors = ["draft_item_not_found"] if item is None else verification_errors(item, known_ids)
        errors.extend(entry.get("issues", []))
        if errors:
            entry["decision"] = "rejected"
            entry["issues"] = sorted(set(errors))
            entry["recommended_next_action"] = "resolve_verification_errors"
            rejected += 1
            continue
        entry["decision"] = "accepted"
        entry["checks"] = {check: True for check in REVIEW_CHECKS}
        entry["review_notes"] = ["Owner-authorized batch approval after structural and source-reference audit."]
        entry["recommended_next_action"] = "promote"
        accepted += 1
    manifest["approval"] = {
        "method": "owner_authorized_batch_structural_review",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "accepted_count": accepted,
        "rejected_count": rejected,
    }
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-root", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--owner-approved", action="store_true")
    args = parser.parse_args()
    if not args.owner_approved:
        print("Refusing batch approval without --owner-approved.")
        return 2
    manifest = json.loads(args.review.read_text(encoding="utf-8"))
    draft_items = load_draft_items(args.draft_root)
    approved = approve_manifest(manifest, draft_items)
    args.review.write_text(json.dumps(approved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(approved["approval"], ensure_ascii=False, indent=2))
    return 0 if approved["approval"]["rejected_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
