"""Machine-checkable MODE CREATE state contracts."""

from __future__ import annotations

from typing import Any

STATUSES = {"A", "B", "Rejected", "Deferred"}
SKILL_ORIGINS = {"example", "adapted-example", "custom"}


def validate_candidate_registry(entries: list[dict[str, Any]], known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    required = {"id", "name", "category", "status", "reason", "dependencies", "conflicts", "source_file"}
    for index, entry in enumerate(entries):
        if entry.get("record_type") == "character_skill_instance":
            errors.extend(f"entry[{index}] {error}" for error in skill_instance_errors(entry))
            continue
        missing = sorted(required - entry.keys())
        if missing: errors.append(f"entry[{index}] missing: {', '.join(missing)}")
        item_id = entry.get("id")
        if not item_id: errors.append(f"entry[{index}] has no id")
        elif item_id not in known_ids: errors.append(f"entry[{index}] has unknown id: {item_id}")
        if entry.get("status") not in STATUSES: errors.append(f"entry[{index}] has invalid status")
    return errors


def skill_instance_errors(instance: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    local_id = str(instance.get("local_id", ""))
    if not local_id.startswith("character-skill."):
        errors.append("requires a character-local ID")
    if instance.get("rule_id") != "skills.overview":
        errors.append("must cite governing rule skills.overview")
    skills = instance.get("skills", [])
    if len(skills) != 4 or len({str(skill).strip().casefold() for skill in skills}) != 4 or any(not str(skill).strip() for skill in skills):
        errors.append("must contain exactly four distinct skills")
    if instance.get("origin") not in SKILL_ORIGINS:
        errors.append("has invalid origin")
    if instance.get("origin") == "adapted-example" and not instance.get("source_example"):
        errors.append("adapted example requires source_example")
    if not isinstance(instance.get("rank"), int) or instance.get("rank", 0) < 1:
        errors.append("requires a positive integer rank")
    for field in ("name", "represents", "concept_fit", "source_file"):
        if not str(instance.get(field, "")).strip():
            errors.append(f"requires {field}")
    return errors


def aggregate_skill_ranks(instances: list[dict[str, Any]], cap: int) -> dict[str, int]:
    totals: dict[str, int] = {}
    for instance in instances:
        rank = int(instance.get("rank", 0))
        for skill in instance.get("skills", []):
            key = str(skill).strip()
            totals[key] = min(cap, totals.get(key, 0) + rank)
    return totals


def skill_rank_assignment_errors(instances: list[dict[str, Any]], available_ranks: int) -> list[str]:
    errors = [error for item in instances for error in skill_instance_errors(item)]
    assigned = sum(int(item.get("rank", 0)) for item in instances if isinstance(item.get("rank"), int))
    if assigned != available_ranks:
        errors.append(f"assigned Skill Ranks {assigned} do not equal available {available_ranks}")
    return errors


def available_skill_ranks(milestone_table: list[dict[str, Any]], starting_milestone: int) -> int:
    return sum(
        int(entry["skill_rank"])
        for entry in milestone_table
        if entry.get("milestone", -1) <= starting_milestone and isinstance(entry.get("skill_rank"), int)
    )


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


def hunger_ledger_errors(ledger: dict[str, Any], known_ids: set[str]) -> list[str]:
    errors: list[str] = []
    base = ledger.get("base_hunger", {})
    adjustments = ledger.get("adjustments", [])
    if base.get("source_id") not in known_ids:
        errors.append("base Hunger source is not in HK-RDB")
    if any(item.get("id") not in known_ids for item in adjustments):
        errors.append("Hunger adjustment source is not in HK-RDB")
    values = [item.get("value") for item in adjustments]
    if any(not isinstance(value, (int, float)) for value in values):
        errors.append("every Hunger adjustment requires a numeric value")
        return errors
    positive = sum(value for value in values if value > 0)
    negative = sum(value for value in values if value < 0)
    other = sum(value for value in values if value == 0)
    if ledger.get("positive_adjustments_total") != positive:
        errors.append("positive adjustment total is incorrect")
    if ledger.get("negative_adjustments_total") != negative:
        errors.append("negative adjustment total is incorrect")
    if ledger.get("other_adjustments_total") != other:
        errors.append("other adjustment total is incorrect")
    if isinstance(base.get("value"), (int, float)):
        expected_final = base["value"] + positive + negative + other
        if ledger.get("final_hunger") != expected_final:
            errors.append("final Hunger is incorrect")
    if isinstance(ledger.get("maximum_hunger"), (int, float)) and isinstance(ledger.get("final_hunger"), (int, float)):
        expected_unused = ledger["maximum_hunger"] - ledger["final_hunger"]
        if ledger.get("unused_hunger") != expected_unused:
            errors.append("unused Hunger is incorrect")
    if not ledger.get("candidate_search_completed"):
        errors.append("Hunger candidate search is incomplete")
    if ledger.get("unused_hunger", 0) > 0:
        if not ledger.get("second_pass_required"):
            errors.append("unused Hunger requires a second pass")
        if not ledger.get("second_pass_completed"):
            errors.append("Hunger second pass is incomplete")
        if not str(ledger.get("unused_hunger_explanation", "")).strip():
            errors.append("unused Hunger requires an explanation")
        affordable = set(ledger.get("affordable_candidate_ids", []))
        disposed = set(ledger.get("selected_after_second_pass", [])) | {
            item.get("id") for item in ledger.get("rejected_after_second_pass", []) if isinstance(item, dict) and item.get("reason")
        }
        if affordable - disposed:
            errors.append("affordable Hunger candidates lack explicit dispositions")
        unknown = affordable - known_ids
        if unknown:
            errors.append("affordable Hunger candidate is not in HK-RDB")
        if ledger.get("suitable_options_remaining"):
            if not ledger.get("player_choice_required"):
                errors.append("suitable Hunger options require a player choice")
            if not ledger.get("player_choice_resolved"):
                errors.append("Hunger player choice is unresolved")
            if ledger.get("player_choice") == "leave-unused" and not ledger.get("player_approved_underutilization"):
                errors.append("unused Hunger lacks explicit player approval")
    if ledger.get("audit_status") != "pass":
        errors.append("Hunger ledger audit has not passed")
    return errors


def path_affinity_errors(selected_path: dict[str, Any], selected_components: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    path_id = selected_path.get("id")
    family = selected_path.get("modifiers", {}).get("family")
    for component in selected_components:
        if component.get("type") == "secret":
            required = [r.get("path_id") for r in component.get("requirements", []) if r.get("type") == "mystic_path"]
            if family != "Mystic Path" or required != [path_id]:
                errors.append(f"{component.get('id')}: Secret does not match selected Mystic Path")
        if component.get("type") == "combat-art":
            martial = any(
                r.get("type") == "path_family" and r.get("value") == "Martial Path"
                for r in component.get("requirements", [])
            )
            if family != "Martial Path" or not martial:
                errors.append(f"{component.get('id')}: Combat Art requires a Martial Path")
    return errors


POST_CREATION_ACTIONS = {"image", "character-sheet", "change", "finish"}


def post_creation_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    audit_status = state.get("audit_status")
    menu_available = state.get("menu_available") is True
    if menu_available and audit_status != "pass":
        errors.append("post-creation menu requires a passing latest audit")
    actions = state.get("selected_actions", [])
    if any(action not in POST_CREATION_ACTIONS for action in actions):
        errors.append("unknown post-creation action")
    sheet = state.get("filled_sheet", {})
    if sheet.get("status") == "current" and sheet.get("character_version") != state.get("character_version"):
        errors.append("filled character sheet is stale")
    if state.get("mechanical_change_pending") and audit_status == "pass":
        errors.append("mechanical change must invalidate the previous audit")
    if state.get("external_action_performed") and not actions:
        errors.append("external action requires explicit player selection")
    return errors
