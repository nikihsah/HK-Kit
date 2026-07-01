# Candidate Registry

Candidate Registry is mandatory.

It stores concrete mechanical candidates. It is the only input allowed for optimization.

## Entry Format

```json
{
  "id": "",
  "name": "",
  "category": "",
  "status": "A | B | Rejected | Deferred",
  "reason": "",
  "dependencies": [],
  "conflicts": [],
  "source_file": "",
  "source_reference": {}
}
```

## Status Meaning

- `A` - strong fit for current vision and constraints.
- `B` - plausible fit, but weaker or dependent on another choice.
- `Rejected` - analyzed and not suitable.
- `Deferred` - cannot decide until another category or player answer is known.

## Rules

- Store concrete options, not vague categories.
- Entries such as “defensive trait”, “suitable path”, “magic enhancement”, or
  “melee weapon” are invalid without a concrete HK-RDB object.
- No valid stable ID in HK-RDB means no candidate.
- Record why each candidate was classified.
- Preserve dependencies and conflicts.
- Do not compress the registry away.
- Do not optimize from memory.

## Narrow exception: created rule instances

Some HK-RDB rules explicitly create character-local instances rather than offering a fixed object list. Умения are governed by `skills.overview` and `skills.md`.

Store them as `record_type: character_skill_instance` with both a local project ID and the governing `rule_id: skills.overview`. The local ID is never an HK-RDB ID. This exception does not permit vague candidates or weaken the stable-ID rule for ordinary mechanical objects.
