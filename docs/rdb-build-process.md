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

Run locally after Layer 0 exists:

```bash
python tools/extract_layer1.py --layer0 "sources/layer0/<pdf-name>.layer0.json"
```

By default, output is written to:

```text
sources/layer1/<pdf-name>.layer1.json
```

Generated Layer 1 files are ignored by Git.

Layer 1 candidates are not final rules. They preserve raw text and source references while adding conservative review metadata:

- candidate ID;
- `needs_review` status;
- category hint;
- title hint;
- raw text;
- page reference;
- review notes.

The category hint is only a hint. Maintainers must review it before building HK-RDB.

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

Generate local drafts:

```bash
python tools/build_rdb.py --layer1 "sources/layer1/<pdf-name>.layer1.json"
```

By default, output is written to:

```text
sources/layer2/<pdf-name>.rdb-draft/data/
```

Generated Layer 2 files are ignored by Git.

Layer 1 marks covers, credits, tables of contents, introductory prose, and
external GM resource pages as `non-rules`. The builder records these candidates
in the manifest with reason `non_rule_content`; they are intentionally excluded
from HK-RDB rather than left as unresolved rule candidates.

`glossary.json` is a derived term index. The builder creates its entries from
canonical objects in `core-rules.json`, `combat-rules.json`,
`travel-rest-rules.json`, and `social-rules.json`. Each glossary entry points
back to its canonical object with a `defined_by` relationship and preserves the
same book page reference. Do not maintain glossary mechanics as a separate
source of truth.

Layer 2 output is still not final HK-RDB. It is an HK-RDB-shaped review workspace:

- every generated object has `needs_manual_review: true`;
- every generated object receives `layer2-draft` and `needs-review` tags;
- unknown candidates are skipped and listed in the draft manifest;
- draft files must not be copied into `HK-RDB/data/` until reviewed.

## Review Manifests

Create a local review manifest:

```bash
python tools/review_drafts.py --draft-root "sources/layer2/<pdf-name>.rdb-draft"
```

By default, output is written to:

```text
sources/reviews/<pdf-name>.review.json
```

Review manifests are ignored by Git.

Each entry starts with:

- `decision: pending`;
- checklist fields set to `false`;
- source page reference;
- recommended next action.

An object may be promoted into final HK-RDB only after maintainer review.

## Promoted Snapshots

Create a local promoted snapshot:

```bash
python tools/promote_reviewed.py \
  --draft-root "sources/layer2/<pdf-name>.rdb-draft" \
  --review "sources/reviews/<pdf-name>.review.json"
```

By default, output is written to:

```text
sources/promoted/<pdf-name>.promotion/HK-RDB/data/
```

Promoted snapshots are ignored by Git.

Only review entries are promoted when:

- `decision` is `accepted`;
- every required review check is `true`;
- `issues` is empty;
- the matching draft object exists.

The promoted snapshot is useful for validation. It is not automatically final HK-RDB.

## Layer 3: Validation

Run:

```bash
python tools/validate_rdb.py
```

MODE CREATE is allowed only when validation reports `mode_create_ready: true`.
