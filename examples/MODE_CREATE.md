# MODE CREATE Example

## User Input

```text
MODE CREATE

Concept:
"A tiny flea wearing another bug's shell. They look fragile, nervous, and fast."
```

## Required First Response

The model validates HK-RDB and asks Intent Lock, Vision Lock, and Constraint Lock questions. It does not choose mechanics yet, including whether the borrowed shell is armor.

## Required Runtime Sequence

After the player answers, the model completes Concept Card, category checkpoints, concrete Candidate Registry, Project Journal, Hunger Budget Ledger, constructed Умения under `skills.overview`, optimization, Build Assembly, and full Rules Audit.

## Post-Creation Handoff

Only after audit passes:

```text
Персонаж полностью собран и прошёл Rules Audit.

Что сделать дальше?
1. Сгенерировать изображение персонажа.
2. Заполнить официальный лист персонажа.
3. Что-то добавить или изменить.
4. Завершить работу.
```

The model performs options 1–3 only after the player explicitly selects them.
