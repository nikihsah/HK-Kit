# MODE CREATE Runtime Route

Purpose: transform the player's concept into a rules-valid character while preserving intent and using HK-RDB as the only rules source.

## Minimal initialization

Read `AGENTS.md`, this file, `HK-RDB/data/index.json`, `manifest.json`, and `validation.json`, then only stage-relevant HK-CAS and HK-RDB files. Stop on validation `fail`, stale manifest, missing required data, or a required `blocked` object. Raw-text-authoritative objects use their preserved `raw_text`; do not infer missing structure.

## Ordered states

1. Repository Initialization and HK-RDB Validation Check.
2. Intent Lock: establish why the character is being made.
3. Vision Lock: establish fantasy, feel, must-preserve details, and aesthetic-only details.
4. Constraint Lock: establish level, sources, bans, campaign and table limits.
5. Concept Card: record the three locks in a compact design target.
6. Category Analysis: use manifest order and counts; do not mix resources, characteristics, derived values, or game entities into one category.
7. Element Cards: for every analyzed object record its ID, rules summary, requirements, effects, costs, dependencies, conflicts, and fit.
8. Candidate Registry and Project Journal update.
9. Category Checkpoint. A category with `complete: false` blocks the next category.
10. Cross-Category Optimization only after every required category checkpoint is valid and complete.
11. Build Assembly.
12. Rules Audit and Final Character Output.

## Runtime contracts

- Candidate Registry entries must name concrete HK-RDB objects and follow `06-candidate-registry.md`. No valid HK-RDB ID means no candidate.
- Project Journal remains separate and compact; update it when analysis changes the concept or priorities.
- Each required category must produce `templates/category-checkpoint.json`, using manifest count and IDs as evidence of coverage.
- Build Assembly may use only registry candidates. Rules Audit must prove legality and cite HK-RDB objects.
- Fail Loudly: never hide missing, invalid, incomplete, stale, or blocked rules data.
- No silent mechanical assumptions. Ask a clarifying question only for a real player choice or a blocking ambiguity.
- A visual or narrative detail is not a mechanical requirement without player confirmation.
- A desired characteristic is not automatically valid for an action. Verify the actual characteristic used by the HK-RDB mechanic. “Melee through Insight” triggers a search for a legal rule path; it does not make ordinary attacks use Insight.
- Conclusions require concrete HK-RDB objects and rules.

## Scope guard

Without a direct user request, do not generate images or office artifacts, execute unrelated code, modify calendars, send email, perform external actions, switch to architecture audit, or propose refactoring during character creation. Put non-blocking framework issues in Deferred Runtime Findings, continue, and report them at the end. Stop only when rules/data/legality is blocked.
