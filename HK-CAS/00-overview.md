# HK-CAS Overview

HK-CAS is a decision pipeline for creating characters while preserving two things:

- the player's fantasy;
- the legal rules data in HK-RDB.

HK-CAS exists because direct prompt-based character creation failed in repeated testing. Models optimized too early, assumed missing intent, forgot why options were preferred, and used incomplete rule access.

## Non-Negotiable Principles

- Player Vision First
- No Silent Assumptions
- HK-RDB Only
- Candidate Registry Before Optimization
- Compact Project Journal
- Explain Major Decisions
- Fail Loudly On Missing Rules
- Audit Before Final Output

## Hunger Budget Optimization

Hunger is a build budget that must be analyzed during Cross-Category Optimization and Build Assembly. Among legal, non-redundant options that materially support the locked vision, the model must attempt to use as much of the available Hunger budget as possible.

The model must:

1. select every legal trait and subtrait that materially supports the locked character vision;
2. search for the highest Hunger utilization achievable with useful, concept-aligned candidates;
3. reject weak, useless, duplicative, or conceptually alien mechanics added only to fill the limit;
4. explicitly explain every remaining unused Hunger point.

Blind `Hunger maximization` with filler mechanics is forbidden. Constrained Hunger maximization—maximizing utilization only after vision fit, legality, usefulness, and non-duplication are satisfied—is mandatory in MODE CREATE.

When unused Hunger remains, the model must perform a second candidate pass before assembly. It may leave budget unused only when every affordable, compatible candidate would be weak, redundant, conceptually alien, illegal, or rejected by the player, and it must identify those candidates and reasons explicitly.

## Boundary

HK-CAS tells the model how to think.

HK-RDB tells the model what the rules are.

Do not mix these roles.

## Concept Is Not Completion

A strong Concept Card is not a completed build. Narrative reframing must never replace mechanical selection, calculation, and audit.

MODE CREATE is complete only after concrete HK-RDB objects have been selected, all derived values have been calculated, Build Assembly has produced a full character sheet, and Rules Audit has passed.

## Reflavor Transparency

Any renamed or reflavored ability must display both:

- its official HK-RDB name and stable ID;
- its separate narrative name.

Reflavoring must not alter the rule's costs, requirements, effects, dependencies, or other mechanics.
