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


def slugify(value: str, fallback: str = "entry") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value, flags=re.IGNORECASE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


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


def clean_title(value: str) -> tuple[str, bool]:
    title = re.sub(r"\s+", " ", value).strip()
    is_subtrait = title.startswith("●")
    title = title.lstrip("●").strip()
    return title, is_subtrait


def parse_number(value: str) -> float | int:
    number = float(value.replace(",", "."))
    return int(number) if number.is_integer() else number


def parse_trait_costs(cost_text: str) -> dict[str, Any]:
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


def split_trait_parts(raw_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {
            "name": "",
            "is_subtrait": False,
            "cost_text": "",
            "body": "",
        }

    name, is_subtrait = clean_title(lines[0])
    cost_lines: list[str] = []
    body_start = 1

    for index in range(1, min(len(lines), 4)):
        window = " ".join(lines[1 : index + 1])
        if re.match(r"^\s*[+-]?\d+(?:[,.]\d+)?", window) and re.search(
            r"Голод|Жут|Привлекательност|Обоим", window, re.IGNORECASE
        ):
            cost_lines = lines[1 : index + 1]
            body_start = index + 1
            break

    body = "\n".join(lines[body_start:]).strip()
    return {
        "name": name,
        "is_subtrait": is_subtrait,
        "cost_text": " ".join(cost_lines).strip(),
        "body": body,
    }


def normalize_trait_rule_object(item: dict[str, Any], raw_text: str) -> dict[str, Any]:
    parts = split_trait_parts(raw_text)
    tags = list(item["tags"])
    if "trait" not in tags:
        tags.append("trait")
    if parts["is_subtrait"] and "subtrait" not in tags:
        tags.append("subtrait")

    item["name"] = parts["name"] or item["name"]
    item["subcategory"] = "Subtrait" if parts["is_subtrait"] else "Trait"
    item["costs"] = parse_trait_costs(parts["cost_text"])
    item["summary"] = summarize_raw_text(parts["body"] or raw_text)
    item["effects"] = [
        {
            "type": "unparsed_effect_text",
            "text": parts["body"] or raw_text,
            "needs_manual_review": True,
        }
    ]
    item["tags"] = tags
    return item


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
