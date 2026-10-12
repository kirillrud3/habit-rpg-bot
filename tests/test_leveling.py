import pytest

from game import config
from game.leveling import level_info, level_for_xp, total_level_info, total_xp_for_level


@pytest.mark.parametrize(
    ("level", "expected"),
    [(1, 100), (2, 283), (3, 520), (4, 800), (9, 2700), (10, 3162)],
)
def test_xp_to_next_level_formula(level, expected):
    assert config.xp_to_next_level(level) == expected


def test_xp_to_next_level_matches_spec_formula():
    for n in range(1, 50):
        assert config.xp_to_next_level(n) == round(100 * n ** 1.5)


@pytest.mark.parametrize(
    ("xp", "level"),
    [(0, 1), (99, 1), (100, 2), (382, 2), (383, 3), (902, 3), (903, 4)],
)
def test_level_boundaries(xp, level):
    assert level_for_xp(xp) == level


def test_level_info_progress():
    info = level_info(150)
    assert info.level == 2
    assert info.xp_into_level == 50
    assert info.xp_for_next == 283
    assert info.xp_total == 150
    assert 0 < info.progress < 1


def test_total_xp_for_level_is_inverse():
    for lvl in range(1, 30):
        need = total_xp_for_level(lvl)
        assert level_for_xp(need) == lvl
        if need > 0:
            assert level_for_xp(need - 1) == lvl - 1


def test_negative_xp_rejected():
    with pytest.raises(ValueError):
        level_info(-1)


def test_total_level_uses_sum_of_all_stats():
    # каждый стат по 90 XP — каждый на 1 уровне, но сумма 540 даёт общий 3-й уровень
    stats = {key: 90 for key in config.STAT_KEYS}
    assert all(level_for_xp(xp) == 1 for xp in stats.values())
    total = total_level_info(stats)
    assert total.xp_total == 540
    assert total.level == 3


def test_total_level_ignores_unknown_stats():
    assert total_level_info({"strength": 100, "luck": 10_000}).xp_total == 100
