# HK-CAS Overview

HK-CAS is a decision pipeline for creating characters while preserving two things:

- the player's fantasy;
- the legal rules data in HK-RDB.

HK-CAS exists because direct prompt-based character creation failed in repeated testing. Models optimized too early, assumed missing intent, forgot why options were preferred, and used incomplete rule access.

## Non-Negotiable Principles

- Player Vision First
- No Silent Assumptions
- HK-RDB Only
- Candidate Registry Before Optimization
- Compact Project Journal
- Explain Major Decisions
- Fail Loudly On Missing Rules
- Audit Before Final Output

## Boundary

HK-CAS tells the model how to think.

HK-RDB tells the model what the rules are.

Do not mix these roles.
