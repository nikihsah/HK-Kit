# HK-Kit

HK-Kit is an LLM-native knowledge pack and character design framework for The Unofficial Hollow Knight RPG.

It exists so a user can give an AI model a repository link, select `MODE CREATE`, provide a character concept, and receive a rules-valid character built through a controlled design pipeline.

HK-Kit is not a character builder application. Its main purpose is to teach an AI model what to do and where to get information.

## Quick Start

Give an AI model this repository and write:

```text
Repository:
https://github.com/nikihsah/HK-Kit

MODE CREATE

Concept:
<your character concept>
```

The model must initialize from `AGENTS.md`.

## Current Scope

Supported mode:

```text
MODE CREATE
```

Unsupported modes such as REVIEW, OPTIMIZE, and EXPLAIN are future work.

## Core Rule

HK-Kit follows:

```text
Player Vision First
```

HK-CAS is not only an optimizer. It is a character interpretation system.

The model should ask questions when the player's fantasy is unclear. Questions are correct behavior.

Good questions:

- What should feel more important: reckless speed or safe mobility?
- Is the shell mostly visual, or should it affect tactics?
- Should the character feel like a predator, survivor, trickster, scout, or duelist?
- Is magic acceptable if it fits the concept, or should the character stay physical?
- What should never happen in this build?

Bad questions:

- What trait do you want?
- Which weapon should I pick?
- Do you want the strongest option?

After Vision Lock, questions should become rarer. The model asks only when multiple options remain equally valid and the difference is about player fantasy, not rules efficiency.

## Rules Source

During character creation, the model must use only `HK-RDB`.

The original PDF rulebook is a maintenance source only. It must not be used during `MODE CREATE`.

## Repository Map

- `AGENTS.md` - operational entry point for AI models.
- `CODEX_BOOTSTRAP.md` - why HK-Kit exists.
- `CAS_EVOLUTION.md` - why HK-CAS has its current architecture.
- `PROJECT_SPEC.md` - v1.0 source of truth.
- `HK-CAS/` - character design pipeline.
- `HK-RDB/` - normalized rules database.
- `examples/` - MODE CREATE examples.
- `docs/` - architecture and maintenance notes.
- `tools/` - maintainer tools.
- `tests/` - validation tests.

## Current Limitation

The initial repository skeleton does not yet contain the full normalized rule database.

If HK-RDB is incomplete, MODE CREATE must stop with:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```
