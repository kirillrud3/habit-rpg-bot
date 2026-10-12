"""Шаблоны привычек, предлагаемые при старте."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from game import config


@dataclass(frozen=True)
class HabitTemplate:
    name: str
    rewards: Mapping[str, int]
    daily_limit: int = config.DEFAULT_DAILY_LIMIT


TEMPLATES: tuple[HabitTemplate, ...] = (
    # 💪 Сила
    HabitTemplate("🏋️ Силовая тренировка", {"strength": 10, "discipline": 2}, 1),
    HabitTemplate("💪 Отжимания", {"strength": 5}),
    # 🏃 Выносливость
    HabitTemplate("🏃 Пробежка", {"endurance": 10, "discipline": 3}),
    HabitTemplate("🚶 Прогулка 30 минут", {"endurance": 5, "spirit": 2}),
    HabitTemplate("🚴 Велотренировка", {"endurance": 8, "strength": 2}),
    # 🧠 Интеллект
    HabitTemplate("📚 Чтение", {"intellect": 5}),
    HabitTemplate("🎓 Учёба / курс", {"intellect": 8, "discipline": 2}),
    HabitTemplate("🌍 Иностранный язык", {"intellect": 6, "charisma": 2}),
    # 🧘 Дух
    HabitTemplate("🧘 Медитация", {"spirit": 8}),
    HabitTemplate("📓 Дневник", {"spirit": 5, "intellect": 2}, 1),
    # 🗣 Харизма
    HabitTemplate("📞 Звонок близким", {"charisma": 6, "spirit": 2}),
    HabitTemplate("🤝 Новое знакомство", {"charisma": 10}),
    HabitTemplate("🎤 Выступление / презентация", {"charisma": 8, "discipline": 2}, 1),
    # ⚙️ Дисциплина
    HabitTemplate("😴 Сон до 23:00", {"discipline": 8, "endurance": 2}, 1),
    HabitTemplate("🧹 Уборка", {"discipline": 5}),
)
