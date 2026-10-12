"""Проверка пользовательского ввода."""
from __future__ import annotations

from collections.abc import Iterable, Mapping

from game import config


class ValidationError(ValueError):
    """Ошибка ввода; текст предназначен для показа пользователю."""


def _clean_name(raw: str | None, max_len: int, what: str) -> str:
    if raw is None:
        raise ValidationError(f"{what} не может быть пустым")
    name = " ".join(raw.split())  # убираем переносы и лишние пробелы
    if not name:
        raise ValidationError(f"{what} не может быть пустым")
    if name.startswith("/"):
        raise ValidationError(f"{what} не может начинаться с «/»")
    if len(name) > max_len:
        raise ValidationError(f"{what} слишком длинное (максимум {max_len} символов)")
    return name


def validate_character_name(raw: str | None) -> str:
    return _clean_name(raw, config.CHARACTER_NAME_MAX_LEN, "Имя")


def validate_habit_name(raw: str | None, existing_names: Iterable[str] = ()) -> str:
    name = _clean_name(raw, config.HABIT_NAME_MAX_LEN, "Название")
    if name.casefold() in {n.casefold() for n in existing_names}:
        raise ValidationError("Привычка с таким названием уже есть")
    return name


def validate_rewards(rewards: Mapping[str, int]) -> dict[str, int]:
    if not rewards:
        raise ValidationError("Привычка должна давать XP хотя бы в одну характеристику")
    result: dict[str, int] = {}
    for stat, xp in rewards.items():
        if stat not in config.STATS_BY_KEY:
            raise ValidationError(f"Неизвестная характеристика: {stat}")
        if isinstance(xp, bool) or not isinstance(xp, int):
            raise ValidationError("XP должен быть целым числом")
        if not 0 < xp <= config.MAX_XP_PER_STAT:
            raise ValidationError(f"XP должен быть от 1 до {config.MAX_XP_PER_STAT}")
        result[stat] = xp
    return result


def parse_int(raw: str | None, low: int, high: int) -> int:
    """Число из текста пользователя в диапазоне [low, high]."""
    text = (raw or "").strip().lstrip("+")
    if not text.isdigit():
        raise ValidationError(f"Нужно целое число от {low} до {high}")
    value = int(text)
    if not low <= value <= high:
        raise ValidationError(f"Нужно число от {low} до {high}")
    return value


def validate_daily_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValidationError("Лимит должен быть целым числом")
    if not config.MIN_DAILY_LIMIT <= limit <= config.MAX_DAILY_LIMIT:
        raise ValidationError(
            f"Лимит должен быть от {config.MIN_DAILY_LIMIT} до {config.MAX_DAILY_LIMIT}"
        )
    return limit
