"""Тексты для пользователя в HTML-разметке Telegram.

Всё, что ввёл пользователь (имена, названия), проходит через esc().
"""
from __future__ import annotations

import html
from collections.abc import Mapping, Sequence

from game import config
from game.achievements import ACHIEVEMENTS, Achievement, PlayerMetrics, unlocked
from game.activity import Activity
from game.leveling import level_info, total_level_info
from game.rewards import RewardOutcome
from game.titles import character_class, rank_for_level

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def days_word(n: int) -> str:
    return plural(n, "день", "дня", "дней")


def progress_bar(current: int, total: int, length: int = config.PROGRESS_BAR_LENGTH) -> str:
    if length <= 0:
        return ""
    if total <= 0:
        filled = length
    else:
        filled = int(length * max(0, current) / total)
        filled = max(0, min(length, filled))
    return config.BAR_FILLED * filled + config.BAR_EMPTY * (length - filled)


def format_rewards(rewards: Mapping[str, int], sign: str = "+") -> str:
    """'+5 🧠 Интеллект, +3 ⚙️ Дисциплина' в порядке статов из конфига."""
    return ", ".join(
        f"{sign}{rewards[key]} {config.STATS_BY_KEY[key].label}"
        for key in config.STAT_KEYS
        if key in rewards
    )


def format_rewards_short(rewards: Mapping[str, int]) -> str:
    """'🧠5 ⚙️3' — для кнопок."""
    return " ".join(
        f"{config.STATS_BY_KEY[key].emoji}{rewards[key]}"
        for key in config.STAT_KEYS
        if key in rewards
    )


# --------------------------------------------------------------- отметки
def format_completion(
    habit_name: str, gains: Mapping[str, int], done_today: int, daily_limit: int, streak: int = 0
) -> str:
    text = (
        f"<b>{esc(habit_name)}</b> выполнено! {format_rewards(gains)} "
        f"• Сегодня: {done_today}/{daily_limit}"
    )
    if streak >= 2:
        text += f"\n🔥 Серия: <b>{streak}</b> {days_word(streak)} подряд"
    return text


def format_level_ups(outcome: RewardOutcome) -> str | None:
    if not outcome.has_level_up:
        return None
    lines = ["🎉 <b>LEVEL UP!</b> 🎉", ""]
    for lu in outcome.stat_level_ups:
        stat = config.STATS_BY_KEY[lu.stat]
        lines.append(f"{stat.label}: {lu.old_level} → <b>{lu.new_level}</b> ⬆️")
    if outcome.total_level_up:
        lu = outcome.total_level_up
        if outcome.stat_level_ups:
            lines.append("")
        lines.append(f"🌟 <b>Общий уровень: {lu.old_level} → {lu.new_level}!</b>")
        old_rank, new_rank = rank_for_level(lu.old_level), rank_for_level(lu.new_level)
        if new_rank != old_rank:
            lines.append(f"🎖 Новое звание: <b>{new_rank}</b>")
    lines += ["", "<i>Так держать, герой!</i> ⚔️"]
    return "\n".join(lines)


def format_new_achievements(items: Sequence[Achievement]) -> str | None:
    if not items:
        return None
    title = "🏆 <b>Достижение получено!</b>" if len(items) == 1 else "🏆 <b>Новые достижения!</b>"
    lines = [title, ""]
    lines += [f"{a.emoji} <b>{a.title}</b> — <i>{a.description}</i>" for a in items]
    return "\n".join(lines)


def format_undo(habit_name: str, gains: Mapping[str, int]) -> str:
    """Для всплывающего уведомления (без HTML)."""
    return f"↩️ Отменено: {habit_name} ({format_rewards(gains, sign='−')})"


# --------------------------------------------------------------- экраны
def format_main_menu(name: str, stats_xp: Mapping[str, int], activity: Activity) -> str:
    level = total_level_info(stats_xp).level
    lines = [
        f"⚔️ <b>{esc(name)}</b>",
        f"<i>{character_class(stats_xp)} • {rank_for_level(level)}</i> • ⭐ ур. <b>{level}</b>",
        "",
        f"🔥 Серия: <b>{activity.streak}</b> {days_word(activity.streak)}"
        f" • Сегодня: <b>+{activity.today_xp}</b> XP",
        "",
        "Что делаем?",
    ]
    return "\n".join(lines)


def format_profile(name: str, stats_xp: Mapping[str, int], activity: Activity, metrics: PlayerMetrics) -> str:
    total = total_level_info(stats_xp)
    lines = [
        f"🛡 <b>{esc(name)}</b>",
        f"<i>{character_class(stats_xp)} • {rank_for_level(total.level)}</i>",
        "",
        f"⭐ <b>Уровень {total.level}</b>",
        f"{progress_bar(total.xp_into_level, total.xp_for_next)}  {total.xp_into_level}/{total.xp_for_next} XP",
        f"Всего опыта: <b>{total.xp_total}</b>",
        f"🔥 Серия: <b>{activity.streak}</b> {days_word(activity.streak)}"
        f" • 🏅 Рекорд: <b>{activity.best_streak}</b>",
        f"🏆 Достижения: <b>{len(unlocked(metrics))}/{len(ACHIEVEMENTS)}</b>",
        "",
        "<b>Характеристики</b>",
    ]
    for stat in config.STATS:
        info = level_info(stats_xp.get(stat.key, 0))
        bar = progress_bar(info.xp_into_level, info.xp_for_next, config.MINI_BAR_LENGTH)
        lines.append(f"{stat.label} — <b>ур. {info.level}</b>")
        lines.append(f"{bar}  {info.xp_into_level}/{info.xp_for_next}")
    return "\n".join(lines)


def format_stats(activity: Activity, names: Mapping[int, str], days: int = config.STATS_HISTORY_DAYS) -> str:
    lines = ["📈 <b>Статистика</b>", ""]
    if activity.today_counts:
        n = activity.today_completions
        lines.append(
            f"<b>Сегодня</b>: {n} {plural(n, 'отметка', 'отметки', 'отметок')}, "
            f"<b>+{activity.today_xp}</b> XP"
        )
        for hid, count in activity.today_counts.items():
            name = esc(names.get(hid, "удалённая привычка"))
            lines.append(f"• {name} ×{count} <i>(+{activity.today_xp_by_habit.get(hid, 0)})</i>")
    else:
        lines.append("<b>Сегодня</b>: пока пусто — самое время начать! 💪")

    week = activity.last_days(days)
    top = max((xp for _, xp in week), default=0)
    lines += ["", f"<b>Последние {days} {days_word(days)}</b>"]
    for day, xp in week:
        bar = progress_bar(xp, top, config.HISTORY_BAR_LENGTH) if top else config.BAR_EMPTY * config.HISTORY_BAR_LENGTH
        lines.append(f"{WEEKDAYS[day.weekday()]} {day:%d.%m}  {bar}  {xp}")

    lines += [
        "",
        f"🔥 Серия: <b>{activity.streak}</b> {days_word(activity.streak)}"
        f" • 🏅 Рекорд: <b>{activity.best_streak}</b>",
        f"✅ Всего выполнений: <b>{activity.completions}</b> • XP: <b>{activity.total_xp}</b>",
    ]
    return "\n".join(lines)


def format_achievements(metrics: PlayerMetrics) -> str:
    got = unlocked(metrics)
    lines = [f"🏆 <b>Достижения</b> ({len(got)}/{len(ACHIEVEMENTS)})", ""]
    for a in ACHIEVEMENTS:
        if a.is_unlocked(metrics):
            lines.append(f"✅ {a.emoji} <b>{a.title}</b> — {a.description}")
        else:
            progress = min(a.value(metrics), a.target)
            lines.append(f"🔒 {a.emoji} {a.title} — {a.description} <i>({progress}/{a.target})</i>")
    return "\n".join(lines)


# --------------------------------------------------------------- привычки
def format_habit_line(name: str, rewards: Mapping[str, int], daily_limit: int) -> str:
    return f"<b>{esc(name)}</b>\n    {format_rewards(rewards)} • до {daily_limit}/день"


def format_habits_list(habits: Sequence[tuple[str, Mapping[str, int], int]], note: str | None = None) -> str:
    lines = [note, ""] if note else []
    if not habits:
        lines.append("⚙️ <b>Привычек пока нет</b>\n\nДобавь свою или выбери из шаблонов 👇")
        return "\n".join(lines)
    lines.append(f"⚙️ <b>Твои привычки</b> ({len(habits)})")
    lines.append("")
    lines += [f"{i}. {format_habit_line(*h)}" for i, h in enumerate(habits, 1)]
    lines += ["", "<i>Нажми на привычку, чтобы изменить или удалить её.</i>"]
    return "\n".join(lines)


def format_habit_card(
    name: str, rewards: Mapping[str, int], daily_limit: int,
    done_today: int, streak: int, total_done: int, note: str | None = None,
) -> str:
    lines = [note, ""] if note else []
    lines += [
        f"<b>{esc(name)}</b>",
        "",
        f"🎁 Награда: {format_rewards(rewards)}",
        f"🔢 Лимит: до {daily_limit} в день • сегодня {done_today}/{daily_limit}",
        f"🔥 Серия: <b>{streak}</b> {days_word(streak)} • ✅ Всего: <b>{total_done}</b>",
    ]
    return "\n".join(lines)


def format_habit_preview(name: str, rewards: Mapping[str, int], daily_limit: int) -> str:
    return (
        "📝 <b>Проверь новую привычку</b>\n\n"
        f"<b>{esc(name)}</b>\n"
        f"🎁 {format_rewards(rewards)}\n"
        f"🔢 До {daily_limit} раз в день"
    )
