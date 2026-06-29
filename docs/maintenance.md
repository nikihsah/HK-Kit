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
