#!/usr/bin/env python3
"""Build Layer 2 HK-RDB draft files from Layer 1 candidates.

This tool does not write final HK-RDB data. It writes maintainer-only draft
files under sources/layer2/ so candidates can be reviewed before final commit.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("sources") / "layer2"

CATEGORY_TO_FILE = {
    "core-rules": "core-rules.json",
    "templates": "templates.json",
    "traits": "traits.json",
    "paths": "paths.json",
    "skills": "skills.json",
    "advancement": "advancement.json",
    "combat-arts": "combat-arts.json",
    "magic": "magic.json",
    "charms": "charms.json",
    "equipment": "equipment.json",
    "combat-rules": "combat-rules.json",
    "travel-rest-rules": "travel-rest-rules.json",
    "social-rules": "social-rules.json",
    "glossary": "glossary.json",
}

FILE_TO_CATEGORY = {
    "core-rules.json": "Core Rules",
    "templates.json": "Templates",
    "traits.json": "Traits",
    "paths.json": "Paths",
    "skills.json": "Skills",
    "advancement.json": "Advancement",
    "combat-arts.json": "Combat Arts",
    "magic.json": "Magic",
    "charms.json": "Charms",
    "equipment.json": "Equipment",
    "combat-rules.json": "Combat Rules",
    "travel-rest-rules.json": "Travel And Rest Rules",
    "social-rules.json": "Social Rules",
    "glossary.json": "Glossary",
}

RU_TOKEN_MAP = {
    "активный": "active",
    "блокирующие": "blocking",
    "большой": "big",
    "быстрый": "fast",
    "выделений": "secretions",
    "выделения": "secretions",
    "выстрел": "shot",
    "выстрелы": "shots",
    "глаза": "eyes",
    "глаз": "eye",
    "жало": "sting",
    "желудок": "stomach",
    "жидкости": "fluids",
    "защитный": "defensive",
    "зрение": "vision",
    "калечащий": "crippling",
    "камуфляж": "camouflage",
    "клешни": "claws",
    "когти": "claws",
    "книжный": "book",
    "клубок": "curl",
    "кровь": "blood",
    "ли": "",
    "линька": "molt",
    "малый": "minor",
    "мелкий": "minor",
    "метка": "mark",
    "недостаток": "flaw",
    "огромные": "huge",
    "один": "one",
    "ослепительный": "dazzling",
    "ослепляющий": "blinding",
    "острые": "sharp",
    "острый": "sharp",
    "панцирь": "shell",
    "песнь": "song",
    "полет": "flight",
    "полёт": "flight",
    "природные": "natural",
    "природный": "natural",
    "руки": "arms",
    "светящийся": "glowing",
    "снаряд": "projectile",
    "спрей": "spray",
    "тяжелый": "heavy",
    "тяжёлый": "heavy",
    "укус": "bite",
    "хвост": "tail",
    "щетинки": "bristles",
    "ядовитый": "venomous",
}

TRAIT_NAME_ALIASES = {
    "безруким": "безрукий",
    "внешним панцирем": "внешний панцирь",
    "плавания": "плавание",
}

MODIFIER_TARGETS = {
    "мощь": "power",
    "мощи": "power",
    "мощью": "power",
    "грация": "grace",
    "грацию": "grace",
    "грации": "grace",
    "панцирь": "shell",
    "панциря": "shell",
    "скорость": "speed",
    "проницательность": "insight",
    "проницательности": "insight",
    "душа": "soul",
    "душу": "soul",
    "вес": "weight",
    "веса": "weight",
    "нагрузка": "load",
    "нагрузку": "load",
    "запас сердца": "heart_max",
    "максимум сердца": "heart_max",
    "максимальная нагрузка": "load_max",
    "наземная скорость": "ground_speed",
    "скорость полета": "flight_speed",
    "скорость полёта": "flight_speed",
}


def slugify(value: str, fallback: str = "entry") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value, flags=re.IGNORECASE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


def transliterate_ru_token(token: str) -> str:
    token = token.lower().replace("ё", "е")
    if token in RU_TOKEN_MAP:
        return RU_TOKEN_MAP[token]
    table = str.maketrans(
        {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "kh",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "shch",
            "ы": "y",
            "э": "e",
            "ю": "yu",
            "я": "ya",
            "ь": "",
            "ъ": "",
        }
    )
    return token.translate(table)


def stable_name_slug(name: str, fallback: str = "entry") -> str:
    cleaned = name.lower().replace("ё", "е")
    tokens = re.findall(r"[a-z0-9а-я]+", cleaned, flags=re.IGNORECASE)
    normalized = [transliterate_ru_token(token) for token in tokens]
    normalized = [token for token in normalized if token]
    return slugify("-".join(normalized), fallback)


def stable_rule_id(category_hint: str, candidate: dict[str, Any]) -> str:
    source = candidate.get("source", {})
    page = source.get("page_start", 0)
    block = source.get("layer0_block", 0)
    title = slugify(candidate.get("title_hint", ""), "candidate")
    return f"{slugify(category_hint, 'unknown')}.p{int(page):03d}.b{int(block):03d}.{title}"


def summarize_raw_text(raw_text: str, max_len: int = 240) -> str:
    text = re.sub(r"\s+", " ", raw_text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def clean_title(value: str) -> tuple[str, bool, int]:
    title = re.sub(r"\s+", " ", value).strip()
    subtrait_depth = 2 if title.startswith("○") else 1 if title.startswith("●") else 0
    is_subtrait = subtrait_depth > 0
    title = title.lstrip("●○").strip()
    return title, is_subtrait, subtrait_depth


def parse_number(value: str) -> float | int:
    number = float(value.replace(",", "."))
    return int(number) if number.is_integer() else number


def parse_trait_base_costs(cost_text: str) -> dict[str, Any]:
    costs: dict[str, Any] = {}
    normalized = re.sub(r"\s+", " ", cost_text).strip()

    hunger = re.search(r"([+-]?\d+(?:[,.]\d+)?)\s*Голод", normalized, re.IGNORECASE)
    if hunger:
        costs["hunger"] = parse_number(hunger.group(1))

    dread = re.search(r"([+-]?\d+(?:[,.]\d+)?)\s*Жут[ьиь]?", normalized, re.IGNORECASE)
    appeal = re.search(r"([+-]?\d+(?:[,.]\d+)?)\s*Привлекательност[ьи]?", normalized, re.IGNORECASE)
    both = re.search(r"([+-]?\d+(?:[,.]\d+)?)\s*Обоим", normalized, re.IGNORECASE)

    if dread:
        costs["dread"] = parse_number(dread.group(1))
    if appeal:
        costs["appeal"] = parse_number(appeal.group(1))
    if both:
        value = parse_number(both.group(1))
        costs["dread"] = value
        costs["appeal"] = value

    if "или" in normalized and ("Жут" in normalized or "Привлекательност" in normalized):
        options = []
        if dread or "Жут" in normalized:
            options.append("dread")
        if appeal or "Привлекательност" in normalized:
            options.append("appeal")
        if options:
            costs["social_cost_options"] = options
            option_value = None
            if dread:
                option_value = parse_number(dread.group(1))
            elif appeal:
                option_value = parse_number(appeal.group(1))
            if option_value is not None:
                for option in options:
                    costs.setdefault(option, option_value)

    if normalized:
        costs["raw"] = normalized

    return costs


def sentence_around(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start))
    right_candidates = [pos for pos in [text.find(".", end), text.find("\n", end)] if pos != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return re.sub(r"\s+", " ", text[left + 1 : right + 1]).strip()


def parse_trait_conditional_costs(body: str) -> list[dict[str, Any]]:
    conditional: list[dict[str, Any]] = []
    patterns = [
        re.compile(r"(?:за|получив)\s*([+-]?\d+(?:[,.]\d+)?)\s*голод[а]?", re.IGNORECASE),
    ]

    for pattern in patterns:
        for match in pattern.finditer(body):
            value = parse_number(match.group(1))
            context = sentence_around(body, match.start(), match.end())
            conditional.append(
                {
                    "when": context,
                    "costs": {
                        "hunger": value,
                    },
                    "raw": match.group(0),
                    "needs_manual_review": True,
                }
            )

    return conditional


def trait_costs(cost_text: str, body: str) -> dict[str, Any]:
    return {
        "base": parse_trait_base_costs(cost_text),
        "conditional": parse_trait_conditional_costs(body),
    }


def split_trait_parts(raw_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {
            "name": "",
            "is_subtrait": False,
            "subtrait_depth": 0,
            "cost_text": "",
            "body": "",
        }

    name, is_subtrait, subtrait_depth = clean_title(lines[0])
    cost_lines: list[str] = []
    body_start = 1

    if len(lines) > 1 and re.match(r"^\s*[+-]?\d+(?:[,.]\d+)?", lines[1]):
        cost_lines.append(lines[1])
        body_start = 2
        while body_start < min(len(lines), 5):
            next_line = lines[body_start]
            combined = " ".join(cost_lines)
            needs_term = not re.search(
                r"Голод|Жут|Привлекательност|Обоим", combined, re.IGNORECASE
            )
            is_continuation = bool(
                next_line.startswith((",", ";"))
                or re.match(r"^(Голод|Жут|Привлекательност|Обоим)\b", next_line, re.IGNORECASE)
                or combined.rstrip().lower().endswith("или")
            )
            if not needs_term and not is_continuation:
                break
            cost_lines.append(next_line)
            body_start += 1

    body = "\n".join(lines[body_start:]).strip()
    return {
        "name": name,
        "is_subtrait": is_subtrait,
        "subtrait_depth": subtrait_depth,
        "cost_text": " ".join(cost_lines).strip(),
        "body": body,
    }


def extract_trait_effect_hints(body: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", body).strip()
    hints: list[dict[str, Any]] = []

    if re.search(r"природн\w* оруж", normalized, re.IGNORECASE):
        hints.append(
            {
                "type": "natural_weapon",
                "value": True,
                "needs_manual_review": True,
            }
        )

    for match in re.finditer(
        r"(?:наносит|наносят|нанести)\s+(\d+)\s+урон", normalized, re.IGNORECASE
    ):
        hints.append(
            {
                "type": "damage",
                "amount": int(match.group(1)),
                "context": sentence_around(normalized, match.start(), match.end()),
                "needs_manual_review": True,
            }
        )

    for match in re.finditer(
        r"(?:радиус действия|дальность(?:ю)?)\s+(\d+)\s+клет", normalized, re.IGNORECASE
    ):
        hints.append(
            {
                "type": "range",
                "cells": int(match.group(1)),
                "context": sentence_around(normalized, match.start(), match.end()),
                "needs_manual_review": True,
            }
        )

    weapon_type = re.search(
        r"природн\w* оруж\w*\s+относится к типу\s+([А-Яа-яЁёA-Za-z-]+)",
        normalized,
        re.IGNORECASE,
    )
    if weapon_type:
        hints.append(
            {
                "type": "weapon_type",
                "value": weapon_type.group(1),
                "needs_manual_review": True,
            }
        )

    hints.extend(extract_trait_repeatability_hints(normalized))

    return hints


def extract_trait_repeatability_hints(body: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", body).strip()
    hints: list[dict[str, Any]] = []

    activation = re.search(
        r"активир\w*\s+(?:эту\s+)?способност\w*\s+несколько\s+раз",
        normalized,
        re.IGNORECASE,
    )
    if activation:
        context = sentence_around(normalized, activation.start(), activation.end())
        activation_hint: dict[str, Any] = {
            "type": "repeatable_activation",
            "allowed": True,
            "context": context,
            "needs_manual_review": True,
        }
        stamina_cost = re.search(
            r"тратя\s+(\d+)\s+выносливост\w*\s+за\s+каждое\s+использование",
            context,
            re.IGNORECASE,
        )
        if stamina_cost:
            activation_hint["cost_per_use"] = {
                "stamina": int(stamina_cost.group(1)),
            }
        hints.append(activation_hint)

    unlimited = re.search(
        r"(?:черту\s+можно\s+использовать|можно\s+брать|может\s+быть\s+взят[ао]?)\s+"
        r"(?:[^.]{0,45})?(?:несколько|множество)\s+раз",
        normalized,
        re.IGNORECASE,
    )
    twice = re.search(
        r"(?:эту\s+)?черту\s+можно\s+взять\s+дважды|можно\s+взять\s+дважды",
        normalized,
        re.IGNORECASE,
    )

    selection_match = unlimited or twice
    if selection_match:
        selection: dict[str, Any] = {
            "type": "repeatable_selection",
            "allowed": True,
            "max": None if unlimited else 2,
            "constraints": [],
            "context": sentence_around(
                normalized, selection_match.start(), selection_match.end()
            ),
            "needs_manual_review": True,
        }

        if re.search(r"разн\w*\s+Подчерт", normalized, re.IGNORECASE):
            selection["constraints"].append(
                {
                    "type": "different_subtraits_per_copy",
                    "value": True,
                }
            )
        if re.search(r"не\s+может\s+иметь\s+несколько\s+Подчерт", normalized, re.IGNORECASE):
            selection["constraints"].append(
                {
                    "type": "max_subtraits_per_copy",
                    "value": 1,
                }
            )
        if re.search(
            r"не\s+более\s+одного\s+раза\s+для\s+одного\s+и\s+того\s+же\s+навыка",
            normalized,
            re.IGNORECASE,
        ):
            selection["constraints"].append(
                {
                    "type": "unique_by",
                    "field": "skill",
                }
            )
        if re.search(r"как\s+подчерт\w*\s+сам\w*\s+себя", normalized, re.IGNORECASE):
            self_subtrait: dict[str, Any] = {
                "type": "self_subtrait_allowed",
                "value": True,
            }
            if re.search(r"дважды\s*,?\s+как\s+подчерт", normalized, re.IGNORECASE):
                self_subtrait["max"] = 2
            selection["constraints"].append(self_subtrait)

        hints.append(selection)

    return hints


def normalize_modifier_target(value: str) -> str | None:
    normalized = re.sub(r"\s+", " ", value).strip().casefold()
    return MODIFIER_TARGETS.get(normalized)


def modifier_is_conditional(context: str) -> bool:
    return bool(re.match(r"^(Когда|Пока|Если|Всякий раз)", context, re.IGNORECASE))


def modifier_entry(
    *, modifier_type: str, target: str, value: float | int, context: str
) -> dict[str, Any]:
    return {
        "type": modifier_type,
        "target": target,
        "value": value,
        "conditional": modifier_is_conditional(context),
        "context": context,
        "needs_manual_review": True,
    }


def extract_trait_modifiers(body: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", body).strip()
    entries: list[dict[str, Any]] = []

    target_pattern = (
        r"Проницательность|Мощь|Грацию|Грация|Панцирь|Скорость|Вес|Нагрузку|Нагрузка|"
        r"Душу|Душа|Запас Сердца|максимальная Нагрузка|Наземная скорость|скорость пол[её]та"
    )

    verb_first = re.compile(
        rf"(?P<verb>увеличьте|увеличивает|уменьшите|уменьшает)\s+(?:его\s+)?"
        rf"(?P<target>{target_pattern})\s+(?P<operator>на|до)\s+"
        rf"(?P<value>\d+(?:[,.]\d+)?)",
        re.IGNORECASE,
    )
    target_first = re.compile(
        rf"(?P<target>{target_pattern})(?:\s+этого\s+жука|\s+жука)?\s+"
        rf"(?P<verb>увеличивается|увеличен|увеличена|уменьшается|уменьшена|снижена)\s+"
        rf"(?P<operator>на|до)\s+(?P<value>\d+(?:[,.]\d+)?)",
        re.IGNORECASE,
    )

    for pattern in [verb_first, target_first]:
        for match in pattern.finditer(normalized):
            target = normalize_modifier_target(match.group("target"))
            if not target:
                continue
            value = parse_number(match.group("value"))
            verb = match.group("verb").casefold()
            operator = match.group("operator").casefold()
            if operator == "до":
                modifier_type = "set_to"
            else:
                modifier_type = "delta"
                if verb.startswith("уменьш") or verb.startswith("сниж"):
                    value = -abs(value)
            context = sentence_around(normalized, match.start(), match.end())
            entries.append(
                modifier_entry(
                    modifier_type=modifier_type,
                    target=target,
                    value=value,
                    context=context,
                )
            )

    pair_pattern = re.compile(
        rf"(?P<first>{target_pattern})\s+и\s+(?P<second>{target_pattern})\s+"
        rf"(?P<verb>увеличиваются|увеличены|уменьшаются|уменьшены)\s+на\s+"
        rf"(?P<value>\d+(?:[,.]\d+)?)",
        re.IGNORECASE,
    )
    for match in pair_pattern.finditer(normalized):
        value = parse_number(match.group("value"))
        if match.group("verb").casefold().startswith("уменьш"):
            value = -abs(value)
        context = sentence_around(normalized, match.start(), match.end())
        for target_text in [match.group("first"), match.group("second")]:
            target = normalize_modifier_target(target_text)
            if target:
                entries.append(
                    modifier_entry(
                        modifier_type="delta",
                        target=target,
                        value=value,
                        context=context,
                    )
                )

    heart_max = re.finditer(
        r"получает\s+([+-]\d+(?:[,.]\d+)?)\s+к\s+максимуму\s+Сердца",
        normalized,
        re.IGNORECASE,
    )
    for match in heart_max:
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            modifier_entry(
                modifier_type="delta",
                target="heart_max",
                value=parse_number(match.group(1)),
                context=context,
            )
        )

    equals = re.finditer(
        rf"(?P<target>{target_pattern})\s+(?:всегда\s+)?считается\s+равной\s+"
        rf"(?P<value>\d+(?:[,.]\d+)?)",
        normalized,
        re.IGNORECASE,
    )
    for match in equals:
        target = normalize_modifier_target(match.group("target"))
        if target:
            context = sentence_around(normalized, match.start(), match.end())
            entries.append(
                modifier_entry(
                    modifier_type="set_to",
                    target=target,
                    value=parse_number(match.group("value")),
                    context=context,
                )
            )

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, float | int, str]] = set()
    for entry in entries:
        key = (entry["type"], entry["target"], entry["value"], entry["context"])
        if key not in seen:
            unique.append(entry)
            seen.add(key)
    return unique


def parse_count_word(value: str) -> int:
    normalized = value.strip().casefold()
    words = {
        "один": 1,
        "одна": 1,
        "два": 2,
        "две": 2,
        "три": 3,
    }
    return words.get(normalized, int(normalized) if normalized.isdigit() else 0)


def roll_modifier_entry(
    *, modifier_type: str, value: int, target: str, context: str
) -> dict[str, Any]:
    return {
        "type": modifier_type,
        "value": value,
        "target": re.sub(r"\s+", " ", target).strip(" .,"),
        "conditional": modifier_is_conditional(context),
        "context": context,
        "needs_manual_review": True,
    }


def extract_trait_roll_modifiers(body: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", body).strip()
    entries: list[dict[str, Any]] = []

    dice_pattern = re.compile(
        r"(?P<value>[+-]\d+)\s+(?:бонус\s+)?кубик(?:а|ов)?\s+"
        r"(?:к|ко|на)\s+(?P<target>[^.,]+)",
        re.IGNORECASE,
    )
    for match in dice_pattern.finditer(normalized):
        value = int(match.group("value"))
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            roll_modifier_entry(
                modifier_type="dice_bonus" if value > 0 else "dice_penalty",
                value=value,
                target=match.group("target"),
                context=context,
            )
        )

    bare_penalty = re.compile(
        r"(?:со\s+)?штраф(?:ом)?\s+(-\d+)\s+кубик(?:а|ов)?\b(?!\s+(?:к|ко|на))",
        re.IGNORECASE,
    )
    for match in bare_penalty.finditer(normalized):
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            roll_modifier_entry(
                modifier_type="dice_penalty",
                value=int(match.group(1)),
                target="use_context",
                context=context,
            )
        )

    hit_bonus = re.compile(
        r"(?P<value>[+-]\d+)\s+кубик(?:а|ов)?,?\s+чтобы\s+(?P<target>[^.]+)",
        re.IGNORECASE,
    )
    for match in hit_bonus.finditer(normalized):
        value = int(match.group("value"))
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            roll_modifier_entry(
                modifier_type="dice_bonus" if value > 0 else "dice_penalty",
                value=value,
                target=match.group("target"),
                context=context,
            )
        )

    reroll_patterns = [
        re.compile(
            r"(?P<value>[+-]\d+)\s+переброс(?:а|ов)?\s+(?:к|ко|на)\s+(?P<target>[^.,]+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?P<value>[+-]\d+)\s+(?:к\s+)?(?:повторн\w+\s+брос(?:ок|ка)|перебросу)\s+"
            r"(?:к|ко|на)\s+(?P<target>[^.,]+)",
            re.IGNORECASE,
        ),
    ]
    for pattern in reroll_patterns:
        for match in pattern.finditer(normalized):
            context = sentence_around(normalized, match.start(), match.end())
            entries.append(
                roll_modifier_entry(
                    modifier_type="reroll_bonus",
                    value=int(match.group("value")),
                    target=match.group("target"),
                    context=context,
                )
            )

    automatic_success = re.compile(
        r"(?P<count>один|одна|два|две|три|\d+)\s+(?:из\s+[^.]{0,35}\s+)?"
        r"кубик(?:а|ов)?\s+автоматически\s+"
        r"(?:становится|становятся|считается|считаются)\s+успешн\w*",
        re.IGNORECASE,
    )
    for match in automatic_success.finditer(normalized):
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            {
                "type": "automatic_success",
                "count": parse_count_word(match.group("count")),
                "target": "roll_described_in_context",
                "conditional": modifier_is_conditional(context),
                "context": context,
                "needs_manual_review": True,
            }
        )

    no_roll = re.finditer(
        r"не\s+(?:должен|нужно)\s+(?:бросать|кидать)\s+кубик[^.]*",
        normalized,
        re.IGNORECASE,
    )
    for match in no_roll:
        context = sentence_around(normalized, match.start(), match.end())
        entries.append(
            {
                "type": "roll_not_required",
                "target": match.group(0).strip(),
                "conditional": modifier_is_conditional(context),
                "context": context,
                "needs_manual_review": True,
            }
        )

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        key = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            unique.append(entry)
            seen.add(key)
    return unique


def normalize_resource_name(value: str) -> str | None:
    normalized = value.casefold()
    if normalized.startswith("выносливост"):
        return "stamina"
    if normalized.startswith("душ"):
        if "слав" in normalized:
            return "glory_soul"
        return "soul"
    if normalized.startswith("сытост"):
        return "satiety"
    if normalized.startswith("серд"):
        return "heart"
    if normalized.startswith("прочност"):
        return "durability"
    return None


def extract_trait_resource_usage_hints(body: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"\s+", " ", body).strip()
    hints: list[dict[str, Any]] = []

    numeric_cost = re.compile(
        r"(?:потратить|потратив|тратя|за)\s+(\d+)\s+"
        r"(?:единиц[уы]?\s+|очк[ао]?\s+)?"
        r"(Выносливост\w*|Душ\w*|Сытост\w*)",
        re.IGNORECASE,
    )
    for match in numeric_cost.finditer(normalized):
        resource = normalize_resource_name(match.group(2))
        if resource:
            context = sentence_around(normalized, match.start(), match.end())
            hints.append(
                {
                    "type": "resource_cost",
                    "resource": resource,
                    "amount": int(match.group(1)),
                    "context": context,
                    "needs_manual_review": True,
                }
            )

    variable_cost = re.compile(
        r"(?:потратить|потратив)\s+(Выносливост\w*|Душ\w*|Сытост\w*)\s*,?\s*"
        r"равн\w+\s+([^.,]+)",
        re.IGNORECASE,
    )
    for match in variable_cost.finditer(normalized):
        resource = normalize_resource_name(match.group(1))
        if resource:
            context = sentence_around(normalized, match.start(), match.end())
            hints.append(
                {
                    "type": "resource_cost",
                    "resource": resource,
                    "amount_expression": match.group(2).strip(),
                    "context": context,
                    "needs_manual_review": True,
                }
            )

    resource_change = re.compile(
        r"(?P<verb>получает|восстанавливает|восстанавливают|исцеляет|теряет)\s+"
        r"(?P<amount>\d+)\s+(?:единиц[уы]?\s+|очк[ао]?\s+|дополнительн\w+\s+)?"
        r"(?P<resource>Сытост\w*|Душ\w*(?:\s+Славы)?|Серд\w*|Прочност\w*)",
        re.IGNORECASE,
    )
    for match in resource_change.finditer(normalized):
        resource = normalize_resource_name(match.group("resource"))
        if not resource:
            continue
        verb = match.group("verb").casefold()
        hint_type = "resource_loss" if verb == "теряет" else "resource_restore"
        if verb == "получает":
            hint_type = "resource_gain"
        context = sentence_around(normalized, match.start(), match.end())
        clause_start = max(
            normalized.rfind(".", 0, match.start()),
            normalized.rfind(",", 0, match.start()),
        )
        local_subject = normalized[clause_start + 1 : match.start()]
        subject = "target" if re.search(r"жертва", local_subject, re.IGNORECASE) else "self"
        hints.append(
            {
                "type": hint_type,
                "resource": resource,
                "amount": int(match.group("amount")),
                "subject": subject,
                "conditional": modifier_is_conditional(context),
                "context": context,
                "needs_manual_review": True,
            }
        )

    extra_heart = re.finditer(
        r"восстанавлива\w+\s+дополнительн\w+\s+Сердце", normalized, re.IGNORECASE
    )
    for match in extra_heart:
        context = sentence_around(normalized, match.start(), match.end())
        hints.append(
            {
                "type": "resource_restore",
                "resource": "heart",
                "amount": 1,
                "timing": "per_rest" if re.search(r"кажд\w+\s+отдых", context, re.IGNORECASE) else None,
                "context": context,
                "needs_manual_review": True,
            }
        )

    usage_patterns = [
        (r"один\s+раз\s+за\s+ход", "turn"),
        (r"первый\s+раз\s+за\s+ход", "turn"),
        (r"один\s+раз\s+за\s+раунд", "round"),
        (r"один\s+раз\s+за\s+способност\w*", "ability"),
    ]
    for pattern, period in usage_patterns:
        for match in re.finditer(pattern, normalized, re.IGNORECASE):
            context = sentence_around(normalized, match.start(), match.end())
            hints.append(
                {
                    "type": "usage_limit",
                    "max_uses": 1,
                    "period": period,
                    "context": context,
                    "needs_manual_review": True,
                }
            )

    timing_patterns = [
        (r"после\s+отдыха", "after_rest"),
        (r"во\s+время\s+отдыха", "during_rest"),
        (r"кажд\w+\s+отдых", "per_rest"),
        (r"за\s+каждый\s+Отдых", "per_rest"),
    ]
    for pattern, timing in timing_patterns:
        for match in re.finditer(pattern, normalized, re.IGNORECASE):
            context = sentence_around(normalized, match.start(), match.end())
            hints.append(
                {
                    "type": "timing",
                    "value": timing,
                    "context": context,
                    "needs_manual_review": True,
                }
            )

    capacity = re.finditer(
        r"до\s+(\d+)\s+дополнительн\w+\s+Сытост\w*", normalized, re.IGNORECASE
    )
    for match in capacity:
        context = sentence_around(normalized, match.start(), match.end())
        hints.append(
            {
                "type": "resource_capacity",
                "resource": "satiety",
                "additional": int(match.group(1)),
                "context": context,
                "needs_manual_review": True,
            }
        )

    exchange = re.search(
        r"(\d+)\s+Сытост\w*\s+за\s+кажд\w+\s+потраченн\w+\s+Выносливост\w*",
        normalized,
        re.IGNORECASE,
    )
    if exchange:
        context = sentence_around(normalized, exchange.start(), exchange.end())
        hints.append(
            {
                "type": "resource_exchange",
                "from": {"resource": "satiety", "amount": int(exchange.group(1))},
                "to": {"resource": "stamina", "amount": 1},
                "context": context,
                "needs_manual_review": True,
            }
        )

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hint in hints:
        key = json.dumps(hint, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            unique.append(hint)
            seen.add(key)
    return unique


def normalize_trait_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    parts = split_trait_parts(raw_text)
    tags = list(item["tags"])
    if "trait" not in tags:
        tags.append("trait")
    if parts["is_subtrait"] and "subtrait" not in tags:
        tags.append("subtrait")

    item["name"] = parts["name"] or item["name"]
    item["subcategory"] = "Subtrait" if parts["is_subtrait"] else "Trait"
    item["subtrait_depth"] = parts["subtrait_depth"]
    item["costs"] = trait_costs(parts["cost_text"], parts["body"])
    item["summary"] = summarize_raw_text(parts["body"] or raw_text)
    item["effects"] = [
        {
            "type": "unparsed_effect_text",
            "text": parts["body"] or raw_text,
            "needs_manual_review": True,
        }
    ] + extract_trait_effect_hints(parts["body"] or raw_text) + extract_trait_resource_usage_hints(
        parts["body"] or raw_text
    )
    item["modifiers"] = {
        "entries": extract_trait_modifiers(parts["body"] or raw_text)
        + extract_trait_roll_modifiers(parts["body"] or raw_text),
    }
    item["tags"] = tags
    return item


def unique_id(base_id: str, used_ids: set[str]) -> str:
    candidate = base_id
    counter = 2
    while candidate in used_ids:
        candidate = f"{base_id}-{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate


def infer_trait_relationships(items: list[dict[str, Any]]) -> None:
    current_root_id: str | None = None
    current_root_slug: str | None = None
    current_level_one_id: str | None = None
    current_level_one_slug: str | None = None
    used_ids: set[str] = set()
    for item in items:
        original_id = item.get("id")
        if original_id:
            item.setdefault("draft_id", original_id)

        if item.get("subcategory") == "Trait":
            base_id = f"traits.{stable_name_slug(item.get('name', ''), 'trait')}"
            item["id"] = unique_id(base_id, used_ids)
            current_root_id = item.get("id")
            current_root_slug = current_root_id.removeprefix("traits.")
            current_level_one_id = None
            current_level_one_slug = None
            continue
        if item.get("subcategory") != "Subtrait" or not current_root_id:
            continue
        depth = int(item.get("subtrait_depth", 1))
        parent_id = current_root_id
        parent_slug = current_root_slug
        if depth >= 2 and current_level_one_id:
            parent_id = current_level_one_id
            parent_slug = current_level_one_slug
        subtrait_slug = stable_name_slug(item.get("name", ""), "subtrait")
        base_id = f"traits.{parent_slug}.{subtrait_slug}" if parent_slug else f"traits.{subtrait_slug}"
        item["id"] = unique_id(base_id, used_ids)
        if depth == 1:
            current_level_one_id = item["id"]
            current_level_one_slug = item["id"].removeprefix("traits.")
        relationships = item.setdefault("relationships", [])
        if not any(
            relationship.get("type") == "subtrait_of"
            and relationship.get("target") == parent_id
            for relationship in relationships
            if isinstance(relationship, dict)
        ):
            relationships.append(
                {
                    "type": "subtrait_of",
                    "target": parent_id,
                    "inferred": True,
                    "needs_manual_review": True,
                }
            )


def trait_body(item: dict[str, Any]) -> str:
    for effect in item.get("effects", []):
        if effect.get("type") == "unparsed_effect_text":
            return str(effect.get("text", ""))
    return ""


def resolve_trait_target(name: str, name_map: dict[str, str]) -> str | None:
    normalized = re.sub(r"\s+", " ", name).strip(" .,").casefold()
    normalized = TRAIT_NAME_ALIASES.get(normalized, normalized)
    return name_map.get(normalized)


def append_relationship(
    item: dict[str, Any], relationship_type: str, target: str, source_text: str
) -> None:
    relationships = item.setdefault("relationships", [])
    if any(
        relationship.get("type") == relationship_type
        and relationship.get("target") == target
        for relationship in relationships
        if isinstance(relationship, dict)
    ):
        return
    relationships.append(
        {
            "type": relationship_type,
            "target": target,
            "source_text": source_text,
            "inferred": True,
            "needs_manual_review": True,
        }
    )


def infer_trait_constraints(items: list[dict[str, Any]]) -> None:
    name_map = {
        re.sub(r"\s+", " ", item.get("name", "")).strip().casefold(): item["id"]
        for item in items
        if item.get("name") and item.get("id")
    }

    for item in items:
        body = re.sub(r"\s+", " ", item.get("raw_text", "")).strip()
        if not body:
            continue

        for pattern, relationship_type in [
            (
                r"не\s+может\s+быть\s+взят[ао]?\s+с\s+([А-ЯЁ][А-Яа-яЁё -]+?)(?=\s+Если\b|\.|$)",
                "conflicts_with",
            ),
            (
                r"несовместим[ао]?\s+с\s+([А-ЯЁ][А-Яа-яЁё -]+?)(?=\s+Если\b|\.|$)",
                "conflicts_with",
            ),
            (r"если\s+у\s+[^.]{0,80}?есть\s+черта\s+([А-ЯЁ][А-Яа-яЁё -]+)", "synergy_with"),
        ]:
            match = re.search(pattern, body, re.IGNORECASE)
            if not match:
                continue
            source_text = sentence_around(body, match.start(), match.end())
            target = resolve_trait_target(match.group(1), name_map)
            if target:
                append_relationship(item, relationship_type, target, source_text)

        parent_match = re.search(
            r"может\s+быть\s+взят[ао]?\s+как\s+Подчерт[ауы]\s+([А-ЯЁ][А-Яа-яЁё -]+)",
            body,
            re.IGNORECASE,
        )
        if parent_match:
            source_text = sentence_around(body, parent_match.start(), parent_match.end())
            target = resolve_trait_target(parent_match.group(1), name_map)
            if target:
                append_relationship(item, "may_be_subtrait_of", target, source_text)

        if re.search(r"как\s+подчерт\w*\s+любой\s+другой\s+черты", body, re.IGNORECASE):
            item.setdefault("requirements", []).append(
                {
                    "type": "subtrait_parent_scope",
                    "scope": "any_trait",
                    "needs_manual_review": True,
                }
            )

        if re.search(
            r"как\s+подчерт\w*\s+природного\s+оружия\s+для\s+атаки\s+укусом",
            body,
            re.IGNORECASE,
        ):
            item.setdefault("requirements", []).append(
                {
                    "type": "subtrait_parent_scope",
                    "scope": "natural_weapon",
                    "weapon_form": "bite",
                    "needs_manual_review": True,
                }
            )

        size_match = re.search(
            r"должен\s+быть\s+Маленького\s+размера", body, re.IGNORECASE
        )
        if size_match:
            item.setdefault("requirements", []).append(
                {
                    "type": "size",
                    "operator": "equals",
                    "value": "Small",
                    "source_text": size_match.group(0),
                    "needs_manual_review": True,
                }
            )

        restrictions: list[dict[str, Any]] = []
        if re.search(r"не\s+могут\s+быть\s+парным\s+оружием", body, re.IGNORECASE):
            restrictions.append(
                {
                    "type": "cannot_dual_wield",
                    "value": True,
                    "needs_manual_review": True,
                }
            )
        no_stack = re.search(r"не\s+суммируется\s+с\s+([^.,]+)", body, re.IGNORECASE)
        if no_stack:
            restrictions.append(
                {
                    "type": "does_not_stack",
                    "with": no_stack.group(1).strip(),
                    "needs_manual_review": True,
                }
            )
        item.setdefault("effects", []).extend(restrictions)


def candidate_to_rule_object(candidate: dict[str, Any]) -> dict[str, Any]:
    category_hint = candidate.get("category_hint", "unknown")
    file_name = CATEGORY_TO_FILE[category_hint]
    category = FILE_TO_CATEGORY[file_name]
    source = candidate.get("source", {})
    raw_text = candidate.get("raw_text", "")

    item = {
        "id": stable_rule_id(category_hint, candidate),
        "type": category_hint,
        "category": category,
        "subcategory": "",
        "name": candidate.get("title_hint") or stable_rule_id(category_hint, candidate),
        "raw_text": raw_text,
        "summary": summarize_raw_text(raw_text),
        "costs": {},
        "requirements": [],
        "effects": [],
        "modifiers": {},
        "relationships": [],
        "tags": ["layer2-draft", "needs-review"],
        "source": {
            "book": source.get("book", ""),
            "page_start": int(source.get("page_start", 0)),
            "page_end": int(source.get("page_end", 0)),
        },
        "needs_manual_review": True,
    }

    if category_hint == "traits":
        item = normalize_trait_rule_object(item, raw_text)

    return item


def empty_container(file_name: str) -> dict[str, Any]:
    return {
        "category": FILE_TO_CATEGORY[file_name],
        "file": file_name,
        "complete": False,
        "items": [],
        "draft_metadata": {
            "artifact": "HK-RDB Layer 2 Draft",
            "mode_create_allowed": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def build_draft_containers(layer1: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    containers = {file_name: empty_container(file_name) for file_name in FILE_TO_CATEGORY}
    skipped: list[dict[str, Any]] = []

    for candidate in layer1.get("candidates", []):
        category_hint = candidate.get("category_hint", "unknown")
        if category_hint not in CATEGORY_TO_FILE:
            skipped.append(
                {
                    "id": candidate.get("id"),
                    "category_hint": category_hint,
                    "reason": "unknown_or_unsupported_category_hint",
                }
            )
            continue
        containers[CATEGORY_TO_FILE[category_hint]]["items"].append(
            candidate_to_rule_object(candidate)
        )

    infer_trait_relationships(containers["traits.json"]["items"])
    infer_trait_constraints(containers["traits.json"]["items"])

    return containers, skipped


def load_layer1(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("artifact") != "HK-RDB Layer 1":
        raise ValueError("input is not an HK-RDB Layer 1 artifact")
    if data.get("mode_create_allowed") is not False:
        raise ValueError("Layer 1 artifact must declare mode_create_allowed: false")
    return data


def write_drafts(
    *,
    layer1_path: Path,
    containers: dict[str, dict[str, Any]],
    skipped: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    base_name = layer1_path.name
    if base_name.endswith(".layer1.json"):
        base_name = base_name[: -len(".layer1.json")]
    else:
        base_name = layer1_path.stem

    draft_root = output_dir / f"{base_name}.rdb-draft"
    data_dir = draft_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    written_files = []
    for file_name, container in sorted(containers.items()):
        output_path = data_dir / file_name
        output_path.write_text(
            json.dumps(container, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written_files.append(str(output_path))

    manifest = {
        "artifact": "HK-RDB Layer 2 Draft",
        "mode_create_allowed": False,
        "source_layer": "Layer 1",
        "source_layer1": str(layer1_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "written_files": written_files,
        "skipped_candidates": skipped,
        "policy": "Draft files are maintainer-only. Do not copy into HK-RDB/data without review.",
    }
    manifest_path = draft_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build maintainer-only HK-RDB draft files from Layer 1 candidates."
    )
    parser.add_argument("--layer1", required=True, type=Path, help="Path to Layer 1 JSON.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory. Defaults to sources/layer2/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    layer1_path = args.layer1.resolve()
    if not layer1_path.exists():
        print(f"Layer 1 file not found: {layer1_path}")
        return 1

    try:
        layer1 = load_layer1(layer1_path)
        containers, skipped = build_draft_containers(layer1)
        manifest = write_drafts(
            layer1_path=layer1_path,
            containers=containers,
            skipped=skipped,
            output_dir=args.out_dir,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid Layer 1 input: {exc}")
        return 1

    counts = {
        file_name: len(container["items"])
        for file_name, container in sorted(containers.items())
        if container["items"]
    }
    print(
        json.dumps(
            {
                "draft_root": str(Path(manifest["written_files"][0]).parents[1])
                if manifest["written_files"]
                else None,
                "item_counts": counts,
                "skipped_count": len(skipped),
                "mode_create_allowed": manifest["mode_create_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
