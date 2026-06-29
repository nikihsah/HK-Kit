# HK-Kit

HK-Kit is an LLM-native knowledge pack and character design framework for The Unofficial Hollow Knight RPG.

It exists so a user can give an AI model a repository link, select `MODE CREATE`, provide a character concept, and receive a rules-valid character built through a controlled design pipeline.

## Quick Start

Give an AI model this repository and write:

```text
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

The model should ask questions when the player's fantasy is unclear. Questions are correct behavior.

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
