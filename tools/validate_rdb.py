#!/usr/bin/env python3
"""Validate HK-RDB and generate an evidence-bearing validation report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generate_manifest import build_manifest, sha256_file

VALIDATOR_VERSION = "2.0.0"
RULE_FILES = [
    "core-rules.json", "templates.json", "traits.json", "paths.json", "skills.json",
    "advancement.json", "combat-arts.json", "magic.json", "charms.json", "equipment.json",
    "combat-rules.json", "travel-rest-rules.json", "social-rules.json", "glossary.json",
]
REQUIRED_FILES = RULE_FILES + ["manifest.json", "validation.json", "version.json"]
RULE_REQUIRED_FIELDS = [
    "id", "type", "category", "subcategory", "name", "raw_text", "summary", "costs",
    "requirements", "effects", "modifiers", "relationships", "tags", "source",
    "needs_manual_review", "parsing_status",
]
CONTAINER_REQUIRED_FIELDS = ["category", "file", "complete", "items"]
PARSING_STATUSES = {"structured", "raw_text_authoritative", "manual_review_required", "blocked"}
MODE_CREATE_INCOMPLETE_MESSAGE = (
    "The HK-RDB is incomplete for this operation. Update the database before continuing."
)


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    incomplete_files: list[str]
    item_count: int
    report: dict[str, Any] = field(default_factory=dict)

    @property
    def has_critical_errors(self) -> bool:
        return bool(self.errors)

    @property
    def mode_create_ready(self) -> bool:
        return self.report.get("status") in {"pass", "pass_with_warnings"} and not self.incomplete_files


def load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"missing file: {path.as_posix()}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path.as_posix()}: {exc}"


def contains_unparsed_effect(item: dict[str, Any]) -> bool:
    return any(
        isinstance(effect, dict)
        and ("unparsed" in str(effect.get("type", "")).lower() or "raw-only" in str(effect.get("type", "")).lower())
        for effect in item.get("effects", [])
    )


def validate_rdb(root: Path, *, write_report: bool = False) -> ValidationResult:
    data_dir = root / "HK-RDB" / "data"
    errors: list[str] = []
    warnings: list[str] = []
    incomplete: list[str] = []
    missing_fields: list[dict[str, str]] = []
    duplicates: list[str] = []
    broken: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    path_affinity_errors: list[dict[str, str]] = []
    blocked: list[str] = []
    manual: list[str] = []
    parsing_counts: Counter[str] = Counter()
    counts_file: dict[str, int] = {}
    counts_category: Counter[str] = Counter()
    counts_type: Counter[str] = Counter()
    hashes: dict[str, str] = {}
    seen: dict[str, str] = {}
    containers: dict[str, dict[str, Any]] = {}

    for file_name in RULE_FILES:
        data, error = load_json(data_dir / file_name)
        if error:
            errors.append(error); continue
        if not isinstance(data, dict):
            errors.append(f"{file_name}: top-level value must be an object"); continue
        containers[file_name] = data
        hashes[file_name] = sha256_file(data_dir / file_name)
        for name in CONTAINER_REQUIRED_FIELDS:
            if name not in data: missing_fields.append({"file": file_name, "field": name})
        if data.get("file") != file_name: errors.append(f"{file_name}: incorrect file field")
        if data.get("complete") is not True: incomplete.append(file_name)
        items = data.get("items", [])
        if not isinstance(items, list): errors.append(f"{file_name}: items must be an array"); continue
        counts_file[file_name] = len(items)
        for index, item in enumerate(items):
            if not isinstance(item, dict): errors.append(f"{file_name}[{index}]: item must be an object"); continue
            for name in RULE_REQUIRED_FIELDS:
                if name not in item: missing_fields.append({"file": file_name, "id": str(item.get("id", index)), "field": name})
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                if item_id in seen: duplicates.append(item_id)
                else: seen[item_id] = file_name
            status = item.get("parsing_status")
            if status not in PARSING_STATUSES: errors.append(f"{file_name}[{index}]: invalid parsing_status '{status}'")
            else: parsing_counts[status] += 1
            if contains_unparsed_effect(item) and status != "raw_text_authoritative":
                errors.append(f"{item_id}: unparsed effect must be raw_text_authoritative")
            if item.get("needs_manual_review") is True and status != "manual_review_required":
                errors.append(f"{item_id}: review flag contradicts parsing_status")
            if status == "manual_review_required": manual.append(str(item_id))
            if status == "blocked": blocked.append(str(item_id))
            counts_category[str(item.get("category", ""))] += 1
            counts_type[str(item.get("type", ""))] += 1

    known = set(seen)
    for file_name, data in containers.items():
        for item in data.get("items", []):
            for relationship in item.get("relationships", []):
                if not isinstance(relationship, dict): continue
                target = relationship.get("target")
                if target and target not in known:
                    finding = {"source_id": item.get("id", ""), "target": target, "file": file_name}
                    if relationship.get("required") is False: unresolved.append(finding)
                    else: broken.append(finding)

    path_families = {
        item.get("id"): item.get("modifiers", {}).get("family")
        for item in containers.get("paths.json", {}).get("items", [])
        if item.get("type") == "path"
    }
    for item in containers.get("magic.json", {}).get("items", []):
        if item.get("type") != "secret":
            continue
        requirements = [r for r in item.get("requirements", []) if r.get("type") == "mystic_path"]
        path_id = requirements[0].get("path_id") if len(requirements) == 1 else None
        id_path = ".".join(str(item.get("id", "")).split(".")[:2]).replace("magic.", "paths.")
        relationship_targets = {
            r.get("target") for r in item.get("relationships", []) if r.get("type") == "requires_path"
        }
        if (
            len(requirements) != 1
            or path_families.get(path_id) != "Mystic Path"
            or path_id != id_path
            or relationship_targets != {path_id}
        ):
            path_affinity_errors.append({
                "id": str(item.get("id")),
                "expected_family": "Mystic Path",
                "path_id": str(path_id),
                "reason": "Secret ID, requirement, relationship, and Mystic Path must agree",
            })
    for item in containers.get("combat-arts.json", {}).get("items", []):
        if item.get("type") != "combat-art":
            continue
        family_requirements = [
            r for r in item.get("requirements", [])
            if r.get("type") == "path_family" and r.get("value") == "Martial Path"
        ]
        if len(family_requirements) != 1:
            path_affinity_errors.append({
                "id": str(item.get("id")),
                "expected_family": "Martial Path",
                "path_id": "selected_at_runtime",
                "reason": "Combat Art must require the Martial Path family",
            })

    if duplicates: errors.append("duplicate stable IDs found")
    if broken: errors.append("broken relationship targets found")
    if missing_fields: errors.append("missing required fields found")
    if path_affinity_errors: errors.append("path affinity errors found")
    manifest, manifest_error = load_json(data_dir / "manifest.json")
    expected_manifest = build_manifest(data_dir, generated_at=(manifest or {}).get("generated_at") if isinstance(manifest, dict) else None)
    manifest_stale = bool(manifest_error or not isinstance(manifest, dict) or manifest != expected_manifest)
    if manifest_stale: errors.append("manifest is missing or stale")
    if blocked: errors.append("blocked items found")
    if manual: warnings.append("manual review remains")
    if parsing_counts.get("raw_text_authoritative", 0):
        warnings.append("machine structure is incomplete for raw-text-authoritative items")

    version, _ = load_json(data_dir / "version.json")
    critical_errors = sorted(set(errors))
    status = "fail" if critical_errors else "pass_with_warnings" if warnings else "pass"
    report = {
        "category": "Validation", "file": "validation.json", "complete": status != "fail", "items": [],
        "status": status, "schema_version": "1.1.0", "data_version": (version or {}).get("rdb_version", "unknown"),
        "generated_at": datetime.now(timezone.utc).isoformat(), "validator_version": VALIDATOR_VERSION,
        "critical_errors": critical_errors, "warnings": sorted(set(warnings)),
        "counts_by_file": dict(sorted(counts_file.items())), "counts_by_category": dict(sorted(counts_category.items())),
        "counts_by_type": dict(sorted(counts_type.items())), "total_item_count": sum(counts_file.values()),
        "duplicate_ids": sorted(set(duplicates)), "missing_required_fields": missing_fields,
        "broken_relationship_targets": broken, "unresolved_relationships": unresolved,
        "path_affinity_errors": path_affinity_errors,
        "parsing_status_counts": dict(sorted(parsing_counts.items())), "manual_review_remaining": manual,
        "blocked_items": blocked, "manifest_hash": sha256_file(data_dir / "manifest.json") if not manifest_error else None,
        "hashes_by_file": dict(sorted(hashes.items())), "manifest_stale": manifest_stale,
        "checks_performed": ["required_files", "required_fields", "unique_ids", "relationship_targets", "path_affinity", "parsing_status", "manifest_freshness", "counts"],
    }
    if write_report:
        (data_dir / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ValidationResult(critical_errors, report["warnings"], incomplete, report["total_item_count"], report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true", help="Do not rewrite validation.json.")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    result = validate_rdb(args.root, write_report=not args.check)
    print(json.dumps(result.report, ensure_ascii=False, indent=2))
    if result.has_critical_errors: return 1
    if not result.mode_create_ready:
        print(MODE_CREATE_INCOMPLETE_MESSAGE); return 0 if args.allow_incomplete else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
