# Post-Creation Handoff

This file is the normative contract for interaction after Final Character Output.

## Entry gate

Enter this state only when the latest character version has completed Build Assembly and passed a full Rules Audit. Before that gate, do not show the post-creation menu.

## Menu

Tell the player the character is complete and audited, then offer one or more actions:

1. Generate a character image.
2. Fill the official character-sheet template.
3. Add or change something in the character.
4. Finish without additional actions.

Offering the menu is allowed after audit. Performing image generation, filling an artifact, or another external action still requires the player's explicit selection.

## Change loop

For a mechanical change:

1. identify affected Locks, Concept Card fields, categories, dependencies, Candidate Registry entries, Journal entries, Hunger ledger values, and calculations;
2. preserve unaffected category checkpoints;
3. reopen every affected dependency;
4. invalidate the previous audit and any previously filled character sheet;
5. update registry and journal;
6. repeat affected optimization and Build Assembly;
7. run a full Rules Audit of the resulting character;
8. show this menu again only after the new audit passes.

For a purely narrative or visual change, record it and verify whether Vision Lock or descriptive fields changed. Do not repeat mechanical calculation when mechanics are provably unaffected. Then show this menu again.

Choosing Finish exits the loop.

## Character sheet

Follow `character-sheet.md`. Use only the latest audited character version. Never overwrite the official template. If the character changes afterward, mark the filled sheet stale.

## Image generation

After explicit selection, build a visual specification from Vision Lock, Concept Card, final description, species, scale/proportions, head/face/mask, chitin, clothing/armor, weapons, colors, distinctive features, pose/personality, environment, and must-not-change details.

Mechanical names do not imply appearance unless the player established it. Ask one compact question when an important visual choice remains ambiguous. If image generation is unavailable, say so and provide a usable visual specification or prompt. Return to this menu afterward if interaction continues.
