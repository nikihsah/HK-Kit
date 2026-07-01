# MODE CREATE Runtime Route

Purpose: transform the player's concept into a rules-valid character while preserving intent and using HK-RDB as the only rules source.

## Minimal initialization

Read `AGENTS.md`, this file, `HK-RDB/data/index.json`, `manifest.json`, and `validation.json`, then only stage-relevant HK-CAS and HK-RDB files. Do not read `CODEX_BOOTSTRAP.md`, `CAS_EVOLUTION.md`, or `PROJECT_SPEC.md` during MODE CREATE. Stop on validation `fail`, stale manifest, missing required data, or a required `blocked` object. For every `raw_text_authoritative` object considered during analysis, read the complete preserved `raw_text` and treat it as the authoritative rule; its structured effects are incomplete and must not be used as a substitute. Do not infer missing structure.

## First response gate

The first substantive response to every new concept may only report repository/HK-RDB validation and ask the minimum necessary Intent Lock, Vision Lock, and Constraint Lock questions. This gate applies even when the concept seems clear.

Until all three Locks are complete, do not name or recommend HK-RDB mechanical objects, propose paths or templates, recommend traits or equipment, calculate character values, or present any partial build. Violating this gate is a runtime protocol failure.

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
10. Cross-Category Optimization only after every required category checkpoint is valid and complete; complete the Hunger Budget Ledger and compare all relevant skill candidates rather than stopping at the first fit.
11. Build Assembly, including every materially useful and legal selection supported by the locked vision.
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
- A strong Concept Card is not a completed build. Narrative reframing must never replace mechanical selection, calculation, Build Assembly, or Rules Audit.
- Every renamed or reflavored ability must show its official HK-RDB name and stable ID alongside its separate narrative name, with an explicit statement that its mechanics are unchanged.
- Maximize Hunger utilization only among legal, useful, non-redundant mechanics that support the locked vision; never add filler merely to reach the limit. Maintain `templates/hunger-budget-ledger.yaml`. If any Hunger remains, perform a second pass over every affordable compatible trait and subtrait, record concrete IDs and dispositions, and explain every unused point.
- Do not stop at one suitable skill. Analyze the complete Skills category and, when legal and conceptually useful, select up to three skills. If fewer are selected, explain why the remaining slots should not be filled.

## Scope guard

Without a direct user request, do not generate images or office artifacts, execute unrelated code, modify calendars, send email, perform external actions, switch to architecture audit, or propose refactoring during character creation. Put non-blocking framework issues in Deferred Runtime Findings, continue, and report them at the end. Stop only when rules/data/legality is blocked.
