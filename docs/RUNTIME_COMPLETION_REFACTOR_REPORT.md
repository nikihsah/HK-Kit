# Runtime Completion Refactor Report

## Causes found

- Умения were treated like closed class choices and the CAS hard-coded “up to three.” HK-RDB instead defines free Skill sets and grants Skill Ranks by milestone.
- Hunger optimization recorded remaining budget but did not block assembly while useful choices still awaited the player.
- MODE CREATE ended at Final Character Output and had no audited post-creation state, change invalidation loop, or artifact freshness tracking.
- No character-sheet template existed in the repository. The supplied three-page PDF contains no usable form fields, so safe filling requires a separate overlay copy.

## Implemented behavior

- `HK-CAS/skills.md` defines example, adapted-example, and custom Skill instances. Each has four distinct skills, a character-local ID, and governing rule `skills.overview`.
- Available Skill Ranks are derived from `advancement.progression`: one through milestone 0, two through milestone 2, and three through milestone 4. This is not a fixed instance count because ranks may be combined.
- Hunger optimization blocks Build Assembly when a useful affordable option remains until the player selects a package or explicitly approves unused budget.
- `10-post-creation-handoff.md` adds an audit-gated cyclic menu for image, official sheet, changes, and finish. Mechanical changes invalidate the old audit and sheet.
- The supplied PDF is stored unchanged at `assets/character-sheet/hollow-knight-rpg-bug-sheet.pdf`. `tools/fill_character_sheet.py` produces a separate audited output under `output/pdf/`.

## Ambiguity decisions

- The word Умение denotes the four-skill competence set; individual entries inside it remain навыки. Local instance IDs are project state, not new HK-RDB rule IDs.
- The starting number is determined from the locked milestone table, not the earlier CAS phrase “up to three.” At the recommended milestone 2, two Skill Ranks are available; the player can create two rank-1 instances or invest ranks according to the governing rules.
- The PDF is non-fillable despite declaring an AcroForm container. The implementation uses an overlay so the official source remains byte-for-byte unchanged.

## Verification

- HK-RDB data was not changed.
- The full unit suite covers constructed Skill instances, overlapping rank aggregation/cap, Hunger player gate, post-creation audit gate and invalidation, stale sheets, explicit external-action selection, and PDF output.
- The official PDF and a representative filled copy were rendered as three pages and visually inspected.
