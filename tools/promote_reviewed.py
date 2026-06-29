#!/usr/bin/env python3
"""Promote accepted review entries into a local HK-RDB data snapshot.

This tool is intentionally conservative:

- it reads Layer 2 drafts and a review manifest;
- it promotes only entries with decision `accepted`;
- all required review checks must be true;
- entries with issues are skipped;
- output goes to sources/promoted/ by default, not HK-RDB/data.

The generated snapshot is a review artifact until the project owner explicitly
decides to copy or commit final JSON files.
"""

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

from tools.build_rdb import FILE_TO_CATEGORY
from tools.review_drafts import REVIEW_CHECKS, find_draft_data_dir
from tools.validate_rdb import REQUIRED_FILES


DEFAULT_OUTPUT_DIR = Path("sources") / "promoted"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_draft_items(draft_root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    items: dict[tuple[str, str], dict[str, Any]] = {}
    data_dir = find_draft_data_dir(draft_root)
    for path in sorted(data_dir.glob("*.json")):
        data = load_json(path)
        for item in data.get("items", []):
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                items[(path.name, item_id)] = item
    return items


def entry_is_promotable(entry: dict[str, Any]) -> tuple[bool, str]:
    if entry.get("decision") != "accepted":
        return False, "decision_not_accepted"
    checks = entry.get("checks", {})
    missing = [check for check in REVIEW_CHECKS if checks.get(check) is not True]
    if missing:
        return False, "required_checks_incomplete"
    if entry.get("issues"):
        return False, "entry_has_issues"
    return True, "accepted"


def promoted_item(item: dict[str, Any]) -> dict[str, Any]:
    promoted = json.loads(json.dumps(item, ensure_ascii=False))
    tags = [
        tag
        for tag in promoted.get("tags", [])
        if tag not in {"layer2-draft", "needs-review"}
    ]
    for tag in ["reviewed", "promoted-candidate"]:
        if tag not in tags:
            tags.append(tag)
    promoted["tags"] = tags
    promoted["needs_manual_review"] = False
    return promoted


def empty_container(file_name: str) -> dict[str, Any]:
    return {
        "category": FILE_TO_CATEGORY.get(file_name, file_name.replace(".json", "")),
        "file": file_name,
        "complete": False,
        "items": [],
        "promotion_metadata": {
            "artifact": "HK-RDB Promoted Snapshot",
            "mode_create_allowed": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def index_file() -> dict[str, Any]:
    return {
        "name": "HK-RDB promoted snapshot",
        "version": "0.1.0-promoted",
        "complete": False,
        "mode_create_ready": False,
        "required_files": REQUIRED_FILES,
        "policy": {
            "operational_rules_source": "HK-RDB only",
            "pdf_during_mode_create": "forbidden",
            "promotion_status": "local_review_snapshot",
        },
    }


def build_promoted_snapshot(
    *,
    draft_root: Path,
    review_manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    draft_items = load_draft_items(draft_root)
    containers = {file_name: empty_container(file_name) for file_name in REQUIRED_FILES}
    skipped: list[dict[str, Any]] = []

    for entry in review_manifest.get("entries", []):
        entry_id = entry.get("id")
        file_name = entry.get("file")
        ok, reason = entry_is_promotable(entry)
        if not ok:
            skipped.append({"id": entry_id, "file": file_name, "reason": reason})
            continue
        item = draft_items.get((file_name, entry_id))
        if item is None:
            skipped.append({"id": entry_id, "file": file_name, "reason": "draft_item_not_found"})
            continue
        if file_name not in containers:
            skipped.append({"id": entry_id, "file": file_name, "reason": "unsupported_file"})
            continue
        containers[file_name]["items"].append(promoted_item(item))

    return containers, skipped


def default_output_root(review_path: Path, output_dir: Path) -> Path:
    name = review_path.name
    if name.endswith(".review.json"):
        name = name[: -len(".review.json")]
    else:
        name = review_path.stem
    return output_dir / f"{name}.promotion"


def write_promoted_snapshot(
    *,
    output_root: Path,
    containers: dict[str, dict[str, Any]],
    skipped: list[dict[str, Any]],
    draft_root: Path,
    review_path: Path,
) -> dict[str, Any]:
    data_dir = output_root / "HK-RDB" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "index.json").write_text(
        json.dumps(index_file(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written_files = [str(data_dir / "index.json")]

    for file_name, container in sorted(containers.items()):
        path = data_dir / file_name
        path.write_text(
            json.dumps(container, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written_files.append(str(path))

    promoted_count = sum(len(container["items"]) for container in containers.values())
    manifest = {
        "artifact": "HK-RDB Promotion Manifest",
        "mode_create_allowed": False,
        "final_hk_rdb_write_allowed": False,
        "draft_root": str(draft_root),
        "review_manifest": str(review_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "promoted_count": promoted_count,
        "skipped_count": len(skipped),
        "skipped_entries": skipped,
        "written_files": written_files,
        "policy": "Local promoted snapshot only. Do not commit as final HK-RDB without owner approval.",
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote accepted review entries into a local HK-RDB snapshot."
    )
    parser.add_argument("--draft-root", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory. Defaults to sources/promoted/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    draft_root = args.draft_root.resolve()
    review_path = args.review.resolve()
    if not draft_root.exists():
        print(f"Draft root not found: {draft_root}")
        return 1
    if not review_path.exists():
        print(f"Review manifest not found: {review_path}")
        return 1

    try:
        review_manifest = load_json(review_path)
        if review_manifest.get("artifact") != "HK-RDB Draft Review Manifest":
            raise ValueError("input is not an HK-RDB Draft Review Manifest")
        containers, skipped = build_promoted_snapshot(
            draft_root=draft_root,
            review_manifest=review_manifest,
        )
        output_root = default_output_root(review_path, args.out_dir)
        manifest = write_promoted_snapshot(
            output_root=output_root,
            containers=containers,
            skipped=skipped,
            draft_root=draft_root,
            review_path=review_path,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid promotion input: {exc}")
        return 1

    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "promoted_count": manifest["promoted_count"],
                "skipped_count": manifest["skipped_count"],
                "mode_create_allowed": manifest["mode_create_allowed"],
                "final_hk_rdb_write_allowed": manifest["final_hk_rdb_write_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
