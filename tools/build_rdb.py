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


TEMPLATE_SIZE_BY_NAME = {
    "Мелкий Жук": "Small",
    "Средний Жук": "Medium",
    "Большой Жук": "Large",
}

TEMPLATE_ID_BY_NAME = {
    "Мелкий Жук": "templates.small-bug",
    "Средний Жук": "templates.medium-bug",
    "Большой Жук": "templates.large-bug",
}


def split_template_table_blocks(raw_text: str) -> list[str]:
    names = list(TEMPLATE_SIZE_BY_NAME)
    ranges: list[tuple[int, str]] = []
    for name in names:
        match = re.search(re.escape(name), raw_text, re.IGNORECASE)
        if match:
            ranges.append((match.start(), name))
    if not ranges:
        return [raw_text]

    ranges.sort()
    blocks: list[str] = []
    for index, (start, _name) in enumerate(ranges):
        end = ranges[index + 1][0] if index + 1 < len(ranges) else len(raw_text)
        template_tail = raw_text.find("Шаблоны", start, end)
        if template_tail != -1:
            end = template_tail
        block = raw_text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def parse_template_numbers(block: str) -> dict[str, Any]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return {}

    def numbers_after(label: str) -> list[float | int]:
        for index, line in enumerate(lines):
            if label in line and index + 1 < len(lines):
                return [parse_number(value) for value in re.findall(r"-?\d+(?:[,.]\d+)?", lines[index + 1])]
        return []

    main_values = numbers_after("Мощь Проницательность Панцирь Грация")
    resource_values = numbers_after("Сердце Выносливость Душа")
    social_values = numbers_after("Привлекательность Жуть")

    grace = main_values[3] if len(main_values) >= 4 else None
    if grace is None:
        for index, line in enumerate(lines):
            if "Сердце Выносливость Душа" in line and index + 2 < len(lines):
                maybe_grace = re.findall(r"-?\d+(?:[,.]\d+)?", lines[index + 2])
                if len(maybe_grace) == 1:
                    grace = parse_number(maybe_grace[0])

    start_hunger = None
    max_hunger = None
    speed = None
    for index, line in enumerate(lines):
        if line.startswith("Старт:"):
            match = re.search(r"-?\d+(?:[,.]\d+)?", line)
            if match:
                start_hunger = parse_number(match.group(0))
        if line.startswith("Максимум:"):
            values = [parse_number(value) for value in re.findall(r"-?\d+(?:[,.]\d+)?", line)]
            if values:
                max_hunger = values[0]
            if len(values) > 1:
                speed = values[1]
            else:
                for next_line in lines[index + 1 : index + 3]:
                    next_values = [
                        parse_number(value)
                        for value in re.findall(r"-?\d+(?:[,.]\d+)?", next_line)
                    ]
                    if next_values:
                        speed = next_values[-1]
                        break

    parsed: dict[str, Any] = {
        "characteristics": {
            "power": main_values[0] if len(main_values) > 0 else None,
            "insight": main_values[1] if len(main_values) > 1 else None,
            "shell": main_values[2] if len(main_values) > 2 else None,
            "grace": grace,
        },
        "resources": {
            "heart": resource_values[0] if len(resource_values) > 0 else None,
            "stamina": resource_values[1] if len(resource_values) > 1 else None,
            "soul": resource_values[2] if len(resource_values) > 2 else None,
        },
        "social": {
            "appeal": social_values[0] if len(social_values) > 0 else None,
            "dread": social_values[1] if len(social_values) > 1 else None,
            "bonus_to_appeal_or_dread": social_values[2] if len(social_values) > 2 else None,
        },
        "hunger": {
            "start": start_hunger,
            "maximum": max_hunger,
        },
        "speed": speed,
    }
    return parsed


def normalize_template_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    name = next((template for template in TEMPLATE_SIZE_BY_NAME if template in raw_text), item["name"])
    item["draft_id"] = item["id"]
    item["id"] = TEMPLATE_ID_BY_NAME.get(name, f"templates.{stable_name_slug(name, 'template')}")
    item["type"] = "template"
    item["subcategory"] = "Character Template"
    item["name"] = name
    item["summary"] = summarize_raw_text(raw_text)
    item["tags"] = sorted(set(item["tags"] + ["template", "character-creation"]))
    item["modifiers"] = parse_template_numbers(raw_text)
    item["modifiers"]["size"] = TEMPLATE_SIZE_BY_NAME.get(name)
    item["effects"] = [
        {
            "type": "sets_base_template",
            "size": TEMPLATE_SIZE_BY_NAME.get(name),
            "needs_manual_review": True,
        }
    ]
    return item


def template_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    objects: list[dict[str, Any]] = []
    for index, block in enumerate(split_template_table_blocks(raw_text), start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = block
        split_candidate["title_hint"] = next(
            (template for template in TEMPLATE_SIZE_BY_NAME if template in block),
            candidate.get("title_hint"),
        )
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        item = candidate_to_rule_object(split_candidate)
        objects.append(item)
    return objects


MARTIAL_PATHS = {
    "Гвоздь": "nail",
    "Игла": "needle",
    "Клык": "fang",
    "Крюк": "hook",
    "Чрево": "maw",
    "Ракушка": "shell",
    "Праща": "sling",
    "Склянка": "vial",
}

MYSTIC_PATHS = {
    "Шпиль": "spire",
    "Плащ": "cloak",
    "Грёзы": "dreams",
    "Кошмары": "nightmares",
    "Цветение": "bloom",
    "Шип": "thorn",
    "Пыль": "dust",
}

PATH_SLUGS = {**MARTIAL_PATHS, **MYSTIC_PATHS}


def extract_path_name(raw_text: str) -> str | None:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    for line in lines[:8]:
        cleaned = re.sub(r"^\d+\s*", "", line).strip()
        if cleaned in PATH_SLUGS:
            return cleaned
    for name in PATH_SLUGS:
        if re.search(rf"(^|\n)\s*{re.escape(name)}\s*(\n|$)", raw_text, re.IGNORECASE):
            return name
    return None


def path_family(path_name: str | None, raw_text: str) -> str | None:
    if path_name in MARTIAL_PATHS:
        return "Martial Path"
    if path_name in MYSTIC_PATHS:
        return "Mystic Path"
    if "Военные Пути" in raw_text or "Военные пути" in raw_text:
        return "Martial Path"
    if "Мистические Пути" in raw_text:
        return "Mystic Path"
    return None


def extract_path_rank_entries(raw_text: str) -> list[dict[str, Any]]:
    normalized = re.sub(r"[ \t]+", " ", raw_text).strip()
    pattern = re.compile(
        r"Ранг\s*(?P<rank>[123])\s*[-–]?\s*(?P<title>[^\n]+)",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(normalized))
    entries: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        rank = int(match.group("rank"))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        body = normalized[match.end() : end].strip()
        ability_names = []
        for line in body.splitlines():
            candidate = line.strip()
            if not candidate or len(candidate) > 70:
                continue
            if candidate.endswith((".", ",", ";", ":")):
                continue
            if re.search(r"\d", candidate):
                continue
            ability_names.append(candidate)
        entries.append(
            {
                "rank": rank,
                "rank_title": match.group("title").strip(),
                "ability_names": ability_names[:6],
                "text": body,
                "needs_manual_review": True,
            }
        )
    return entries


def normalize_path_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    name = extract_path_name(raw_text)
    family = path_family(name, raw_text)
    item["draft_id"] = item["id"]

    if name:
        item["id"] = f"paths.{PATH_SLUGS[name]}"
        item["type"] = "path"
        item["subcategory"] = family or "Path"
        item["name"] = name
        item["tags"] = sorted(set(item["tags"] + ["path", "character-creation"]))
        item["modifiers"] = {
            "family": family,
            "rank_max": 3,
            "rank_entries": extract_path_rank_entries(raw_text),
        }
        item["effects"] = [
            {
                "type": "path_rank_features",
                "rank_entries": extract_path_rank_entries(raw_text),
                "needs_manual_review": True,
            }
        ]
    else:
        item["id"] = "paths.overview"
        item["type"] = "path-rules"
        item["subcategory"] = "Path Overview"
        item["name"] = "Пути"
        item["tags"] = sorted(set(item["tags"] + ["path-rules", "character-creation"]))
        item["modifiers"] = {
            "starting_rank": 1,
            "rank_max": 3,
            "rank_up_grants_mark": True,
            "martial_rank_resource_increase": "stamina",
            "mystic_rank_resource_increase": "soul",
            "resource_cap": 7,
        }
        item["effects"] = [
            {
                "type": "path_advancement_rules",
                "text": raw_text,
                "needs_manual_review": True,
            }
        ]

    item["summary"] = summarize_raw_text(raw_text)
    return item


EXAMPLE_SKILL_SETS = {
    "Солдат",
    "Жрец",
    "Знать",
    "Фермер",
    "Охотник",
    "Фокусник",
    "Бандит",
}

SAMPLE_SKILL_NAMES = {
    "Этичность",
    "Интуиция",
    "Медицина",
    "Уход за снаряжением",
    "Уход за оружием",
    "Атлетика",
    "Готовка",
    "Выживание",
    "Обман",
    "Восприятие",
}


def compact_wrapped_text(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" - ", "")
    text = text.replace("- ", "")
    return text.strip()


def extract_example_skill_sets(raw_text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    sets: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        name = lines[index]
        if name in EXAMPLE_SKILL_SETS and index + 4 < len(lines):
            skills = lines[index + 1 : index + 5]
            sets.append(
                {
                    "name": name,
                    "skills": skills,
                    "source": "example",
                    "needs_manual_review": True,
                }
            )
            index += 5
            continue
        index += 1
    return sets


def normalized_skill_heading(lines: list[str], index: int) -> tuple[str | None, int]:
    line = lines[index].strip()
    if index + 1 < len(lines):
        two_line = f"{line} {lines[index + 1].strip()}"
        if two_line in SAMPLE_SKILL_NAMES:
            return two_line, index + 2
    if line in SAMPLE_SKILL_NAMES:
        return line, index + 1
    return None, index


def extract_named_text_examples(raw_text: str, names: set[str]) -> list[dict[str, Any]]:
    lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        split_inline = False
        for name in sorted(names, key=len, reverse=True):
            if line.startswith(f"{name} "):
                lines.append(name)
                lines.append(line[len(name) :].strip())
                split_inline = True
                break
        if not split_inline:
            lines.append(line)
    examples: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        name, body_start = normalized_skill_heading(lines, index)
        if not name or name not in names:
            index += 1
            continue
        body: list[str] = []
        cursor = body_start
        while cursor < len(lines):
            next_name, _next_start = normalized_skill_heading(lines, cursor)
            if next_name and next_name in names:
                break
            if lines[cursor] in {
                "Раскрытие Тайны и",
                "Сложность задачи",
                "Шкала Сложности",
                "Пример мастерства",
                "Примеры Умения",
                "Примеры навыков",
            }:
                break
            body.append(lines[cursor])
            cursor += 1
        examples.append(
            {
                "name": name,
                "text": compact_wrapped_text(body),
                "needs_manual_review": True,
            }
        )
        index = cursor
    return examples


def normalize_skill_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["type"] = "skill-rules"
    item["tags"] = sorted(set(item["tags"] + ["skills", "character-creation"]))

    if "Пример мастерства" in raw_text:
        item["id"] = "skills.mastery-and-difficulty"
        item["subcategory"] = "Skill Mastery And Difficulty"
        item["name"] = "Мастерство и сложность задач"
        item["modifiers"] = {
            "mastery_examples": extract_named_text_examples(raw_text, SAMPLE_SKILL_NAMES),
            "alternate_rank_2_option": {
                "type": "learn_secret_or_art_instead_of_skill_rank",
                "source_text": "Когда жук достигнет второго Ранга, вместо него он может изучить одну Тайну или Искусство.",
                "needs_manual_review": True,
            },
            "difficulty_scale": [
                {"label": "Простая задача", "successes": 1, "check": "4+", "needs_manual_review": True},
                {"label": "Обычная задача", "successes": 1, "needs_manual_review": True},
                {"label": "Сложная задача", "successes": 2, "needs_manual_review": True},
                {"label": "Путь боли", "successes": 3, "needs_manual_review": True},
            ],
        }
        item["effects"] = [
            {
                "type": "skill_mastery_examples_and_task_difficulty",
                "text": raw_text,
                "needs_manual_review": True,
            }
        ]
    else:
        item["id"] = "skills.overview"
        item["subcategory"] = "Skill Rules"
        item["name"] = "Умения"
        item["modifiers"] = {
            "skill_slots_per_skill_set": 4,
            "rank_max": 3,
            "duplicate_skill_rank_cap": 3,
            "example_skill_sets": extract_example_skill_sets(raw_text),
            "sample_skill_descriptions": extract_named_text_examples(
                raw_text.split("Примеры навыков", 1)[1]
                if "Примеры навыков" in raw_text
                else "",
                SAMPLE_SKILL_NAMES,
            ),
        }
        item["effects"] = [
            {
                "type": "skill_set_rules",
                "text": raw_text,
                "needs_manual_review": True,
            }
        ]

    item["summary"] = summarize_raw_text(raw_text)
    return item


def extract_advancement_milestones(raw_text: str) -> list[dict[str, Any]]:
    milestones: list[dict[str, Any]] = []
    for match in re.finditer(
        r"(?m)^\s*(?P<milestone>\d+)\s+"
        r"(?P<path_rank>\d+|-)\s+"
        r"(?P<minor>\d+|-)\s+"
        r"(?P<skill_rank>\d+|-)\s*$",
        raw_text,
    ):
        def value(token: str) -> int | None:
            return None if token == "-" else int(token)

        milestones.append(
            {
                "milestone": int(match.group("milestone")),
                "path_rank": value(match.group("path_rank")),
                "minor_advancement": value(match.group("minor")),
                "skill_rank": value(match.group("skill_rank")),
                "needs_manual_review": True,
            }
        )
    return milestones


def extract_minor_advancement_options(raw_text: str) -> list[dict[str, Any]]:
    if "Малое Продвижение" not in raw_text:
        return []
    section = raw_text.split("Малое Продвижение", 1)[1]
    options: list[dict[str, Any]] = []
    for chunk in re.split(r"\n\s*●\s*", section):
        text = compact_wrapped_text(chunk.splitlines())
        if not text or "Когда жук получает Малое Продвижение" in text:
            continue
        if text.endswith("47"):
            text = text[:-2].rstrip()
        option_type = "unclassified_minor_advancement"
        if "+0.5" in text and "Характеристик" in text:
            option_type = "increase_main_characteristic"
        elif "+1" in text and "Скорости" in text:
            option_type = "increase_speed"
        elif "+1" in text and "Нагрузке" in text:
            option_type = "increase_load"
        elif "Ячейку Техники" in text:
            option_type = "increase_technique_slots"
        elif "Качество" in text:
            option_type = "increase_natural_quality"
        elif "модификацию" in text:
            option_type = "add_natural_weapon_modification"
        elif "ограниченных Черт" in text or "Мастерства" in text:
            option_type = "increase_limited_trait_or_mastery_uses"
        options.append(
            {
                "type": option_type,
                "text": text,
                "needs_manual_review": True,
            }
        )
    return options


def normalize_advancement_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["id"] = "advancement.progression"
    item["type"] = "advancement-rules"
    item["subcategory"] = "Progression"
    item["name"] = "Продвижение"
    item["tags"] = sorted(set(item["tags"] + ["advancement", "character-creation"]))
    item["modifiers"] = {
        "milestone_table": extract_advancement_milestones(raw_text),
        "progression_pattern": {
            "even_milestones_after_zero": "skill_rank",
            "odd_milestones": "minor_advancement",
            "needs_manual_review": True,
        },
        "starting_recommendations": {
            "start_at_milestone": 2,
            "extra_art_or_secret_choice": True,
            "source_text": "Игрокам, впервые пробующим эту систему, будет проще начать со второй вехи.",
            "needs_manual_review": True,
        },
        "mystic_path_rank_grants_secret": "same_path",
        "minor_advancement_options": extract_minor_advancement_options(raw_text),
    }
    item["effects"] = [
        {
            "type": "advancement_rules",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["summary"] = summarize_raw_text(raw_text)
    return item


COMBAT_ART_TYPES = {
    "Обычное": "normal",
    "Усиление": "boost",
    "Реакция": "reaction",
    "Уникальное": "unique",
    "Особое": "special",
}


def split_combat_art_entries(raw_text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title_pattern = re.compile(
        r"^(?P<name>[А-ЯЁA-Z][^-\n]{2,80})\s+-\s+"
        r"(?P<type>Обычное|Усиление|Реакция|Уникальное|Особое)"
        r"(?:\s+или\s+(?P<alt_type>Реакция|Особое|Обычное|Усиление|Уникальное))?$",
        re.IGNORECASE,
    )
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = title_pattern.match(line)
        if match:
            starts.append((index, match))

    entries: list[dict[str, Any]] = []
    for position, (start, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        entry_lines = lines[start:end]
        cost_line = entry_lines[1] if len(entry_lines) > 1 else ""
        body_start = 2
        if (
            len(entry_lines) > 2
            and " - " in cost_line
            and re.match(r"^[а-яё]", entry_lines[2])
            and len(entry_lines[2]) <= 40
        ):
            cost_line = f"{cost_line} {entry_lines[2]}"
            body_start = 3
        body_lines = entry_lines[body_start:] if len(entry_lines) > body_start else []
        entries.append(
            {
                "name": match.group("name").strip(),
                "art_types": [
                    COMBAT_ART_TYPES.get(match.group("type"), match.group("type").casefold())
                ]
                + (
                    [COMBAT_ART_TYPES.get(match.group("alt_type"), match.group("alt_type").casefold())]
                    if match.group("alt_type")
                    else []
                ),
                "cost_line": cost_line,
                "body": "\n".join(body_lines).strip(),
                "raw_text": "\n".join(entry_lines).strip(),
            }
        )
    return entries


def parse_combat_art_costs(cost_line: str) -> dict[str, Any]:
    costs: dict[str, Any] = {"raw": cost_line}
    stamina = re.search(r"(\d+|X)\s+Выносливост\w*", cost_line, re.IGNORECASE)
    if stamina:
        value = stamina.group(1)
        costs["stamina"] = value if value == "X" else int(value)
    soul = re.search(r"(\d+|X)\s+Душ\w*", cost_line, re.IGNORECASE)
    if soul:
        value = soul.group(1)
        costs["soul"] = value if value == "X" else int(value)
    if "Концентрация" in cost_line:
        costs["focus"] = True
    return costs


def parse_combat_art_requirements(cost_line: str) -> list[dict[str, Any]]:
    if " - " not in cost_line:
        return []
    requirement_text = cost_line.split(" - ", 1)[1].strip()
    values = [part.strip() for part in re.split(r",|\s+и\s+", requirement_text) if part.strip()]
    return [
        {
            "type": "weapon_or_condition",
            "value": value,
            "needs_manual_review": True,
        }
        for value in values
    ]


def normalize_combat_art_overview(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["id"] = "combat-arts.overview"
    item["type"] = "combat-art-rules"
    item["subcategory"] = "Combat Art Rules"
    item["name"] = "Боевые Искусства"
    item["tags"] = sorted(set(item["tags"] + ["combat-arts", "character-creation"]))
    item["modifiers"] = {
        "prepared_in_technique_slots": True,
        "normally_one_art_per_turn": True,
        "types": sorted(set(COMBAT_ART_TYPES.values())),
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "combat_art_usage_rules",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["summary"] = summarize_raw_text(raw_text)
    return item


def normalize_combat_art_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    entries = split_combat_art_entries(raw_text)
    if not entries:
        return normalize_combat_art_overview(item, raw_text)
    entry = entries[0]
    item["draft_id"] = item["id"]
    item["id"] = f"combat-arts.{stable_name_slug(entry['name'], 'art')}"
    item["type"] = "combat-art"
    item["subcategory"] = "Combat Art"
    item["name"] = entry["name"]
    item["raw_text"] = entry["raw_text"]
    item["summary"] = summarize_raw_text(entry["body"] or entry["raw_text"])
    item["costs"] = parse_combat_art_costs(entry["cost_line"])
    item["requirements"] = parse_combat_art_requirements(entry["cost_line"])
    item["modifiers"] = {
        "art_types": entry["art_types"],
        "cost_line": entry["cost_line"],
    }
    item["effects"] = [
        {
            "type": "unparsed_combat_art_effect",
            "text": entry["body"],
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["combat-art", "character-creation"]))
    return item


def combat_art_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    if "6. Боевые Искусства" in raw_text:
        return [candidate_to_rule_object(candidate)]
    entries = split_combat_art_entries(raw_text)
    if not entries:
        return [candidate_to_rule_object(candidate)]

    objects: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = entry["raw_text"]
        split_candidate["title_hint"] = entry["name"]
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        objects.append(candidate_to_rule_object(split_candidate))
    return objects


MAGIC_PATHS = {
    "Тайна Шпиля": "spire",
    "Тайна Плаща": "cloak",
    "Тайна Грёз": "dreams",
    "Тайна Кошмаров": "nightmares",
    "Тайна Цветения": "bloom",
    "Тайна Шипа": "thorn",
    "Тайна Пыли": "dust",
}
MAGIC_PATHS_CASEFOLD = {name.casefold(): path for name, path in MAGIC_PATHS.items()}

MAGIC_PAGE_PATH_HINTS = [
    (62, 63, "spire"),
    (64, 64, "cloak"),
    (65, 66, "dreams"),
    (67, 67, "nightmares"),
    (68, 68, "bloom"),
    (69, 70, "thorn"),
    (71, 71, "dust"),
]


def magic_path_for_page(page: int) -> str | None:
    for start, end, path in MAGIC_PAGE_PATH_HINTS:
        if start <= page <= end:
            return path
    return None


def split_magic_entries(raw_text: str, path_hint: str | None = None) -> list[dict[str, Any]]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    current_path: str | None = path_hint
    starts: list[tuple[int, str, str | None]] = []
    for index, line in enumerate(lines):
        if line.casefold() in MAGIC_PATHS_CASEFOLD:
            current_path = MAGIC_PATHS_CASEFOLD[line.casefold()]
            continue
        if index + 1 < len(lines) and re.match(r"^Сложност[ьиmъ]*:?\s*\d+", lines[index + 1], re.IGNORECASE):
            if not line.startswith(("Тайна", "Дальность", "Длительность", "Стоимость", "Требования")):
                starts.append((index, line, current_path))

    entries: list[dict[str, Any]] = []
    for position, (start, name, path) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        entry_lines = lines[start:end]
        text = "\n".join(entry_lines)
        difficulty = re.search(r"Сложност[ьиmъ]*:?\s*(\d+)", text, re.IGNORECASE)
        range_match = re.search(r"Дал[аьъ]ност[ьиmъ]*\s*(?:[АБAB])?:?\s*([^\n]+)", text, re.IGNORECASE)
        duration = re.search(r"Дл[иu]тел[ьиmъ]*ност[ьиmъ]*:?\s*([^\n]+)", text, re.IGNORECASE)
        body_start = 1
        while body_start < len(entry_lines) and re.match(
            r"^(Сложност|Дал|Дл)", entry_lines[body_start], re.IGNORECASE
        ):
            body_start += 1
        entries.append(
            {
                "name": name,
                "path": path,
                "difficulty": int(difficulty.group(1)) if difficulty else None,
                "range": range_match.group(1).strip() if range_match else None,
                "duration": duration.group(1).strip() if duration else None,
                "body": "\n".join(entry_lines[body_start:]).strip(),
                "raw_text": text.strip(),
            }
        )
    return entries


def normalize_magic_overview(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    if "7.Магия" in raw_text:
        item["id"] = "magic.overview"
        item["name"] = "Магия"
    elif "Примеры Ритуалов" in raw_text or "Стоимость:" in raw_text:
        item["id"] = f"magic.rituals.p{item['source']['page_start']:03d}"
        item["name"] = "Примеры Ритуалов"
    elif "Сущность" in raw_text and item["source"]["page_start"] == 59:
        item["id"] = "magic.essence"
        item["name"] = "Сущность"
    else:
        item["id"] = f"magic.rules.p{item['source']['page_start']:03d}"
        item["name"] = "Правила магии"
    item["type"] = "magic-rules"
    item["subcategory"] = "Magic Rules"
    item["tags"] = sorted(set(item["tags"] + ["magic", "character-creation"]))
    item["modifiers"] = {
        "prepared_with_technique_slots": True,
        "prepared_complexity_limit": "twice_mystic_rank",
        "normally_one_spell_per_turn": True,
        "soul_cost_equals_difficulty": True,
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "magic_usage_rules",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["summary"] = summarize_raw_text(raw_text)
    return item


def normalize_spell_modification_rules(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["id"] = (
        "magic.spell-modifications"
        if "Модификации Заклинаний" in raw_text
        else "magic.spell-modifications.advanced-casting"
    )
    item["type"] = "magic-rules"
    item["subcategory"] = "Spell Modifications"
    item["name"] = "Модификации Заклинаний"
    item["tags"] = sorted(set(item["tags"] + ["magic", "spell-modifications"]))
    item["modifiers"] = {
        "range_can_be_modified": "Таблица Дальности" in raw_text,
        "damage_or_healing_can_be_increased": "Урон/Исцеление" in raw_text,
        "duration_can_be_increased": "Длительность Заклинания" in raw_text,
        "expanded_spells": "Расширенные заклинания" in raw_text,
        "quickened_spells": "Ускоренные заклинания" in raw_text,
        "conjured_spells": "Сотворенные заклинания" in raw_text,
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "spell_modification_rules",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["summary"] = summarize_raw_text(raw_text)
    return item


def normalize_magic_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    page_hint = magic_path_for_page(item["source"]["page_start"])
    entries = split_magic_entries(raw_text, page_hint)
    if not entries:
        if "Модификации Заклинаний" in raw_text or "Расширенные заклинания" in raw_text:
            return normalize_spell_modification_rules(item, raw_text)
        return normalize_magic_overview(item, raw_text)

    entry = entries[0]
    entry_path = item.pop("_magic_path", None) or entry["path"] or page_hint
    item["draft_id"] = item["id"]
    item["id"] = f"magic.{entry_path or 'unknown'}.{stable_name_slug(entry['name'], 'secret')}"
    item["type"] = "secret"
    item["subcategory"] = "Secret"
    item["name"] = entry["name"]
    item["raw_text"] = entry["raw_text"]
    item["summary"] = summarize_raw_text(entry["body"] or entry["raw_text"])
    item["costs"] = {
        "difficulty": entry["difficulty"],
        "soul": entry["difficulty"],
        "needs_manual_review": True,
    }
    item["requirements"] = (
        [
            {
                "type": "mystic_path",
                "value": entry_path,
                "needs_manual_review": True,
            }
        ]
        if entry_path
        else []
    )
    item["modifiers"] = {
        "path": entry_path,
        "difficulty": entry["difficulty"],
        "range": entry["range"],
        "duration": entry["duration"],
    }
    item["effects"] = [
        {
            "type": "unparsed_secret_effect",
            "text": entry["body"],
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["magic", "secret", "character-creation"]))
    return item


def magic_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    if "7.Магия" in raw_text or "Модификации Заклинаний" in raw_text or "Расширенные заклинания" in raw_text:
        return [candidate_to_rule_object(candidate)]
    page = int(candidate.get("source", {}).get("page_start", 0))
    entries = split_magic_entries(raw_text, magic_path_for_page(page))
    if not entries:
        return [candidate_to_rule_object(candidate)]

    objects: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = entry["raw_text"]
        split_candidate["title_hint"] = entry["name"]
        split_candidate["_magic_path"] = entry["path"]
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        objects.append(candidate_to_rule_object(split_candidate))
    return objects


CHARM_RARITIES = {
    "Обычный": "common",
    "Обычная": "common",
    "Необычный": "uncommon",
    "Необычная": "uncommon",
    "Редкий": "rare",
    "Редкая": "rare",
    "Уникальный": "unique",
    "Уникальная": "unique",
    "Легендарный": "legendary",
    "Легендарная": "legendary",
    "Проклятый": "cursed",
    "Проклятая": "cursed",
    "Хрупкий": "fragile",
    "Хрупкая": "fragile",
}

CHARM_GROUP_HEADINGS = {
    "Амулеты Смерти": "death",
    "Общие Амулеты": "general",
    "Амулеты Общения": "social",
    "Боевые Амулеты": "combat",
    "Амулеты Владения Орудием": "tool-mastery",
    "Магические Амулеты": "magic",
    "Амулеты Путей": "path",
}

CHARM_PAGE_GROUP_HINTS = [
    (75, 75, "death"),
    (76, 80, "general"),
    (81, 81, "general"),
    (82, 82, "social"),
    (83, 83, "combat"),
    (84, 84, "combat"),
    (85, 85, "magic"),
    (86, 87, "path"),
]


def charm_group_for_page(page: int) -> str | None:
    for start, end, group in CHARM_PAGE_GROUP_HINTS:
        if start <= page <= end:
            return group
    return None


def normalize_charm_lines(raw_text: str) -> list[str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    normalized: list[str] = []
    pending = ""
    for line in lines:
        if pending:
            line = f"{pending} {line}".strip()
            pending = ""
        if line.endswith("-") or line.endswith(","):
            pending = line
            continue
        normalized.append(line)
    if pending:
        normalized.append(pending)
    return normalized


def split_charm_entries(raw_text: str, group_hint: str | None = None) -> list[dict[str, Any]]:
    lines = normalize_charm_lines(raw_text)
    rarity_pattern = "|".join(sorted(CHARM_RARITIES, key=len, reverse=True))
    title_pattern = re.compile(
        rf"^(?P<name>[А-ЯЁA-Z][^⊚\n]{{2,120}}?)\s+-\s*(?P<rarity>{rarity_pattern})\.?$",
        re.IGNORECASE,
    )
    current_group = group_hint
    starts: list[tuple[int, re.Match[str] | None, str, str | None]] = []
    for index, line in enumerate(lines):
        heading = CHARM_GROUP_HEADINGS.get(line)
        if heading:
            current_group = heading
            continue
        match = title_pattern.match(line)
        if match and index + 1 < len(lines) and "⊚" in lines[index + 1]:
            starts.append((index, match, match.group("name").strip(), current_group))
            continue
        if (
            index + 1 < len(lines)
            and "⊚" in lines[index + 1]
            and re.match(r"^[А-ЯЁA-Z][^:]{2,80}$", line)
            and line not in CHARM_GROUP_HEADINGS
        ):
            starts.append((index, None, line.strip(), current_group))

    entries: list[dict[str, Any]] = []
    for position, (start, match, name, group) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        entry_lines = lines[start:end]
        notch_line = entry_lines[1] if len(entry_lines) > 1 else ""
        body_start = 2
        requirement_lines: list[str] = []
        while body_start < len(entry_lines) and (
            entry_lines[body_start].startswith("Требования:")
            or (requirement_lines and len(entry_lines[body_start]) <= 80 and not entry_lines[body_start].endswith("."))
        ):
            requirement_lines.append(entry_lines[body_start])
            body_start += 1
            if requirement_lines and body_start < len(entry_lines) and not entry_lines[body_start - 1].rstrip().endswith(("или", ",")):
                break
        rarity_raw = match.group("rarity") if match else None
        entries.append(
            {
                "name": name,
                "rarity": CHARM_RARITIES.get(rarity_raw) if rarity_raw else None,
                "rarity_raw": rarity_raw,
                "group": group,
                "notches": notch_line.count("⊚"),
                "notch_line": notch_line,
                "requirements_raw": " ".join(requirement_lines).strip(),
                "body": "\n".join(entry_lines[body_start:]).strip(),
                "raw_text": "\n".join(entry_lines).strip(),
            }
        )
    return entries


def parse_charm_requirements(requirements_raw: str) -> list[dict[str, Any]]:
    if not requirements_raw:
        return []
    text = re.sub(r"\s+", " ", requirements_raw).strip()
    requirements: list[dict[str, Any]] = [
        {
            "type": "raw_requirement",
            "text": text,
            "needs_manual_review": True,
        }
    ]
    for rank, path in re.findall(r"(\d+)\s+Ранг\s+([А-ЯЁа-яё ,]+)", text, re.IGNORECASE):
        requirements.append(
            {
                "type": "path_rank",
                "rank": int(rank),
                "path_raw": path.strip(" ."),
                "needs_manual_review": True,
            }
        )
    return requirements


def normalize_charm_overview(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["id"] = "charms.overview" if "8. Амулеты" in raw_text else f"charms.rules.p{item['source']['page_start']:03d}"
    item["type"] = "charm-rules"
    item["subcategory"] = "Charm Rules"
    item["name"] = "Амулеты" if "8. Амулеты" in raw_text else item["name"]
    item["summary"] = summarize_raw_text(raw_text)
    item["modifiers"] = {
        "rarity_prices_present": "Цена:" in raw_text,
        "overcharm_rules_present": "Переочарован" in raw_text,
        "death_charms_present": "Амулеты Смерти" in raw_text,
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "unparsed_charm_rule_text",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["charms", "character-creation"]))
    return item


def normalize_charm_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    page = int(item["source"]["page_start"])
    entries = split_charm_entries(raw_text, charm_group_for_page(page))
    if not entries:
        return normalize_charm_overview(item, raw_text)

    entry = entries[0]
    group = item.pop("_charm_group", None) or entry["group"] or charm_group_for_page(page)
    item["draft_id"] = item["id"]
    item["id"] = f"charms.{group or 'unknown'}.{stable_name_slug(entry['name'], 'charm')}"
    item["type"] = "charm"
    item["subcategory"] = "Charm"
    item["name"] = entry["name"]
    item["raw_text"] = entry["raw_text"]
    item["summary"] = summarize_raw_text(entry["body"] or entry["raw_text"])
    item["costs"] = {
        "notches": entry["notches"],
        "raw": entry["notch_line"],
        "needs_manual_review": True,
    }
    item["requirements"] = parse_charm_requirements(entry["requirements_raw"])
    item["modifiers"] = {
        "group": group,
        "rarity": entry["rarity"],
        "rarity_raw": entry["rarity_raw"],
    }
    item["effects"] = [
        {
            "type": "unparsed_charm_effect",
            "text": entry["body"],
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["charm", "character-creation"]))
    return item


def charm_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    page = int(candidate.get("source", {}).get("page_start", 0))
    entries = split_charm_entries(raw_text, charm_group_for_page(page))
    if not entries:
        return [candidate_to_rule_object(candidate)]

    objects: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = entry["raw_text"]
        split_candidate["title_hint"] = entry["name"]
        split_candidate["_charm_group"] = entry["group"]
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        objects.append(candidate_to_rule_object(split_candidate))
    return objects


EQUIPMENT_PAGE_SECTIONS = [
    (88, 88, "equipment-rules"),
    (89, 92, "weapon"),
    (93, 94, "weapon-modification"),
    (95, 95, "shield"),
    (96, 96, "shield-modification"),
    (97, 97, "armor"),
    (98, 98, "armor-modification"),
    (99, 99, "magic-focus"),
    (100, 100, "food"),
    (101, 102, "potion"),
    (103, 103, "alcohol"),
    (104, 106, "flask"),
    (107, 108, "poison"),
    (109, 111, "trap"),
    (112, 112, "tool"),
    (113, 114, "treasure"),
    (115, 116, "belt-item"),
]

EQUIPMENT_RARITIES = {
    "Обычный": "common",
    "Обычная": "common",
    "Обычное": "common",
    "Необычный": "uncommon",
    "Необычная": "uncommon",
    "Необычное": "uncommon",
    "Редкий": "rare",
    "Редкая": "rare",
    "Редкое": "rare",
    "Легендарный": "legendary",
    "Легендарная": "legendary",
    "Легендарное": "legendary",
}

EQUIPMENT_WEAPON_TYPES = [
    "Гвоздь",
    "Игла",
    "Крюк",
    "Клык",
    "Праща",
    "Природное",
]


def equipment_section_for_page(page: int) -> str | None:
    for start, end, section in EQUIPMENT_PAGE_SECTIONS:
        if start <= page <= end:
            return section
    return None


def clean_equipment_lines(raw_text: str) -> list[str]:
    ignored = {
        "Оружие Тип Урон Дальность боя Хватка Вес Цена",
        "Оружие Тип Урон Дальность боя Вес Цена",
        "Модификация Эффект Цена",
        "Щит Качество Вес Цена",
        "Броня         Максимальная Прочность   Понижение урона Вес Цена",
        "Фокусировка Тип Урон Дальность Хватка Вес Цена",
        "Еда Сытость в порции Вес порции Цена порции",
        "Зелье Редкость Крепость Цена",
        "Алкоголь Редкость Крепость Цена",
        "Склянка Редкость Восстанавливается? Цена",
        "Яд Редкость Дозы Цена",
        "Ловушка Редкость Многоразовая? Вес Цена",
        "Инструмент Навыки и применение Оружейный аналог Вес Цена",
        "Предмет Вес Цена",
        "Находка Эффекты Цена",
        "Хватка",
    }
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines()]
    return [
        line
        for line in lines
        if line
        and line not in ignored
        and not re.fullmatch(r"\d{2,3}", line)
        and not re.search(r"\(\d+/\d+\)$", line)
    ]


def parse_equipment_price(value: str) -> int | str:
    cleaned = value.strip().rstrip("!*")
    return int(cleaned) if cleaned.isdigit() else value.strip()


def parse_equipment_weight(value: str) -> int | float | str:
    cleaned = value.strip().replace(",", ".")
    if cleaned.isdigit():
        return int(cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return value.strip()


def match_equipment_window(lines: list[str], index: int, max_window: int = 4) -> tuple[re.Match[str] | None, int]:
    first_line = lines[index].strip()
    if (
        len(first_line) > 55
        or len(first_line.split()) > 10
        or "." in first_line
        or re.match(r"^[а-яё]", first_line)
        or first_line.endswith((".", ":"))
        or first_line.startswith(("+", "-", "Направленный:", "Окружение", "Окружение+", "Прием внутрь:", "Передозировка:"))
        or re.match(
            r"^(Атакующий|Атака|При |Прием|При попадании|Попытка|Может |Броски|Предел|Держа|Подготовленные|Ошеломляет|Вызывает|Также|Цель|Игнорирует|Это |Соединенная|Модификации|Качество|Владелец|Жук |Носитель|Если |Когда |Чтобы |Для |Примеры|Предмет,)",
            first_line,
            re.IGNORECASE,
        )
    ):
        return None, 0

    weapon_types = "|".join(EQUIPMENT_WEAPON_TYPES)
    weapon_pattern = re.compile(
        rf"^(?P<name>.+?) (?P<item_type>{weapon_types}(?:, ?(?:{weapon_types}))*) "
        r"(?P<damage>\d+|-) (?:(?P<range>Ближний|Дальний \(\d+\)|Досяг\.) )?"
        r"(?P<grip>[012]Р\+?) (?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) (?P<price>\d+|-)$",
        re.IGNORECASE,
    )
    shield_pattern = re.compile(
        r"^(?P<name>Щит-[А-ЯЁа-яё-]+|Панцирный щит) (?P<quality>-?\d+) "
        r"(?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) (?P<price>\d+|-)$",
        re.IGNORECASE,
    )
    armor_pattern = re.compile(
        r"^(?P<name>[А-ЯЁа-яё]+ броня) (?P<durability>\d+) (?P<damage_reduction>\d+) "
        r"(?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) (?P<price>\d+|-)$",
        re.IGNORECASE,
    )
    rarity_pattern = "|".join(sorted(EQUIPMENT_RARITIES, key=len, reverse=True))
    rarity_item_pattern = re.compile(
        rf"^(?P<name>.+?) (?P<rarity>{rarity_pattern}) "
        r"(?:(?P<reusable>Да|Нет) )?(?:(?P<potency>\d+|-) )?"
        r"(?:(?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) )?"
        r"(?P<price>\d+\*?|Бесценно!?|Только найти)$",
        re.IGNORECASE,
    )
    food_pattern = re.compile(
        r"^(?P<name>.+?) (?P<satiety>\d+|Полная) (?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) "
        r"(?P<price>\d+\*?|Бесценно!?)$",
        re.IGNORECASE,
    )
    simple_item_pattern = re.compile(
        r"^(?P<name>.+?) (?P<weight>Легкое|Легкий|\d+(?:[.,]\d+)?) (?P<price>\d+\*?|Только найти)$",
        re.IGNORECASE,
    )

    patterns = [weapon_pattern, shield_pattern, armor_pattern, rarity_item_pattern, food_pattern, simple_item_pattern]
    for size in range(1, max_window + 1):
        text = " ".join(lines[index : index + size])
        for pattern in patterns:
            match = pattern.match(text)
            if match:
                return match, size
    return None, 0


def split_equipment_entries(raw_text: str, section_hint: str | None) -> list[dict[str, Any]]:
    if section_hint == "equipment-rules":
        return []
    lines = clean_equipment_lines(raw_text)
    starts: list[tuple[int, int, re.Match[str]]] = []
    index = 0
    while index < len(lines):
        match, size = match_equipment_window(lines, index)
        if match:
            starts.append((index, size, match))
            index += max(size, 1)
        else:
            index += 1

    entries: list[dict[str, Any]] = []
    for position, (start, size, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        row_lines = lines[start : start + size]
        body_lines = lines[start + size : end]
        groups = match.groupdict()
        rarity_raw = groups.get("rarity")
        entries.append(
            {
                "name": groups.get("name", "").strip(),
                "section": section_hint,
                "raw_stats": " ".join(row_lines),
                "body": "\n".join(body_lines).strip(),
                "raw_text": "\n".join(lines[start:end]).strip(),
                "stats": {
                    key: value.strip()
                    for key, value in groups.items()
                    if key != "name" and value is not None and value.strip()
                },
                "rarity": EQUIPMENT_RARITIES.get(rarity_raw) if rarity_raw else None,
            }
        )
    return entries


def normalize_equipment_overview(item: dict[str, Any], raw_text: str, section: str | None) -> dict[str, Any]:
    item["draft_id"] = item["id"]
    item["id"] = "equipment.overview" if "9.Снаряжение" in raw_text else f"equipment.rules.p{item['source']['page_start']:03d}"
    item["type"] = "equipment-rules"
    item["subcategory"] = section or "equipment-rules"
    item["name"] = "Снаряжение" if "9.Снаряжение" in raw_text else item["name"]
    item["summary"] = summarize_raw_text(raw_text)
    item["modifiers"] = {
        "section": section,
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "unparsed_equipment_rule_text",
            "text": raw_text,
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["equipment", "character-creation"]))
    return item


def normalize_equipment_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    page = int(item["source"]["page_start"])
    section = item.pop("_equipment_section", None) or equipment_section_for_page(page)
    entries = split_equipment_entries(raw_text, section)
    if not entries:
        return normalize_equipment_overview(item, raw_text, section)

    entry = entries[0]
    stats = entry["stats"]
    item["draft_id"] = item["id"]
    item["id"] = f"equipment.{entry['section'] or 'unknown'}.{stable_name_slug(entry['name'], 'item')}"
    item["type"] = "equipment-item"
    item["subcategory"] = entry["section"] or "equipment"
    item["name"] = entry["name"]
    item["raw_text"] = entry["raw_text"]
    item["summary"] = summarize_raw_text(entry["body"] or entry["raw_text"])
    item["costs"] = {}
    if stats.get("price"):
        item["costs"]["geo"] = parse_equipment_price(stats["price"])
    item["requirements"] = []
    item["modifiers"] = {
        "section": entry["section"],
        "raw_stats": entry["raw_stats"],
        "stats": stats,
        "rarity": entry["rarity"],
    }
    if stats.get("weight"):
        item["modifiers"]["weight"] = parse_equipment_weight(stats["weight"])
    item["effects"] = [
        {
            "type": "unparsed_equipment_effect",
            "text": entry["body"],
            "needs_manual_review": True,
        }
    ]
    item["tags"] = sorted(set(item["tags"] + ["equipment", "character-creation"]))
    return item


def equipment_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    page = int(candidate.get("source", {}).get("page_start", 0))
    section = equipment_section_for_page(page)
    entries = split_equipment_entries(raw_text, section)
    if not entries:
        return [candidate_to_rule_object(candidate)]

    objects: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = entry["raw_text"]
        split_candidate["title_hint"] = entry["name"]
        split_candidate["_equipment_section"] = entry["section"]
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        objects.append(candidate_to_rule_object(split_candidate))
    return objects


COMBAT_RULE_HEADINGS = {
    "10. Сражение": ("overview", "Сражение"),
    "Порядок Инициативы": ("initiative", "Порядок Инициативы"),
    "Клетки и Движение": ("movement-grid", "Клетки и Движение"),
    "Клетки": ("spaces", "Клетки"),
    "Сжимание": ("squeezing", "Сжимание"),
    "Действия": ("actions", "Действия"),
    "Атака": ("attack", "Атака"),
    "Площадь эффекта": ("area-effects", "Площадь эффекта"),
    "Конусы": ("cones", "Конусы"),
    "Налог Выносливости": ("stamina-tax", "Налог Выносливости"),
    "Провоцированные атаки": ("provoked-attacks", "Провоцированные атаки"),
    "Отступление": ("withdraw", "Отступление"),
    "Захват": ("grapple", "Захват"),
    "Рывок и Прыжок": ("dash-jump", "Рывок и Прыжок"),
    "Удар с отскоком": ("pogo-strike", "Удар с отскоком"),
    "Действия Навыков": ("skill-actions", "Действия Навыков"),
    "Использование действий Навыков": ("skill-action-examples", "Использование действий Навыков"),
    "Малые Действия": ("minor-actions", "Малые Действия"),
    "Отсроченные ходы": ("delayed-turns", "Отсроченные ходы"),
    "Подготовка": ("prepared-actions", "Подготовка"),
    "Защита": ("defense", "Защита"),
    "Парирование": ("parry", "Парирование"),
    "Уклонение": ("dodge", "Уклонение"),
    "Глоссарий Выносливости": ("stamina-glossary", "Глоссарий Выносливости"),
    "Потраченная Выносливость": ("spent-stamina", "Потраченная Выносливость"),
    "Вложенная Выносливость": ("invested-stamina", "Вложенная Выносливость"),
    "Урон и Состояния": ("damage-and-conditions", "Урон и Состояния"),
    "Вычисление вероятного урона": ("probable-damage", "Вычисление вероятного урона"),
    "Понижение урона (ПУ)": ("damage-reduction", "Понижение урона"),
    "Впитывание урона": ("damage-absorption", "Впитывание урона"),
    "Магический урон": ("magic-damage", "Магический урон"),
    "Природный урон": ("natural-damage", "Природный урон"),
    "Урон по Выносливости и Душе": ("stamina-and-soul-damage", "Урон по Выносливости и Душе"),
    "Несмертельный урон": ("nonlethal-damage", "Несмертельный урон"),
    "Дисбаланс": ("imbalance", "Дисбаланс"),
    "Врата Смерти": ("death-gates", "Врата Смерти"),
    "Потеря сознания": ("unconsciousness", "Потеря сознания"),
    "Удушение": ("suffocation", "Удушение"),
    "Отложенный урон (ОУ)": ("delayed-damage", "Отложенный урон"),
    "Эффект состояния": ("status-effect", "Эффект состояния"),
    "Износ": ("wear", "Износ"),
    "Износ природного оружия": ("natural-weapon-wear", "Износ природного оружия"),
    "Невидимые атаки": ("invisible-attacks", "Невидимые атаки"),
    "Укрытие": ("cover", "Укрытие"),
    "Пересеченная местность": ("difficult-terrain", "Пересеченная местность"),
    "Фокусировка/Концентрация": ("focus-concentration", "Фокусировка/Концентрация"),
    "Фокусировка Души": ("soul-focus", "Фокусировка Души"),
    "Фокусировка Заклинания": ("spell-focus", "Фокусировка Заклинания"),
    "Фокусировка Припасов": ("supplies-focus", "Фокусировка Припасов"),
}


def split_combat_rule_entries(raw_text: str) -> list[dict[str, Any]]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw_text.splitlines() if line.strip()]
    starts: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        if line in COMBAT_RULE_HEADINGS:
            slug, title = COMBAT_RULE_HEADINGS[line]
            starts.append((index, slug, title))

    if not starts:
        return []

    entries: list[dict[str, Any]] = []
    for position, (start, slug, title) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        entry_lines = lines[start:end]
        body = "\n".join(entry_lines[1:]).strip()
        if not body:
            continue
        entries.append(
            {
                "slug": slug,
                "name": title,
                "body": body,
                "raw_text": "\n".join(entry_lines).strip(),
            }
        )
    return entries


def infer_combat_rule_tags(entry_slug: str, text: str) -> list[str]:
    tags = ["combat", "combat-rules", "character-creation"]
    groups = {
        "movement": ["movement-grid", "spaces", "squeezing", "dash-jump", "pogo-strike", "difficult-terrain"],
        "action-economy": ["actions", "minor-actions", "delayed-turns", "prepared-actions", "stamina-tax"],
        "attack": ["attack", "area-effects", "cones", "provoked-attacks", "grapple"],
        "defense": ["defense", "parry", "dodge", "cover", "invisible-attacks"],
        "damage": [
            "damage-and-conditions",
            "probable-damage",
            "damage-reduction",
            "damage-absorption",
            "magic-damage",
            "natural-damage",
            "stamina-and-soul-damage",
            "nonlethal-damage",
            "delayed-damage",
        ],
        "conditions": ["imbalance", "death-gates", "unconsciousness", "suffocation", "status-effect", "wear"],
        "focus": ["focus-concentration", "soul-focus", "spell-focus", "supplies-focus"],
    }
    for tag, slugs in groups.items():
        if entry_slug in slugs:
            tags.append(tag)
    if "Вынослив" in text:
        tags.append("stamina")
    if "Душ" in text:
        tags.append("soul")
    return sorted(set(tags))


def normalize_combat_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    entries = split_combat_rule_entries(raw_text)
    if not entries:
        item["draft_id"] = item["id"]
        item["id"] = f"combat-rules.rules.p{item['source']['page_start']:03d}"
        item["type"] = "combat-rule"
        item["subcategory"] = "combat-rules"
        item["summary"] = summarize_raw_text(raw_text)
        item["effects"] = [
            {
                "type": "unparsed_combat_rule_text",
                "text": raw_text,
                "needs_manual_review": True,
            }
        ]
        item["tags"] = sorted(set(item["tags"] + ["combat", "combat-rules", "character-creation"]))
        return item

    entry = entries[0]
    entry_slug = entry["slug"]
    if entry_slug == "stamina-tax" and int(item["source"]["page_start"]) == 120:
        entry_slug = "stamina-tax-definition"
    item["draft_id"] = item["id"]
    item["id"] = f"combat-rules.{entry_slug}"
    item["type"] = "combat-rule"
    item["subcategory"] = entry_slug
    item["name"] = entry["name"]
    item["raw_text"] = entry["raw_text"]
    item["summary"] = summarize_raw_text(entry["body"] or entry["raw_text"])
    item["costs"] = {}
    item["requirements"] = []
    item["modifiers"] = {
        "rule_slug": entry_slug,
        "needs_manual_review": True,
    }
    item["effects"] = [
        {
            "type": "unparsed_combat_rule_text",
            "text": entry["body"],
            "needs_manual_review": True,
        }
    ]
    item["tags"] = infer_combat_rule_tags(entry_slug, entry["raw_text"])
    return item


def combat_rule_objects_from_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw_text = candidate.get("raw_text", "")
    entries = split_combat_rule_entries(raw_text)
    if not entries:
        return [candidate_to_rule_object(candidate)]

    objects: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        split_candidate = dict(candidate)
        split_candidate["raw_text"] = entry["raw_text"]
        split_candidate["title_hint"] = entry["name"]
        split_candidate["source"] = dict(candidate.get("source", {}))
        split_candidate["source"]["layer0_block"] = (
            int(split_candidate["source"].get("layer0_block", 0)) * 100 + index
        )
        objects.append(candidate_to_rule_object(split_candidate))
    return objects


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
    if "_magic_path" in candidate:
        item["_magic_path"] = candidate["_magic_path"]
    if "_charm_group" in candidate:
        item["_charm_group"] = candidate["_charm_group"]
    if "_equipment_section" in candidate:
        item["_equipment_section"] = candidate["_equipment_section"]

    if category_hint == "traits":
        item = normalize_trait_rule_object(item, raw_text)
    elif category_hint == "templates":
        item = normalize_template_rule_object(item, raw_text)
    elif category_hint == "paths":
        item = normalize_path_rule_object(item, raw_text)
    elif category_hint == "skills":
        item = normalize_skill_rule_object(item, raw_text)
    elif category_hint == "advancement":
        item = normalize_advancement_rule_object(item, raw_text)
    elif category_hint == "combat-arts":
        item = normalize_combat_art_rule_object(item, raw_text)
    elif category_hint == "magic":
        item = normalize_magic_rule_object(item, raw_text)
    elif category_hint == "charms":
        item = normalize_charm_rule_object(item, raw_text)
    elif category_hint == "equipment":
        item = normalize_equipment_rule_object(item, raw_text)
    elif category_hint == "combat-rules":
        item = normalize_combat_rule_object(item, raw_text)

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
        if category_hint == "templates":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                template_rule_objects_from_candidate(candidate)
            )
        elif category_hint == "combat-arts":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                combat_art_rule_objects_from_candidate(candidate)
            )
        elif category_hint == "magic":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                magic_rule_objects_from_candidate(candidate)
            )
        elif category_hint == "charms":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                charm_rule_objects_from_candidate(candidate)
            )
        elif category_hint == "equipment":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                equipment_rule_objects_from_candidate(candidate)
            )
        elif category_hint == "combat-rules":
            containers[CATEGORY_TO_FILE[category_hint]]["items"].extend(
                combat_rule_objects_from_candidate(candidate)
            )
        else:
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
