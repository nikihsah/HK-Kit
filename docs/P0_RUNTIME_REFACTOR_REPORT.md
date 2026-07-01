# P0 Runtime Refactor Report

## Outcome

MODE CREATE now has a short runtime route, evidence-based category coverage, concrete candidate contracts, generated database metadata, and honest handling of incompletely structured effects. Game rules and stable IDs were not changed.

## Problems fixed

- Runtime no longer requires maintainer architecture documents.
- Manifest counts, IDs, subcategories, dependencies, and SHA-256 hashes are generated from canonical files.
- Validation is generated and checks manifest freshness, counts, IDs, relationships, parsing status, and blockers.
- Candidate Registry rejects missing or unknown IDs; optimization is gated by complete checkpoints.
- Design intent is explicitly separated from rules claims and visual details from mechanical requirements.
- MODE CREATE is guarded from unrelated tools and external actions.

## Files added

- `HK-CAS/runtime-create.md`
- `HK-CAS/templates/category-checkpoint.json`
- `HK-RDB/data/manifest.json`
- `tools/generate_manifest.py`
- `tools/generate_parsing_findings.py`
- `tools/migrate_parsing_status.py`
- `tools/runtime_contracts.py`
- `tests/test_p0_runtime.py`
- `docs/P0_UNPARSED_FINDINGS.json`
- `docs/P0_RUNTIME_REFACTOR_REPORT.md`

## Files changed

- Runtime/docs: `AGENTS.md`, `README.md`, `HK-CAS/README.md`, `HK-CAS/06-candidate-registry.md`, `HK-CAS/08-optimization.md`.
- Schema/metadata: `HK-RDB/schema/schema.json`, `schema.md`, `HK-RDB/data/index.json`, `validation.json`.
- Release tooling/tests: `tools/validate_rdb.py`, `publish_rdb.py`, `approve_review.py`, `tests/test_required_categories.py`, `test_schema.py`.
- All 14 rule data files received only the new `parsing_status` field plus normalized JSON formatting.

## Data migration and findings

All 760 rule objects now have `parsing_status`: 156 are `structured`; 604 containing `unparsed_*` effects are `raw_text_authoritative`. No object is marked `manual_review_required` or `blocked`. The complete per-ID report, including evidence required before further structuring, is `docs/P0_UNPARSED_FINDINGS.json`.

The raw rule text remains authoritative for those 604 objects. They were not reinterpreted. This is why current validation is `pass_with_warnings`, not `pass`.

No game rule, stable ID, rule text, cost, modifier, requirement, effect, or relationship was changed. A semantic comparison against `HEAD`, after removing only `parsing_status`, found zero differences in rule objects.

## Validation results

- Full test suite: 136 tests passed.
- HK-RDB validator: `pass_with_warnings`; 760 items; zero critical errors, duplicate IDs, missing fields, broken relationship targets, manual-review items, or blocked items.
- Manifest freshness: current; actual counts and hashes match.
- JSON: all files parse and are canonically formatted; all 14 rule containers pass the HK-RDB JSON Schema.

## Known limitations and P1 recommendations

- Machine-readable effects remain incomplete for 604 objects; runtime must use `raw_text` for them.
- P1 should structure effects category by category only after maintainer source verification, replacing `raw_text_authoritative` status only when evidence supports it.
- Add versioned schemas for generated `manifest.json`, `validation.json`, and runtime state artifacts if external consumers begin exchanging them.

## Repeatable blind test

1. In a fresh checkout, run `python tools/generate_manifest.py`.
2. Run `python tools/validate_rdb.py`; expect `pass_with_warnings`, 760 items, 604 `raw_text_authoritative`, 156 `structured`, and no critical errors.
3. Run `python -m unittest discover -s tests -v`; expect 136 passing tests.
4. Give a new model only the repository and a simple `MODE CREATE` concept.
5. Verify it reads `AGENTS.md`, `runtime-create.md`, index, manifest, and validation without reading maintainer architecture documents.
6. Verify it completes locks, per-category checkpoints, concrete Candidate Registry entries, Project Journal, assembly, and audit in order.
7. Present an ambiguous visual detail and verify it asks whether the detail is mechanical.
8. Present “melee through Insight” and verify it searches HK-RDB for a legal path rather than changing the default attack characteristic.
9. Leave one checkpoint incomplete and verify optimization is refused.
10. Verify no unrelated image, office, calendar, email, code, external-action, or refactoring workflow is invoked.
