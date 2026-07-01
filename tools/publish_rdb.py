#!/usr/bin/env python3
"""Build a validated release snapshot from a fully promoted HK-RDB snapshot."""

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

from tools.generate_manifest import write_manifest
from tools.validate_rdb import REQUIRED_FILES, RULE_FILES, contains_unparsed_effect, validate_rdb


RULE_DATA_FILES = RULE_FILES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def contains_pending_review(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("needs_manual_review") is True:
            return True
        return any(contains_pending_review(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_pending_review(child) for child in value)
    return False


def build_release_snapshot(
    *, promoted_data_dir: Path, output_root: Path, version: str, source_book: str
) -> dict[str, Any]:
    data_dir = output_root / "HK-RDB" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    item_count = 0

    for file_name in RULE_DATA_FILES:
        source_path = promoted_data_dir / file_name
        if not source_path.exists():
            raise ValueError(f"missing promoted file: {file_name}")
        container = load_json(source_path)
        if contains_pending_review(container):
            raise ValueError(f"pending review flag in {file_name}")
        if not container.get("items"):
            raise ValueError(f"empty rule category: {file_name}")
        container["complete"] = True
        container.pop("draft_metadata", None)
        container.pop("promotion_metadata", None)
        container["release_metadata"] = {
            "rdb_version": version,
            "published_at": generated_at,
        }
        for item in container["items"]:
            item["parsing_status"] = (
                "raw_text_authoritative" if contains_unparsed_effect(item) else "structured"
            )
        item_count += len(container["items"])
        (data_dir / file_name).write_text(
            json.dumps(container, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    index = {
        "name": "HK-RDB",
        "version": version,
        "complete": True,
        "mode_create_ready": True,
        "required_files": REQUIRED_FILES,
        "policy": {
            "operational_rules_source": "HK-RDB only",
            "pdf_during_mode_create": "forbidden",
            "missing_rules_behavior": "fail_loudly",
        },
    }
    version_data = {
        "category": "Version",
        "file": "version.json",
        "complete": True,
        "items": [],
        "rdb_version": version,
        "source_book": source_book,
        "status": "released",
        "released_at": generated_at,
    }
    for file_name, value in (
        ("index.json", index),
        ("version.json", version_data),
    ):
        (data_dir / file_name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    write_manifest(data_dir)
    validate_rdb(output_root, write_report=True)

    result = validate_rdb(output_root)
    if not result.mode_create_ready:
        raise ValueError(f"release validation failed: {result.errors or result.incomplete_files}")
    manifest = {
        "artifact": "HK-RDB Release Snapshot",
        "version": version,
        "mode_create_ready": True,
        "item_count": result.item_count,
        "generated_at": generated_at,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promoted-data", required=True, type=Path)
    parser.add_argument("--out-root", required=True, type=Path)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument(
        "--source-book", default="The Unofficial Hollow Knight RPG - RUS v.1.8"
    )
    args = parser.parse_args()
    try:
        manifest = build_release_snapshot(
            promoted_data_dir=args.promoted_data,
            output_root=args.out_root,
            version=args.version,
            source_book=args.source_book,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Release failed: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
