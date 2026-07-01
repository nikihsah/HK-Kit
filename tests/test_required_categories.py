from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "HK-RDB" / "data"


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
    "manifest.json",
    "validation.json",
    "version.json",
]


class TestRequiredCategories(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        for file_name in REQUIRED_FILES:
            with self.subTest(file=file_name):
                self.assertTrue((DATA / file_name).exists())

    def test_index_lists_required_files(self) -> None:
        index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["required_files"], REQUIRED_FILES)

    def test_release_containers_are_marked_complete(self) -> None:
        for file_name in [name for name in REQUIRED_FILES if name != "manifest.json"]:
            data = json.loads((DATA / file_name).read_text(encoding="utf-8"))
            with self.subTest(file=file_name):
                self.assertIs(data["complete"], True)


if __name__ == "__main__":
    unittest.main()
