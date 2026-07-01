# Official Character Sheet

The official template is `assets/character-sheet/hollow-knight-rpg-bug-sheet.pdf`. It is a three-page, non-fillable PDF used as an immutable background.

Fill it only after the latest character version passes Rules Audit and the player explicitly chooses the sheet action in Post-Creation Handoff. Use `tools/fill_character_sheet.py` to create a separate PDF under `output/pdf/`; never overwrite the template.

## Build-data mapping

- Page 1: character/player names, size/milestone, main characteristics, Heart/Soul/Stamina, custom resources, social values, Speed/Maneuver/Satiety, Paths/ranks, Traits with social/Hunger adjustments, equipped Charms/marks, description.
- Page 2: equipment/weight, weapons and shields, armor, currency/load, prepared Techniques (Arts, Secrets, recipes), and Умения with rank, mastery, and their four skills.
- Page 3: overflow notes, source IDs, dependency notes, audit summary, and content that does not fit safely on pages 1–2.

Input must be the latest audited character-sheet JSON described by the filler CLI. The output filename is sanitized from the character name. If a character changes later, the existing output is stale and must not be presented as current; offer to regenerate it after the new audit passes.
