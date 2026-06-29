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
- Record why each candidate was classified.
- Preserve dependencies and conflicts.
- Do not compress the registry away.
- Do not optimize from memory.
