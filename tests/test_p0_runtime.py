from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader


from tools.generate_manifest import build_manifest
from tools.fill_character_sheet import TEMPLATE, fill_sheet
from tools.runtime_contracts import aggregate_skill_ranks, available_skill_ranks, checkpoint_is_complete, hunger_ledger_errors, optimization_allowed, path_affinity_errors, post_creation_errors, skill_instance_errors, skill_rank_assignment_errors, validate_candidate_registry
from tools.validate_rdb import RULE_FILES, validate_rdb

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "HK-RDB" / "data"


class TestP0Runtime(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
        cls.known_ids = {
            item_id for entry in cls.manifest["files"] for item_id in entry["ids"]
        }

    def test_manifest_ids_counts_and_hashes_match(self) -> None:
        for entry in self.manifest["files"]:
            path = DATA / entry["file"]
            actual = json.loads(path.read_text(encoding="utf-8"))["items"]
            self.assertEqual(entry["ids"], [item["id"] for item in actual])
            self.assertEqual(entry["object_count"], len(actual))
            self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_manifest_hash_changes_with_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for name in RULE_FILES:
                (data / name).write_bytes((DATA / name).read_bytes())
            before = build_manifest(data)
            path = data / RULE_FILES[0]
            value = json.loads(path.read_text(encoding="utf-8"))
            value["test_non_rule_metadata"] = True
            path.write_text(json.dumps(value), encoding="utf-8")
            after = build_manifest(data)
            before_hash = next(x["sha256"] for x in before["files"] if x["file"] == RULE_FILES[0])
            after_hash = next(x["sha256"] for x in after["files"] if x["file"] == RULE_FILES[0])
            self.assertNotEqual(before_hash, after_hash)

    def test_released_ids_unique_and_relationships_valid(self) -> None:
        result = validate_rdb(ROOT)
        self.assertEqual(result.report["duplicate_ids"], [])
        self.assertEqual(result.report["broken_relationship_targets"], [])
        self.assertEqual(result.report["path_affinity_errors"], [])

    def test_secret_and_combat_art_runtime_path_affinity(self) -> None:
        paths = {item["id"]: item for item in json.loads((DATA / "paths.json").read_text(encoding="utf-8"))["items"]}
        secrets = [item for item in json.loads((DATA / "magic.json").read_text(encoding="utf-8"))["items"] if item["type"] == "secret"]
        arts = [item for item in json.loads((DATA / "combat-arts.json").read_text(encoding="utf-8"))["items"] if item["type"] == "combat-art"]
        nightmare = next(item for item in secrets if item["id"] == "magic.nightmares.ognennyy-shar")
        self.assertEqual(path_affinity_errors(paths["paths.nightmares"], [nightmare]), [])
        self.assertTrue(path_affinity_errors(paths["paths.dreams"], [nightmare]))
        self.assertEqual(path_affinity_errors(paths["paths.nail"], [arts[0]]), [])
        self.assertTrue(path_affinity_errors(paths["paths.spire"], [arts[0]]))

    def test_unparsed_objects_have_honest_status(self) -> None:
        for name in RULE_FILES:
            for item in json.loads((DATA / name).read_text(encoding="utf-8"))["items"]:
                unparsed = any("unparsed" in effect.get("type", "") for effect in item["effects"])
                if unparsed:
                    self.assertEqual(item["parsing_status"], "raw_text_authoritative")

    def test_blocked_items_and_status_are_reported(self) -> None:
        report = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))
        self.assertIn("blocked_items", report)
        if report["critical_errors"]:
            self.assertNotEqual(report["status"], "pass")

    def test_candidate_registry_requires_known_id(self) -> None:
        base = {"name": "x", "category": "x", "status": "A", "reason": "x", "dependencies": [], "conflicts": [], "source_file": "x"}
        self.assertTrue(validate_candidate_registry([base], self.known_ids))
        self.assertTrue(validate_candidate_registry([{**base, "id": "unknown.id"}], self.known_ids))

    def test_checkpoint_and_optimization_gate(self) -> None:
        item_id = next(iter(self.known_ids))
        checkpoint = {"expected_count": 2, "analyzed_count": 1, "skipped_ids": [], "skip_reasons": {}, "candidate_ids": [item_id], "registry_entries_are_concrete": True, "unresolved_dependencies": [], "unresolved_questions": [], "critical_validation_errors": [], "complete": True}
        self.assertFalse(checkpoint_is_complete(checkpoint, self.known_ids))
        self.assertFalse(optimization_allowed([checkpoint], self.known_ids))
        checkpoint.update({"skipped_ids": ["skipped.id"], "skip_reasons": {"skipped.id": "not applicable"}})
        self.assertTrue(checkpoint_is_complete(checkpoint, self.known_ids))

    def test_hunger_ledger_requires_sources_math_and_unused_explanation(self) -> None:
        source_id = next(iter(self.known_ids))
        ledger = {
            "base_hunger": {"value": 4, "source_id": source_id, "source_file": "templates.json"},
            "adjustments": [{"id": source_id, "name": "x", "category": "Traits", "value": 2, "source_file": "traits.json", "reason_selected": "vision fit"}],
            "positive_adjustments_total": 2,
            "negative_adjustments_total": 0,
            "other_adjustments_total": 0,
            "final_hunger": 6,
            "maximum_hunger": 10,
            "unused_hunger": 4,
            "candidate_search_completed": True,
            "second_pass_required": True,
            "second_pass_completed": True,
            "affordable_candidate_ids": [source_id],
            "selected_after_second_pass": [source_id],
            "rejected_after_second_pass": [],
            "player_approved_underutilization": False,
            "optimization_status": "complete",
            "unused_hunger_explanation": "No remaining candidate materially supports the locked vision.",
            "audit_status": "pass",
        }
        self.assertEqual(hunger_ledger_errors(ledger, self.known_ids), [])
        ledger["unused_hunger_explanation"] = ""
        self.assertIn("unused Hunger requires an explanation", hunger_ledger_errors(ledger, self.known_ids))

    def test_unused_hunger_forces_second_pass_and_candidate_dispositions(self) -> None:
        source_id = next(iter(self.known_ids))
        ledger = {
            "base_hunger": {"value": 4, "source_id": source_id, "source_file": "templates.json"},
            "adjustments": [],
            "positive_adjustments_total": 0,
            "negative_adjustments_total": 0,
            "other_adjustments_total": 0,
            "final_hunger": 4,
            "maximum_hunger": 20,
            "unused_hunger": 16,
            "candidate_search_completed": True,
            "second_pass_required": False,
            "second_pass_completed": False,
            "affordable_candidate_ids": [source_id],
            "selected_after_second_pass": [],
            "rejected_after_second_pass": [],
            "unused_hunger_explanation": "Large budget remains.",
            "audit_status": "pass",
        }
        errors = hunger_ledger_errors(ledger, self.known_ids)
        self.assertIn("unused Hunger requires a second pass", errors)
        self.assertIn("Hunger second pass is incomplete", errors)
        self.assertIn("affordable Hunger candidates lack explicit dispositions", errors)

    def test_useful_remaining_hunger_blocks_until_player_choice(self) -> None:
        source_id = next(iter(self.known_ids))
        ledger = {
            "base_hunger": {"value": 4, "source_id": source_id, "source_file": "templates.json"},
            "adjustments": [], "positive_adjustments_total": 0, "negative_adjustments_total": 0,
            "other_adjustments_total": 0, "final_hunger": 4, "maximum_hunger": 20, "unused_hunger": 16,
            "candidate_search_completed": True, "second_pass_required": True, "second_pass_completed": True,
            "affordable_candidate_ids": [source_id], "selected_after_second_pass": [],
            "rejected_after_second_pass": [{"id": source_id, "reason": "player choice pending"}],
            "unused_hunger_explanation": "Useful option remains.", "suitable_options_remaining": True,
            "player_choice_required": True, "player_choice_resolved": False,
            "player_choice": None, "player_approved_underutilization": False, "audit_status": "pass",
        }
        self.assertIn("Hunger player choice is unresolved", hunger_ledger_errors(ledger, self.known_ids))
        ledger.update({"player_choice_resolved": True, "player_choice": "leave-unused", "player_approved_underutilization": True})
        self.assertEqual(hunger_ledger_errors(ledger, self.known_ids), [])

    def test_custom_skill_instance_has_four_distinct_skills_and_rule_link(self) -> None:
        instance = {
            "record_type": "character_skill_instance", "local_id": "character-skill.01",
            "rule_id": "skills.overview", "source_file": "HK-RDB/data/skills.json",
            "name": "Следопыт руин", "represents": "прошлое исследователя",
            "skills": ["Выживание", "Восприятие", "Атлетика", "Знания (руины)"],
            "origin": "custom", "source_example": None, "rank": 1,
            "concept_fit": "поддерживает разведку", "player_confirmed": True,
        }
        self.assertEqual(skill_instance_errors(instance), [])
        self.assertEqual(validate_candidate_registry([instance], self.known_ids), [])
        duplicate = {**instance, "skills": ["Выживание"] * 4}
        self.assertIn("must contain exactly four distinct skills", skill_instance_errors(duplicate))

    def test_multiple_skill_examples_coexist_and_overlaps_sum_with_cap(self) -> None:
        base = {
            "record_type": "character_skill_instance", "rule_id": "skills.overview",
            "source_file": "HK-RDB/data/skills.json", "represents": "background",
            "origin": "example", "source_example": None, "rank": 1,
            "concept_fit": "fit", "player_confirmed": True,
        }
        hunter = {**base, "local_id": "character-skill.01", "name": "Охотник", "skills": ["Выживание", "Восприятие", "Воровство", "Знания (природа)"]}
        soldier = {**base, "local_id": "character-skill.02", "name": "Солдат", "skills": ["Уход", "Атлетика", "Тактика", "Выживание"]}
        self.assertEqual(skill_rank_assignment_errors([hunter, soldier], 2), [])
        self.assertEqual(aggregate_skill_ranks([hunter, soldier], 3)["Выживание"], 2)
        ranked = [{**hunter, "rank": 2}, {**soldier, "rank": 2}]
        self.assertEqual(aggregate_skill_ranks(ranked, 3)["Выживание"], 3)

    def test_available_skill_ranks_come_from_locked_milestone(self) -> None:
        advancement = json.loads((DATA / "advancement.json").read_text(encoding="utf-8"))["items"][0]
        table = advancement["modifiers"]["milestone_table"]
        self.assertEqual(available_skill_ranks(table, 0), 1)
        self.assertEqual(available_skill_ranks(table, 2), 2)
        self.assertEqual(available_skill_ranks(table, 4), 3)

    def test_post_creation_menu_and_change_invalidation(self) -> None:
        state = {
            "character_version": 1, "audit_status": "fail", "menu_available": True,
            "selected_actions": [], "filled_sheet": {"status": "not_created", "character_version": None},
        }
        self.assertIn("post-creation menu requires a passing latest audit", post_creation_errors(state))
        state.update({"audit_status": "pass", "menu_available": True})
        self.assertEqual(post_creation_errors(state), [])
        state.update({"mechanical_change_pending": True})
        self.assertIn("mechanical change must invalidate the previous audit", post_creation_errors(state))
        state.update({"audit_status": "invalidated", "menu_available": False, "filled_sheet": {"status": "stale", "character_version": 1}})
        self.assertEqual(post_creation_errors(state), [])

    def test_filled_sheet_becomes_stale_after_character_version_change(self) -> None:
        state = {
            "character_version": 2, "audit_status": "pass", "menu_available": True,
            "selected_actions": [],
            "filled_sheet": {"status": "current", "character_version": 1, "path": "old.pdf"},
        }
        self.assertIn("filled character sheet is stale", post_creation_errors(state))

    def test_post_creation_document_has_four_action_loop_after_audit(self) -> None:
        handoff = (ROOT / "HK-CAS" / "10-post-creation-handoff.md").read_text(encoding="utf-8")
        self.assertIn("Enter this state only", handoff)
        for phrase in ("Generate a character image", "Fill the official character-sheet template", "Add or change something", "Finish without additional actions"):
            self.assertIn(phrase, handoff)
        self.assertIn("show this menu again only after the new audit passes", handoff)

    def test_external_post_creation_action_requires_selection(self) -> None:
        state = {
            "character_version": 1, "audit_status": "pass", "menu_available": True,
            "selected_actions": [], "external_action_performed": True,
            "filled_sheet": {"status": "not_created", "character_version": None},
        }
        self.assertIn("external action requires explicit player selection", post_creation_errors(state))
        state.update({"selected_actions": ["finish"], "external_action_performed": False, "finished": True})
        self.assertEqual(post_creation_errors(state), [])

    def test_official_pdf_template_is_copied_and_filler_preserves_it(self) -> None:
        before = hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
        data = {
            "audit_status": "pass", "character_version": 1, "name": "Тестовый Жук", "player": "Игрок",
            "characteristics": {}, "resources": {}, "paths": [], "traits": [], "charms": [],
            "equipment": [], "techniques": [], "weapons": [], "skill_instances": [], "notes": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "filled.pdf"
            fill_sheet(data, output)
            self.assertEqual(len(PdfReader(str(output)).pages), 3)
        self.assertEqual(hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(), before)

    def test_pdf_filler_rejects_unaudited_character(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Rules Audit"):
                fill_sheet({"audit_status": "invalidated", "name": "x"}, Path(tmp) / "x.pdf")

    def test_optimization_uses_milestone_skill_ranks_not_fixed_three(self) -> None:
        optimization = (ROOT / "HK-CAS" / "08-optimization.md").read_text(encoding="utf-8")
        self.assertIn("Do not stop after the first suitable example", optimization)
        self.assertIn("do not assume a universal maximum of three instances", optimization)
        self.assertIn("example, adapted-example, and custom", optimization)
        self.assertIn("Constrained Hunger maximization is mandatory", optimization)

    def test_concept_card_cannot_replace_completed_build(self) -> None:
        overview = (ROOT / "HK-CAS" / "00-overview.md").read_text(encoding="utf-8")
        runtime = (ROOT / "HK-CAS" / "runtime-create.md").read_text(encoding="utf-8")
        for document in (overview, runtime):
            self.assertIn("A strong Concept Card is not a completed build", document)
            self.assertIn("mechanical selection, calculation", document)

    def test_reflavor_keeps_official_name_and_id(self) -> None:
        overview = (ROOT / "HK-CAS" / "00-overview.md").read_text(encoding="utf-8")
        runtime = (ROOT / "HK-CAS" / "runtime-create.md").read_text(encoding="utf-8")
        for document in (overview, runtime):
            self.assertIn("official HK-RDB name", document)
            self.assertIn("stable ID", document)
            self.assertIn("narrative name", document)

    def test_readme_quick_start_contains_strict_user_prompt(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Используй репозиторий как обязательную инструкцию", readme)
        self.assertIn("MODE: CREATE", readme)
        self.assertIn("OUTPUT MODE: USER", readme)
        self.assertIn("MODE CREATE должен завершиться полноценным рассчитанным чарником", readme)

    def test_runtime_does_not_require_maintainer_docs(self) -> None:
        runtime = (ROOT / "HK-CAS" / "runtime-create.md").read_text(encoding="utf-8")
        self.assertIn("Do not read `CODEX_BOOTSTRAP.md`", runtime)
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        runtime_section = agents.split("## MODE CREATE Runtime Route", 1)[1].split("## Maintenance and Development", 1)[0]
        self.assertIn("Do not read `CODEX_BOOTSTRAP.md`", runtime_section)
        self.assertIn("raw_text_authoritative", runtime_section)

    def test_first_response_contract_blocks_early_mechanics(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        runtime = (ROOT / "HK-CAS" / "runtime-create.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for document in (agents, runtime, readme):
            self.assertIn("first substantive response", document.lower())
            self.assertIn("Intent Lock", document)
            self.assertIn("Vision Lock", document)
            self.assertIn("Constraint Lock", document)
        self.assertIn("runtime protocol failure", agents)
        self.assertIn("partial or complete build", agents)

    def test_agents_forbids_unrelated_external_actions(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("perform external actions", agents)

    def test_all_json_is_pretty_formatted(self) -> None:
        for path in list(DATA.glob("*.json")) + list((ROOT / "HK-CAS" / "templates").glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(path.read_text(encoding="utf-8"), json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def test_all_rule_files_pass_schema(self) -> None:
        schema = json.loads((ROOT / "HK-RDB" / "schema" / "schema.json").read_text(encoding="utf-8"))
        container_required = set(schema["required"])
        object_schema = schema["$defs"]["ruleObject"]
        object_required = set(object_schema["required"])
        object_properties = set(object_schema["properties"])
        parsing_values = set(object_schema["properties"]["parsing_status"]["enum"])
        for name in RULE_FILES:
            container = json.loads((DATA / name).read_text(encoding="utf-8"))
            self.assertFalse(container_required - container.keys(), name)
            for item in container["items"]:
                self.assertFalse(object_required - item.keys(), item.get("id"))
                self.assertFalse(item.keys() - object_properties, item.get("id"))
                self.assertIn(item["parsing_status"], parsing_values)


if __name__ == "__main__":
    unittest.main()
