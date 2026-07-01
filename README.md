# HK-Kit

HK-Kit is an LLM-native framework for creating rules-valid characters for The Unofficial Hollow Knight RPG.

## Quick Start

Give an AI model this repository and write only:

```text
MODE CREATE

Concept:
<your character concept>
```

You do not need to know or supply HK-CAS internals. The model initializes through `AGENTS.md` and uses the short `HK-CAS/runtime-create.md` route itself. It may ask focused questions when your fantasy creates a real choice.

HK-RDB is the only rules source during character creation; the original PDF is maintainer-only. If required rules are missing or cannot prove legality, HK-Kit fails loudly instead of inventing an answer.

`MODE CREATE` is the only supported v1 mode. Runtime files guide character creation; architecture, build tools, and source-processing documents are for repository maintenance and are not required for ordinary play.

## Информация для пользователя

HK-Kit помогает превратить обычное описание персонажа в готового и легального героя для The Unofficial Hollow Knight RPG. Пользователю не нужно разбираться во внутреннем устройстве HK-CAS, самостоятельно просматривать базу правил или заранее выбирать механики.

Достаточно написать:

```text
MODE CREATE

Концепт:
Маленький жук-разведчик, который носит чужой панцирь и побеждает хитростью, а не силой.
```

Сначала ИИ уточнит только те детали, которые действительно влияют на персонажа: цель игры, желаемый стиль, обязательные элементы образа и ограничения. Например, он может спросить, должен ли чужой панцирь давать механическую защиту или оставаться частью внешности.

После этого ИИ:

- изучит все необходимые варианты из HK-RDB;
- подберёт конкретные легальные механики под задумку;
- соберёт полный лист персонажа;
- опишет его боевой и небоевой стиль игры;
- объяснит ключевые решения;
- проведёт итоговую проверку правил и зависимостей.

Если в HK-RDB недостаточно данных для доказуемо легальной сборки, ИИ остановится и прямо сообщит об этом, а не станет придумывать отсутствующие правила.
