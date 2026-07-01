"""Machine-checkable MODE CREATE state contracts."""

from __future__ import annotations

from typing import Any

STATUSES = {"A", "B", "Rejected", "Deferred"}


def validate_candidate_registry(entries: list[dict[str, Any]], known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    required = {"id", "name", "category", "status", "reason", "dependencies", "conflicts", "source_file"}
    for index, entry in enumerate(entries):
        missing = sorted(required - entry.keys())
        if missing: errors.append(f"entry[{index}] missing: {', '.join(missing)}")
        item_id = entry.get("id")
        if not item_id: errors.append(f"entry[{index}] has no id")
        elif item_id not in known_ids: errors.append(f"entry[{index}] has unknown id: {item_id}")
        if entry.get("status") not in STATUSES: errors.append(f"entry[{index}] has invalid status")
    return errors


def checkpoint_errors(checkpoint: dict[str, Any], known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    expected, analyzed = checkpoint.get("expected_count", 0), checkpoint.get("analyzed_count", 0)
    skipped = checkpoint.get("skipped_ids", [])
    reasons = checkpoint.get("skip_reasons", {})
    if analyzed + len(skipped) != expected: errors.append("analyzed and skipped counts do not cover expected_count")
    if any(item_id not in reasons or not reasons[item_id] for item_id in skipped): errors.append("each skipped id requires a reason")
    if any(item_id not in known_ids for item_id in checkpoint.get("candidate_ids", [])): errors.append("candidate id is not in HK-RDB")
    if not checkpoint.get("registry_entries_are_concrete", False): errors.append("registry entries are not concrete")
    if checkpoint.get("unresolved_dependencies"): errors.append("unresolved dependencies remain")
    if checkpoint.get("unresolved_questions"): errors.append("unresolved questions remain")
    if checkpoint.get("critical_validation_errors"): errors.append("critical validation errors remain")
    return errors


def checkpoint_is_complete(checkpoint: dict[str, Any], known_ids: set[str]) -> bool:
    return checkpoint.get("complete") is True and not checkpoint_errors(checkpoint, known_ids)


def optimization_allowed(checkpoints: list[dict[str, Any]], known_ids: set[str]) -> bool:
    return bool(checkpoints) and all(checkpoint_is_complete(item, known_ids) for item in checkpoints)
