#!/usr/bin/env python3
"""Build Layer 1 rule candidates from Layer 0 page extraction.

Layer 1 is a maintainer-only review queue. It groups page text into candidate
blocks and adds conservative category hints.

Layer 1 is not HK-RDB and must never be used during MODE CREATE.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("sources") / "layer1"

CATEGORY_HINTS = [
    ("templates", ["шаблон", "архетип"]),
    ("traits", ["черта", "подчерта", "особенность"]),
    ("paths", ["военные пути", "мистические пути"]),
    ("skills", ["навык", "навыки"]),
    ("advancement", ["развитие", "опыт", "уровень"]),
    ("combat-arts", ["боевое искусство", "техника", "прием", "приём"]),
    ("magic", ["магия", "заклинание", "душа"]),
    ("charms", ["амулет", "метка", "чары"]),
    ("equipment", ["снаряжение", "оружие", "броня", "предмет"]),
    ("combat-rules", ["бой", "атака", "урон", "защита"]),
    ("travel-rest-rules", ["путешествие", "отдых", "голод"]),
    ("social-rules", ["социаль", "убеждение", "репутация"]),
    ("glossary", ["термин", "словарь"]),
]

PAGE_CATEGORY_HINTS = [
    {
        "page_start": 11,
        "page_end": 11,
        "category_hint": "templates",
        "reason": "templates_table_page_range",
    },
    {
        "page_start": 12,
        "page_end": 28,
        "category_hint": "traits",
        "reason": "traits_section_page_range",
    },
    {
        "page_start": 29,
        "page_end": 44,
        "category_hint": "paths",
        "reason": "paths_section_page_range",
    },
]


def slugify(value: str, fallback: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9а-яё]+", "-", value, flags=re.IGNORECASE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


def normalize_block_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_cost_window(text: str) -> bool:
    return bool(
        re.search(
            r"^\s*[+-]?\d+(?:[.,]\d+)?\s*(?:[А-Яа-яЁё]+\s*){0,3}(Голод|Жуть|Жути|Привлекательность|Обоим)",
            text,
        )
    )


def is_bullet_start(line: str) -> bool:
    return line.strip().startswith(("●", "○", "- "))


def is_probable_title(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return False
    if stripped.endswith((".", ",", ";", ":")):
        return False
    if re.match(r"^[+-]?\d", stripped):
        return False
    return True


def rule_list_start_indices(lines: list[str]) -> list[int]:
    starts: list[int] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if is_bullet_start(stripped):
            starts.append(index)
            continue
        if not is_probable_title(stripped):
            continue
        cost_window = " ".join(lines[index + 1 : index + 3])
        if is_cost_window(cost_window):
            starts.append(index)
    return starts


def split_rule_list_blocks(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    starts = rule_list_start_indices(lines)
    if len(starts) < 2:
        return []

    blocks: list[str] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end]).strip()
        if block:
            blocks.append(block)
    return blocks


def split_page_into_blocks(text: str) -> list[str]:
    text = normalize_block_text(text)
    if not text:
        return []

    rule_blocks = split_rule_list_blocks(text)
    if rule_blocks:
        return rule_blocks

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) > 1:
        return blocks

    # Some PDF pages extract as single-line-ish text. Keep conservative chunks
    # rather than trying to infer rule boundaries too aggressively.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        current.append(sentence)
        current_len += len(sentence)
        if current_len >= 900:
            chunks.append(" ".join(current).strip())
            current = []
            current_len = 0
    if current:
        chunks.append(" ".join(current).strip())
    return chunks or [text]


def guess_category(text: str) -> str:
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_HINTS:
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score:
            scores[category] = score
    if not scores:
        return "unknown"
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]


def page_category_hint(page: int) -> tuple[str | None, str | None]:
    for hint in PAGE_CATEGORY_HINTS:
        if hint["page_start"] <= page <= hint["page_end"]:
            return hint["category_hint"], hint["reason"]
    return None, None


def choose_category_hint(text: str, page: int) -> tuple[str, str]:
    page_hint, reason = page_category_hint(page)
    if page_hint:
        return page_hint, reason or "page_range"
    keyword_hint = guess_category(text)
    return keyword_hint, "keyword"


def candidate_title(text: str, max_len: int = 80) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    first_line = re.sub(r"\s+", " ", first_line)
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 3].rstrip() + "..."


def build_candidates(layer0: dict[str, Any], min_chars: int = 40) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    book = layer0.get("book", "")
    source = layer0.get("source", {})
    pages = layer0.get("pages", [])

    for page in pages:
        page_number = page.get("page")
        text = page.get("text", "")
        if not isinstance(page_number, int) or not isinstance(text, str):
            continue
        page_hint, _page_reason = page_category_hint(page_number)
        blocks = [normalize_block_text(text)] if page_hint == "paths" else split_page_into_blocks(text)
        for block_index, block in enumerate(blocks, start=1):
            if len(block) < min_chars:
                continue
            category, category_hint_source = choose_category_hint(block, page_number)
            candidate_id = f"l1.p{page_number:03d}.b{block_index:03d}.{slugify(category, 'unknown')}"
            candidates.append(
                {
                    "id": candidate_id,
                    "status": "needs_review",
                    "category_hint": category,
                    "category_hint_source": category_hint_source,
                    "title_hint": candidate_title(block),
                    "raw_text": block,
                    "source": {
                        "book": book,
                        "pdf_name": source.get("pdf_name"),
                        "pdf_sha256": source.get("pdf_sha256"),
                        "page_start": page_number,
                        "page_end": page_number,
                        "layer0_page": page_number,
                        "layer0_block": block_index,
                    },
                    "review_notes": [],
                }
            )

    return {
        "artifact": "HK-RDB Layer 1",
        "purpose": "Maintainer-only rule candidate queue for reviewed HK-RDB normalization.",
        "mode_create_allowed": False,
        "source_layer": "Layer 0",
        "source_layer0": {
            "book": book,
            "pdf_name": source.get("pdf_name"),
            "pdf_sha256": source.get("pdf_sha256"),
            "page_count": layer0.get("page_count"),
        },
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def default_output_path(layer0_path: Path, output_dir: Path) -> Path:
    stem = layer0_path.name
    if stem.endswith(".layer0.json"):
        stem = stem[: -len(".layer0.json")]
    else:
        stem = layer0_path.stem
    return output_dir / f"{stem}.layer1.json"


def load_layer0(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("artifact") != "HK-RDB Layer 0":
        raise ValueError("input is not an HK-RDB Layer 0 artifact")
    if data.get("mode_create_allowed") is not False:
        raise ValueError("Layer 0 artifact must declare mode_create_allowed: false")
    return data


def write_layer1(document: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract maintainer-only Layer 1 rule candidates from Layer 0 JSON."
    )
    parser.add_argument("--layer0", required=True, type=Path, help="Path to Layer 0 JSON.")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output JSON path. Defaults to sources/layer1/<name>.layer1.json.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=40,
        help="Ignore candidate blocks shorter than this many characters.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    layer0_path = args.layer0.resolve()
    if not layer0_path.exists():
        print(f"Layer 0 file not found: {layer0_path}")
        return 1

    try:
        layer0 = load_layer0(layer0_path)
        document = build_candidates(layer0, min_chars=args.min_chars)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid Layer 0 input: {exc}")
        return 1

    output_path = args.out or default_output_path(layer0_path, DEFAULT_OUTPUT_DIR)
    write_layer1(document, output_path)

    category_counts: dict[str, int] = {}
    for candidate in document["candidates"]:
        category = candidate["category_hint"]
        category_counts[category] = category_counts.get(category, 0) + 1

    print(
        json.dumps(
            {
                "output": str(output_path),
                "candidate_count": document["candidate_count"],
                "category_hint_counts": dict(sorted(category_counts.items())),
                "mode_create_allowed": document["mode_create_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
