from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.build_rdb import (
    build_draft_containers,
    candidate_to_rule_object,
    extract_trait_effect_hints,
    extract_trait_modifiers,
    extract_trait_roll_modifiers,
    extract_trait_resource_usage_hints,
    extract_trait_repeatability_hints,
    infer_trait_constraints,
    infer_trait_relationships,
    parse_trait_base_costs,
    parse_trait_conditional_costs,
    split_trait_parts,
    stable_rule_id,
    stable_name_slug,
    split_template_table_blocks,
    template_rule_objects_from_candidate,
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
    def test_equipment_modifications_are_atomic_and_keep_costs(self) -> None:
        from tools.build_rdb import split_equipment_entries

        entries = split_equipment_entries(
            "Модификации оружия\nИзношенное\nШтраф -1 к Качеству.\n"
            "Нитяное\nПозволяет прикрепить нить.\n25",
            "weapon-modification",
        )

        self.assertEqual([entry["name"] for entry in entries], ["Изношенное", "Нитяное"])
        self.assertEqual(entries[0]["stats"]["price"], "half_weapon_price")
        self.assertEqual(entries[1]["stats"]["price"], "25")

    def test_food_page_yields_rules_and_concrete_food_items(self) -> None:
        from tools.build_rdb import split_equipment_entries

        entries = split_equipment_entries(
            "Припасы и рецепты\nМожно изучать рецепты.\n"
            "Использование Припасов\nЗелье используется за 1 Выносливость.\n"
            "Сырые растения 5 0.5 1\nПаек с мясом 15 0.2 10",
            "food",
        )
        food = {entry["name"]: entry for entry in entries if entry["section"] == "food"}

        self.assertIn("Припасы и рецепты", [entry["name"] for entry in entries])
        self.assertEqual(food["Сырые растения"]["stats"]["satiety"], "5")
        self.assertFalse(food["Паек с мясом"]["stats"]["spoils"])

    def test_misordered_shield_cell_uses_verified_body(self) -> None:
        from tools.build_rdb import split_equipment_entries

        entries = split_equipment_entries(
            "Обманка 50 + нач. цена\nПрактичный\n"
            "Этот щит также считается инструментом.",
            "shield-modification",
        )
        by_name = {entry["name"]: entry for entry in entries}

        self.assertIn("сменить форму на оружие", by_name["Обманка"]["body"])
        self.assertIn("считается инструментом", by_name["Практичный"]["body"])

    def test_armor_modification_conflicts_are_explicit(self) -> None:
        candidate = sample_candidate("equipment")
        candidate["source"]["page_start"] = 98
        candidate["source"]["page_end"] = 98
        candidate["raw_text"] = (
            "Модификации брони\nСтеганая\n+1 к Впитыванию.\n70\n"
            "Утяжеленная\n+1 к весу.\n100\nШипованная\nЧерта Шипастый.\n150"
        )
        containers, _ = build_draft_containers({"candidates": [candidate]})
        items = {item["name"]: item for item in containers["equipment.json"]["items"]}

        self.assertEqual(items["Стеганая"]["requirements"][0]["value"], "armor")
        self.assertEqual(
            {relation["target"] for relation in items["Стеганая"]["relationships"]},
            {
                "equipment.armor-modification.utyazhelennaya",
                "equipment.armor-modification.shipovannaya",
            },
        )

    def test_magic_split_handles_wrapped_difficulty_value(self) -> None:
        from tools.build_rdb import split_magic_entries

        entries = split_magic_entries(
            "Зеркальный союзник\nСложность:\nДальность:\nКасание\n2\n"
            "Длительность: Краткая\nТекст эффекта.",
            "dreams",
        )

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "Зеркальный союзник")
        self.assertEqual(entries[0]["difficulty"], 2)

    def test_dust_shells_are_linked_to_dust_path(self) -> None:
        candidate = sample_candidate("paths")
        candidate["raw_text"] = (
            "Оболочки\nОболочка имеет те же Черты, что и при жизни. "
            "У неё на 2 Скорости меньше, 2 Жути, 0 Проницательности, "
            "3 Выносливости, 2 Души и Поглощение 10."
        )
        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "paths.dust.shells")
        self.assertEqual(item["relationships"], [{"type": "part_of", "target": "paths.dust"}])
        self.assertEqual(item["modifiers"]["absorption"], 10)

    def test_core_rules_are_split_into_atomic_objects(self) -> None:
        candidate = sample_candidate("core-rules")
        candidate["raw_text"] = (
            "Проверки Характеристик\nОбщее правило проверок.\n"
            "Обычные броски\nБросьте Главную Характеристику и Ранг навыка.\n"
            "Спасброски\nУспехи отменяют успехи противника."
        )
        containers, _ = build_draft_containers({"candidates": [candidate]})
        items = containers["core-rules.json"]["items"]
        self.assertEqual([item["id"] for item in items], [
            "core-rules.characteristic-checks",
            "core-rules.standard-checks",
            "core-rules.saving-checks",
        ])
        self.assertEqual(items[1]["modifiers"]["dice_pool"], [
            "main_characteristic", "highest_applicable_skill_rank"
        ])
        self.assertEqual(items[1]["relationships"], [
            {"type": "uses", "target": "core-rules.characteristics"}
        ])

    def test_dice_rules_capture_success_faces_and_rerolls(self) -> None:
        candidate = sample_candidate("core-rules")
        candidate["raw_text"] = (
            "Как работают броски костей\nБросаются шестигранные кубики; 5 и 6 являются успехами.\n"
            "Повторные броски\nПосле проверки можно перебросить кости и оставить лучший результат."
        )
        containers, _ = build_draft_containers({"candidates": [candidate]})
        items = containers["core-rules.json"]["items"]

        self.assertEqual(items[0]["modifiers"]["die"], "d6")
        self.assertEqual(items[0]["modifiers"]["success_faces"], [5, 6])
        self.assertEqual(items[1]["modifiers"]["keep"], "best_result")

    def test_glossary_indexes_canonical_rules_with_valid_relationships(self) -> None:
        candidate = sample_candidate("core-rules")
        candidate["raw_text"] = "Мощь\nСила и физическая подготовленность жука."
        containers, _ = build_draft_containers({"candidates": [candidate]})
        entries = containers["glossary.json"]["items"]

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "glossary.power")
        self.assertEqual(entries[0]["modifiers"]["canonical_rule_id"], "core-rules.power")
        self.assertEqual(entries[0]["relationships"], [
            {"type": "defined_by", "target": "core-rules.power"}
        ])

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

    def test_extract_trait_modifiers_parses_direct_delta(self) -> None:
        modifiers = extract_trait_modifiers("Этот жук увеличивает его Грацию на 0.5.")

        self.assertEqual(modifiers[0]["type"], "delta")
        self.assertEqual(modifiers[0]["target"], "grace")
        self.assertEqual(modifiers[0]["value"], 0.5)

    def test_extract_trait_modifiers_parses_decrease(self) -> None:
        modifiers = extract_trait_modifiers("Уменьшите его Грацию на 1.")

        self.assertEqual(modifiers[0]["value"], -1)

    def test_extract_trait_modifiers_parses_set_to(self) -> None:
        modifiers = extract_trait_modifiers("До прибавок увеличьте его Проницательность до 4.")

        self.assertEqual(modifiers[0]["type"], "set_to")
        self.assertEqual(modifiers[0]["target"], "insight")
        self.assertEqual(modifiers[0]["value"], 4)

    def test_extract_trait_modifiers_parses_pair_decrease(self) -> None:
        modifiers = extract_trait_modifiers("Его Проницательность и Душа уменьшаются на 1.")
        values = {modifier["target"]: modifier["value"] for modifier in modifiers}

        self.assertEqual(values, {"insight": -1, "soul": -1})

    def test_extract_trait_modifiers_parses_heart_max(self) -> None:
        modifiers = extract_trait_modifiers("Он получает +1 к максимуму Сердца.")

        self.assertEqual(modifiers[0]["target"], "heart_max")
        self.assertEqual(modifiers[0]["value"], 1)

    def test_extract_trait_modifiers_marks_conditional_context(self) -> None:
        modifiers = extract_trait_modifiers(
            "Когда у этого жука 1 Сердце или меньше, его Скорость увеличивается на 2."
        )

        self.assertTrue(modifiers[0]["conditional"])

    def test_roll_modifiers_parse_dice_penalty(self) -> None:
        entries = extract_trait_roll_modifiers("Он имеет штраф -2 кубика к проверкам Инициативы.")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["type"], "dice_penalty")
        self.assertEqual(entries[0]["value"], -2)
        self.assertEqual(entries[0]["target"], "проверкам Инициативы")

    def test_roll_modifiers_parse_dice_bonus(self) -> None:
        entries = extract_trait_roll_modifiers("Он имеет +2 бонус кубика к проверкам Инициативы.")

        self.assertEqual(entries[0]["type"], "dice_bonus")
        self.assertEqual(entries[0]["value"], 2)

    def test_roll_modifiers_parse_reroll_bonus(self) -> None:
        entries = extract_trait_roll_modifiers("У них есть +2 переброса к проверкам захвата.")

        self.assertEqual(entries[0]["type"], "reroll_bonus")
        self.assertEqual(entries[0]["value"], 2)
        self.assertEqual(entries[0]["target"], "проверкам захвата")

    def test_roll_modifiers_parse_automatic_success(self) -> None:
        talent = extract_trait_roll_modifiers(
            "Один из этих кубиков автоматически становится успешным и не выбрасывается."
        )
        scavenger = extract_trait_roll_modifiers(
            "Два из брошенных кубиков автоматически считаются успешными."
        )

        self.assertEqual(talent[0]["type"], "automatic_success")
        self.assertEqual(talent[0]["count"], 1)
        self.assertEqual(scavenger[0]["count"], 2)

    def test_roll_modifiers_parse_roll_not_required(self) -> None:
        entries = extract_trait_roll_modifiers(
            "Жук не должен бросать кубик, чтобы карабкаться по обычной поверхности."
        )

        self.assertEqual(entries[0]["type"], "roll_not_required")

    def test_resource_hints_parse_numeric_stamina_cost(self) -> None:
        hints = extract_trait_resource_usage_hints(
            "Для этого нужно потратить 1 Выносливость."
        )

        self.assertEqual(hints[0]["type"], "resource_cost")
        self.assertEqual(hints[0]["resource"], "stamina")
        self.assertEqual(hints[0]["amount"], 1)

    def test_resource_hints_parse_gain_and_target_loss(self) -> None:
        hints = extract_trait_resource_usage_hints(
            "При успехе жук получает 5 Сытости, а жертва теряет 10 Сытости."
        )
        by_type = {hint["type"]: hint for hint in hints}

        self.assertEqual(by_type["resource_gain"]["subject"], "self")
        self.assertEqual(by_type["resource_gain"]["amount"], 5)
        self.assertEqual(by_type["resource_loss"]["subject"], "target")
        self.assertEqual(by_type["resource_loss"]["amount"], 10)

    def test_resource_hints_parse_capacity_and_exchange(self) -> None:
        hints = extract_trait_resource_usage_hints(
            "Жук хранит до 20 дополнительной Сытости. Этот Запас можно потратить вместо "
            "Выносливости по курсу 10 Сытости за каждую потраченную Выносливость."
        )
        by_type = {hint["type"]: hint for hint in hints}

        self.assertEqual(by_type["resource_capacity"]["additional"], 20)
        self.assertEqual(by_type["resource_exchange"]["from"]["amount"], 10)
        self.assertEqual(by_type["resource_exchange"]["to"]["amount"], 1)

    def test_resource_hints_parse_round_limit_and_cost(self) -> None:
        hints = extract_trait_resource_usage_hints(
            "Один раз за раунд, за 3 единицы Выносливости, жук может прыгнуть."
        )
        by_type = {hint["type"]: hint for hint in hints}

        self.assertEqual(by_type["usage_limit"]["period"], "round")
        self.assertEqual(by_type["resource_cost"]["amount"], 3)

    def test_resource_hints_parse_rest_restore(self) -> None:
        hints = extract_trait_resource_usage_hints("После отдыха жук восстанавливает 1 душу.")
        by_type = {hint["type"]: hint for hint in hints}

        self.assertEqual(by_type["resource_restore"]["resource"], "soul")
        self.assertEqual(by_type["resource_restore"]["amount"], 1)
        self.assertEqual(by_type["timing"]["value"], "after_rest")

    def test_resource_hints_distinguish_glory_soul(self) -> None:
        hints = extract_trait_resource_usage_hints(
            "Если количество Душ максимально, он вместо этого получает 1 Душу Славы."
        )

        self.assertEqual(hints[0]["resource"], "glory_soul")

    def test_split_template_table_blocks_finds_three_templates(self) -> None:
        raw = (
            "r 2. СОЗДАНИЕ ЖУКА\n"
            "Мелкий Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "2 3 3\n"
            "Сердце Выносливость Душа\n"
            "6 3 3\n"
            "4\n"
            "Привлекательность Жуть\n"
            "1.5 1 1\n"
            "Голод Скорость\n"
            "Старт: -1\n"
            "Максимум: 15 7\n"
            "Средний Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "3 3 3\n"
            "Сердце Выносливость Душа\n"
            "7 3 3\n"
            "3\n"
            "Привлекательность Жуть\n"
            "1 1 1.5\n"
            "Голод Скорость\n"
            "Старт: 4\n"
            "Максимум: 20 6\n"
            "Большой Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "4 3 4\n"
            "Сердце Выносливость Душа\n"
            "8 3 3\n"
            "2\n"
            "Привлекательность Жуть\n"
            "1 1.5 1\n"
            "Голод Скорость\n"
            "Старт: 9\n"
            "Максимум: 25\n"
            "L\n"
            "5\n"
            "Шаблоны\n"
        )

        blocks = split_template_table_blocks(raw)

        self.assertEqual(len(blocks), 3)
        self.assertTrue(blocks[0].startswith("Мелкий Жук"))
        self.assertTrue(blocks[2].startswith("Большой Жук"))

    def test_template_rule_objects_extract_base_values(self) -> None:
        candidate = sample_candidate("templates")
        candidate["raw_text"] = (
            "Мелкий Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "2 3 3\n"
            "Сердце Выносливость Душа\n"
            "6 3 3\n"
            "4\n"
            "Привлекательность Жуть\n"
            "1.5 1 1\n"
            "Голод Скорость\n"
            "Старт: -1\n"
            "Максимум: 15 7\n"
        )

        item = template_rule_objects_from_candidate(candidate)[0]

        self.assertEqual(item["id"], "templates.small-bug")
        self.assertEqual(item["type"], "template")
        self.assertEqual(item["subcategory"], "Character Template")
        self.assertEqual(item["modifiers"]["size"], "Small")
        self.assertEqual(item["modifiers"]["characteristics"]["power"], 2)
        self.assertEqual(item["modifiers"]["characteristics"]["grace"], 4)
        self.assertEqual(item["modifiers"]["resources"]["heart"], 6)
        self.assertEqual(item["modifiers"]["social"]["appeal"], 1.5)
        self.assertEqual(item["modifiers"]["hunger"]["start"], -1)
        self.assertEqual(item["modifiers"]["hunger"]["maximum"], 15)
        self.assertEqual(item["modifiers"]["speed"], 7)

    def test_build_draft_containers_expands_template_page(self) -> None:
        candidate = sample_candidate("templates")
        candidate["raw_text"] = (
            "Мелкий Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "2 3 3\n"
            "Сердце Выносливость Душа\n"
            "6 3 3\n"
            "4\n"
            "Привлекательность Жуть\n"
            "1.5 1 1\n"
            "Голод Скорость\n"
            "Старт: -1\n"
            "Максимум: 15 7\n"
            "Средний Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "3 3 3\n"
            "Сердце Выносливость Душа\n"
            "7 3 3\n"
            "3\n"
            "Привлекательность Жуть\n"
            "1 1 1.5\n"
            "Голод Скорость\n"
            "Старт: 4\n"
            "Максимум: 20 6\n"
            "Большой Жук\n"
            "Мощь Проницательность Панцирь Грация\n"
            "4 3 4\n"
            "Сердце Выносливость Душа\n"
            "8 3 3\n"
            "2\n"
            "Привлекательность Жуть\n"
            "1 1.5 1\n"
            "Голод Скорость\n"
            "Старт: 9\n"
            "Максимум: 25\n"
            "L\n"
            "5\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)

        self.assertEqual(skipped, [])
        self.assertEqual(len(containers["templates.json"]["items"]), 3)
        self.assertEqual(containers["templates.json"]["items"][2]["id"], "templates.large-bug")
        self.assertEqual(containers["templates.json"]["items"][2]["modifiers"]["speed"], 5)

    def test_candidate_to_rule_object_normalizes_path_overview(self) -> None:
        candidate = sample_candidate("paths")
        candidate["raw_text"] = (
            "3.Пути\n"
            "Новый жук начинает с Рангом 1 в выбранном Пути. Максимальным является Ранг 3. "
            "Жук получает дополнительную Метку, а также увеличивает Душу при Мистическом пути; "
            "Выносливость при Военном."
        )
        candidate["title_hint"] = "3.Пути"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "paths.overview")
        self.assertEqual(item["type"], "path-rules")
        self.assertEqual(item["modifiers"]["starting_rank"], 1)
        self.assertEqual(item["modifiers"]["rank_max"], 3)
        self.assertEqual(item["modifiers"]["martial_rank_resource_increase"], "stamina")
        self.assertEqual(item["modifiers"]["mystic_rank_resource_increase"], "soul")

    def test_candidate_to_rule_object_normalizes_path_rank_entries(self) -> None:
        candidate = sample_candidate("paths")
        candidate["raw_text"] = (
            "Военные Пути\n"
            "Гвоздь\n"
            "Ранг 1 - Воин с гвоздём\n"
            "Пробитие защиты\n"
            "Четвёрки считаются за успех.\n"
            "Ранг 2 - Мастер гвоздя\n"
            "Боевая стойка\n"
            "Провоцирует атаку.\n"
            "Ранг 3 - Гуру гвоздя\n"
            "Военный мастер\n"
            "Может использовать дополнительное Искусство за ход.\n"
        )
        candidate["title_hint"] = "Гвоздь"

        item = candidate_to_rule_object(candidate)
        rank_entries = item["modifiers"]["rank_entries"]

        self.assertEqual(item["id"], "paths.nail")
        self.assertEqual(item["type"], "path")
        self.assertEqual(item["subcategory"], "Martial Path")
        self.assertEqual(item["modifiers"]["rank_max"], 3)
        self.assertEqual([entry["rank"] for entry in rank_entries], [1, 2, 3])
        self.assertEqual(rank_entries[0]["rank_title"], "Воин с гвоздём")
        self.assertIn("Пробитие защиты", rank_entries[0]["ability_names"])

    def test_candidate_to_rule_object_normalizes_skill_overview(self) -> None:
        candidate = sample_candidate("skills")
        candidate["raw_text"] = (
            "4.Умения\n"
            "Умение включает в себя четыре разных навыка. Ранг 3 - максимальный.\n"
            "Солдат\n"
            "Уход за снаряжением\n"
            "Атлетика\n"
            "Тактика\n"
            "Знания (военные)\n"
            "Жрец\n"
            "Медицина\n"
            "Убеждение\n"
            "Ритуалы\n"
            "Знания (богословие)\n"
            "Примеры навыков\n"
            "Этичность\n"
            "Игрок пытается произвести хорошее впечатление.\n"
            "Интуиция\n"
            "Игрок пытается оценить поведение другого жука.\n"
        )
        candidate["title_hint"] = "4.Умения"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "skills.overview")
        self.assertEqual(item["type"], "skill-rules")
        self.assertEqual(item["modifiers"]["skill_slots_per_skill_set"], 4)
        self.assertEqual(item["modifiers"]["rank_max"], 3)
        self.assertEqual(item["modifiers"]["example_skill_sets"][0]["name"], "Солдат")
        self.assertEqual(
            item["modifiers"]["example_skill_sets"][0]["skills"],
            ["Уход за снаряжением", "Атлетика", "Тактика", "Знания (военные)"],
        )
        self.assertEqual(item["modifiers"]["sample_skill_descriptions"][0]["name"], "Этичность")

    def test_candidate_to_rule_object_normalizes_skill_mastery(self) -> None:
        candidate = sample_candidate("skills")
        candidate["raw_text"] = (
            "Пример мастерства\n"
            "Этичность\n"
            "Один раз за сцену, если неудачная социальная проверка влияет на положение жука, она не учитывается.\n"
            "Медицина\n"
            "За 1 Выносливость игрок может кинуть проверку Медицины.\n"
            "Раскрытие Тайны и\n"
            "практика Искусства\n"
            "Когда жук достигнет второго Ранга, вместо него он может изучить одну Тайну или Искусство.\n"
            "Сложность задачи\n"
            "Шкала Сложности\n"
        )
        candidate["title_hint"] = "Пример мастерства"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "skills.mastery-and-difficulty")
        self.assertEqual(item["subcategory"], "Skill Mastery And Difficulty")
        self.assertEqual(item["modifiers"]["mastery_examples"][0]["name"], "Этичность")
        self.assertEqual(
            item["modifiers"]["alternate_rank_2_option"]["type"],
            "learn_secret_or_art_instead_of_skill_rank",
        )
        self.assertEqual(item["modifiers"]["difficulty_scale"][0]["label"], "Простая задача")

    def test_candidate_to_rule_object_normalizes_advancement(self) -> None:
        candidate = sample_candidate("advancement")
        candidate["raw_text"] = (
            "5.Продвижение\n"
            "Таблица Продвижения\n"
            "Веха Ранг Пути Малое Продвижение Ранг Умения\n"
            "0 1 - 1\n"
            "1 - 1 -\n"
            "2 1 - 1\n"
            "3 - 1 -\n"
            "И так далее: каждая четная веха дает Ранг Умения, а каждая нечетная — Малое Продвижение.\n"
            "Мистические Ранги\n"
            "Когда жук получает Ранг в Мистическом Пути, он также изучает одну Тайну из него.\n"
            "Малое Продвижение\n"
            "Когда жук получает Малое Продвижение, есть несколько вариантов того, как он может его использовать:\n"
            "● Добавить +0.5 к любой Главной Характеристике жука.\n"
            "● Добавить +1 к Скорости жука (не более 7).\n"
            "● Добавить +1 к Нагрузке жука.\n"
            "● Добавить 1 Ячейку Техники жуку.\n"
        )
        candidate["title_hint"] = "5.Продвижение"

        item = candidate_to_rule_object(candidate)
        modifiers = item["modifiers"]

        self.assertEqual(item["id"], "advancement.progression")
        self.assertEqual(item["type"], "advancement-rules")
        self.assertEqual(modifiers["milestone_table"][0]["milestone"], 0)
        self.assertEqual(modifiers["milestone_table"][0]["path_rank"], 1)
        self.assertIsNone(modifiers["milestone_table"][1]["path_rank"])
        self.assertEqual(modifiers["progression_pattern"]["odd_milestones"], "minor_advancement")
        self.assertEqual(modifiers["mystic_path_rank_grants_secret"], "same_path")
        self.assertEqual(
            modifiers["minor_advancement_options"][0]["type"],
            "increase_main_characteristic",
        )

    def test_candidate_to_rule_object_normalizes_combat_art_overview(self) -> None:
        candidate = sample_candidate("combat-arts")
        candidate["raw_text"] = (
            "6. Боевые Искусства\n"
            "Жук может применить одно Искусство за ход.\n"
            "Искусства бывают следующих типов:\n"
            "Обычные Боевые Искусства\n"
            "Искусства Усиления\n"
        )
        candidate["title_hint"] = "6. Боевые Искусства"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "combat-arts.overview")
        self.assertEqual(item["type"], "combat-art-rules")
        self.assertTrue(item["modifiers"]["normally_one_art_per_turn"])
        self.assertIn("boost", item["modifiers"]["types"])

    def test_build_draft_containers_expands_combat_arts(self) -> None:
        candidate = sample_candidate("combat-arts")
        candidate["raw_text"] = (
            "Замах - Усиление\n"
            "1 Выносливость\n"
            "Жук получает штраф -1 к урону от следующей атаки.\n"
            "Выпад - Обычное\n"
            "3 Выносливости - Оружие ближнего боя\n"
            "Жук перемещается на 2 клетки по прямой.\n"
        )
        candidate["title_hint"] = "Обычные Боевые Искусства"
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["combat-arts.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "combat-arts.zamakh")
        self.assertEqual(items[0]["costs"]["stamina"], 1)
        self.assertEqual(items[0]["modifiers"]["art_types"], ["boost"])
        self.assertEqual(items[1]["requirements"][0]["value"], "Оружие ближнего боя")

    def test_combat_art_cost_requirements_join_wrapped_lines(self) -> None:
        candidate = sample_candidate("combat-arts")
        candidate["raw_text"] = (
            "Быстрая Рука - Уникальное\n"
            "3 Выносливости - Праща, оружие ближнего\n"
            "боя с досягаемостью\n"
            "Жук крайне проворен.\n"
        )
        candidate["title_hint"] = "Быстрая Рука"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(
            [requirement["value"] for requirement in item["requirements"]],
            ["Праща", "оружие ближнего боя с досягаемостью"],
        )

    def test_candidate_to_rule_object_normalizes_magic_overview(self) -> None:
        candidate = sample_candidate("magic")
        candidate["raw_text"] = (
            "7.Магия\n"
            "Тайны — это строительные блоки магии.\n"
            "Подготовка\n"
            "Подготовленные заклинания со Сложностью, вдвое превышающей его Мистический Ранг.\n"
        )
        candidate["title_hint"] = "7.Магия"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "magic.overview")
        self.assertEqual(item["type"], "magic-rules")
        self.assertTrue(item["modifiers"]["prepared_with_technique_slots"])
        self.assertTrue(item["modifiers"]["soul_cost_equals_difficulty"])

    def test_candidate_to_rule_object_normalizes_spell_modifications(self) -> None:
        candidate = sample_candidate("magic")
        candidate["raw_text"] = (
            "Модификации Заклинаний\n"
            "Таблица Дальности\n"
            "Урон/Исцеление\n"
            "Длительность Заклинания\n"
            "Расширенные заклинания\n"
            "Ускоренные заклинания\n"
            "Сотворенные заклинания\n"
        )
        candidate["title_hint"] = "Модификации Заклинаний"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "magic.spell-modifications")
        self.assertTrue(item["modifiers"]["range_can_be_modified"])
        self.assertTrue(item["modifiers"]["quickened_spells"])

    def test_candidate_to_rule_object_normalizes_advanced_spell_modifications(self) -> None:
        candidate = sample_candidate("magic")
        candidate["raw_text"] = (
            "Расширенные заклинания\n"
            "Ускоренные заклинания\n"
            "Сотворенные заклинания\n"
        )
        candidate["title_hint"] = "Расширенные заклинания"

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "magic.spell-modifications.advanced-casting")
        self.assertTrue(item["modifiers"]["expanded_spells"])

    def test_build_draft_containers_expands_magic_secrets(self) -> None:
        candidate = sample_candidate("magic")
        candidate["raw_text"] = (
            "Тайна Шпиля\n"
            "Рассеивание\n"
            "Сложность: 2\n"
            "Дальность: Касание\n"
            "Магический эффект развеивается.\n"
            "Левитация\n"
            "Сложность: 1\n"
            "Дальность А: Близко\n"
            "Длительность: Краткая\n"
            "Поднимает цель над землей.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["magic.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "magic.spire.rasseivanie")
        self.assertEqual(items[0]["costs"]["difficulty"], 2)
        self.assertEqual(items[0]["requirements"][0]["value"], "spire")
        self.assertEqual(items[1]["modifiers"]["duration"], "Краткая")

    def test_build_draft_containers_expands_charm_entries(self) -> None:
        candidate = sample_candidate("charms")
        candidate["source"]["page_start"] = 82
        candidate["source"]["page_end"] = 82
        candidate["raw_text"] = (
            "Боевые Амулеты\n"
            "Древняя Сила - Обычный\n"
            "⊚⊚\n"
            "Природное оружие носителя получает одну модификацию оружия.\n"
            "Острая Тень - Обычный\n"
            "⊚⊚\n"
            "Требования: 1 Ранг Плаща\n"
            "Один раз в ход носитель может нанести 2 урона.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["charms.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "charms.combat.drevnyaya-sila")
        self.assertEqual(items[0]["costs"]["notches"], 2)
        self.assertEqual(items[0]["modifiers"]["rarity"], "common")
        self.assertEqual(items[0]["modifiers"]["group"], "combat")
        self.assertEqual(items[1]["requirements"][0]["type"], "raw_requirement")
        self.assertEqual(items[1]["requirements"][1]["rank"], 1)

    def test_candidate_to_rule_object_normalizes_charm_overview(self) -> None:
        candidate = sample_candidate("charms")
        candidate["source"]["page_start"] = 74
        candidate["source"]["page_end"] = 74
        candidate["raw_text"] = (
            "8. Амулеты\n"
            "Амулеты занимают Метки.\n"
            "Переочарованные жуки получают удвоенный урон.\n"
            "Редкость Амулетов\n"
            "Обычные Амулеты\n"
            "Цена: 100 Гео\n"
        )

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "charms.overview")
        self.assertEqual(item["type"], "charm-rules")
        self.assertTrue(item["modifiers"]["rarity_prices_present"])
        self.assertTrue(item["modifiers"]["overcharm_rules_present"])

    def test_build_draft_containers_expands_equipment_weapons(self) -> None:
        candidate = sample_candidate("equipment")
        candidate["source"]["page_start"] = 89
        candidate["source"]["page_end"] = 89
        candidate["raw_text"] = (
            "Оружие (1/4)\n"
            "Оружие Тип Урон Дальность боя Хватка Вес Цена\n"
            "Гвоздь Гвоздь 3\n"
            "Ближний\n"
            "1Р 1 100\n"
            "Атакующий может перебросить один проваленный бросок.\n"
            "Игла Игла 3 1Р 1 100\n"
            "+2 к броску Инициативы.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["equipment.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "equipment.weapon.gvozd")
        self.assertEqual(items[0]["costs"]["geo"], 100)
        self.assertEqual(items[0]["modifiers"]["weight"], 1)
        self.assertEqual(items[0]["modifiers"]["stats"]["item_type"], "Гвоздь")
        self.assertEqual(items[0]["modifiers"]["stats"]["damage"], "3")

    def test_build_draft_containers_expands_equipment_consumables(self) -> None:
        candidate = sample_candidate("equipment")
        candidate["source"]["page_start"] = 104
        candidate["source"]["page_end"] = 104
        candidate["raw_text"] = (
            "Склянки (1/3)\n"
            "Склянка Редкость Восстанавливается? Цена\n"
            "С водой Обычная Нет 10\n"
            "Направленный: Весь огонь на цели затухает.\n"
            "С пыльцой Необычная Да 50\n"
            "Окружение+: Все жуки восстанавливают 1 Сердце.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["equipment.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "equipment.flask.s-vodoy")
        self.assertEqual(items[0]["modifiers"]["rarity"], "common")
        self.assertEqual(items[0]["modifiers"]["stats"]["reusable"], "Нет")
        self.assertEqual(items[1]["costs"]["geo"], 50)

    def test_build_draft_containers_expands_combat_rule_sections(self) -> None:
        candidate = sample_candidate("combat-rules")
        candidate["source"]["page_start"] = 117
        candidate["source"]["page_end"] = 117
        candidate["raw_text"] = (
            "10. Сражение\n"
            "Порядок Инициативы\n"
            "Инициатива определяется Грацией.\n"
            "Клетки и Движение\n"
            "Жук может переместиться на количество клеток, равное его Скорости.\n"
            "Атака\n"
            "Атака требует траты хотя бы 1 Выносливости.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["combat-rules.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual([item["id"] for item in items], [
            "combat-rules.initiative",
            "combat-rules.movement-grid",
            "combat-rules.attack",
        ])
        self.assertEqual(items[0]["type"], "combat-rule")
        self.assertIn("stamina", items[2]["tags"])
        self.assertEqual(items[2]["modifiers"]["rule_slug"], "attack")

    def test_combat_stamina_tax_glossary_entry_gets_distinct_id(self) -> None:
        candidate = sample_candidate("combat-rules")
        candidate["source"]["page_start"] = 120
        candidate["source"]["page_end"] = 120
        candidate["raw_text"] = (
            "Потраченная Выносливость\n"
            "Выносливость, потраченная на действие.\n"
            "Налог Выносливости\n"
            "Потраченная на действие Выносливость, которая его не усиливает.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["combat-rules.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual([item["id"] for item in items], [
            "combat-rules.spent-stamina",
            "combat-rules.stamina-tax-definition",
        ])

    def test_build_draft_containers_expands_travel_rest_sections(self) -> None:
        candidate = sample_candidate("travel-rest-rules")
        candidate["source"]["page_start"] = 123
        candidate["source"]["page_end"] = 123
        candidate["raw_text"] = (
            "11.ВРЕМЯ, ОТДЫХ И ПУТЕШЕСТВИЕ\n"
            "Время\n"
            "Время отслеживается через сцены и отдых.\n"
            "Отдых\n"
            "Когда жуки останавливаются, они уходят на отдых.\n"
            "Ремесло\n"
            "Жук может совершить подходящую проверку Навыка.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["travel-rest-rules.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual([item["id"] for item in items], [
            "travel-rest-rules.time",
            "travel-rest-rules.rest",
            "travel-rest-rules.crafting",
        ])
        self.assertEqual(items[0]["type"], "travel-rest-rule")
        self.assertIn("rest", items[1]["tags"])
        self.assertIn("downtime", items[2]["tags"])

    def test_build_draft_containers_expands_social_rules(self) -> None:
        candidate = sample_candidate("social-rules")
        candidate["source"]["page_start"] = 125
        candidate["source"]["page_end"] = 125
        candidate["raw_text"] = (
            "12. ОБЩЕНИЕ\n"
            "Общение использует характеристику и подходящий навык.\n"
            "Очарование\n"
            "Сложите Привлекательность и ранг подходящего навыка, например Этичности.\n"
            "Запугивание\n"
            "Сложите Жуть и ранг Запугивания.\n"
            "Обман\n"
            "Сложите Проницательность и ранг Обмана. Цель противостоит Проницательностью или Интуицией.\n"
            "Убеждение\n"
            "Сложите Проницательность и ранг Убеждения.\n"
            "Впечатление\n"
            "Выберите Силу, Проницательность, Панцирь, Грацию, Жуть или Привлекательность и добавьте Впечатление или Исполнение.\n"
        )
        layer1 = {
            "artifact": "HK-RDB Layer 1",
            "mode_create_allowed": False,
            "candidates": [candidate],
        }

        containers, skipped = build_draft_containers(layer1)
        items = containers["social-rules.json"]["items"]

        self.assertEqual(skipped, [])
        self.assertEqual([item["id"] for item in items], [
            "social-rules.overview",
            "social-rules.charm",
            "social-rules.intimidation",
            "social-rules.deception",
            "social-rules.persuasion",
            "social-rules.impression",
        ])
        self.assertEqual(items[1]["modifiers"]["characteristics"], ["appeal"])
        self.assertTrue(items[3]["modifiers"]["opposed"])
        self.assertEqual(items[3]["modifiers"]["opposed_by"], ["insight", "Интуиция"])
        self.assertEqual(
            items[5]["modifiers"]["characteristic_options"],
            ["power", "insight", "shell", "grace", "dread", "appeal"],
        )

    def test_magic_secret_uses_page_path_hint_when_header_is_missing(self) -> None:
        candidate = sample_candidate("magic")
        candidate["source"]["page_start"] = 63
        candidate["source"]["page_end"] = 63
        candidate["raw_text"] = (
            "Подавление\n"
            "Сложность: 1\n"
            "Дальность: Касание\n"
            "Длительность: Краткая\n"
            "Метки и Ячейки Техники цели уменьшаются на 1.\n"
        )

        item = candidate_to_rule_object(candidate)

        self.assertEqual(item["id"], "magic.spire.podavlenie")
        self.assertEqual(item["requirements"][0]["value"], "spire")

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

    def test_infer_trait_relationships_supports_two_bullet_levels(self) -> None:
        raws = [
            ("Мягкое Тело", "Мягкое Тело\n+1 Голод\nОписание."),
            ("● Внешний Панцирь", "● Внешний Панцирь\n+5 Голод\nОписание."),
            ("○ Скряга", "○ Скряга\n+2 Голод\nОписание."),
            ("● Регенерация", "● Регенерация\n+5 Голод\nОписание."),
        ]
        items = []
        for title, raw in raws:
            candidate = sample_candidate("traits")
            candidate["title_hint"] = title
            candidate["raw_text"] = raw
            items.append(candidate_to_rule_object(candidate))

        infer_trait_relationships(items)

        root, external_shell, hoarder, regeneration = items
        self.assertEqual(external_shell["relationships"][0]["target"], root["id"])
        self.assertEqual(hoarder["relationships"][0]["target"], external_shell["id"])
        self.assertEqual(regeneration["relationships"][0]["target"], root["id"])
        self.assertEqual(hoarder["subtrait_depth"], 2)

    def test_infer_trait_constraints_resolves_named_conflict(self) -> None:
        no_arms = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": "Безрукий\n-10 Голод\nОписание.",
                "title_hint": "Безрукий",
            }
        )
        one_arm = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": "Одна Рука\n-4 Голод\nНе может быть взят с Безруким.",
                "title_hint": "Одна Рука",
            }
        )
        items = [no_arms, one_arm]
        infer_trait_relationships(items)
        infer_trait_constraints(items)

        conflict = next(r for r in one_arm["relationships"] if r["type"] == "conflicts_with")
        self.assertEqual(conflict["target"], no_arms["id"])

    def test_infer_trait_constraints_resolves_specific_subtrait_parent(self) -> None:
        swimming = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": "Плавание\n+2 Голод\nОписание.",
                "title_hint": "Плавание",
            }
        )
        underwater = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": "Дыхание Под Водой\n+2 Голод\nМожет быть взята как Подчерта Плавания.",
                "title_hint": "Дыхание Под Водой",
            }
        )
        items = [swimming, underwater]
        infer_trait_relationships(items)
        infer_trait_constraints(items)

        relation = next(
            r for r in underwater["relationships"] if r["type"] == "may_be_subtrait_of"
        )
        self.assertEqual(relation["target"], swimming["id"])

    def test_infer_trait_constraints_extracts_size_requirement(self) -> None:
        tiny = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": "Кроха\n+2 Голод, +1 Привлекательность должен быть Маленького размера\nОписание.",
                "title_hint": "Кроха",
            }
        )
        infer_trait_relationships([tiny])
        infer_trait_constraints([tiny])

        self.assertIn(
            {
                "type": "size",
                "operator": "equals",
                "value": "Small",
                "source_text": "должен быть Маленького размера",
                "needs_manual_review": True,
            },
            tiny["requirements"],
        )

    def test_infer_trait_constraints_extracts_venomous_bite_restrictions(self) -> None:
        bite = candidate_to_rule_object(
            {
                **sample_candidate("traits"),
                "raw_text": (
                    "Ядовитый Укус\n+3 Голод\nЭто не суммируется с другими ОУ от той же атаки. "
                    "Ядовитые укусы не могут быть парным оружием."
                ),
                "title_hint": "Ядовитый Укус",
            }
        )
        infer_trait_relationships([bite])
        infer_trait_constraints([bite])
        restriction_types = {effect["type"] for effect in bite["effects"]}

        self.assertIn("does_not_stack", restriction_types)
        self.assertIn("cannot_dual_wield", restriction_types)
        no_stack = next(effect for effect in bite["effects"] if effect["type"] == "does_not_stack")
        self.assertEqual(no_stack["with"], "другими ОУ от той же атаки")

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
