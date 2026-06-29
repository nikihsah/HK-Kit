#!/usr/bin/env python3
"""Create maintainer review manifests for Layer 2 HK-RDB drafts.

Review manifests are local working artifacts. They help maintainers decide
which draft objects can eventually be promoted into HK-RDB/data.

This tool does not modify HK-RDB/data and does not approve rules automatically.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("sources") / "reviews"
REVIEW_CHECKS = [
    "category_verified",
    "subcategory_verified",
    "name_verified",
    "summary_verified",
    "costs_verified",
    "requirements_verified",
    "effects_verified",
    "modifiers_verified",
    "relationships_verified",
    "source_pages_verified",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_draft_data_dir(draft_root: Path) -> Path:
    if draft_root.name == "data" and draft_root.is_dir():
        return draft_root
    data_dir = draft_root / "data"
    if data_dir.is_dir():
        return data_dir
    raise ValueError(f"Draft data directory not found under {draft_root}")


def iter_draft_files(draft_root: Path) -> list[Path]:
    data_dir = find_draft_data_dir(draft_root)
    return sorted(data_dir.glob("*.json"))


def review_priority(item: dict[str, Any]) -> str:
    raw_len = len(item.get("raw_text", ""))
    if raw_len > 3000:
        return "high"
    if item.get("needs_manual_review") is True:
        return "normal"
    return "low"


def build_review_entry(file_name: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id", ""),
        "file": file_name,
        "decision": "pending",
        "priority": review_priority(item),
        "name": item.get("name", ""),
        "category": item.get("category", ""),
        "subcategory": item.get("subcategory", ""),
        "source": item.get("source", {}),
        "checks": {check: False for check in REVIEW_CHECKS},
        "issues": [],
        "review_notes": [],
        "recommended_next_action": "review_against_source_text",
    }


def build_review_manifest(draft_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    file_counts: dict[str, int] = {}
    source_pages: dict[str, list[int]] = {}

    for path in iter_draft_files(draft_root):
        data = load_json(path)
        items = data.get("items", [])
        file_counts[path.name] = len(items)
        for item in items:
            entry = build_review_entry(path.name, item)
            entries.append(entry)
            page = entry["source"].get("page_start")
            if isinstance(page, int):
                source_pages.setdefault(path.name, []).append(page)

    return {
        "artifact": "HK-RDB Draft Review Manifest",
        "mode_create_allowed": False,
        "draft_root": str(draft_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "review_policy": {
            "final_hk_rdb_write_allowed": False,
            "required_decision_before_promotion": "accepted",
            "required_checks": REVIEW_CHECKS,
        },
        "summary": {
            "entry_count": len(entries),
            "file_counts": file_counts,
            "page_ranges": {
                file_name: {
                    "min": min(pages),
                    "max": max(pages),
                }
                for file_name, pages in sorted(source_pages.items())
                if pages
            },
        },
        "entries": entries,
    }


def default_output_path(draft_root: Path, output_dir: Path) -> Path:
    name = draft_root.name
    if name == "data":
        name = draft_root.parent.name
    if name.endswith(".rdb-draft"):
        name = name[: -len(".rdb-draft")]
    return output_dir / f"{name}.review.json"


def write_review_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a maintainer review manifest for Layer 2 drafts."
    )
    parser.add_argument("--draft-root", required=True, type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        help="Output review JSON. Defaults to sources/reviews/<draft-name>.review.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    draft_root = args.draft_root.resolve()
    if not draft_root.exists():
        print(f"Draft root not found: {draft_root}")
        return 1

    try:
        manifest = build_review_manifest(draft_root)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid draft input: {exc}")
        return 1

    output_path = args.out or default_output_path(draft_root, DEFAULT_OUTPUT_DIR)
    write_review_manifest(manifest, output_path)

    print(
        json.dumps(
            {
                "output": str(output_path),
                "entry_count": manifest["summary"]["entry_count"],
                "mode_create_allowed": manifest["mode_create_allowed"],
                "final_hk_rdb_write_allowed": manifest["review_policy"][
                    "final_hk_rdb_write_allowed"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
