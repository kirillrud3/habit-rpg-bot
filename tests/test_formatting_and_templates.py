import re
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from game import config
from game.achievements import PlayerMetrics
from game.activity import build_activity
from game.formatting import (
    esc,
    format_achievements,
    format_completion,
    format_habit_card,
    format_level_ups,
    format_new_achievements,
    format_profile,
    format_stats,
    plural,
    progress_bar,
)
from game.rewards import apply_rewards
from game.templates import TEMPLATES
from game.validation import (
    ValidationError,
    parse_int,
    validate_character_name,
    validate_daily_limit,
    validate_habit_name,
    validate_rewards,
)

NOW = datetime(2026, 10, 12, 10, 0, tzinfo=UTC)


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


@dataclass
class Log:
    habit_id: int
    timestamp: datetime
    xp: int


@pytest.mark.parametrize(
    ("cur", "total", "length", "expected"),
    [(0, 100, 6, "▱▱▱▱▱▱"), (50, 100, 6, "▰▰▰▱▱▱"), (100, 100, 6, "▰▰▰▰▰▰"), (150, 100, 6, "▰▰▰▰▰▰"), (5, 0, 4, "▰▰▰▰")],
)
def test_progress_bar(cur, total, length, expected):
    assert progress_bar(cur, total, length) == expected


def test_completion_message_matches_spec():
    text = format_completion("📚 Чтение", {"intellect": 5}, 2, 3)
    assert strip_tags(text) == "📚 Чтение выполнено! +5 🧠 Интеллект • Сегодня: 2/3"
    assert "<b>📚 Чтение</b>" in text


def test_completion_message_multi_stat_and_streak():
    text = format_completion("🏃 Пробежка", {"endurance": 10, "discipline": 3}, 1, 3, streak=5)
    assert "+10 🏃 Выносливость, +3 ⚙️ Дисциплина" in text
    assert "Серия: <b>5</b> дней" in text
    assert "Серия" not in format_completion("x", {"intellect": 1}, 1, 3, streak=1)


def test_user_input_is_escaped():
    assert esc("<b>&") == "&lt;b&gt;&amp;"
    text = format_completion("<script>", {"intellect": 1}, 1, 1)
    assert "<script>" not in text and "&lt;script&gt;" in text
    profile = format_profile("<i>Hacker</i>", {}, build_activity([], NOW), PlayerMetrics())
    assert "&lt;i&gt;Hacker&lt;/i&gt;" in profile


@pytest.mark.parametrize(("n", "word"), [(1, "день"), (2, "дня"), (5, "дней"), (11, "дней"), (21, "день"), (22, "дня"), (112, "дней")])
def test_plural(n, word):
    assert plural(n, "день", "дня", "дней") == word


def test_level_up_message_with_rank():
    outcome = apply_rewards({"intellect": 98}, {"intellect": 5})
    text = format_level_ups(outcome)
    assert "🧠 Интеллект: 1 → <b>2</b>" in text
    assert "Общий уровень: 1 → 2" in text
    assert format_level_ups(apply_rewards({}, {"intellect": 1})) is None


def test_profile_contains_all_stats_and_class():
    text = format_profile("Артур", {"strength": 150}, build_activity([], NOW), PlayerMetrics())
    assert "Артур" in text and "⚔️ Воин" in text
    for stat in config.STATS:
        assert stat.label in text


def test_stats_screen():
    logs = [Log(1, NOW, 5), Log(1, NOW, 5), Log(2, NOW, 13)]
    text = format_stats(build_activity(logs, NOW), {1: "📚 Чтение", 2: "🏃 Пробежка"})
    assert "3 отметки" in text and "+23" in text
    assert "📚 Чтение ×2" in text
    assert "Всего выполнений: <b>3</b>" in text
    empty = format_stats(build_activity([], NOW), {})
    assert "пока пусто" in empty


def test_achievements_screen_and_notification():
    text = format_achievements(PlayerMetrics(completions=5))
    assert "✅ 🌱 <b>Первый шаг</b>" in text
    assert "(5/10)" in text
    assert format_new_achievements([]) is None


def test_habit_card():
    text = format_habit_card("🧘 Медитация", {"spirit": 8}, 3, done_today=1, streak=4, total_done=20)
    assert "сегодня 1/3" in text and "<b>20</b>" in text and "4</b> дня" in text


def test_templates_count_and_coverage():
    assert 12 <= len(TEMPLATES) <= 15
    covered = {stat for t in TEMPLATES for stat in t.rewards}
    assert covered == set(config.STAT_KEYS)
    names = [t.name.casefold() for t in TEMPLATES]
    assert len(names) == len(set(names))
    for t in TEMPLATES:
        validate_rewards(t.rewards)
        validate_daily_limit(t.daily_limit)
        validate_habit_name(t.name)


def test_name_validation():
    assert validate_character_name("  Сэр   Ланселот \n") == "Сэр Ланселот"
    for bad in ["", "   ", None, "/start", "x" * 100]:
        with pytest.raises(ValidationError):
            validate_character_name(bad)
    with pytest.raises(ValidationError):
        validate_habit_name("чтение", existing_names=["Чтение"])


def test_parse_int():
    assert parse_int(" 7 ", 1, 10) == 7
    assert parse_int("+3", 1, 10) == 3
    for bad in ["", "abc", "0", "11", "-2", "2.5", None]:
        with pytest.raises(ValidationError):
            parse_int(bad, 1, 10)
