# Sources

This directory is for maintainer-only source processing.

## Layer 0

Layer 0 is raw page extraction from the PDF rulebook.

It is used to build reviewed HK-RDB entries with page references.

Layer 0 is not an operational rules source and must not be used during `MODE CREATE`.

## Git Policy

Raw Layer 0 extraction files may contain large portions of the source rulebook.

Do not commit generated Layer 0 JSON files unless the project owner has explicitly confirmed that redistribution is allowed.

Generated files under `sources/layer0/` are ignored by default.

## Layer 1

Layer 1 contains rule candidates extracted from Layer 0.

Layer 1 is also maintainer-only. It is a review queue, not HK-RDB.

Generated files under `sources/layer1/` are ignored by default.
