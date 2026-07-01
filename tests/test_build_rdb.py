from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_rdb import (
    build_draft_containers,
    candidate_to_rule_object,
    extract_trait_effect_hints,
    extract_trait_repeatability_hints,
    infer_trait_relationships,
    parse_trait_base_costs,
    parse_trait_conditional_costs,
    split_trait_parts,
    stable_rule_id,
    stable_name_slug,
    trait_costs,
    write_drafts,
)


def sample_candidate(category_hint: str = "traits") -> dict:
    return {
        "id": "l1.p001.b001.traits",
        "status": "needs_review",
        "category_hint": category_hint,
        "title_hint": "Черта панциря",
        "raw_text": "Черта панциря. Текст правила для проверки черновика.",
        "source": {
            "book": "Test Book",
            "pdf_name": "test.pdf",
            "pdf_sha256": "abc123",
            "page_start": 1,
            "page_end": 1,
            "layer0_page": 1,
            "layer0_block": 1,
        },
        "review_notes": [],
    }


class TestBuildRdb(unittest.TestCase):
    def test_stable_name_slug_uses_known_trait_terms(self) -> None:
        self.assertEqual(stable_name_slug("Природный Снаряд"), "natural-projectile")
        self.assertEqual(stable_name_slug("Жидкости"), "fluids")

    def test_parse_trait_costs_extracts_hunger_and_social_costs(self) -> None:
        costs = parse_trait_base_costs("+3 Голод, +0.5 Жуть или Привлекательность")

        self.assertEqual(costs["hunger"], 3)
        self.assertEqual(costs["dread"], 0.5)
        self.assertEqual(costs["appeal"], 0.5)
        self.assertEqual(costs["social_cost_options"], ["dread", "appeal"])
        self.assertEqual(costs["raw"], "+3 Голод, +0.5 Жуть или Привлекательность")

    def test_parse_trait_costs_handles_both(self) -> None:
        costs = parse_trait_base_costs("-1 Голод, +0.5 Обоим")

        self.assertEqual(costs["hunger"], -1)
        self.assertEqual(costs["dread"], 0.5)
        self.assertEqual(costs["appeal"], 0.5)

    def test_parse_trait_conditional_costs_detects_inline_hunger(self) -> None:
        costs = parse_trait_conditional_costs(
            "Выберите один обычный эффект Склянки, или необычный, за +2 голода."
        )

        self.assertEqual(len(costs), 1)
        self.assertEqual(costs[0]["costs"]["hunger"], 2)
        self.assertIn("необычный", costs[0]["when"])
        self.assertTrue(costs[0]["needs_manual_review"])

    def test_split_trait_parts_detects_subtrait_without_cost(self) -> None:
        parts = split_trait_parts("● Калечащий Выстрел\nОписание эффекта.")

        self.assertEqual(parts["name"], "Калечащий Выстрел")
        self.assertTrue(parts["is_subtrait"])
        self.assertEqual(parts["cost_text"], "")
        self.assertEqual(parts["body"], "Описание эффекта.")

    def test_split_trait_parts_does_not_treat_inline_cost_as_main_cost(self) -> None:
        parts = split_trait_parts(
            "● Жидкости\nВыберите обычный эффект или необычный, за +2 голода.\nОписание."
        )

        self.assertEqual(parts["cost_text"], "")
        self.assertEqual(
            parts["body"],
            "Выберите обычный эффект или необычный, за +2 голода.\nОписание.",
        )

    def test_split_trait_parts_joins_multiline_cost(self) -> None:
        parts = split_trait_parts(
            "Щупальце\n+3 Голод\n, +0.5 Жуть\nОписание эффекта."
        )

        self.assertEqual(parts["cost_text"], "+3 Голод , +0.5 Жуть")
        self.assertEqual(parts["body"], "Описание эффекта.")

    def test_split_trait_parts_joins_or_both_cost(self) -> None:
        parts = split_trait_parts(
            "Мелкий Недостаток\n-1 Голод, +0.5 Жути, Привлекательности или\nОбоим\nОписание."
        )

        self.assertIn("Обоим", parts["cost_text"])
        self.assertEqual(parts["body"], "Описание.")

    def test_extract_trait_effect_hints_finds_explicit_mechanics(self) -> None:
        hints = extract_trait_effect_hints(
            "Этот жук запускает снаряд. Он наносит 2 урона и имеет радиус действия 4 клетки. "
            "Это природное оружие относится к типу Праща. Черта может быть взята несколько раз."
        )
        by_type = {hint["type"]: hint for hint in hints}

        self.assertTrue(by_type["natural_weapon"]["value"])
        self.assertEqual(by_type["damage"]["amount"], 2)
        self.assertEqual(by_type["range"]["cells"], 4)
        self.assertEqual(by_type["weapon_type"]["value"], "Праща")
        self.assertTrue(by_type["repeatable_selection"]["allowed"])

    def test_repeatable_selection_twice_sets_max_two(self) -> None:
        hints = extract_trait_repeatability_hints("Эту черту можно взять дважды.")

        self.assertEqual(hints[0]["type"], "repeatable_selection")
        self.assertEqual(hints[0]["max"], 2)

    def test_natural_projectile_repeatability_preserves_subtrait_constraints(self) -> None:
        hints = extract_trait_repeatability_hints(
            "Эта Черта не может иметь несколько Подчерт, но может быть взята несколько раз "
            "с разными Подчертами на каждом из них."
        )
        selection = hints[0]
        constraints = {constraint["type"]: constraint for constraint in selection["constraints"]}

        self.assertIsNone(selection["max"])
        self.assertEqual(constraints["max_subtraits_per_copy"]["value"], 1)
        self.assertTrue(constraints["different_subtraits_per_copy"]["value"])

    def test_talent_repeatability_is_unique_by_skill(self) -> None:
        hints = extract_trait_repeatability_hints(
            "Эту Черту можно использовать несколько раз, но не более одного раза для одного "
            "и того же навыка."
        )
        constraints = hints[0]["constraints"]

        self.assertIn({"type": "unique_by", "field": "skill"}, constraints)

    def test_minor_flaw_repeatability_tracks_self_subtrait_limit(self) -> None:
        hints = extract_trait_repeatability_hints(
            "Может быть взята множество раз и дважды, как подчерта самой себя."
        )
        selection = hints[0]

        self.assertIsNone(selection["max"])
        self.assertIn(
            {"type": "self_subtrait_allowed", "value": True, "max": 2},
            selection["constraints"],
        )

    def test_repeatable_activation_is_not_selection(self) -> None:
        hints = extract_trait_repeatability_hints(
            "Жук может активировать эту способность несколько раз, тратя 1 Выносливость "
            "за каждое использование."
        )

        self.assertEqual([hint["type"] for hint in hints], ["repeatable_activation"])
        self.assertEqual(hints[0]["cost_per_use"]["stamina"], 1)

    def test_extract_trait_effect_hints_accepts_infinitive_damage(self) -> None:
        hints = extract_trait_effect_hints("Щупальце может нанести 1 урон.")
        damage = [hint for hint in hints if hint["type"] == "damage"]

        self.assertEqual(damage[0]["amount"], 1)

    def test_candidate_to_rule_object_normalizes_traits(self) -> None:
        candidate = sample_candidate("traits")
        candidate["raw_text"] = "Раздражающие Щетинки\n+3 Голод, +0.5 Привлекательность\nОписание."
        candidate["title_hint"] = "Раздражающие Щетинки"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["subcategory"], "Trait")
        self.assertEqual(item["costs"]["base"]["hunger"], 3)
        self.assertEqual(item["costs"]["base"]["appeal"], 0.5)
        self.assertEqual(item["costs"]["conditional"], [])
        self.assertEqual(item["summary"], "Описание.")
        self.assertEqual(item["effects"][0]["type"], "unparsed_effect_text")
        self.assertIn("trait", item["tags"])

    def test_candidate_to_rule_object_normalizes_subtraits(self) -> None:
        candidate = sample_candidate("traits")
        candidate["raw_text"] = "● Калечащий Выстрел\nОписание подчерты."
        candidate["title_hint"] = "● Калечащий Выстрел"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["name"], "Калечащий Выстрел")
        self.assertEqual(item["subcategory"], "Subtrait")
        self.assertIn("subtrait", item["tags"])

    def test_trait_costs_separates_base_and_conditional(self) -> None:
        costs = trait_costs(
            "",
            "Выберите обычный эффект или необычный, за +2 голода.",
        )

        self.assertEqual(costs["base"], {})
        self.assertEqual(costs["conditional"][0]["costs"]["hunger"], 2)

    def test_infer_trait_relationships_links_subtraits_to_previous_trait(self) -> None:
        parent = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "id": "parent",
                "raw_text": "Природный Снаряд\n+4 Голод\nОписание.",
                "title_hint": "Природный Снаряд",
            }
        )
        child = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "id": "child",
                "raw_text": "● Жидкости\nВыберите необычный эффект, за +2 голода.",
                "title_hint": "● Жидкости",
            }
        )

        infer_trait_relationships([parent, child])

        self.assertEqual(parent["id"], "traits.natural-projectile")
        self.assertEqual(child["id"], "traits.natural-projectile.fluids")
        self.assertEqual(parent["draft_id"], "traits.p001.b001.candidate")
        self.assertEqual(child["draft_id"], "traits.p001.b001.candidate")
        self.assertEqual(child["relationships"][0]["type"], "subtrait_of")
        self.assertEqual(child["relationships"][0]["target"], parent["id"])
        self.assertTrue(child["relationships"][0]["needs_manual_review"])

    def test_candidate_to_rule_object_is_review_draft(self) -> None:
        item = candidate_to_rule_object(sample_candidate())

        self.assertTrue(item["needs_manual_review"])
        self.assertEqual(item["category"], "Traits")
        self.assertEqual(item["type"], "traits")
        self.assertIn("layer2-draft", item["tags"])
        self.assertEqual(item["source"]["page_start"], 1)
        self.assertEqual(item["requirements"], [])
        self.assertEqual(item["effects"][0]["type"], "unparsed_effect_text")
        self.assertTrue(item["effects"][0]["needs_manual_review"])

    def test_stable_rule_id_uses_source_position(self) -> None:
        item_id = stable_rule_id("traits", sample_candidate())
        self.assertTrue(item_id.startswith("traits.p001.b001."))

    def test_build_draft_containers_skips_unknown(self) -> None:
        layer1 = {
            "candidates": [
                sample_candidate("traits"),
                sample_candidate("unknown"),
            ]
        }

        containers, skipped = build_draft_containers(layer1)

        self.assertEqual(len(containers["traits.json"]["items"]), 1)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["reason"], "unknown_or_unsupported_category_hint")

    def test_write_drafts_creates_manifest_and_data_files(self) -> None:
        layer1 = {"candidates": [sample_candidate("traits")]}
        containers, skipped = build_draft_containers(layer1)

        with tempfile.TemporaryDirectory() as tmp:
            manifest = write_drafts(
                layer1_path=Path("book.layer1.json"),
                containers=containers,
                skipped=skipped,
                output_dir=Path(tmp),
            )

            self.assertFalse(manifest["mode_create_allowed"])
            self.assertTrue((Path(tmp) / "book.rdb-draft" / "manifest.json").exists())
            self.assertTrue((Path(tmp) / "book.rdb-draft" / "data" / "traits.json").exists())


if __name__ == "__main__":
    unittest.main()
