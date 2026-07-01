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
