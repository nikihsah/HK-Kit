#!/usr/bin/env python3
"""Validate HK-RDB structure.

This validator intentionally fails MODE CREATE readiness while placeholder data
files are incomplete. Structural validity and operational completeness are
reported separately so maintainers can bootstrap the repository safely.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "core-rules.json",
    "templates.json",
    "traits.json",
    "paths.json",
    "skills.json",
    "advancement.json",
    "combat-arts.json",
    "magic.json",
    "charms.json",
    "equipment.json",
    "combat-rules.json",
    "travel-rest-rules.json",
    "social-rules.json",
    "glossary.json",
    "validation.json",
    "version.json",
]

RULE_REQUIRED_FIELDS = [
    "id",
    "type",
    "category",
    "subcategory",
    "name",
    "raw_text",
    "summary",
    "costs",
    "requirements",
    "effects",
    "modifiers",
    "relationships",
    "tags",
    "source",
    "needs_manual_review",
]

CONTAINER_REQUIRED_FIELDS = ["category", "file", "complete", "items"]

MODE_CREATE_INCOMPLETE_MESSAGE = (
    "The HK-RDB is incomplete for this operation. "
    "Update the database before continuing."
)


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    incomplete_files: list[str]
    item_count: int

    @property
    def has_critical_errors(self) -> bool:
        return bool(self.errors)

    @property
    def mode_create_ready(self) -> bool:
        return not self.errors and not self.incomplete_files and self.item_count > 0


def load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"missing file: {path.as_posix()}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path.as_posix()}: {exc}"


def validate_rule_object(item: dict[str, Any], file_name: str, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"{file_name}[{index}]"

    for field in RULE_REQUIRED_FIELDS:
        if field not in item:
            errors.append(f"{prefix}: missing required field '{field}'")

    if "raw_text" in item and not str(item["raw_text"]).strip():
        errors.append(f"{prefix}: raw_text must not be empty")

    source = item.get("source")
    if not isinstance(source, dict):
        errors.append(f"{prefix}: source must be an object")
    else:
        for field in ["book", "page_start", "page_end"]:
            if field not in source:
                errors.append(f"{prefix}: source missing '{field}'")

    return errors


def validate_rdb(root: Path) -> ValidationResult:
    data_dir = root / "HK-RDB" / "data"
    errors: list[str] = []
    warnings: list[str] = []
    incomplete_files: list[str] = []
    item_count = 0
    seen_ids: dict[str, str] = {}

    index, index_error = load_json(data_dir / "index.json")
    if index_error:
        errors.append(index_error)
    elif isinstance(index, dict):
        listed = index.get("required_files", [])
        if listed != REQUIRED_FILES:
            warnings.append("index.json required_files differs from validator REQUIRED_FILES")
    else:
        errors.append("index.json must be an object")

    for file_name in REQUIRED_FILES:
        path = data_dir / file_name
        data, error = load_json(path)
        if error:
            errors.append(error)
            continue
        if not isinstance(data, dict):
            errors.append(f"{file_name}: top-level value must be an object")
            continue

        for field in CONTAINER_REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{file_name}: missing required field '{field}'")

        if data.get("file") != file_name:
            errors.append(f"{file_name}: file field must equal '{file_name}'")

        if data.get("complete") is not True:
            incomplete_files.append(file_name)

        items = data.get("items")
        if not isinstance(items, list):
            errors.append(f"{file_name}: items must be an array")
            continue

        item_count += len(items)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"{file_name}[{index}]: item must be an object")
                continue
            errors.extend(validate_rule_object(item, file_name, index))
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                if item_id in seen_ids:
                    errors.append(
                        f"duplicate id '{item_id}' in {file_name}; first seen in {seen_ids[item_id]}"
                    )
                else:
                    seen_ids[item_id] = file_name

    known_ids = set(seen_ids)
    for file_name in REQUIRED_FILES:
        data, error = load_json(data_dir / file_name)
        if error or not isinstance(data, dict) or not isinstance(data.get("items"), list):
            continue
        for index, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                continue
            for relationship in item.get("relationships", []):
                if not isinstance(relationship, dict):
                    errors.append(f"{file_name}[{index}]: relationship must be an object")
                    continue
                target = relationship.get("target")
                if target and target not in known_ids:
                    errors.append(
                        f"{file_name}[{index}]: relationship target '{target}' does not exist"
                    )

    return ValidationResult(errors, warnings, incomplete_files, item_count)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HK-RDB.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Return success when structure is valid but HK-RDB is not MODE CREATE ready.",
    )
    args = parser.parse_args()

    result = validate_rdb(args.root)

    report = {
        "mode_create_ready": result.mode_create_ready,
        "item_count": result.item_count,
        "errors": result.errors,
        "warnings": result.warnings,
        "incomplete_files": result.incomplete_files,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if result.has_critical_errors:
        return 1
    if not result.mode_create_ready:
        print(MODE_CREATE_INCOMPLETE_MESSAGE)
        return 0 if args.allow_incomplete else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
