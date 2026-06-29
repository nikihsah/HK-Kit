# HK-RDB Build Process

HK-RDB should be built in layers.

## Layer 0: Raw Extraction

Extract text from the PDF with page references.

This layer is for maintainers only and is not used during MODE CREATE.

## Layer 1: Rule Candidates

Split extracted text into candidate rule objects.

Do not normalize aggressively yet.

## Layer 2: Normalized Rule Objects

Convert candidates into schema-compliant HK-RDB objects:

- stable ID;
- type;
- category;
- subcategory;
- name;
- raw text;
- summary;
- costs;
- requirements;
- effects;
- modifiers;
- relationships;
- tags;
- source;
- manual review flag.

## Layer 3: Validation

Run:

```bash
python tools/validate_rdb.py
```

MODE CREATE is allowed only when validation reports `mode_create_ready: true`.
