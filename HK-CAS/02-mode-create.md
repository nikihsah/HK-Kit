# MODE CREATE

MODE CREATE transforms a player concept into a legal character.

No state may be skipped.

## Pipeline

1. STATE 0.1 - Repository Initialization
2. STATE 0.2 - HK-RDB Validation Check
3. STATE 0.3 - Intent Lock
4. STATE 0.4 - Vision Lock
5. STATE 0.5 - Constraint Lock
6. STATE 1 - Concept Card
7. STATE 2 - Category Analysis
8. STATE 3 - Element Cards
9. STATE 4 - Candidate Registry
10. STATE 5 - Project Journal Update
11. STATE 6 - Cross-Category Optimization
12. STATE 7 - Build Assembly
13. STATE 8 - Rules Audit
14. STATE 9 - Final Character Output
15. STATE 10 - Post-Creation Handoff (only after a passing Rules Audit)

## Stop Conditions

Stop immediately if:

- HK-RDB validation reports critical errors;
- required rule categories are missing;
- a required mechanic has no source reference;
- player intent is too ambiguous to continue safely;
- a requested mechanic is not present in HK-RDB.

For incomplete HK-RDB, say:

```text
The HK-RDB is incomplete for this operation. Update the database before continuing.
```
