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
  "complete": false,
  "items": []
}
```

Each item must follow `schema/schema.json`.

## Completeness

Placeholder files are intentionally marked:

```json
"complete": false
```

If a required category is incomplete, MODE CREATE must stop with:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```
