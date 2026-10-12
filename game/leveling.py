"""Расчёт уровней по накопленному XP."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from game import config


@dataclass(frozen=True)
class LevelInfo:
    level: int
    xp_total: int        # весь накопленный XP
    xp_into_level: int   # сколько набрано на текущем уровне
    xp_for_next: int     # сколько нужно на текущем уровне до следующего

    @property
    def progress(self) -> float:
        if self.xp_for_next <= 0:
            return 1.0
        return min(1.0, self.xp_into_level / self.xp_for_next)


def level_info(xp: int) -> LevelInfo:
    """Уровень и прогресс для заданного суммарного XP."""
    if xp < 0:
        raise ValueError("XP не может быть отрицательным")
    level = config.START_LEVEL
    remaining = xp
    while level < config.MAX_LEVEL:
        need = config.xp_to_next_level(level)
        if remaining < need:
            break
        remaining -= need
        level += 1
    return LevelInfo(
        level=level,
        xp_total=xp,
        xp_into_level=remaining,
        xp_for_next=config.xp_to_next_level(level),
    )


def level_for_xp(xp: int) -> int:
    return level_info(xp).level


def total_xp_for_level(level: int) -> int:
    """Минимальный суммарный XP, при котором достигается `level`."""
    if level < config.START_LEVEL:
        raise ValueError("Уровень меньше стартового")
    return sum(config.xp_to_next_level(n) for n in range(config.START_LEVEL, level))


def total_xp(stats_xp: Mapping[str, int]) -> int:
    return sum(stats_xp.get(key, 0) for key in config.STAT_KEYS)


def total_level_info(stats_xp: Mapping[str, int]) -> LevelInfo:
    """Общий уровень персонажа: та же формула от суммы XP всех статов."""
    return level_info(total_xp(stats_xp))
