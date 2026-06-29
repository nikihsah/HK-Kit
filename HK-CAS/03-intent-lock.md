# Intent Lock

Intent Lock determines why the player is creating the character.

Ask before optimization if intent is unclear.

## Common Intents

- campaign character
- one-shot character
- optimized build
- roleplay-first character
- thematic character
- experimental build
- beginner-friendly build

## Output

Maintain an internal Intent Lock record:

```json
{
  "intent": "",
  "confidence": "low | medium | high",
  "questions": [],
  "player_answers": []
}
```

Proceed only when the intent is clear enough to guide later choices.
