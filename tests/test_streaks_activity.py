from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from game.activity import build_activity
from game.limits import local_day
from game.streaks import current_streak, longest_streak

TODAY = date(2026, 10, 12)


def days_back(*offsets: int) -> set[date]:
    return {TODAY - timedelta(days=o) for o in offsets}


def test_current_streak_including_today():
    assert current_streak(days_back(0, 1, 2), TODAY) == 3


def test_streak_alive_if_only_yesterday_marked():
    assert current_streak(days_back(1, 2, 3, 4), TODAY) == 4


def test_streak_broken():
    assert current_streak(days_back(2, 3), TODAY) == 0
    assert current_streak(set(), TODAY) == 0


def test_streak_stops_at_gap():
    assert current_streak(days_back(0, 1, 3, 4, 5), TODAY) == 2


def test_longest_streak():
    assert longest_streak(days_back(0, 1, 3, 4, 5, 6, 10)) == 4
    assert longest_streak([]) == 0
    assert longest_streak([TODAY, TODAY]) == 1


def test_local_day_krasnoyarsk():
    assert local_day(datetime(2026, 10, 12, 16, 59, tzinfo=UTC), "Asia/Krasnoyarsk") == date(2026, 10, 12)
    assert local_day(datetime(2026, 10, 12, 17, 0, tzinfo=UTC), "Asia/Krasnoyarsk") == date(2026, 10, 13)


@dataclass
class Log:
    habit_id: int
    timestamp: datetime
    xp: int


def test_build_activity():
    now = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)  # 17:00 по Красноярску
    logs = [
        Log(1, now - timedelta(days=2), 5),
        Log(1, now - timedelta(days=1), 5),
        Log(1, now, 5),
        Log(1, now - timedelta(hours=1), 5),
        Log(2, now, 13),
        Log(2, now - timedelta(days=5), 13),
    ]
    act = build_activity(logs, now, "Asia/Krasnoyarsk")
    assert act.today == date(2026, 10, 12)
    assert act.today_counts == {1: 2, 2: 1}
    assert act.today_xp == 23
    assert act.today_completions == 3
    assert act.completions == 6
    assert act.total_xp == 46
    assert act.streak == 3
    assert act.best_streak == 3
    assert act.habit_streak(1) == 3
    assert act.habit_streak(2) == 1
    assert act.habit_streak(99) == 0
    assert act.habit_totals == {1: 4, 2: 2}
    week = act.last_days(7)
    assert len(week) == 7 and week[-1] == (act.today, 23) and week[0][0] == date(2026, 10, 6)


def test_activity_respects_timezone_midnight():
    # 16:30 UTC = 23:30 в Красноярске, 17:30 UTC = 00:30 следующего дня
    late = datetime(2026, 10, 12, 16, 30, tzinfo=UTC)
    after_midnight = datetime(2026, 10, 12, 17, 30, tzinfo=UTC)
    act = build_activity([Log(1, late, 5)], after_midnight, "Asia/Krasnoyarsk")
    assert act.today_counts == {}  # лимит сбросился
    assert act.streak == 1         # но серия со вчера жива
