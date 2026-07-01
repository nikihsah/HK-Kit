#!/usr/bin/env python3
"""Generate the machine-readable report for incomplete effect structures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generate_manifest import rule_files


def build_findings(data_dir: Path) -> dict:
    findings = []
    for path in rule_files(data_dir):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            if item.get("parsing_status") != "raw_text_authoritative":
                continue
            findings.append({
                "file": f"HK-RDB/data/{path.name}",
                "id": item["id"],
                "current_state": "raw_text_authoritative; machine effect structure incomplete",
                "why_problematic": "Runtime must consult raw_text and cannot treat effects as fully structured.",
                "evidence_needed_for_change": "Maintainer verification against the source text and an approved structured representation.",
            })
    return {
        "report": "P0 unparsed/raw-only HK-RDB findings",
        "finding_count": len(findings),
        "rules_changed": False,
        "findings": findings,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    report = build_findings(root / "HK-RDB" / "data")
    target = root / "docs" / "P0_UNPARSED_FINDINGS.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"file": str(target), "finding_count": report["finding_count"]}, ensure_ascii=False))
