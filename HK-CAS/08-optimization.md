# Optimization

Optimization begins only after Candidate Registry exists for every required category
and every category checkpoint is valid with `complete: true`.

If the registry is missing required categories, stop.
If any checkpoint is missing, invalid, or incomplete, stop.

## Goals

- preserve player vision;
- preserve legality;
- remove duplicates;
- resolve conflicts;
- avoid unnecessary complexity;
- avoid mechanics that change the character fantasy unless explicitly approved.

## Hunger budget

Hunger is a build budget. Cross-Category Optimization and Build Assembly must maintain `templates/hunger-budget-ledger.yaml` and attempt to use the maximum budget possible among legal, useful, non-redundant, concept-aligned candidates.

The model must analyze all legal traits and subtraits that materially support the locked vision, including meaningful uses of remaining budget. It must not add a weak, useless, duplicative, or conceptually alien option merely to reach maximum Hunger. Every unused Hunger point requires an explicit explanation supported by concrete considered candidate IDs.

- Blind `Hunger maximization` through filler is forbidden.
- Constrained Hunger maximization is mandatory after vision fit, legality, usefulness, and non-duplication are satisfied.
- If `unused_hunger > 0`, a second pass over all affordable compatible trait and subtrait candidates is mandatory.

Optimization is incomplete while the ledger has `candidate_search_completed: false`, an incomplete required second pass, an unexplained positive `unused_hunger`, affordable candidates without explicit dispositions, an unverified adjustment, or a failed audit status.

## Skill selection breadth

Follow `skills.md`. Determine available Skill Ranks from the locked milestone and `advancement.progression`; do not assume a universal maximum of three instances. Assign every available rank. Multiple example sets may coexist, and adapted or custom instances are valid under `skills.overview`.

Do not stop after the first suitable example. For each rank that may create a new instance, compare example, adapted-example, and custom options. Skill construction never authorizes invented mechanical effects: each instance remains governed by `skills.overview`.

## Unused Hunger player gate

After the second Hunger pass, if at least one affordable, legal, useful, non-duplicative, vision-compatible trait or package remains, Build Assembly is blocked. Present a compact player choice: useful package A, useful package B when available, or intentionally leave the budget unused.

Only explicit player confirmation may authorize unused budget while a suitable option remains. Record the amount, rejected candidate IDs/reasons, and confirmation in both Hunger Budget Ledger and Project Journal. If no suitable option exists, continue only with ledger evidence that the complete second pass found none.

## Inputs

Optimization may use:

- Candidate Registry;
- Project Journal;
- Intent Lock;
- Vision Lock;
- Constraint Lock;
- HK-RDB source references.

Optimization must not use:

- memory of the PDF;
- invented mechanics;
- untracked candidates;
- unsupported rule sources.
