from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestSchema(unittest.TestCase):
    def test_schema_json_is_valid(self) -> None:
        schema_path = ROOT / "HK-RDB" / "schema" / "schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "HK-RDB Data File")
        self.assertIn("ruleObject", schema["$defs"])

    def test_rule_object_requires_source_and_raw_text(self) -> None:
        schema_path = ROOT / "HK-RDB" / "schema" / "schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = set(schema["$defs"]["ruleObject"]["required"])
        self.assertIn("raw_text", required)
        self.assertIn("source", required)
        self.assertIn("parsing_status", required)


if __name__ == "__main__":
    unittest.main()
