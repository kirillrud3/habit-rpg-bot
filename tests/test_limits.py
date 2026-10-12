from datetime import UTC, datetime

import pytest

from game.limits import check_limit, day_bounds_utc, resolve_timezone


@pytest.mark.parametrize(
    ("done", "limit", "allowed", "remaining"),
    [(0, 3, True, 3), (2, 3, True, 1), (3, 3, False, 0), (5, 3, False, 0), (0, 1, True, 1), (1, 1, False, 0)],
)
def test_check_limit(done, limit, allowed, remaining):
    status = check_limit(done, limit)
    assert status.allowed is allowed
    assert status.remaining == remaining


@pytest.mark.parametrize(("done", "limit"), [(-1, 3), (0, 0)])
def test_check_limit_invalid(done, limit):
    with pytest.raises(ValueError):
        check_limit(done, limit)


def test_day_bounds_krasnoyarsk_before_midnight():
    # 16:59 UTC = 23:59 в Красноярске (UTC+7) — ещё 12 октября
    now = datetime(2026, 10, 12, 16, 59, tzinfo=UTC)
    start, end = day_bounds_utc(now, "Asia/Krasnoyarsk")
    assert start == datetime(2026, 10, 11, 17, 0, tzinfo=UTC)
    assert end == datetime(2026, 10, 12, 17, 0, tzinfo=UTC)
    assert start <= now < end


def test_day_bounds_krasnoyarsk_after_midnight():
    # 17:00 UTC = 00:00 13 октября по Красноярску — уже новый день
    now = datetime(2026, 10, 12, 17, 0, tzinfo=UTC)
    start, end = day_bounds_utc(now, "Asia/Krasnoyarsk")
    assert start == datetime(2026, 10, 12, 17, 0, tzinfo=UTC)
    assert end == datetime(2026, 10, 13, 17, 0, tzinfo=UTC)


def test_day_bounds_custom_start_hour():
    # день начинается в 04:00 местного: 02:00 местного относится к предыдущему дню
    now = datetime(2026, 10, 12, 19, 0, tzinfo=UTC)  # 02:00 13 октября по Красноярску
    start, end = day_bounds_utc(now, "Asia/Krasnoyarsk", day_start_hour=4)
    assert start == datetime(2026, 10, 11, 21, 0, tzinfo=UTC)  # 12 окт 04:00 местного
    assert end == datetime(2026, 10, 12, 21, 0, tzinfo=UTC)


def test_day_bounds_requires_aware_datetime():
    with pytest.raises(ValueError):
        day_bounds_utc(datetime(2026, 10, 12, 12, 0), "Asia/Krasnoyarsk")


def test_unknown_timezone_falls_back_to_default():
    assert resolve_timezone("Mars/Olympus").key == "Asia/Krasnoyarsk"
    assert resolve_timezone(None).key == "Asia/Krasnoyarsk"
