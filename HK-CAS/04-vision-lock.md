# Vision Lock

Vision Lock determines how the player imagines the character.

This state prevents the model from turning visual or narrative details into mechanics without permission.

## Clarify

- appearance
- fantasy
- combat feeling
- movement style
- personality
- role in group
- what must be avoided
- whether magic is allowed
- whether strange body mechanics are allowed
- whether a visual concept should become mechanics or stay aesthetic

## Rule

If player fantasy influences mechanics, ask.

Do not silently assume.

## Output

Maintain an internal Vision Lock record:

```json
{
  "fantasy": "",
  "must_preserve": [],
  "must_avoid": [],
  "mechanical_permissions": [],
  "aesthetic_only": [],
  "questions": [],
  "player_answers": []
}
```
