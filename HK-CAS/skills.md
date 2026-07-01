# Skill Instance Contract

This file is the normative HK-CAS contract for creating character Skill instances under `skills.overview`.

## Rule model

An Умение is a job, background, activity, or other competence area. The named sets in `skills.overview` are examples, not classes, a closed list, or mutually exclusive choices. A character may possess several examples at once and may use adapted or custom sets.

Each available Skill Rank from `advancement.progression` must be assigned to a new or existing Skill instance. The number available at creation comes from the locked starting milestone; it is not a universal three-slot limit.

For every rank that could create a new instance, compare:

1. an HK-RDB example;
2. an adapted example;
3. a custom Skill built for the concept.

Do not leave an available rank unassigned merely because no example fits. Ask the player when creating or naming the missing competence is a real vision choice.

## Character-local instance

Use `templates/character-skill-instance.json`. A local ID such as `character-skill.01` identifies project state, not an HK-RDB rule object. `rule_id` must remain `skills.overview`.

Every instance must contain exactly four distinct skills, its narrative purpose, origin (`example`, `adapted-example`, or `custom`), source example when applicable, concept-fit explanation, rank, and player-confirmation state.

When skills overlap between instances, sum their contributing ranks and apply the cap from `skills.overview`. Preserve the per-instance contributions so the audit can reproduce the total.
