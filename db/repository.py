"""Все SQL-запросы приложения.

Методы с пометкой «внутри transaction()» не коммитят сами — их вызывают
из сервисов внутри `async with db.transaction()`.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime

from db.database import Database
from db.models import Habit, LogEntry, User, from_db_ts, to_db_ts
from game import config


def _order_rewards(rewards: Mapping[str, int]) -> dict[str, int]:
    return {k: rewards[k] for k in config.STAT_KEYS if k in rewards}


class Repository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------ users
    async def get_user(self, tg_id: int) -> User | None:
        row = await self.db.fetchone(
            "SELECT tg_id, character_name, timezone, created_at FROM users WHERE tg_id = ?",
            (tg_id,),
        )
        if row is None:
            return None
        return User(row["tg_id"], row["character_name"], row["timezone"], from_db_ts(row["created_at"]))

    async def create_user(self, tg_id: int, character_name: str, timezone: str) -> None:
        async with self.db.transaction():
            await self.db.execute(
                "INSERT INTO users (tg_id, character_name, timezone, created_at) "
                "VALUES (?, ?, ?, ?) ON CONFLICT (tg_id) DO NOTHING",
                (tg_id, character_name, timezone, to_db_ts(datetime.now(UTC))),
            )
            await self.db.executemany(
                "INSERT INTO stats (user_id, stat, xp) VALUES (?, ?, 0) "
                "ON CONFLICT (user_id, stat) DO NOTHING",
                [(tg_id, key) for key in config.STAT_KEYS],
            )

    async def update_character_name(self, tg_id: int, name: str) -> None:
        async with self.db.transaction():
            await self.db.execute("UPDATE users SET character_name = ? WHERE tg_id = ?", (name, tg_id))

    async def update_timezone(self, tg_id: int, timezone: str) -> None:
        async with self.db.transaction():
            await self.db.execute("UPDATE users SET timezone = ? WHERE tg_id = ?", (timezone, tg_id))

    # ------------------------------------------------------------------ stats
    async def get_stats(self, user_id: int) -> dict[str, int]:
        rows = await self.db.fetchall("SELECT stat, xp FROM stats WHERE user_id = ?", (user_id,))
        stats = {key: 0 for key in config.STAT_KEYS}
        for row in rows:
            if row["stat"] in stats:
                stats[row["stat"]] = row["xp"]
        return stats

    async def add_stats_xp(self, user_id: int, gains: Mapping[str, int]) -> None:
        """Внутри transaction()."""
        await self.db.executemany(
            "INSERT INTO stats (user_id, stat, xp) VALUES (?, ?, ?) "
            "ON CONFLICT (user_id, stat) DO UPDATE SET xp = stats.xp + excluded.xp",
            [(user_id, stat, xp) for stat, xp in gains.items()],
        )

    async def subtract_stats_xp(self, user_id: int, losses: Mapping[str, int]) -> None:
        """Внутри transaction(). XP не уходит ниже нуля."""
        await self.db.executemany(
            "UPDATE stats SET xp = CASE WHEN xp > ? THEN xp - ? ELSE 0 END "
            "WHERE user_id = ? AND stat = ?",
            [(xp, xp, user_id, stat) for stat, xp in losses.items()],
        )

    # ----------------------------------------------------------------- habits
    async def _load_rewards(self, habit_ids: list[int]) -> dict[int, dict[str, int]]:
        if not habit_ids:
            return {}
        placeholders = ", ".join("?" for _ in habit_ids)
        rows = await self.db.fetchall(
            f"SELECT habit_id, stat, xp FROM habit_rewards WHERE habit_id IN ({placeholders})",
            habit_ids,
        )
        result: dict[int, dict[str, int]] = {hid: {} for hid in habit_ids}
        for row in rows:
            result[row["habit_id"]][row["stat"]] = row["xp"]
        return {hid: _order_rewards(r) for hid, r in result.items()}

    async def get_habit_rewards(self, habit_id: int) -> dict[str, int]:
        return (await self._load_rewards([habit_id]))[habit_id]

    async def list_habits(self, user_id: int) -> list[Habit]:
        rows = await self.db.fetchall(
            "SELECT id, user_id, name, daily_limit, is_active FROM habits "
            "WHERE user_id = ? AND is_active = ? ORDER BY id",
            (user_id, True),
        )
        rewards = await self._load_rewards([row["id"] for row in rows])
        return [
            Habit(r["id"], r["user_id"], r["name"], r["daily_limit"], bool(r["is_active"]), rewards[r["id"]])
            for r in rows
        ]

    async def habit_names(self, user_id: int) -> dict[int, str]:
        """Имена всех привычек, включая удалённые (для истории)."""
        rows = await self.db.fetchall("SELECT id, name FROM habits WHERE user_id = ?", (user_id,))
        return {row["id"]: row["name"] for row in rows}

    async def get_habit(self, user_id: int, habit_id: int) -> Habit | None:
        """Активная привычка пользователя или None (чужие/удалённые не отдаём)."""
        row = await self.db.fetchone(
            "SELECT id, user_id, name, daily_limit, is_active FROM habits "
            "WHERE id = ? AND user_id = ? AND is_active = ?",
            (habit_id, user_id, True),
        )
        if row is None:
            return None
        rewards = await self._load_rewards([row["id"]])
        return Habit(row["id"], row["user_id"], row["name"], row["daily_limit"], True, rewards[row["id"]])

    async def count_active_habits(self, user_id: int) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) AS n FROM habits WHERE user_id = ? AND is_active = ?", (user_id, True)
        )
        return row["n"] if row else 0

    async def _insert_habit(
        self, user_id: int, name: str, daily_limit: int, rewards: Mapping[str, int]
    ) -> int:
        row = await self.db.fetchone(
            "INSERT INTO habits (user_id, name, daily_limit, is_active, created_at) "
            "VALUES (?, ?, ?, ?, ?) RETURNING id",
            (user_id, name, daily_limit, True, to_db_ts(datetime.now(UTC))),
        )
        assert row is not None
        habit_id = row["id"]
        await self.db.executemany(
            "INSERT INTO habit_rewards (habit_id, stat, xp) VALUES (?, ?, ?)",
            [(habit_id, stat, xp) for stat, xp in rewards.items()],
        )
        return habit_id

    async def create_habit(
        self, user_id: int, name: str, daily_limit: int, rewards: Mapping[str, int]
    ) -> int:
        async with self.db.transaction():
            return await self._insert_habit(user_id, name, daily_limit, rewards)

    async def create_habits(
        self, user_id: int, items: Iterable[tuple[str, int, Mapping[str, int]]]
    ) -> int:
        count = 0
        async with self.db.transaction():
            for name, daily_limit, rewards in items:
                await self._insert_habit(user_id, name, daily_limit, rewards)
                count += 1
        return count

    async def update_habit_name(self, user_id: int, habit_id: int, name: str) -> bool:
        async with self.db.transaction():
            return await self.db.execute(
                "UPDATE habits SET name = ? WHERE id = ? AND user_id = ? AND is_active = ?",
                (name, habit_id, user_id, True),
            ) > 0

    async def update_habit_limit(self, user_id: int, habit_id: int, daily_limit: int) -> bool:
        async with self.db.transaction():
            return await self.db.execute(
                "UPDATE habits SET daily_limit = ? WHERE id = ? AND user_id = ? AND is_active = ?",
                (daily_limit, habit_id, user_id, True),
            ) > 0

    async def replace_habit_rewards(self, user_id: int, habit_id: int, rewards: Mapping[str, int]) -> bool:
        async with self.db.transaction():
            owned = await self.db.fetchone(
                "SELECT id FROM habits WHERE id = ? AND user_id = ? AND is_active = ?",
                (habit_id, user_id, True),
            )
            if owned is None:
                return False
            await self.db.execute("DELETE FROM habit_rewards WHERE habit_id = ?", (habit_id,))
            await self.db.executemany(
                "INSERT INTO habit_rewards (habit_id, stat, xp) VALUES (?, ?, ?)",
                [(habit_id, stat, xp) for stat, xp in rewards.items()],
            )
        return True

    async def deactivate_habit(self, user_id: int, habit_id: int) -> bool:
        async with self.db.transaction():
            changed = await self.db.execute(
                "UPDATE habits SET is_active = ? WHERE id = ? AND user_id = ? AND is_active = ?",
                (False, habit_id, user_id, True),
            )
        return changed > 0

    # ------------------------------------------------------------------- logs
    @staticmethod
    def _log(row) -> LogEntry:
        return LogEntry(row["id"], row["user_id"], row["habit_id"], from_db_ts(row["timestamp"]), row["xp"])

    async def list_logs(self, user_id: int) -> list[LogEntry]:
        rows = await self.db.fetchall(
            "SELECT id, user_id, habit_id, timestamp, xp FROM logs "
            "WHERE user_id = ? ORDER BY timestamp, id",
            (user_id,),
        )
        return [self._log(r) for r in rows]

    async def last_log(self, user_id: int, start: datetime, end: datetime) -> LogEntry | None:
        row = await self.db.fetchone(
            "SELECT id, user_id, habit_id, timestamp, xp FROM logs "
            "WHERE user_id = ? AND timestamp >= ? AND timestamp < ? "
            "ORDER BY timestamp DESC, id DESC LIMIT 1",
            (user_id, to_db_ts(start), to_db_ts(end)),
        )
        return self._log(row) if row else None

    async def get_log_rewards(self, log_id: int) -> dict[str, int]:
        rows = await self.db.fetchall("SELECT stat, xp FROM log_rewards WHERE log_id = ?", (log_id,))
        return _order_rewards({row["stat"]: row["xp"] for row in rows})

    async def insert_log(
        self, user_id: int, habit_id: int, ts: datetime, gains: Mapping[str, int]
    ) -> LogEntry:
        """Внутри transaction()."""
        xp = sum(gains.values())
        row = await self.db.fetchone(
            "INSERT INTO logs (user_id, habit_id, timestamp, xp) VALUES (?, ?, ?, ?) RETURNING id",
            (user_id, habit_id, to_db_ts(ts), xp),
        )
        assert row is not None
        await self.db.executemany(
            "INSERT INTO log_rewards (log_id, stat, xp) VALUES (?, ?, ?)",
            [(row["id"], stat, v) for stat, v in gains.items()],
        )
        return LogEntry(row["id"], user_id, habit_id, ts, xp)

    async def delete_log(self, log_id: int) -> None:
        """Внутри transaction()."""
        await self.db.execute("DELETE FROM log_rewards WHERE log_id = ?", (log_id,))
        await self.db.execute("DELETE FROM logs WHERE id = ?", (log_id,))
