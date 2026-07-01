# AGENTS.md

HK-Kit is an LLM-native framework for creating characters for The Unofficial Hollow Knight RPG. Version 1 supports only `MODE CREATE` and always preserves `Player Vision First`.

## MODE CREATE Runtime Route

For a normal `MODE CREATE` request, read in this order:

1. `AGENTS.md`
2. `HK-CAS/runtime-create.md`
3. `HK-RDB/data/index.json`
4. `HK-RDB/data/manifest.json`
5. `HK-RDB/data/validation.json`

Do not read `CODEX_BOOTSTRAP.md`, `CAS_EVOLUTION.md`, or `PROJECT_SPEC.md` during normal character creation. After initialization, read only the HK-CAS and HK-RDB files required by the current stage.

## Mandatory First Response Contract

After receiving a new `MODE CREATE` concept, do not select or recommend any template, path, trait, weapon, skill, art, charm, spell, equipment item, or other mechanical build component.

The first substantive response must perform only:

1. Repository and HK-RDB validation.
2. Intent Lock questions.
3. Vision Lock questions.
4. Constraint Lock questions.

This applies even when the concept appears clear. A clear concept may reduce the number of questions, but it never permits skipping any of the three Locks.

Before all three Locks are complete, the response must not contain:

- selected HK-RDB object names;
- proposed paths or templates;
- trait or equipment recommendations;
- calculated character values;
- a partial or complete build.

Mentioning a mechanical object before all three Locks are complete is a runtime protocol failure.

HK-RDB is the only runtime rules source. Never read the PDF, invent a mechanic, or silently fill a data gap. If required rules are missing, invalid, blocked, or insufficient to prove legality, stop and say:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```

Follow every state and contract in `runtime-create.md`. Candidate Registry and Project Journal are separate. Candidates must be concrete HK-RDB objects with valid stable IDs.

For an object with `parsing_status: raw_text_authoritative`, read and use its preserved `raw_text` as the authoritative rule. Its structured effects are incomplete and must not replace, shorten, or reinterpret that text.

During MODE CREATE, unless the user directly requests it, do not generate images; create documents, presentations, or spreadsheets; run unrelated code; alter calendars; send email; perform external actions; switch to an architecture audit; or propose repository refactoring mid-creation.

Record non-blocking framework issues in Deferred Runtime Findings and continue. Report them after character creation. Stop immediately only for a rules violation, insufficient data, or inability to prove build legality.

## Maintenance and Development

This section applies only when changing, validating, rebuilding, or auditing HK-Kit itself. It is never part of normal `MODE CREATE`. Read in this exact order:

1. `CODEX_BOOTSTRAP.md`
2. `CAS_EVOLUTION.md`
3. `PROJECT_SPEC.md`

Then read the task-relevant architecture, schema, tools, and tests. Maintainers rebuilding HK-RDB may use the PDF; MODE CREATE may not. Preserve the flow:

```text
PDF -> HK-RDB -> HK-CAS -> Character
```
