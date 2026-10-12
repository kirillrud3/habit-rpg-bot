-- Схема написана на SQL, совместимом с SQLite и (почти) с PostgreSQL.
-- Для PostgreSQL замени:
--   INTEGER PRIMARY KEY AUTOINCREMENT -> BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
--   tg_id / user_id INTEGER           -> BIGINT
--   is_active INTEGER                 -> BOOLEAN
--   TEXT для дат                      -> TIMESTAMPTZ

CREATE TABLE IF NOT EXISTS users (
    tg_id          INTEGER PRIMARY KEY,
    character_name TEXT    NOT NULL,
    timezone       TEXT    NOT NULL DEFAULT 'Asia/Krasnoyarsk',
    created_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS stats (
    user_id INTEGER NOT NULL REFERENCES users (tg_id) ON DELETE CASCADE,
    stat    TEXT    NOT NULL,
    xp      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, stat)
);

CREATE TABLE IF NOT EXISTS habits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users (tg_id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    daily_limit INTEGER NOT NULL DEFAULT 3,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_habits_user ON habits (user_id, is_active);

CREATE TABLE IF NOT EXISTS habit_rewards (
    habit_id INTEGER NOT NULL REFERENCES habits (id) ON DELETE CASCADE,
    stat     TEXT    NOT NULL,
    xp       INTEGER NOT NULL,
    PRIMARY KEY (habit_id, stat)
);

-- История всех выполнений. Привычки удаляются "мягко" (is_active = 0),
-- поэтому логи сохраняют ссылку на привычку.
CREATE TABLE IF NOT EXISTS logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users (tg_id) ON DELETE CASCADE,
    habit_id  INTEGER NOT NULL REFERENCES habits (id),
    timestamp TEXT    NOT NULL,  -- ISO 8601, UTC
    xp        INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_user_ts ON logs (user_id, timestamp);

-- Сколько XP и в какие статы начислено конкретной отметкой.
-- Нужно, чтобы корректно отменять отметку даже после изменения наград привычки.
CREATE TABLE IF NOT EXISTS log_rewards (
    log_id INTEGER NOT NULL REFERENCES logs (id) ON DELETE CASCADE,
    stat   TEXT    NOT NULL,
    xp     INTEGER NOT NULL,
    PRIMARY KEY (log_id, stat)
);
