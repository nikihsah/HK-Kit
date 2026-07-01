# HK-Kit

HK-Kit is an LLM-native framework for creating rules-valid characters for The Unofficial Hollow Knight RPG.

## Quick Start

Отправьте ИИ следующий запрос, заменив текст в квадратных скобках своей концепцией:

```text
Используй репозиторий как обязательную инструкцию выполнения задачи:

https://github.com/nikihsah/HK-Kit

MODE: CREATE
OUTPUT MODE: USER

Концепция персонажа:
[ВСТАВИТЬ КОНЦЕПЦИЮ]

ОБЯЗАТЕЛЬНЫЙ ПРОТОКОЛ

1. Сначала открой и прочитай:
   - AGENTS.md
   - HK-CAS/runtime-create.md
   - HK-RDB/data/index.json
   - HK-RDB/data/manifest.json
   - HK-RDB/data/validation.json

2. HK-CAS является обязательным алгоритмом, а не рекомендацией.
   Нельзя заменять его обычным творческим ответом или общими советами.

3. Используй только HK-RDB как источник игровых правил.
   Не используй память модели для названий, требований, чисел и эффектов.

4. До завершения Intent Lock, Vision Lock и Constraint Lock запрещено:
   - выбирать шаблон;
   - выбирать путь;
   - предлагать черты;
   - выбирать Умение;
   - выбирать оружие, Искусства, магию, амулеты или снаряжение;
   - рассчитывать характеристики;
   - показывать частичную или готовую сборку.

5. Даже если концепция кажется ясной, три Lock-этапа нельзя пропускать.

6. Первый содержательный ответ должен содержать только:
   - подтверждение успешной инициализации HK-Kit;
   - результат проверки HK-RDB;
   - вопросы Intent Lock;
   - вопросы Vision Lock;
   - вопросы Constraint Lock.

7. Не придумывай ответы за игрока.
   В частности, нельзя самостоятельно назначать:
   - стартовую Веху или Ранг;
   - формат игры;
   - роль персонажа;
   - допустимые источники;
   - отношение внешнего образа к механике;
   - предпочтение между мобильностью, стойкостью, уроном и контролем.

8. После Lock-этапов следуй полному pipeline из runtime-create.md:
   Concept Card → Category Analysis → Element Cards →
   Candidate Registry → Category Checkpoints →
   Cross-Category Optimization → Build Assembly →
   Rules Audit → Final Character Sheet.

9. Candidate Registry может содержать только конкретные объекты HK-RDB
   с реальными ID. Абстрактные записи вроде «подходящая черта» запрещены.

10. Художественное переименование механики не заменяет механический выбор.
    Для любого reflavor указывай:
    - официальное название и ID из HK-RDB;
    - отдельное художественное название;
    - подтверждение, что механика не изменилась.

11. MODE CREATE должен завершиться полноценным рассчитанным чарником,
    а не только концептом, описанием или рекомендациями.

12. Если репозиторий не прочитан, HK-RDB невалидна или обязательные данные
    отсутствуют, остановись по Fail Loudly. Не продолжай по памяти.

Перед первым ответом внутренне проверь:

- Прочитан ли runtime-create.md?
- Завершена ли проверка HK-RDB?
- Не выбрал ли я механику раньше Locks?
- Не сделал ли я предположение вместо игрока?

Начни только с инициализации и Lock-вопросов.
```

Expected first response:

```text
I have initialized HK-Kit and validated HK-RDB.

Before selecting mechanics, I need to lock the character intent,
vision, and campaign constraints:

1. ...
2. ...
3. ...
```

You do not need to know or supply HK-CAS internals. The model initializes through `AGENTS.md` and uses the short `HK-CAS/runtime-create.md` route itself. It may ask focused questions when your fantasy creates a real choice.

HK-RDB is the only rules source during character creation; the original PDF is maintainer-only. If required rules are missing or cannot prove legality, HK-Kit fails loudly instead of inventing an answer.

`MODE CREATE` is the only supported v1 mode. Runtime files guide character creation; architecture, build tools, and source-processing documents are for repository maintenance and are not required for ordinary play.

## Mandatory First Response Contract

After receiving a new `MODE CREATE` concept, the model must not select or recommend any template, path, trait, weapon, skill, art, charm, spell, equipment item, or mechanical build component.

The first substantive response must perform only:

1. Repository and HK-RDB validation.
2. Intent Lock.
3. Vision Lock.
4. Constraint Lock questions.

This rule applies even when the concept appears clear. A clear concept may reduce the number of questions, but it never permits skipping the three Locks. Mechanical recommendations and character assembly begin only after all three Locks are complete.

## Информация для пользователя

HK-Kit помогает превратить обычное описание персонажа в готового и легального героя для The Unofficial Hollow Knight RPG. Пользователю не нужно разбираться во внутреннем устройстве HK-CAS, самостоятельно просматривать базу правил или заранее выбирать механики.

Достаточно написать:

```text
MODE CREATE

Концепт:
Маленький жук-разведчик, который носит чужой панцирь и побеждает хитростью, а не силой.
```

Первый содержательный ответ ИИ не должен предлагать путь, шаблон, черты, оружие, снаряжение или готовую сборку. Сначала он подтверждает загрузку HK-Kit и проверку HK-RDB, затем задаёт вопросы Intent Lock, Vision Lock и Constraint Lock. Даже ясный концепт не позволяет пропустить эти три этапа.

Сначала ИИ уточнит только те детали, которые действительно влияют на персонажа: цель игры, желаемый стиль, обязательные элементы образа и ограничения. Например, он может спросить, должен ли чужой панцирь давать механическую защиту или оставаться частью внешности.

После этого ИИ:

- изучит все необходимые варианты из HK-RDB;
- подберёт конкретные легальные механики под задумку;
- соберёт полный лист персонажа;
- опишет его боевой и небоевой стиль игры;
- объяснит ключевые решения;
- проведёт итоговую проверку правил и зависимостей.

Если в HK-RDB недостаточно данных для доказуемо легальной сборки, ИИ остановится и прямо сообщит об этом, а не станет придумывать отсутствующие правила.
