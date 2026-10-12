# ⚔️ RPG-трекер привычек (Telegram-бот)

Отмечай привычки, получай XP в 6 характеристик и качай уровень персонажа.

## Возможности

- ✅ Отметка привычек с дневным лимитом, начисление XP сразу в несколько характеристик
- ➕ Свои привычки (кнопка в меню или `/add`): название → статы → XP → лимит → превью
- ⚙️ Карточка привычки: переименовать, поменять награды/лимит, удалить
- 🔥 Серии (дни подряд) — общая и по каждой привычке
- 📈 Статистика: сегодня + график XP за 7 дней
- 🏆 13 достижений с прогрессом и уведомлениями
- 🎖 Звание по уровню и класс по главной характеристике (Воин, Маг, Бард…)
- ↩️ Отмена последней отметки за сегодня
- 🔧 Настройки: часовой пояс, имя героя

Команды: `/menu`, `/add`, `/profile`, `/stats`, `/achievements`, `/help`.

## Запуск

Нужен Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
copy .env.example .env          # Linux / macOS: cp .env.example .env
```

Впиши в `.env` токен от [@BotFather](https://t.me/BotFather) (`BOT_TOKEN=...`), затем:

```bash
python main.py
```

База SQLite создастся сама в `data/bot.db`.

## Тесты

```bash
pytest
```

## Структура

```
main.py            точка входа
game/              игровая логика (чистые функции, без aiogram)
  config.py        ВСЕ константы и формулы — крути здесь (уровни, лимиты, звания, классы)
  leveling.py      XP → уровень
  rewards.py       начисление XP в несколько статов, level-up
  limits.py        дневные лимиты, границы дня в часовом поясе
  streaks.py       серии дней подряд
  activity.py      сводка активности по истории
  achievements.py  список достижений и проверка
  titles.py        звание и класс персонажа
  templates.py     шаблоны привычек
  formatting.py    тексты (HTML) и прогресс-бары
  validation.py    проверка ввода
db/                schema.sql, подключение, модели, все SQL-запросы
bot/               хендлеры, клавиатуры, middleware, FSM-состояния
tests/             pytest для game/
```

## Настройка игры

Всё в `game/config.py`:

- `XP_BASE`, `XP_EXPONENT` — формула `round(XP_BASE * N ** XP_EXPONENT)` для перехода N → N+1;
- `DEFAULT_DAILY_LIMIT`, `DAILY_LIMIT_CHOICES`, `XP_CHOICES` — лимиты и кнопки выбора;
- `DEFAULT_TIMEZONE`, `DAY_START_HOUR` — часовой пояс и время сброса дня;
- `STATS` — характеристики (не меняй `key` у уже существующих — это ключ в БД).

Шаблоны привычек — в `game/templates.py`.

## Переход на PostgreSQL

- SQL-запросы лежат только в `db/repository.py`, подключение — только в `db/database.py`.
- Напиши аналог `Database` на `asyncpg` с теми же методами
  (`execute`, `executemany`, `fetchone`, `fetchall`, `transaction`).
- Замени плейсхолдеры `?` на `$1, $2, ...`.
- В `db/schema.sql` в комментарии указано, какие типы поменять.
  `ON CONFLICT` и `RETURNING` работают в обеих СУБД.

## Важно знать

- Состояния диалогов (FSM) хранятся в памяти: при перезапуске бота незаконченное
  создание привычки сбросится. Для продакшена подключи `RedisStorage`.
- Удаление привычки «мягкое» (`is_active = 0`): опыт и история в `logs` сохраняются.
