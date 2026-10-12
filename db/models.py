from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class User:
    tg_id: int
    character_name: str
    timezone: str
    created_at: datetime


@dataclass(frozen=True)
class Habit:
    id: int
    user_id: int
    name: str
    daily_limit: int
    is_active: bool
    rewards: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class LogEntry:
    id: int
    user_id: int
    habit_id: int
    timestamp: datetime
    xp: int


def to_db_ts(dt: datetime) -> str:
    """Единый формат времени в БД: ISO 8601 в UTC (строки сравниваются лексикографически)."""
    if dt.tzinfo is None:
        raise ValueError("datetime должен быть timezone-aware")
    return dt.astimezone(UTC).isoformat(timespec="microseconds")


def from_db_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)
