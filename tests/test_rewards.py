import pytest

from game import config
from game.rewards import apply_rewards
from game.validation import ValidationError


def zero_stats():
    return {key: 0 for key in config.STAT_KEYS}


def test_reward_into_multiple_stats():
    stats = zero_stats()
    outcome = apply_rewards(stats, {"endurance": 10, "discipline": 3})
    assert outcome.gains == {"endurance": 10, "discipline": 3}
    assert outcome.new_stats["endurance"] == 10
    assert outcome.new_stats["discipline"] == 3
    assert outcome.new_stats["strength"] == 0
    assert outcome.total_gain == 13
    assert stats == zero_stats(), "исходный словарь не должен меняться"


def test_gains_are_ordered_like_config():
    outcome = apply_rewards(zero_stats(), {"discipline": 3, "strength": 5})
    assert list(outcome.gains) == ["strength", "discipline"]


def test_missing_stats_default_to_zero():
    outcome = apply_rewards({}, {"spirit": 4})
    assert outcome.new_stats["spirit"] == 4
    assert set(outcome.new_stats) == set(config.STAT_KEYS)


def test_no_level_up_below_threshold():
    stats = zero_stats() | {"intellect": 90}
    outcome = apply_rewards(stats, {"intellect": 5})
    assert not outcome.has_level_up
    assert outcome.stat_level_ups == []
    assert outcome.total_level_up is None


def test_stat_level_up_detected():
    stats = zero_stats() | {"intellect": 98}
    outcome = apply_rewards(stats, {"intellect": 5, "charisma": 1})
    assert len(outcome.stat_level_ups) == 1
    lu = outcome.stat_level_ups[0]
    assert (lu.stat, lu.old_level, lu.new_level) == ("intellect", 1, 2)
    # общий XP 104 — общий уровень тоже стал 2
    assert outcome.total_level_up is not None
    assert (outcome.total_level_up.old_level, outcome.total_level_up.new_level) == (1, 2)


def test_total_level_up_without_stat_level_up():
    stats = zero_stats() | {"strength": 50, "endurance": 48}
    outcome = apply_rewards(stats, {"spirit": 5})
    assert outcome.stat_level_ups == []
    assert outcome.total_level_up is not None


def test_level_up_on_higher_level():
    # 380 XP = 2 ур.; порог 3-го уровня — 100 + 283 = 383
    outcome = apply_rewards(zero_stats() | {"strength": 380}, {"strength": 5})
    lu = outcome.stat_level_ups[0]
    assert (lu.old_level, lu.new_level) == (2, 3)


@pytest.mark.parametrize(
    "rewards",
    [{}, {"luck": 5}, {"strength": 0}, {"strength": -3}, {"strength": 999}, {"strength": 2.5}, {"strength": True}],
)
def test_invalid_rewards_rejected(rewards):
    with pytest.raises(ValidationError):
        apply_rewards(zero_stats(), rewards)
