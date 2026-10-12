"""Достижения. Вычисляются из метрик игрока — хранить их в БД не нужно."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from game import config
from game.leveling import level_for_xp, total_level_info


@dataclass(frozen=True)
class PlayerMetrics:
    completions: int = 0
    best_streak: int = 0
    total_level: int = 1
    max_stat_level: int = 1
    min_stat_level: int = 1


@dataclass(frozen=True)
class Achievement:
    key: str
    emoji: str
    title: str
    description: str
    metric: str   # имя поля PlayerMetrics
    target: int

    def value(self, metrics: PlayerMetrics) -> int:
        return getattr(metrics, self.metric)

    def is_unlocked(self, metrics: PlayerMetrics) -> bool:
        return self.value(metrics) >= self.target


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("first_step", "🌱", "Первый шаг", "выполни первую привычку", "completions", 1),
    Achievement("ten", "🔟", "Разминка", "10 выполнений", "completions", 10),
    Achievement("fifty", "🎯", "Вторая натура", "50 выполнений", "completions", 50),
    Achievement("hundred", "💯", "Сотня", "100 выполнений", "completions", 100),
    Achievement("five_hundred", "🏛", "Живая легенда", "500 выполнений", "completions", 500),
    Achievement("streak_3", "🔥", "Разгон", "3 дня подряд с отметками", "best_streak", 3),
    Achievement("streak_7", "🔥", "Неделя огня", "7 дней подряд", "best_streak", 7),
    Achievement("streak_30", "🌋", "Месяц без пропусков", "30 дней подряд", "best_streak", 30),
    Achievement("level_5", "⭐", "Опытный", "общий уровень 5", "total_level", 5),
    Achievement("level_10", "🌟", "Ветеран", "общий уровень 10", "total_level", 10),
    Achievement("level_20", "👑", "Легенда", "общий уровень 20", "total_level", 20),
    Achievement("master", "🎓", "Мастер", "любая характеристика 5 уровня", "max_stat_level", 5),
    Achievement("harmony", "☯️", "Гармония", "все характеристики 3 уровня", "min_stat_level", 3),
)


def build_metrics(stats_xp: Mapping[str, int], completions: int, best_streak: int) -> PlayerMetrics:
    levels = [level_for_xp(stats_xp.get(key, 0)) for key in config.STAT_KEYS]
    return PlayerMetrics(
        completions=completions,
        best_streak=best_streak,
        total_level=total_level_info(stats_xp).level,
        max_stat_level=max(levels),
        min_stat_level=min(levels),
    )


def unlocked(metrics: PlayerMetrics) -> list[Achievement]:
    return [a for a in ACHIEVEMENTS if a.is_unlocked(metrics)]


def newly_unlocked(before: PlayerMetrics, after: PlayerMetrics) -> list[Achievement]:
    return [a for a in ACHIEVEMENTS if a.is_unlocked(after) and not a.is_unlocked(before)]
