# HK-RDB Build Process

HK-RDB should be built in layers.

## Layer 0: Raw Extraction

Extract text from the PDF with page references.

This layer is for maintainers only and is not used during MODE CREATE.

Run locally:

```bash
python tools/extract_layer0.py --pdf "<path-to-rulebook.pdf>"
```

By default, output is written to:

```text
sources/layer0/<pdf-name>.layer0.json
```

Generated Layer 0 files are ignored by Git because they may contain large portions of the source rulebook.

Do not commit Layer 0 output unless redistribution is explicitly approved.

Layer 0 records are page records, not rules. They preserve:

- source PDF name;
- source PDF hash;
- book name;
- extraction timestamp;
- page number;
- page text;
- extraction warnings.

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
