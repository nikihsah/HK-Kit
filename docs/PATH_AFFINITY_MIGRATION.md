# Path Affinity Migration

The source layer places four page-66 Secrets after the `Тайна кошмаров` heading. They were incorrectly published under `dreams` because the page fallback covered pages 65–66.

Stable ID migrations:

- `magic.dreams.pozhiratel-snov` → `magic.nightmares.pozhiratel-snov`
- `magic.dreams.vostorg` → `magic.nightmares.vostorg`
- `magic.dreams.ognennyy-shar` → `magic.nightmares.ognennyy-shar`
- `magic.dreams.manipulyatsiya` → `magic.nightmares.manipulyatsiya`

All 51 Secrets now carry an exact `mystic_path.path_id` and `requires_path` relationship to an HK-RDB `Mystic Path`. All 48 Combat Arts now explicitly require the `Martial Path` family in addition to their existing weapon or condition requirements.

The validator fails on mismatched Secret IDs, path requirements, path relationships, non-mystic targets, or Combat Arts without the Martial Path family requirement.
