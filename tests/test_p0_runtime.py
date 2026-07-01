from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


from tools.generate_manifest import build_manifest
from tools.runtime_contracts import checkpoint_is_complete, optimization_allowed, validate_candidate_registry
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

    def test_runtime_does_not_require_maintainer_docs(self) -> None:
        runtime = (ROOT / "HK-CAS" / "runtime-create.md").read_text(encoding="utf-8")
        self.assertNotIn("CODEX_BOOTSTRAP.md", runtime)
        self.assertNotIn("CAS_EVOLUTION.md", runtime)

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
