CAS_EVOLUTION.md
Why HK-CAS Looks Like This
This document explains how HK-CAS evolved.
It is intended for developers and AI models maintaining HK-Kit.
Do not skip this document.
Without understanding this evolution it is very easy to accidentally simplify HK-CAS and reintroduce old
problems.
Initial Goal
Originally we wanted a very simple workflow.
Player
->
Character Concept
->
AI
->
Finished Character
It looked elegant.
In practice it failed.
Problem 1
The AI optimized immediately.
It selected mechanics before understanding the player.
This produced technically correct characters that often felt wrong.

Example:
Player:
"A tiny flea wearing another bug's shell."
AI immediately optimized around armor.
Later we discovered that the shell was intended as visual storytelling only.
The entire build had to be rebuilt.
Lesson
Optimization must never happen before understanding the player's vision.
Solution
Vision Lock.
Vision Lock became mandatory.
Problem 2
The AI silently assumed missing information.
Whenever several options looked equally good it simply picked one.
Different AI models produced different characters.
Lesson
Questions are desirable.
Questions reduce mistakes.
Questions improve player satisfaction.

Solution
No Silent Assumptions.
Whenever player fantasy influences mechanics, the AI must ask.
Problem 3
The AI analyzed categories correctly but later forgot why certain options had been preferred.
Optimization became inconsistent.
Lesson
Reasoning must survive category transitions.
Solution
Candidate Registry.
Every category now stores:
A Candidates
B Candidates
Rejected
Reasons
Dependencies
Optimization never relies on memory.
It relies on Candidate Registry.
Problem 4
Project Journal became too large.

It contained:
history
reasoning
candidate tracking
priorities
This made it difficult to maintain.
Lesson
Different kinds of information require different storage.
Solution
Project Journal now stores only project evolution.
Candidate Registry stores mechanical decisions.
Problem 5
HK-CAS depended directly on the PDF.
Different AI models accessed PDFs differently.
Some skipped pages.
Some searched.
Some summarized.
The same workflow produced different results.
Lesson
The rulebook cannot be the operational rules source.

Solution
HK-RDB.
HK-RDB became the only rules source.
The PDF became a maintenance artifact.
Problem 6
Optimization started before every category had been fully analyzed.
This caused hidden inconsistencies.
Lesson
Optimization must wait until all required information exists.
Solution
Candidate Registry must exist for every required category before optimization begins.
If not:
STOP.
Problem 7
Sometimes the AI did not have complete access to the rulebook.
Instead of stopping it continued anyway.
This produced invalid recommendations.
Lesson
Missing data is more dangerous than no data.

Solution
Fail Loudly.
Never invent rules.
Never continue with incomplete rule data.
Problem 8
The AI sometimes optimized away the player's fantasy.
The resulting character became mechanically stronger but no longer matched the original concept.
Lesson
Optimization exists to realize the player's fantasy.
It does not replace it.
Solution
Player Vision First.
This became the central design principle of HK-Kit.
Final Philosophy
HK-CAS is no longer a character builder.
It is a Character Design Pipeline.
Its job is to transform:
Player Fantasy
->
Rules

->
Reasoning
->
Character
while preserving both legality and identity.
Design Principles
Every future modification must preserve the following:
Player Vision First
No Silent Assumptions
Rule Fidelity
Candidate Registry
Project Journal
One Source of Truth
HK-RDB Only
Deterministic Behaviour
Explainability
Auditability
Fail Loudly
If a proposed simplification violates one of these principles, it should be rejected.
Why This Repository Exists
The purpose of HK-Kit is not simply to generate characters.
The purpose is to create an LLM-native framework that any modern AI can use consistently.

The repository should contain enough knowledge that the AI does not need additional explanation from
the user.
The user provides:
Repository
MODE CREATE
Character Concept
Everything else should come from HK-Kit.
Instruction to Future Contributors
Do not simplify HK-CAS unless you first understand why each stage exists.
Almost every stage was added because a real failure occurred during practical testing.
The current architecture is the result of iterative design, not theoretical planning.
Any future improvement should preserve this philosophy.

