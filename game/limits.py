"""Дневные лимиты и границы «дня» в часовом поясе пользователя."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from game import config


@dataclass(frozen=True)
class LimitStatus:
    done_today: int
    daily_limit: int

    @property
    def allowed(self) -> bool:
        return self.done_today < self.daily_limit

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.done_today)


def check_limit(done_today: int, daily_limit: int) -> LimitStatus:
    if done_today < 0:
        raise ValueError("done_today не может быть отрицательным")
    if daily_limit < 1:
        raise ValueError("daily_limit должен быть >= 1")
    return LimitStatus(done_today, daily_limit)


def resolve_timezone(tz_name: str | None) -> ZoneInfo:
    """ZoneInfo по имени; при неизвестной зоне — зона по умолчанию."""
    try:
        return ZoneInfo(tz_name or config.DEFAULT_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(config.DEFAULT_TIMEZONE)


def local_day(
    ts: datetime,
    tz_name: str | None = None,
    day_start_hour: int = config.DAY_START_HOUR,
) -> date:
    """К какому «дню» пользователя относится момент `ts`."""
    if ts.tzinfo is None:
        raise ValueError("datetime должен быть timezone-aware")
    if not 0 <= day_start_hour <= 23:
        raise ValueError("day_start_hour должен быть в диапазоне 0..23")
    local = ts.astimezone(resolve_timezone(tz_name))
    return (local - timedelta(hours=day_start_hour)).date()


def day_bounds_utc(
    now: datetime,
    tz_name: str | None = None,
    day_start_hour: int = config.DAY_START_HOUR,
) -> tuple[datetime, datetime]:
    """Начало и конец текущего «дня» пользователя в UTC: [start, end)."""
    day = local_day(now, tz_name, day_start_hour)
    tz = resolve_timezone(tz_name)
    start = datetime.combine(day, time(day_start_hour), tzinfo=tz)
    end = datetime.combine(day + timedelta(days=1), time(day_start_hour), tzinfo=tz)
    return start.astimezone(UTC), end.astimezone(UTC)
