# Maintenance

Maintainers may use the PDF rulebook to rebuild HK-RDB.

The operational creation flow must remain:

```text
HK-RDB -> HK-CAS -> Character
```

The maintenance flow may use:

```text
PDF -> Layer 0 -> reviewed extraction -> HK-RDB
```

## Rules

- Do not add unsourced rule objects.
- Every rule object needs page references.
- Mark uncertain entries with `needs_manual_review: true`.
- Run `tools/validate_rdb.py` after edits.
- Keep HK-CAS free of game mechanics.
- Keep generated Layer 0 files out of Git unless redistribution is explicitly approved.

## Local Layer 0 Extraction

Use:

```bash
python tools/extract_layer0.py --pdf "<path-to-rulebook.pdf>"
```

The generated file is maintainer-only. It is not HK-RDB and must not be used during MODE CREATE.

## Local Layer 1 Candidate Extraction

Use:

```bash
python tools/extract_layer1.py --layer0 "sources/layer0/<pdf-name>.layer0.json"
```

The generated file is a review queue. It is not HK-RDB and must not be used during MODE CREATE.

Layer 1 candidates may be noisy. A candidate becomes HK-RDB only after maintainer review, normalization, schema validation, and source verification.
