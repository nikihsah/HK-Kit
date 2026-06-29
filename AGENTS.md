# AGENTS.md

## Operational Entry Point

You are using HK-Kit, an LLM-native framework for creating characters for The Unofficial Hollow Knight RPG.

HK-Kit is currently focused only on:

```text
MODE CREATE
```

Do not run unsupported modes.

## Required Reading Order

Before designing, implementing, or using HK-Kit, read these files in this exact order:

1. `CODEX_BOOTSTRAP.md` - why this project exists.
2. `CAS_EVOLUTION.md` - what failures shaped HK-CAS and why the architecture must not be simplified casually.
3. `PROJECT_SPEC.md` - what v1.0 must build.

After those files, read only the additional files required for the current task.

## Core Principle

Always preserve:

```text
Player Vision First
```

Optimization must begin only after the player's intent, fantasy, desired playstyle, and constraints are understood.

Questions are correct behavior when the concept is ambiguous.

## Rules Source Policy

During MODE CREATE:

- use HK-RDB as the only rules source;
- do not read the original PDF rulebook;
- do not invent missing mechanics;
- stop if required rules are missing, invalid, or incomplete.

If HK-RDB is incomplete for an operation, say:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```

## Required MODE CREATE Behavior

MODE CREATE must follow HK-CAS and must not skip states.

The model must:

- start with repository initialization;
- validate HK-RDB availability before using rules;
- perform Intent Lock, Vision Lock, and Constraint Lock before optimization;
- ask clarifying questions when player fantasy affects mechanics;
- maintain Candidate Registry;
- maintain Project Journal;
- optimize only from Candidate Registry;
- explain major decisions;
- perform final audit before output.

## Candidate Registry

Candidate Registry stores mechanical candidates.

It must preserve concrete options, statuses, reasons, dependencies, conflicts, and source references.

Do not compress Candidate Registry away.

## Project Journal

Project Journal is separate from Candidate Registry.

It stores compact project evolution: player answers, priority shifts, unresolved weaknesses, open questions, and resolved conflicts.

## Maintenance Note

The PDF rulebook may be used only by maintainers rebuilding HK-RDB.

The operational flow is:

```text
PDF -> HK-RDB -> HK-CAS -> Character
```

The repository should teach future AI models how to work without additional explanation from the user.
