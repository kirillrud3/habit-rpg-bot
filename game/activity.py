"""Сводка активности пользователя по истории выполнений."""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Protocol

from game import config
from game.limits import local_day
from game.streaks import current_streak, longest_streak


class LogLike(Protocol):
    @property
    def habit_id(self) -> int: ...
    @property
    def timestamp(self) -> datetime: ...
    @property
    def xp(self) -> int: ...


@dataclass(frozen=True)
class Activity:
    today: date
    days: frozenset[date]                    # дни, когда была хоть одна отметка
    habit_days: Mapping[int, frozenset[date]]
    daily_xp: Mapping[date, int]
    today_counts: Mapping[int, int]          # habit_id -> отметок сегодня
    today_xp_by_habit: Mapping[int, int]
    habit_totals: Mapping[int, int]          # habit_id -> отметок за всё время
    completions: int
    total_xp: int

    @property
    def streak(self) -> int:
        return current_streak(self.days, self.today)

    @property
    def best_streak(self) -> int:
        return longest_streak(self.days)

    @property
    def today_xp(self) -> int:
        return self.daily_xp.get(self.today, 0)

    @property
    def today_completions(self) -> int:
        return sum(self.today_counts.values())

    def habit_streak(self, habit_id: int) -> int:
        return current_streak(self.habit_days.get(habit_id, frozenset()), self.today)

    def last_days(self, n: int) -> list[tuple[date, int]]:
        """[(день, XP)] за последние n дней, от старых к новым, включая сегодня."""
        return [
            (day, self.daily_xp.get(day, 0))
            for day in (self.today - timedelta(days=i) for i in range(n - 1, -1, -1))
        ]


def build_activity(
    logs: Iterable[LogLike],
    now: datetime,
    tz_name: str | None = None,
    day_start_hour: int = config.DAY_START_HOUR,
) -> Activity:
    today = local_day(now, tz_name, day_start_hour)
    habit_days: dict[int, set[date]] = defaultdict(set)
    daily_xp: Counter[date] = Counter()
    today_counts: Counter[int] = Counter()
    today_xp: Counter[int] = Counter()
    totals: Counter[int] = Counter()
    completions = total_xp = 0

    for log in logs:
        day = local_day(log.timestamp, tz_name, day_start_hour)
        habit_days[log.habit_id].add(day)
        daily_xp[day] += log.xp
        totals[log.habit_id] += 1
        completions += 1
        total_xp += log.xp
        if day == today:
            today_counts[log.habit_id] += 1
            today_xp[log.habit_id] += log.xp

    return Activity(
        today=today,
        days=frozenset(daily_xp),
        habit_days={hid: frozenset(d) for hid, d in habit_days.items()},
        daily_xp=dict(daily_xp),
        today_counts=dict(today_counts),
        today_xp_by_habit=dict(today_xp),
        habit_totals=dict(totals),
        completions=completions,
        total_xp=total_xp,
    )
