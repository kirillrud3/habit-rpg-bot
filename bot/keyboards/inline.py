from collections.abc import Collection, Mapping, Sequence

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import FormCb, HabitCb, MarkCb, MenuCb, SettingsCb, TplCb, UndoCb
from db.models import Habit
from game import config
from game.formatting import format_rewards_short
from game.templates import HabitTemplate


def _back(kb: InlineKeyboardBuilder, text: str = "⬅️ Меню", action: str = "main") -> None:
    kb.button(text=text, callback_data=MenuCb(action=action))


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Отметить", callback_data=MenuCb(action="mark"))
    kb.button(text="📊 Профиль", callback_data=MenuCb(action="profile"))
    kb.button(text="📈 Статистика", callback_data=MenuCb(action="stats"))
    kb.button(text="⚙️ Привычки", callback_data=MenuCb(action="habits"))
    kb.button(text="🏆 Достижения", callback_data=MenuCb(action="achievements"))
    kb.button(text="➕ Новая привычка", callback_data=MenuCb(action="add"))
    kb.button(text="🔧 Настройки", callback_data=MenuCb(action="settings"))
    kb.adjust(1, 2, 2, 2)
    return kb.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    _back(kb)
    return kb.as_markup()


def profile_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Отметить", callback_data=MenuCb(action="mark"))
    kb.button(text="🏆 Достижения", callback_data=MenuCb(action="achievements"))
    _back(kb)
    kb.adjust(2, 1)
    return kb.as_markup()


def stats_kb(can_undo: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if can_undo:
        kb.button(text="↩️ Отменить последнюю отметку", callback_data=UndoCb(source="stats"))
    kb.button(text="✅ Отметить", callback_data=MenuCb(action="mark"))
    _back(kb)
    kb.adjust(1, 2) if can_undo else kb.adjust(2)
    return kb.as_markup()


def mark_list_kb(
    habits: Sequence[Habit], done_today: Mapping[int, int], streaks: Mapping[int, int], can_undo: bool
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for habit in habits:
        done = done_today.get(habit.id, 0)
        prefix = "✔️ " if done >= habit.daily_limit else ""
        streak = streaks.get(habit.id, 0)
        fire = f"  🔥{streak}" if streak >= 2 else ""
        kb.button(
            text=f"{prefix}{habit.name} · {done}/{habit.daily_limit}{fire}",
            callback_data=MarkCb(habit_id=habit.id),
        )
    rows = [1] * len(habits)
    if can_undo:
        kb.button(text="↩️ Отменить последнюю", callback_data=UndoCb(source="mark"))
        rows.append(1)
    kb.button(text="➕ Привычка", callback_data=MenuCb(action="add"))
    _back(kb)
    kb.adjust(*rows, 2)
    return kb.as_markup()


def no_habits_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Своя привычка", callback_data=MenuCb(action="add"))
    kb.button(text="📋 Из шаблонов", callback_data=HabitCb(action="templates"))
    _back(kb)
    kb.adjust(2, 1)
    return kb.as_markup()


def templates_kb(
    templates: Sequence[HabitTemplate], available: Sequence[int], selected: Collection[int]
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx in available:
        tpl = templates[idx]
        mark = "✅" if idx in selected else "▫️"
        kb.button(
            text=f"{mark} {tpl.name} · {format_rewards_short(tpl.rewards)}",
            callback_data=TplCb(action="toggle", idx=idx),
        )
    kb.button(text=f"💾 Готово ({len(selected)})", callback_data=TplCb(action="done"))
    kb.button(text="⏭ Пропустить", callback_data=TplCb(action="skip"))
    kb.adjust(*([1] * len(available)), 2)
    return kb.as_markup()


def habits_menu_kb(habits: Sequence[Habit]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for habit in habits:
        kb.button(text=habit.name, callback_data=HabitCb(action="open", habit_id=habit.id))
    kb.button(text="➕ Своя привычка", callback_data=MenuCb(action="add"))
    kb.button(text="📋 Из шаблонов", callback_data=HabitCb(action="templates"))
    _back(kb)
    kb.adjust(*([2] * (len(habits) // 2)), *([1] * (len(habits) % 2)), 2, 1)
    return kb.as_markup()


def habit_card_kb(habit_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Название", callback_data=HabitCb(action="edit_name", habit_id=habit_id))
    kb.button(text="🎁 Награды", callback_data=HabitCb(action="edit_rewards", habit_id=habit_id))
    kb.button(text="🔢 Лимит", callback_data=HabitCb(action="edit_limit", habit_id=habit_id))
    kb.button(text="🗑 Удалить", callback_data=HabitCb(action="delete_ask", habit_id=habit_id))
    kb.button(text="⬅️ К привычкам", callback_data=MenuCb(action="habits"))
    kb.adjust(3, 1, 1)
    return kb.as_markup()


def delete_confirm_kb(habit_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Да, удалить", callback_data=HabitCb(action="delete_yes", habit_id=habit_id))
    kb.button(text="↩️ Нет", callback_data=HabitCb(action="open", habit_id=habit_id))
    return kb.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✖️ Отмена", callback_data=FormCb(action="cancel"))
    return kb.as_markup()


def stats_select_kb(selected: Collection[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for stat in config.STATS:
        mark = "✅" if stat.key in selected else "▫️"
        kb.button(text=f"{mark} {stat.label}", callback_data=FormCb(action="stat", value=stat.key))
    kb.button(text=f"➡️ Далее ({len(selected)})", callback_data=FormCb(action="stats_done"))
    kb.button(text="✖️ Отмена", callback_data=FormCb(action="cancel"))
    kb.adjust(2, 2, 2, 2)
    return kb.as_markup()


def xp_select_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for xp in config.XP_CHOICES:
        kb.button(text=f"+{xp}", callback_data=FormCb(action="xp", value=str(xp)))
    kb.button(text="✖️ Отмена", callback_data=FormCb(action="cancel"))
    kb.adjust(4, 4, 1)
    return kb.as_markup()


def limit_select_kb(current: int | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    marked = current if current is not None else config.DEFAULT_DAILY_LIMIT
    for limit in config.DAILY_LIMIT_CHOICES:
        text = f"• {limit} •" if limit == marked else str(limit)
        kb.button(text=text, callback_data=FormCb(action="limit", value=str(limit)))
    kb.button(text="✖️ Отмена", callback_data=FormCb(action="cancel"))
    kb.adjust(len(config.DAILY_LIMIT_CHOICES), 1)
    return kb.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💾 Сохранить", callback_data=FormCb(action="save"))
    kb.button(text="🔄 Заново", callback_data=FormCb(action="restart"))
    kb.button(text="✖️ Отмена", callback_data=FormCb(action="cancel"))
    kb.adjust(1, 2)
    return kb.as_markup()


def settings_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🕐 Часовой пояс", callback_data=SettingsCb(action="tz_menu"))
    kb.button(text="✏️ Имя героя", callback_data=SettingsCb(action="rename"))
    _back(kb)
    kb.adjust(2, 1)
    return kb.as_markup()


def timezones_kb(current: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for idx, (tz, city, offset) in enumerate(config.TIMEZONE_CHOICES):
        mark = "✅ " if tz == current else ""
        kb.button(text=f"{mark}{city} ({offset})", callback_data=SettingsCb(action="tz", idx=idx))
    _back(kb, "⬅️ Назад", "settings")
    kb.adjust(2)
    return kb.as_markup()


def settings_cancel_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✖️ Отмена", callback_data=SettingsCb(action="cancel"))
    return kb.as_markup()
