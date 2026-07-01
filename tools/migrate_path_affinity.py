#!/usr/bin/env python3
"""Migrate canonical Secrets and Combat Arts to explicit path affinity."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "HK-RDB" / "data"

SECRET_ID_MIGRATIONS = {
    "magic.dreams.pozhiratel-snov": "magic.nightmares.pozhiratel-snov",
    "magic.dreams.vostorg": "magic.nightmares.vostorg",
    "magic.dreams.ognennyy-shar": "magic.nightmares.ognennyy-shar",
    "magic.dreams.manipulyatsiya": "magic.nightmares.manipulyatsiya",
}


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def migrate() -> dict[str, int]:
    magic_path = DATA / "magic.json"
    magic = json.loads(magic_path.read_text(encoding="utf-8"))
    secret_count = 0
    for item in magic["items"]:
        if item.get("type") != "secret":
            continue
        old_id = item["id"]
        item["id"] = SECRET_ID_MIGRATIONS.get(old_id, old_id)
        path_slug = item["id"].split(".", 2)[1]
        item["requirements"] = [{
            "type": "mystic_path",
            "value": path_slug,
            "path_id": f"paths.{path_slug}",
            "needs_manual_review": False,
        }]
        item["relationships"] = [{"type": "requires_path", "target": f"paths.{path_slug}"}]
        item["modifiers"]["path"] = path_slug
        secret_count += 1
    write(magic_path, magic)

    arts_path = DATA / "combat-arts.json"
    arts = json.loads(arts_path.read_text(encoding="utf-8"))
    art_count = 0
    for item in arts["items"]:
        if item.get("type") != "combat-art":
            continue
        requirements = [r for r in item.get("requirements", []) if r.get("type") != "path_family"]
        item["requirements"] = [{
            "type": "path_family",
            "value": "Martial Path",
            "needs_manual_review": False,
        }, *requirements]
        art_count += 1
    write(arts_path, arts)
    return {"secrets_migrated": secret_count, "arts_migrated": art_count, "ids_changed": len(SECRET_ID_MIGRATIONS)}


if __name__ == "__main__":
    print(json.dumps(migrate(), ensure_ascii=False, indent=2))
