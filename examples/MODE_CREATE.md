# MODE CREATE Example

This example demonstrates correct behavior while HK-RDB is still incomplete.

## User Input

```text
Repository:
https://github.com/nikihsah/HK-Kit

MODE CREATE

Concept:
"A tiny flea wearing another bug's shell. They look fragile, nervous, and fast."
```

## Model Initialization

The model reads:

1. `AGENTS.md`
2. `CODEX_BOOTSTRAP.md`
3. `CAS_EVOLUTION.md`
4. `PROJECT_SPEC.md`
5. Required HK-CAS files
6. HK-RDB validation data

## Vision Lock Questions

The model should ask before optimizing:

```text
Before choosing mechanics, I need to clarify the shell detail.

1. Is the borrowed shell only visual storytelling, or should it function as armor?
2. Should the character feel evasive and fragile, or surprisingly durable despite being tiny?
3. Is the character meant to use magic, physical mobility, social trickery, or a mix?
```

## Candidate Registry Sample

No mechanical candidates may be finalized while HK-RDB is incomplete.

```json
{
  "status": "blocked",
  "reason": "HK-RDB placeholder data is incomplete.",
  "candidates": []
}
```

## Project Journal Sample

```json
{
  "current_strengths": ["clear visual identity", "strong mobility fantasy"],
  "unresolved_weaknesses": ["shell mechanical meaning is unclear"],
  "player_answers": [],
  "priority_shifts": [],
  "open_questions": [
    "Is the shell aesthetic or mechanical?",
    "Should the build prioritize evasion or durability?"
  ],
  "resolved_conflicts": []
}
```

## Required Stop

Because HK-RDB is incomplete, the model must say:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```

## Audit

```json
{
  "complete": false,
  "blocking_issue": "HK-RDB is incomplete.",
  "pdf_used": false,
  "invented_rules": false
}
```
