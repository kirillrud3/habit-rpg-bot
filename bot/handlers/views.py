"""Сборка экранов (текст + клавиатура), общих для нескольких хендлеров."""
from aiogram.types import InlineKeyboardMarkup

from bot import services, texts
from bot.keyboards import inline
from db.models import User
from db.repository import Repository
from game import config
from game.formatting import (
    esc,
    format_achievements,
    format_habit_card,
    format_habits_list,
    format_main_menu,
    format_profile,
    format_stats,
)

Screen = tuple[str, InlineKeyboardMarkup]


async def main_menu(repo: Repository, user: User, note: str | None = None) -> Screen:
    snap = await services.load_snapshot(repo, user)
    text = format_main_menu(user.character_name, snap.stats, snap.activity)
    if note:
        text = f"{note}\n\n{text}"
    return text, inline.main_menu_kb()


async def profile(repo: Repository, user: User) -> Screen:
    snap = await services.load_snapshot(repo, user)
    return format_profile(user.character_name, snap.stats, snap.activity, snap.metrics), inline.profile_kb()


async def stats(repo: Repository, user: User) -> Screen:
    snap = await services.load_snapshot(repo, user)
    return format_stats(snap.activity, snap.names), inline.stats_kb(snap.activity.today_completions > 0)


async def achievements(repo: Repository, user: User) -> Screen:
    snap = await services.load_snapshot(repo, user)
    return format_achievements(snap.metrics), inline.back_kb()


async def mark_list(repo: Repository, user: User) -> Screen:
    snap = await services.load_snapshot(repo, user)
    if not snap.habits:
        return texts.NO_HABITS, inline.no_habits_kb()
    act = snap.activity
    streaks = {h.id: act.habit_streak(h.id) for h in snap.habits}
    kb = inline.mark_list_kb(snap.habits, act.today_counts, streaks, act.today_completions > 0)
    return texts.MARK_TITLE, kb


async def habits_menu(repo: Repository, user: User, note: str | None = None) -> Screen:
    habits = await repo.list_habits(user.tg_id)
    text = format_habits_list([(h.name, h.rewards, h.daily_limit) for h in habits], note)
    return text, inline.habits_menu_kb(habits)


async def habit_card(repo: Repository, user: User, habit_id: int, note: str | None = None) -> Screen | None:
    snap = await services.load_snapshot(repo, user)
    habit = snap.habit(habit_id)
    if habit is None:
        return None
    act = snap.activity
    text = format_habit_card(
        habit.name, habit.rewards, habit.daily_limit,
        done_today=act.today_counts.get(habit.id, 0),
        streak=act.habit_streak(habit.id),
        total_done=act.habit_totals.get(habit.id, 0),
        note=note,
    )
    return text, inline.habit_card_kb(habit.id)


def timezone_label(tz: str) -> str:
    for key, city, offset in config.TIMEZONE_CHOICES:
        if key == tz:
            return f"{city} ({offset})"
    return tz


def settings(user: User, note: str | None = None) -> Screen:
    lines = [note, ""] if note else []
    lines += [
        "🔧 <b>Настройки</b>",
        "",
        f"🛡 Имя героя: <b>{esc(user.character_name)}</b>",
        f"🕐 Часовой пояс: <b>{timezone_label(user.timezone)}</b>",
        f"🌅 Новый день начинается в {config.DAY_START_HOUR:02d}:00",
    ]
    return "\n".join(lines), inline.settings_kb()
