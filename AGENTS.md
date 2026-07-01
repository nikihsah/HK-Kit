# AGENTS.md

HK-Kit is an LLM-native framework for creating characters for The Unofficial Hollow Knight RPG. Version 1 supports only `MODE CREATE` and always preserves `Player Vision First`.

## Runtime MODE CREATE

For an ordinary character-creation request, read in this order:

1. `AGENTS.md`
2. `HK-CAS/runtime-create.md`
3. `HK-RDB/data/index.json`
4. `HK-RDB/data/manifest.json`
5. `HK-RDB/data/validation.json`
6. only the HK-CAS and HK-RDB files required by the current stage

Do not require architecture or maintainer documents during normal runtime.

HK-RDB is the only runtime rules source. Never read the PDF, invent a mechanic, or silently fill a data gap. If required rules are missing, invalid, blocked, or insufficient to prove legality, stop and say:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```

Follow every state and contract in `runtime-create.md`. Candidate Registry and Project Journal are separate. Candidates must be concrete HK-RDB objects with valid stable IDs.

During MODE CREATE, unless the user directly requests it, do not generate images; create documents, presentations, or spreadsheets; run unrelated code; alter calendars; send email; perform external actions; switch to an architecture audit; or propose repository refactoring mid-creation.

Record non-blocking framework issues in Deferred Runtime Findings and continue. Report them after character creation. Stop immediately only for a rules violation, insufficient data, or inability to prove build legality.

## Maintenance and Development

Before designing or changing HK-Kit itself, read in this exact order:

1. `CODEX_BOOTSTRAP.md`
2. `CAS_EVOLUTION.md`
3. `PROJECT_SPEC.md`

Then read the task-relevant architecture, schema, tools, and tests. Maintainers rebuilding HK-RDB may use the PDF; MODE CREATE may not. Preserve the flow:

```text
PDF -> HK-RDB -> HK-CAS -> Character
```
