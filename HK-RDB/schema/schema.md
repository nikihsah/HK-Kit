# HK-RDB Schema

`schema.json` defines the expected structure for HK-RDB data files.

## File Container

Each data file must contain:

- `category`
- `file`
- `complete`
- `items`

## Rule Object

Every rule object must contain:

- `id`
- `type`
- `category`
- `subcategory`
- `subtrait_depth` (optional; `0` for a trait, `1-2` for nested subtraits)
- `name`
- `raw_text`
- `summary`
- `costs`
- `requirements`
- `effects`
- `modifiers`
- `relationships`
- `tags`
- `source`
- `needs_manual_review`
- `parsing_status`: `structured`, `raw_text_authoritative`, `manual_review_required`, or `blocked`

`raw_text_authoritative` means the preserved rule text is authoritative while the
machine-readable effect structure is incomplete. `blocked` objects cannot be used
in a final build.

Draft-derived objects may also retain optional `draft_id` for maintenance traceability.

## Source

Every rule object must include:

- `book`
- `page_start`
- `page_end`

The source reference lets maintainers trace HK-RDB entries back to the original rulebook without letting MODE CREATE read the PDF directly.
