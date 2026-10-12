from game import config
from game.achievements import ACHIEVEMENTS, PlayerMetrics, build_metrics, newly_unlocked, unlocked
from game.leveling import total_xp_for_level
from game.titles import character_class, rank_for_level


def test_achievement_keys_unique_and_metrics_valid():
    keys = [a.key for a in ACHIEVEMENTS]
    assert len(keys) == len(set(keys))
    fields = PlayerMetrics.__dataclass_fields__
    assert all(a.metric in fields and a.target > 0 for a in ACHIEVEMENTS)


def test_nothing_unlocked_for_new_player():
    assert unlocked(PlayerMetrics()) == []


def test_newly_unlocked_on_first_completion():
    new = newly_unlocked(PlayerMetrics(), PlayerMetrics(completions=1))
    assert [a.key for a in new] == ["first_step"]


def test_newly_unlocked_ignores_already_unlocked():
    before = PlayerMetrics(completions=10, best_streak=2)
    after = PlayerMetrics(completions=11, best_streak=3)
    assert [a.key for a in newly_unlocked(before, after)] == ["streak_3"]


def test_build_metrics():
    stats = {key: 0 for key in config.STAT_KEYS} | {"strength": total_xp_for_level(5)}
    m = build_metrics(stats, completions=42, best_streak=6)
    assert m.completions == 42 and m.best_streak == 6
    assert m.max_stat_level == 5 and m.min_stat_level == 1
    assert m.total_level >= 5


def test_harmony_requires_all_stats():
    level3 = total_xp_for_level(3)
    almost = {key: level3 for key in config.STAT_KEYS} | {"charisma": 0}
    assert build_metrics(almost, 0, 0).min_stat_level == 1
    full = {key: level3 for key in config.STAT_KEYS}
    assert "harmony" in {a.key for a in unlocked(build_metrics(full, 0, 0))}


def test_rank_for_level():
    assert rank_for_level(1) == "Новичок"
    assert rank_for_level(2) == "Новичок"
    assert rank_for_level(3) == "Искатель приключений"
    assert rank_for_level(999) == config.RANKS[-1][1]


def test_character_class():
    assert character_class({}) == config.NO_CLASS
    assert character_class({"intellect": 50, "strength": 10}) == "🔮 Маг"
    # при равенстве — первый по порядку конфига
    assert character_class({"charisma": 20, "strength": 20}) == "⚔️ Воин"
