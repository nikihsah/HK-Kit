#!/usr/bin/env python3
"""Placeholder for extracting PDF text into a maintainer Layer 0 artifact.

This tool is intentionally not implemented yet. It exists to reserve the
maintenance flow:

PDF -> Layer 0 -> HK-RDB -> HK-CAS -> Character

MODE CREATE must never call this tool.
"""

from __future__ import annotations


def main() -> int:
    print("extract_layer0.py is a maintainer placeholder. Do not use during MODE CREATE.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
