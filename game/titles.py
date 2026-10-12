"""Звание (по общему уровню) и класс (по главной характеристике)."""
from __future__ import annotations

from collections.abc import Mapping

from game import config


def rank_for_level(level: int) -> str:
    title = config.RANKS[0][1]
    for min_level, name in config.RANKS:
        if level >= min_level:
            title = name
    return title


def character_class(stats_xp: Mapping[str, int]) -> str:
    """Класс по самому прокачанному стату; при равенстве — первый в порядке конфига."""
    best_key, best_xp = None, 0
    for key in config.STAT_KEYS:
        xp = stats_xp.get(key, 0)
        if xp > best_xp:
            best_key, best_xp = key, xp
    if best_key is None:
        return config.NO_CLASS
    return config.STAT_CLASSES.get(best_key, config.NO_CLASS)
