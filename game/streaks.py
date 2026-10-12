"""Серии — сколько дней подряд были отметки."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

ONE_DAY = timedelta(days=1)


def current_streak(days: Iterable[date], today: date) -> int:
    """Текущая серия. Если сегодня ещё не отмечено, серия со вчера не считается прерванной."""
    marked = set(days)
    if today in marked:
        day = today
    elif today - ONE_DAY in marked:
        day = today - ONE_DAY
    else:
        return 0
    streak = 0
    while day in marked:
        streak += 1
        day -= ONE_DAY
    return streak


def longest_streak(days: Iterable[date]) -> int:
    ordered = sorted(set(days))
    best = run = 0
    prev: date | None = None
    for day in ordered:
        run = run + 1 if prev is not None and day - prev == ONE_DAY else 1
        best = max(best, run)
        prev = day
    return best
