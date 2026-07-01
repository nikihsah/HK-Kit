#!/usr/bin/env python3
"""Generate the runtime HK-RDB manifest from canonical data files."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GENERATOR_VERSION = "1.0.0"
NON_RULE_FILES = {"index.json", "manifest.json", "validation.json", "version.json"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_files(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.glob("*.json") if path.name not in NON_RULE_FILES)


def infer_dependencies(items: list[dict[str, Any]], id_to_file: dict[str, str]) -> list[str]:
    dependencies: set[str] = set()
    for item in items:
        for relationship in item.get("relationships", []):
            if isinstance(relationship, dict):
                target_file = id_to_file.get(relationship.get("target"))
                if target_file:
                    dependencies.add(target_file)
    return sorted(dependencies)


def build_manifest(data_dir: Path, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    files = rule_files(data_dir)
    containers = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in files}
    id_to_file = {
        item["id"]: name
        for name, container in containers.items()
        for item in container.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    entries = []
    for path in files:
        container = containers[path.name]
        items = container.get("items", [])
        ids = [item["id"] for item in items if isinstance(item, dict) and "id" in item]
        subcategory_counts: dict[str, int] = {}
        types: set[str] = set()
        for item in items:
            subcategory = str(item.get("subcategory", ""))
            subcategory_counts[subcategory] = subcategory_counts.get(subcategory, 0) + 1
            if item.get("type"):
                types.add(str(item["type"]))
        entries.append(
            {
                "category": container.get("category", path.stem),
                "file": path.name,
                "object_count": len(items),
                "ids": ids,
                "subcategories": sorted(subcategory_counts),
                "counts_by_subcategory": dict(sorted(subcategory_counts.items())),
                "required_for_mode_create": True,
                "dependencies": infer_dependencies(items, id_to_file),
                "schema": "../schema/schema.json",
                "data_types": sorted(types),
                "sha256": sha256_file(path),
            }
        )
    return {
        "manifest_version": "1.0.0",
        "generated_at": generated_at,
        "generator_version": GENERATOR_VERSION,
        "files": entries,
        "total_object_count": sum(entry["object_count"] for entry in entries),
    }


def write_manifest(data_dir: Path) -> dict[str, Any]:
    manifest = build_manifest(data_dir)
    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    manifest = write_manifest(args.root / "HK-RDB" / "data")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
