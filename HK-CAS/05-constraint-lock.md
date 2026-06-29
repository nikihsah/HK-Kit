# Constraint Lock

Constraint Lock records external limits before rules analysis begins.

## Clarify

- starting level or rank
- allowed rule sources
- banned options
- campaign restrictions
- party role
- expected difficulty
- house rules
- tone restrictions

## Defaults

Defaults may be proposed when harmless, but important uncertainty must be surfaced to the player.

## Output

Maintain an internal Constraint Lock record:

```json
{
  "starting_level": null,
  "allowed_sources": [],
  "banned_options": [],
  "campaign_restrictions": [],
  "party_role": "",
  "difficulty": "",
  "house_rules": [],
  "tone_restrictions": []
}
```
