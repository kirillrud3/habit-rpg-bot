"""Все игровые константы и формулы.

Меняй значения здесь — остальной код (бот, БД, тесты формул) подхватит их сам.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Характеристики
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StatDef:
    key: str          # ключ в БД — не меняй у существующих статов
    emoji: str
    name: str
    description: str

    @property
    def label(self) -> str:
        return f"{self.emoji} {self.name}"


STATS: tuple[StatDef, ...] = (
    StatDef("strength", "💪", "Сила", "силовые упражнения"),
    StatDef("endurance", "🏃", "Выносливость", "кардио"),
    StatDef("intellect", "🧠", "Интеллект", "обучение, чтение"),
    StatDef("spirit", "🧘", "Дух", "медитация, дневник, ментальное здоровье"),
    StatDef("charisma", "🗣", "Харизма", "общение"),
    StatDef("discipline", "⚙️", "Дисциплина", "режим, сон, быт"),
)
STAT_KEYS: tuple[str, ...] = tuple(s.key for s in STATS)
STATS_BY_KEY: dict[str, StatDef] = {s.key: s for s in STATS}


# ---------------------------------------------------------------------------
# Уровни
# ---------------------------------------------------------------------------
XP_BASE = 100
XP_EXPONENT = 1.5
START_LEVEL = 1
MAX_LEVEL = 1000  # страховка от бесконечного цикла при экзотических формулах


def xp_to_next_level(level: int) -> int:
    """Сколько XP нужно, чтобы перейти с уровня `level` на `level + 1`."""
    return max(1, round(XP_BASE * level ** XP_EXPONENT))


# ---------------------------------------------------------------------------
# Привычки
# ---------------------------------------------------------------------------
DEFAULT_DAILY_LIMIT = 3
MIN_DAILY_LIMIT = 1
MAX_DAILY_LIMIT = 20
DAILY_LIMIT_CHOICES: tuple[int, ...] = (1, 2, 3, 5, 10)  # кнопки при создании привычки

XP_CHOICES: tuple[int, ...] = (1, 2, 3, 5, 8, 10, 15, 20)  # кнопки выбора XP
MAX_XP_PER_STAT = 50

MAX_HABITS_PER_USER = 30
HABIT_NAME_MAX_LEN = 40
CHARACTER_NAME_MAX_LEN = 32


# ---------------------------------------------------------------------------
# Время
# ---------------------------------------------------------------------------
DEFAULT_TIMEZONE = "Asia/Krasnoyarsk"
DAY_START_HOUR = 0  # во сколько по местному времени "сбрасывается" день


# Часовые пояса для выбора в настройках: (IANA-имя, город, подпись)
TIMEZONE_CHOICES: tuple[tuple[str, str, str], ...] = (
    ("Europe/Kaliningrad", "Калининград", "UTC+2"),
    ("Europe/Moscow", "Москва", "UTC+3"),
    ("Europe/Samara", "Самара", "UTC+4"),
    ("Asia/Yekaterinburg", "Екатеринбург", "UTC+5"),
    ("Asia/Omsk", "Омск", "UTC+6"),
    ("Asia/Novosibirsk", "Новосибирск", "UTC+7"),
    ("Asia/Krasnoyarsk", "Красноярск", "UTC+7"),
    ("Asia/Irkutsk", "Иркутск", "UTC+8"),
    ("Asia/Yakutsk", "Якутск", "UTC+9"),
    ("Asia/Vladivostok", "Владивосток", "UTC+10"),
    ("Asia/Magadan", "Магадан", "UTC+11"),
    ("Asia/Kamchatka", "Камчатка", "UTC+12"),
)


# ---------------------------------------------------------------------------
# Звания и классы
# ---------------------------------------------------------------------------
# (минимальный общий уровень, звание) — по возрастанию уровня
RANKS: tuple[tuple[int, str], ...] = (
    (1, "Новичок"),
    (3, "Искатель приключений"),
    (5, "Странник"),
    (8, "Ветеран"),
    (12, "Герой"),
    (16, "Чемпион"),
    (20, "Легенда"),
    (30, "Мифический герой"),
)

# Класс персонажа определяется самой прокачанной характеристикой
STAT_CLASSES: dict[str, str] = {
    "strength": "⚔️ Воин",
    "endurance": "🏹 Следопыт",
    "intellect": "🔮 Маг",
    "spirit": "☯️ Монах",
    "charisma": "🎻 Бард",
    "discipline": "🛡 Паладин",
}
NO_CLASS = "🌱 Новобранец"


# ---------------------------------------------------------------------------
# Отображение
# ---------------------------------------------------------------------------
PROGRESS_BAR_LENGTH = 10
MINI_BAR_LENGTH = 8
HISTORY_BAR_LENGTH = 8
STATS_HISTORY_DAYS = 7
BAR_FILLED = "▰"
BAR_EMPTY = "▱"
