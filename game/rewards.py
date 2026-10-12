"""Начисление XP за выполнение привычки."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from game import config
from game.leveling import level_for_xp, total_xp
from game.validation import validate_rewards


@dataclass(frozen=True)
class LevelUp:
    stat: str | None  # None — общий уровень персонажа
    old_level: int
    new_level: int


@dataclass(frozen=True)
class RewardOutcome:
    gains: dict[str, int]          # сколько XP начислено в каждый стат
    new_stats: dict[str, int]      # XP всех статов после начисления
    stat_level_ups: list[LevelUp] = field(default_factory=list)
    total_level_up: LevelUp | None = None

    @property
    def total_gain(self) -> int:
        return sum(self.gains.values())

    @property
    def has_level_up(self) -> bool:
        return bool(self.stat_level_ups) or self.total_level_up is not None


def apply_rewards(stats_xp: Mapping[str, int], rewards: Mapping[str, int]) -> RewardOutcome:
    """Начисляет `rewards` к `stats_xp` (исходный словарь не меняется)."""
    gains = validate_rewards(rewards)
    old = {key: stats_xp.get(key, 0) for key in config.STAT_KEYS}
    new = dict(old)
    for stat, xp in gains.items():
        new[stat] += xp

    stat_level_ups = []
    for stat in config.STAT_KEYS:  # стабильный порядок
        if stat not in gains:
            continue
        before, after = level_for_xp(old[stat]), level_for_xp(new[stat])
        if after > before:
            stat_level_ups.append(LevelUp(stat, before, after))

    total_before, total_after = level_for_xp(total_xp(old)), level_for_xp(total_xp(new))
    total_level_up = (
        LevelUp(None, total_before, total_after) if total_after > total_before else None
    )

    ordered_gains = {k: gains[k] for k in config.STAT_KEYS if k in gains}
    return RewardOutcome(ordered_gains, new, stat_level_ups, total_level_up)
