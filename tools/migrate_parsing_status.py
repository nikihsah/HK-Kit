#!/usr/bin/env python3
"""One-time, mechanical parsing-status migration for released HK-RDB objects."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generate_manifest import rule_files


def has_unparsed_effect(item: dict) -> bool:
    return any(
        isinstance(effect, dict)
        and ("unparsed" in str(effect.get("type", "")).lower() or "raw-only" in str(effect.get("type", "")).lower())
        for effect in item.get("effects", [])
    )


def migrate(data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in rule_files(data_dir):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            if item.get("needs_manual_review") is True:
                status = "manual_review_required"
            elif has_unparsed_effect(item):
                status = "raw_text_authoritative"
            else:
                status = "structured"
            item["parsing_status"] = status
            counts[status] = counts.get(status, 0) + 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return counts


if __name__ == "__main__":
    print(json.dumps(migrate(Path("HK-RDB/data")), indent=2))
