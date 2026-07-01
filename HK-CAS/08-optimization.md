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

Hunger is a build budget, not a score to maximize. Cross-Category Optimization and Build Assembly must maintain `templates/hunger-budget-ledger.yaml`.

The model must analyze all legal traits and subtraits that materially support the locked vision, including meaningful uses of remaining budget. It must not add a weak, useless, duplicative, or conceptually alien option merely to reach maximum Hunger. Every unused Hunger point requires an explicit explanation.

- `Hunger maximization` is forbidden as a standalone objective.
- `Hunger budget optimization` is mandatory.

Optimization is incomplete while the ledger has `candidate_search_completed: false`, an unexplained positive `unused_hunger`, an unverified adjustment, or a failed audit status.

## Skill selection breadth

Do not stop after finding the first suitable skill. Analyze the full Skills category and compare all concept-relevant candidates. A legal build may include up to three skills; select every materially useful skill, up to that limit, when supported by the locked vision and HK-RDB. Selecting fewer than three is valid, but the Project Journal or final explanation must state why additional skills would be redundant, weak, illegal, or outside the concept.

Skill selection must still cite the governing HK-RDB rules. This instruction expands search breadth; it does not authorize inventing skills or bypassing rank, cost, or dependency rules.

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
