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

## Source

Every rule object must include:

- `book`
- `page_start`
- `page_end`

The source reference lets maintainers trace HK-RDB entries back to the original rulebook without letting MODE CREATE read the PDF directly.
