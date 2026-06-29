PROJECT_SPEC.md
HK-Kit v1.0 Project Specification
1. Purpose
HK-Kit is an LLM-native knowledge pack and character design framework for The Unofficial Hollow
Knight RPG.
The repository exists so that a user can give an AI model a repository link, select a mode, provide a
character concept, and receive a rules-valid character built through a deterministic design pipeline.
HK-Kit is currently focused only on:
MODE CREATE
Other modes may be documented as future extensions, but they are not part of the v1.0
implementation target.
2. Primary User Workflow
The final user workflow must be as simple as possible.
The user should be able to write:
Repository:
https://github.com/<owner>/<repo>
MODE CREATE
Concept:
<character concept>
The model should then initialize itself from the repository and proceed.
The user should not need to manually explain HK-CAS.
The user should not need to attach the rulebook PDF.
The user should not need to attach multiple JSON files.
The repository itself must contain everything the AI needs.

3. Design Target
HK-Kit is primarily designed for AI models, not humans.
This means:
documentation must be LLM-friendly;
files should be small and focused;
the repository should have a clear entry point;
required reading order must be explicit;
rules must be normalized and machine-readable;
the AI must not need to infer repository structure.
The repository should be understandable by a modern LLM after reading AGENTS.md.
4. Core Principle
The central principle is:
Player Vision First
The system must optimize the character only after it understands the player's intent, fantasy, desired
playstyle, and constraints.
Questions are allowed.
Questions are encouraged.
A model asking good questions is behaving correctly.
5. Mandatory Behaviour for AI Models
Any AI model using this repository must:
Read AGENTS.md first.
Follow the reading order defined there.
Use HK-CAS as the decision pipeline.
Use HK-RDB as the only rules source.
Never read the PDF during character creation.
Start MODE CREATE with Intent Lock, Vision Lock, and Constraint Lock.
Ask questions if the player's concept is ambiguous.
Maintain Candidate Registry.
Maintain Project Journal.
Perform final audit before output.
Stop if rules are missing or invalid.
Never invent missing mechanics.
Explain major decisions.

6. Repository Structure
The repository must use this structure:
HK-Kit/
  README.md
  AGENTS.md
  PROJECT_SPEC.md
  CHANGELOG.md
  LICENSE
  HK-CAS/
    README.md
    00-overview.md
    01-modes.md
    02-mode-create.md
    03-intent-lock.md
    04-vision-lock.md
    05-constraint-lock.md
    06-candidate-registry.md
    07-project-journal.md
    08-optimization.md
    09-audit.md
    prompt-template.md
  HK-RDB/
    README.md
    schema/
      schema.json
      schema.md
    data/
      index.json
      core-rules.json
      templates.json
      traits.json
      paths.json
      skills.json
      advancement.json
      combat-arts.json
      magic.json
      charms.json
      equipment.json
      combat-rules.json
      travel-rest-rules.json
      social-rules.json
      glossary.json
      validation.json
      version.json

examples/
    MODE_CREATE.md
    example-concept.md
    example-output.md
  docs/
    architecture.md
    design-principles.md
    faq.md
    maintenance.md
    rdb-build-process.md
  tools/
    extract_layer0.py
    build_rdb.py
    validate_rdb.py
    export_sqlite.py
  tests/
    test_schema.py
    test_required_categories.py
    test_relationships.py
7. AGENTS.md
AGENTS.md is the most important file for AI models.
It must explain:
what HK-Kit is;
how to initialize;
what files to read;
which mode is currently supported;
that PDF is forbidden during character creation;
how to handle missing data;
how to ask player questions;
how to maintain Candidate Registry and Project Journal.
AGENTS.md must be short enough to read quickly but precise enough to guide model behaviour.
It is the operational entry point.
8. README.md
README.md is for human users.
It must be short and practical.

It should explain:
what HK-Kit is;
how to use it;
quick start;
current limitations;
repository structure;
supported mode: MODE CREATE.
It should not contain the full specification.
9. HK-CAS
HK-CAS is the character design pipeline.
It does not contain rules.
It only describes how to reason, compare, ask questions, optimize, and audit.
HK-CAS must use HK-RDB for all mechanics.
10. MODE CREATE Pipeline
MODE CREATE must follow this order:
STATE 0.1 - Repository Initialization
STATE 0.2 - HK-RDB Validation Check
STATE 0.3 - Intent Lock
STATE 0.4 - Vision Lock
STATE 0.5 - Constraint Lock
STATE 1 - Concept Card
STATE 2 - Category Analysis
STATE 3 - Element Cards
STATE 4 - Candidate Registry
STATE 5 - Project Journal Update
STATE 6 - Cross-Category Optimization
STATE 7 - Build Assembly
STATE 8 - Rules Audit
STATE 9 - Final Character Output
No state may be skipped.
11. Intent Lock
Intent Lock determines why the player is creating the character.

Examples:
campaign character;
one-shot character;
optimized build;
roleplay-first character;
thematic character;
experimental build;
beginner-friendly build.
If unclear, the model asks.
12. Vision Lock
Vision Lock determines how the player imagines the character.
The model should clarify:
appearance;
fantasy;
combat feeling;
movement style;
personality;
role in group;
what must be avoided;
whether magic is allowed;
whether strange body mechanics are allowed;
whether a visual concept should become mechanics or stay aesthetic.
The model must not fear questions here.
This stage exists specifically to prevent silent assumptions.
13. Constraint Lock
Constraint Lock determines:
starting level/rank;
allowed rule sources;
banned options;
campaign restrictions;
party role;
expected difficulty;
house rules;
tone restrictions.
If unknown, defaults may be proposed, but important uncertainty should be surfaced.

14. Category Analysis
For each relevant category, the model must:
read relevant HK-RDB files;
build a full category map;
identify subcategories;
analyze every applicable element;
create Element Cards;
classify candidates;
update Candidate Registry.
The model must not skip a category because it appears irrelevant.
15. Element Cards
Each analyzed element must produce an internal card containing:
id;
name;
type;
category;
subcategory;
rules summary;
cost;
requirements;
conflicts;
role;
what it adds;
what weakness it solves;
synergies;
conflicts with concept;
candidate status.
Element Cards may be summarized in user output, but they must exist in reasoning and Candidate
Registry.
16. Candidate Registry
Candidate Registry is mandatory.
It stores concrete candidates, not vague categories.
Each entry must include:
id;
name;
category;

status: A / B / Rejected / Deferred;
reason;
dependencies;
conflicts;
source reference.
Candidate Registry must never be compressed away.
Optimization may only use Candidate Registry.
17. Project Journal
Project Journal is separate from Candidate Registry.
It stores:
current strengths;
unresolved weaknesses;
player answers;
priority shifts;
open questions;
resolved conflicts.
It must remain compact.
18. Optimization
Optimization begins only after Candidate Registry exists for every required category.
Optimization must:
remove duplicates;
resolve conflicts;
preserve player vision;
preserve legality;
avoid unnecessary complexity;
avoid mechanics that change the character fantasy unless explicitly approved.
19. Audit
Audit must verify:
template legality;
characteristic values;
resource values;
hunger limit;

trait count;
subtrait parent requirements;
load;
path requirements;
skill rank;
arts and techniques;
charms and marks;
equipment;
combat loop;
missing fields;
unresolved dependencies.
A character is not complete before audit.
20. HK-RDB
HK-RDB is the only rules source during character creation.
It must contain normalized rules from the book.
HK-RDB must be split into focused JSON files rather than one huge file.
Each rule object must include:
id;
type;
category;
subcategory;
name;
raw_text;
summary;
costs;
requirements;
effects;
modifiers;
relationships;
tags;
source;
needs_manual_review.
21. HK-RDB Data Files
Required files:
core-rules.json
templates.json
traits.json
paths.json

skills.json
advancement.json
combat-arts.json
magic.json
charms.json
equipment.json
combat-rules.json
travel-rest-rules.json
social-rules.json
glossary.json
validation.json
version.json
22. HK-RDB Object Requirements
Every object must have:
{
"id": "stable.id",
"type": "trait",
"category": "Traits",
"subcategory": "Natural Weapons",
"name": "Example",
"raw_text": "...",
"summary": "...",
"costs": {},
"requirements": [],
"effects": [],
"modifiers": {},
"relationships": [],
"tags": [],
"source": {
"book": "The Unofficial Hollow Knight RPG - RUS",
"page_start": 0,
"page_end": 0
},
"needs_manual_review": false
}
23. Source References
Every object must include page references.
The AI must be able to trace any decision back to HK-RDB and then to the original book page if needed.

24. Validation
Validation must check:
required files exist;
JSON is valid;
IDs are unique;
required categories exist;
suboptions have valid parents;
relationships point to existing objects;
no object is missing raw_text;
no object is missing source;
all required categories have coverage;
critical errors are absent.
If validation has critical errors, MODE CREATE must stop.
25. PDF Policy
PDF is allowed only for maintainers rebuilding HK-RDB.
PDF is forbidden during MODE CREATE.
If HK-RDB is incomplete, the model must stop and request HK-RDB update.
26. Examples
The repository must include at least one MODE CREATE example showing:
user input;
model initialization;
Vision Lock questions;
Candidate Registry sample;
Project Journal sample;
final character output;
audit.
27. Tools
Tools should support:
extracting PDF into Layer 0;
building HK-RDB from extracted text;
validating HK-RDB;
exporting optional SQLite.

Tools are for maintainers, not ordinary users.
28. Initial Implementation Target
For the first implementation, Codex should create:
repository structure;
README.md;
AGENTS.md;
HK-CAS documents;
HK-RDB schema;
placeholder data files;
validation scripts;
example MODE CREATE;
documentation explaining how to build HK-RDB from PDF.
Do not fabricate complete rules data unless the source PDF is provided and processed.
29. Handling Missing Rule Data
If HK-RDB is incomplete, the model must say:
"The HK-RDB is incomplete for this operation. Update the database before continuing."
It must not fill missing rules from memory.
30. Success Criteria for v1.0
v1.0 is successful when:
a user can provide repository link and MODE CREATE;
an AI model can initialize from AGENTS.md;
the AI can validate HK-RDB availability;
the AI starts with Intent Lock and Vision Lock;
the AI asks useful questions when needed;
the AI creates Candidate Registry;
the AI creates Project Journal;
the AI builds and audits a character using only HK-RDB;
the AI does not consult PDF during character creation.
31. Codex Implementation Instructions
Before coding:
Read this full PROJECT_SPEC.

Summarize the architecture.
Identify ambiguities.
Ask questions if required.
Propose implementation order.
Wait for approval before large implementation.
Do not immediately generate the whole project unless explicitly instructed.

