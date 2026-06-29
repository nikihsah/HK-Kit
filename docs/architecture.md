# Architecture

HK-Kit separates three responsibilities:

```text
PDF -> HK-RDB -> HK-CAS -> Character
```

## PDF

The PDF is a maintenance source. It is used only to rebuild or verify HK-RDB.

MODE CREATE must not read the PDF.

## HK-RDB

HK-RDB is the normalized rules database.

It stores machine-readable rules with stable IDs, summaries, raw text, requirements, effects, relationships, tags, and source references.

## HK-CAS

HK-CAS is the character design pipeline.

It does not store rules. It defines how the model should understand the player, compare options, maintain Candidate Registry, update Project Journal, optimize, assemble, and audit.

## Character

The final character is an output of HK-CAS using HK-RDB.

If HK-RDB is incomplete, no final character may be produced.
