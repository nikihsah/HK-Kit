from __future__ import annotations

import unittest
from pathlib import Path

from tools.extract_layer1 import (
    build_candidates,
    choose_category_hint,
    default_output_path,
    guess_category,
    page_category_hint,
    split_page_into_blocks,
    split_rule_list_blocks,
)


class TestExtractLayer1(unittest.TestCase):
    def test_split_page_into_blocks_prefers_blank_lines(self) -> None:
        text = "First rule block.\n\nSecond rule block."
        self.assertEqual(split_page_into_blocks(text), ["First rule block.", "Second rule block."])

    def test_split_rule_list_blocks_detects_title_cost_entries(self) -> None:
        text = "\n".join(
            [
                "Раздражающие Щетинки",
                "+3 Голод, +0.5 Привлекательность",
                "Описание первой черты.",
                "Природный Снаряд",
                "+4 Голод",
                "Описание второй черты.",
            ]
        )

        blocks = split_rule_list_blocks(text)

        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0].startswith("Раздражающие Щетинки"))
        self.assertTrue(blocks[1].startswith("Природный Снаряд"))

    def test_split_rule_list_blocks_detects_split_cost_lines(self) -> None:
        text = "\n".join(
            [
                "Ядовитый Укус",
                "+3",
                "Голод, +0.5 Жуть или Привлекательность",
                "Описание укуса.",
                "Книжный Червь",
                "+1 Голод",
                "Описание червя.",
            ]
        )

        blocks = split_rule_list_blocks(text)

        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0].startswith("Ядовитый Укус"))
        self.assertTrue(blocks[1].startswith("Книжный Червь"))

    def test_split_rule_list_blocks_detects_bullet_subtraits(self) -> None:
        text = "\n".join(
            [
                "Полет",
                "+4 Голод",
                "Описание полета.",
                "● Воздушный",
                "Описание подчерты.",
            ]
        )

        blocks = split_rule_list_blocks(text)

        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[1].startswith("● Воздушный"))

    def test_split_rule_list_blocks_detects_nested_circle_subtraits(self) -> None:
        text = "\n".join(
            [
                "Мягкое Тело",
                "+1 Голод",
                "Описание.",
                "● Внешний Панцирь",
                "+5 Голод",
                "Описание подчерты.",
                "○ Скряга",
                "+2 Голод",
                "Описание вложенной подчерты.",
            ]
        )

        blocks = split_rule_list_blocks(text)

        self.assertEqual(len(blocks), 3)
        self.assertTrue(blocks[2].startswith("○ Скряга"))

    def test_guess_category_is_conservative(self) -> None:
        self.assertEqual(guess_category("Эта черта дает необычную особенность."), "traits")
        self.assertEqual(guess_category("Completely unrelated text."), "unknown")

    def test_page_category_hint_routes_traits_section(self) -> None:
        self.assertEqual(page_category_hint(7), ("core-rules", "core_rules_section_page_range"))
        self.assertEqual(page_category_hint(10), ("core-rules", "core_rules_section_page_range"))
        self.assertEqual(page_category_hint(11), ("templates", "templates_table_page_range"))
        self.assertEqual(page_category_hint(12), ("traits", "traits_section_page_range"))
        self.assertEqual(page_category_hint(21), ("traits", "traits_section_page_range"))
        self.assertEqual(page_category_hint(32), ("paths", "paths_section_page_range"))
        self.assertEqual(page_category_hint(46), ("skills", "skills_section_page_range"))
        self.assertEqual(page_category_hint(47), ("skills", "skills_section_page_range"))
        self.assertEqual(page_category_hint(48), ("advancement", "advancement_section_page_range"))
        self.assertEqual(page_category_hint(49), ("combat-arts", "combat_arts_section_page_range"))
        self.assertEqual(page_category_hint(57), ("combat-arts", "combat_arts_section_page_range"))
        self.assertEqual(page_category_hint(58), ("magic", "magic_section_page_range"))
        self.assertEqual(page_category_hint(73), ("magic", "magic_section_page_range"))
        self.assertEqual(page_category_hint(74), ("charms", "charms_section_page_range"))
        self.assertEqual(page_category_hint(87), ("charms", "charms_section_page_range"))
        self.assertEqual(page_category_hint(88), ("equipment", "equipment_section_page_range"))
        self.assertEqual(page_category_hint(116), ("equipment", "equipment_section_page_range"))
        self.assertEqual(page_category_hint(117), ("combat-rules", "combat_rules_section_page_range"))
        self.assertEqual(page_category_hint(122), ("combat-rules", "combat_rules_section_page_range"))
        self.assertEqual(page_category_hint(123), ("travel-rest-rules", "travel_rest_rules_section_page_range"))
        self.assertEqual(page_category_hint(124), ("travel-rest-rules", "travel_rest_rules_section_page_range"))
        self.assertEqual(page_category_hint(125), ("social-rules", "social_rules_section_page_range"))
        self.assertEqual(page_category_hint(126), (None, None))

    def test_choose_category_hint_prefers_template_page_context(self) -> None:
        category, source = choose_category_hint("Душа и магия рядом с таблицей шаблонов", 11)
        self.assertEqual(category, "templates")
        self.assertEqual(source, "templates_table_page_range")

    def test_choose_category_hint_keeps_front_matter_unknown(self) -> None:
        category, source = choose_category_hint("Оглавление Боевые Искусства Амулеты", 4)
        self.assertEqual(category, "unknown")
        self.assertEqual(source, "front_matter")

    def test_build_candidates_keeps_path_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 32,
                    "text": "Военные пути\nКлык\n" + ("Очень длинное описание. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "paths")
        self.assertIn("Очень длинное описание", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_skill_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 46,
                    "text": "4.Умения\nСолдат\nАтлетика\nТактика\n" + ("Описание. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "skills")
        self.assertIn("Солдат", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_advancement_page_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 48,
                    "text": "5.Продвижение\nТаблица Продвижения\n0 1 - 1\n" + ("Описание. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "advancement")
        self.assertIn("Таблица Продвижения", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_combat_art_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 50,
                    "text": "Обычные Боевые Искусства\nЗамах - Усиление\n1 Выносливость\n"
                    + ("Описание. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "combat-arts")
        self.assertIn("Замах", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_magic_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 62,
                    "text": "Тайна\nТайна Шпиля\nРассеивание\nСложность: 2\nДальность: Касание\n"
                    + ("Описание. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "magic")
        self.assertIn("Рассеивание", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_charm_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 82,
                    "text": "Боевые Амулеты\nДревняя Сила - Обычный\n⊚⊚\n"
                    + ("Описание эффекта. " * 120),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "charms")
        self.assertIn("Древняя Сила", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_equipment_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 89,
                    "text": "Оружие (1/4)\nГвоздь Гвоздь 3\nБлижний\n1Р 1 100\n"
                    + ("Атакующий может перебросить один проваленный бросок. " * 80),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "equipment")
        self.assertIn("Гвоздь", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_combat_rule_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 117,
                    "text": "10. Сражение\nПорядок Инициативы\nИнициатива определяется Грацией.\n"
                    + ("Клетки и Движение\nЖук может переместиться. " * 80),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "combat-rules")
        self.assertIn("Порядок Инициативы", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_travel_rest_pages_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 123,
                    "text": "11.ВРЕМЯ, ОТДЫХ И ПУТЕШЕСТВИЕ\nВремя\nВремя отслеживается через сцены.\n"
                    + ("Отдых\nЖуки уходят на отдых. " * 80),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "travel-rest-rules")
        self.assertIn("Время", document["candidates"][0]["raw_text"])

    def test_build_candidates_keeps_social_rule_page_whole(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {"pdf_name": "test.pdf", "pdf_sha256": "abc123"},
            "page_count": 1,
            "pages": [
                {
                    "page": 125,
                    "text": "12. ОБЩЕНИЕ\nОчарование\nПроверка Привлекательности и Этичности.\n"
                    + ("Обман\nПроверка Проницательности и Обмана. " * 80),
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["candidate_count"], 1)
        self.assertEqual(document["candidates"][0]["category_hint"], "social-rules")
        self.assertIn("Очарование", document["candidates"][0]["raw_text"])

    def test_choose_category_hint_prefers_page_context(self) -> None:
        category, source = choose_category_hint("еда, отдых, путешествие", 21)
        self.assertEqual(category, "traits")
        self.assertEqual(source, "traits_section_page_range")

    def test_build_candidates_marks_layer1_as_maintainer_only(self) -> None:
        layer0 = {
            "artifact": "HK-RDB Layer 0",
            "mode_create_allowed": False,
            "book": "Test Book",
            "source": {
                "pdf_name": "test.pdf",
                "pdf_sha256": "abc123",
            },
            "page_count": 1,
            "pages": [
                {
                    "page": 6,
                    "text": "Черта панциря.\n\nЭта черта помогает описать защиту персонажа.",
                }
            ],
        }

        document = build_candidates(layer0, min_chars=10)

        self.assertEqual(document["artifact"], "HK-RDB Layer 1")
        self.assertFalse(document["mode_create_allowed"])
        self.assertEqual(document["candidate_count"], 2)
        self.assertEqual(document["candidates"][0]["status"], "needs_review")
        self.assertEqual(document["candidates"][0]["source"]["page_start"], 6)
        self.assertEqual(document["candidates"][1]["category_hint"], "traits")
        self.assertEqual(document["candidates"][1]["category_hint_source"], "keyword")

    def test_default_output_path_replaces_layer0_suffix(self) -> None:
        output = default_output_path(Path("book.layer0.json"), Path("sources/layer1"))
        self.assertEqual(output.as_posix(), "sources/layer1/book.layer1.json")


if __name__ == "__main__":
    unittest.main()
