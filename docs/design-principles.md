# Design Principles

## Player Vision First

The model must understand the player's fantasy before optimization.

## No Silent Assumptions

If player fantasy changes mechanics, ask.

## HK-RDB Only

During MODE CREATE, all rules must come from HK-RDB.

## Candidate Registry

The model must track concrete candidates, statuses, reasons, dependencies, conflicts, and source references.

## Project Journal

The model must keep compact project evolution separate from mechanical candidate tracking.

## Fail Loudly

Missing rules are safer than invented rules.

If HK-RDB is incomplete, stop.
