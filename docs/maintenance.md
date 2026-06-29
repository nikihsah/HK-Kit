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
