#!/usr/bin/env python3
"""Overlay the latest audited character data onto the official PDF template."""

from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "character-sheet" / "hollow-knight-rpg-bug-sheet.pdf"
DEFAULT_OUTPUT = ROOT / "output" / "pdf"


def safe_name(value: str) -> str:
    value = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip("-._")
    return value or "character"


def register_font() -> str:
    candidates = [Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/times.ttf")]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("HKSheet", str(path)))
            return "HKSheet"
    return "Helvetica"


def text(c: canvas.Canvas, font: str, value: Any, x: float, y: float, size: float = 22, max_chars: int = 55) -> None:
    rendered = str(value if value is not None else "")
    if len(rendered) > max_chars:
        rendered = rendered[: max_chars - 1].rstrip() + "..."
    c.setFont(font, size)
    c.drawString(x, y, rendered)


def lines(c: canvas.Canvas, font: str, values: list[Any], x: float, y: float, step: float, size: float = 18, limit: int | None = None) -> list[Any]:
    shown = values if limit is None else values[:limit]
    for index, value in enumerate(shown):
        text(c, font, value, x, y - index * step, size=size)
    return values[len(shown):]


def page_overlay(width: float, height: float, draw) -> PdfReader:
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=(width, height))
    draw(c)
    c.save()
    stream.seek(0)
    return PdfReader(stream)


def fill_page_one(c: canvas.Canvas, font: str, data: dict[str, Any], overflow: list[str]) -> None:
    text(c, font, data.get("name"), 335, 2255, 30)
    text(c, font, data.get("player"), 1490, 2255, 26)
    text(c, font, data.get("milestone"), 950, 2320, 22)
    text(c, font, data.get("size"), 1090, 2315, 18)
    characteristics = data.get("characteristics", {})
    for key, xy in {"power": (935, 2100), "insight": (935, 1905), "shell": (935, 1700), "grace": (935, 1500)}.items():
        text(c, font, characteristics.get(key), *xy, 24)
    resources = data.get("resources", {})
    for key, xy in {"heart": (1115, 2000), "soul": (1390, 2000), "stamina": (1665, 2000)}.items():
        value = resources.get(key, {})
        text(c, font, f"{value.get('current','')}/{value.get('maximum','')}", *xy, 20)
    social = data.get("social", {})
    text(c, font, social.get("appeal"), 1080, 1580, 20)
    text(c, font, social.get("dread"), 1215, 1580, 20)
    text(c, font, data.get("speed"), 1420, 1580, 20)
    text(c, font, data.get("maneuver"), 1585, 1580, 20)
    satiety = data.get("satiety", {})
    text(c, font, f"{satiety.get('current','')}/{satiety.get('maximum','')}", 1780, 1580, 18)
    text(c, font, data.get("description"), 105, 1390, 17, 105)
    paths = [f"{item.get('name')} (Ранг {item.get('rank')})" for item in data.get("paths", [])]
    overflow.extend(f"Путь: {value}" for value in lines(c, font, paths, 1090, 1390, 80, 18, 6))
    traits = [f"{item.get('name')} [{item.get('id','')}]" for item in data.get("traits", [])]
    overflow.extend(f"Черта: {value}" for value in lines(c, font, traits, 115, 800, 68, 17, 10))
    charms = [f"{item.get('name')} [{item.get('id','')}]" for item in data.get("charms", [])]
    overflow.extend(f"Амулет: {value}" for value in lines(c, font, charms, 1090, 720, 78, 17, 8))


def fill_page_two(c: canvas.Canvas, font: str, data: dict[str, Any], overflow: list[str]) -> None:
    equipment = [f"{item.get('name')} ({item.get('weight','-')})" for item in data.get("equipment", [])]
    overflow.extend(f"Снаряжение: {value}" for value in lines(c, font, equipment, 115, 2190, 86, 17, 10))
    techniques = [f"{item.get('name')} [{item.get('id','')}]" for item in data.get("techniques", [])]
    overflow.extend(f"Техника: {value}" for value in lines(c, font, techniques, 815, 2190, 86, 17, 9))
    weapons = [f"{item.get('name')} | урон {item.get('damage','-')} | вес {item.get('weight','-')}" for item in data.get("weapons", [])]
    overflow.extend(f"Оружие: {value}" for value in lines(c, font, weapons, 110, 1260, 170, 17, 5))
    armor = data.get("armor") or {}
    text(c, font, armor.get("name"), 110, 310, 18)
    text(c, font, armor.get("weight"), 710, 370, 18)
    text(c, font, data.get("currency"), 160, 135, 18)
    load = data.get("load", {})
    text(c, font, f"{load.get('current','')}/{load.get('maximum','')}", 700, 135, 18)
    skill_instances = data.get("skill_instances", [])
    y = 1260
    for instance in skill_instances[:3]:
        text(c, font, f"{instance.get('name')} (Ранг {instance.get('rank')})", 1170, y, 18)
        lines(c, font, instance.get("skills", []), 1180, y - 48, 42, 15, 4)
        y -= 420
    for instance in skill_instances[3:]:
        overflow.append(f"Умение: {instance.get('name')} (Ранг {instance.get('rank')}): {', '.join(instance.get('skills', []))}")


def fill_page_three(c: canvas.Canvas, font: str, data: dict[str, Any], overflow: list[str]) -> None:
    notes = list(data.get("notes", [])) + overflow
    notes.append(f"Версия персонажа: {data.get('character_version')}")
    notes.append(f"Аудит: {data.get('audit_status')}")
    lines(c, font, notes, 120, 2220, 58, 17, 34)


def fill_sheet(data: dict[str, Any], output: Path, template: Path = TEMPLATE) -> Path:
    if data.get("audit_status") != "pass":
        raise ValueError("character sheet requires the latest Rules Audit status 'pass'")
    if not template.exists():
        raise FileNotFoundError(f"official template not found: {template}")
    reader = PdfReader(str(template))
    if len(reader.pages) != 3:
        raise ValueError("official character sheet must contain exactly three pages")
    font = register_font()
    overflow: list[str] = []
    drawers = [
        lambda c: fill_page_one(c, font, data, overflow),
        lambda c: fill_page_two(c, font, data, overflow),
        lambda c: fill_page_three(c, font, data, overflow),
    ]
    writer = PdfWriter(clone_from=str(template))
    for page, draw in zip(writer.pages, drawers):
        overlay = page_overlay(float(page.mediabox.width), float(page.mediabox.height), draw)
        page.merge_page(overlay.pages[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.character_json.read_text(encoding="utf-8"))
    output = args.output or DEFAULT_OUTPUT / f"{safe_name(str(data.get('name', 'character')))}-character-sheet.pdf"
    print(fill_sheet(data, output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
