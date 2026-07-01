# HK-RDB

HK-RDB is the normalized rules database for HK-Kit.

During `MODE CREATE`, it is the only allowed rules source.

The original PDF rulebook is a maintenance source only. It may be used to rebuild HK-RDB, but it must not be used during character creation.

## Data Shape

Each data file contains:

```json
{
  "category": "Traits",
  "file": "traits.json",
  "complete": true,
  "items": [{ "id": "normalized.rule.object" }]
}
```

Each item must follow `schema/schema.json`.

## Completeness

Released v1.0 data files are marked:

```json
"complete": true
```

If a required category is incomplete, MODE CREATE must stop with:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```
