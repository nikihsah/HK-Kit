# Optimization

Optimization begins only after Candidate Registry exists for every required category
and every category checkpoint is valid with `complete: true`.

If the registry is missing required categories, stop.
If any checkpoint is missing, invalid, or incomplete, stop.

## Goals

- preserve player vision;
- preserve legality;
- remove duplicates;
- resolve conflicts;
- avoid unnecessary complexity;
- avoid mechanics that change the character fantasy unless explicitly approved.

## Inputs

Optimization may use:

- Candidate Registry;
- Project Journal;
- Intent Lock;
- Vision Lock;
- Constraint Lock;
- HK-RDB source references.

Optimization must not use:

- memory of the PDF;
- invented mechanics;
- untracked candidates;
- unsupported rule sources.
