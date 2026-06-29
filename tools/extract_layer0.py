#!/usr/bin/env python3
"""Extract a PDF rulebook into Layer 0 page records.

Layer 0 is a maintainer artifact. It preserves page text and page references so
maintainers can later build reviewed HK-RDB entries.

MODE CREATE must never use Layer 0 or the source PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_OUTPUT_DIR = Path("sources") / "layer0"
DEFAULT_BOOK_NAME = "The Unofficial Hollow Knight RPG - RUS"


def normalize_text(text: str) -> str:
    """Normalize extractor output without changing rule wording."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_layer0_document(
    *,
    source_pdf: Path,
    book: str,
    page_texts: Iterable[str],
    include_source_path: bool,
) -> dict:
    pages = []
    for index, raw_text in enumerate(page_texts, start=1):
        text = normalize_text(raw_text or "")
        warnings = []
        if not text:
            warnings.append("empty_text")
        pages.append(
            {
                "page": index,
                "text": text,
                "char_count": len(text),
                "warnings": warnings,
            }
        )

    document = {
        "artifact": "HK-RDB Layer 0",
        "purpose": "Maintainer-only raw page extraction for later reviewed HK-RDB normalization.",
        "mode_create_allowed": False,
        "book": book,
        "source": {
            "pdf_name": source_pdf.name,
            "pdf_sha256": sha256_file(source_pdf) if source_pdf.exists() else None,
        },
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "pages": pages,
    }

    if include_source_path:
        document["source"]["pdf_path"] = str(source_pdf)

    return document


def extract_pdf_texts(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on local runtime
        raise SystemExit(
            "Missing dependency: pypdf. Install it or use the Codex bundled Python runtime."
        ) from exc

    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


def write_layer0(document: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def default_output_path(pdf_path: Path, output_dir: Path) -> Path:
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", pdf_path.stem).strip("-")
    return output_dir / f"{safe_stem}.layer0.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a PDF rulebook into maintainer-only Layer 0 JSON."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output JSON path. Defaults to sources/layer0/<pdf-name>.layer0.json.",
    )
    parser.add_argument(
        "--book",
        default=DEFAULT_BOOK_NAME,
        help="Book name stored in Layer 0 metadata.",
    )
    parser.add_argument(
        "--include-source-path",
        action="store_true",
        help="Store the local PDF path in output metadata. Off by default for privacy.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return 1

    output_path = args.out or default_output_path(pdf_path, DEFAULT_OUTPUT_DIR)
    page_texts = extract_pdf_texts(pdf_path)
    document = build_layer0_document(
        source_pdf=pdf_path,
        book=args.book,
        page_texts=page_texts,
        include_source_path=args.include_source_path,
    )
    write_layer0(document, output_path)

    empty_pages = [page["page"] for page in document["pages"] if page["warnings"]]
    print(
        json.dumps(
            {
                "output": str(output_path),
                "page_count": document["page_count"],
                "empty_pages": empty_pages,
                "mode_create_allowed": document["mode_create_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
