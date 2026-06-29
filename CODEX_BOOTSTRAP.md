# CODEX_BOOTSTRAP.md

## Purpose

HK-Kit exists because prompt-only character creation for The Unofficial Hollow Knight RPG proved unreliable.

When an AI model received the rulebook and a character concept directly, it often skipped rules, forgot earlier pages, optimized too early, silently assumed player intent, or produced inconsistent builds. The larger the rulebook became, the worse these problems became.

HK-Kit is the engineering answer to that problem.

## What HK-Kit Is

HK-Kit is an LLM-native framework for designing characters.

It is not:

- a character builder;
- a collection of prompts;
- a simple database;
- a direct wrapper around the PDF rulebook.

It is a repository that teaches an AI model how to design a character consistently while preserving both rule fidelity and player fantasy.

## Long-Term Vision

Eventually a player should be able to open ChatGPT or another capable LLM, provide a link to this repository, and write only:

```text
MODE CREATE

Concept:
"My character is ..."
```

The AI should then initialize itself from the repository, understand the framework, ask clarifying questions when needed, use only the normalized rules database, follow the character design pipeline, build the character, explain major decisions, and audit the result.

The user should not need to explain how HK-Kit works.

## Current Scope

Version 1.0 focuses only on:

```text
MODE CREATE
```

Do not implement REVIEW, OPTIMIZE, or EXPLAIN unless their architecture is required to support MODE CREATE.

The first goal is to make MODE CREATE excellent.

## Core Principle

The central principle is:

```text
Player Vision First
```

The AI must understand the player's intent and fantasy before optimization begins.

Questions are not failures. Questions are encouraged.

The AI should never silently assume how a character should behave when the player's fantasy is unclear.

## Rule Source Policy

The AI must never read the original PDF during character creation.

The intended source flow is:

```text
PDF
  -> HK-RDB
  -> HK-CAS
  -> Character
```

The PDF is a maintenance source only.

HK-RDB is the only operational rules source during MODE CREATE.

## Architectural Priorities

HK-Kit should optimize for:

- maintainability;
- deterministic behavior;
- modularity;
- explainability;
- repository readability;
- future extensibility;
- LLM friendliness.

Avoid solutions that only work because of one specific model.

Design the project so that different modern LLMs can understand it.

## Collaboration Rule

Do not rush ahead.

Do not invent major systems without discussion.

If requirements are ambiguous, ask questions.

If a better architecture exists, explain it first.

Treat HK-Kit as a collaborative engineering project where quality matters more than speed.
