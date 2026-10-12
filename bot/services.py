"""Сценарии, связывающие БД и игровую логику. Без зависимости от aiogram."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from db.models import Habit, User
from db.repository import Repository
from game import config
from game.achievements import Achievement, PlayerMetrics, build_metrics, newly_unlocked
from game.activity import Activity, build_activity
from game.limits import check_limit, day_bounds_utc
from game.rewards import RewardOutcome, apply_rewards
from game.templates import TEMPLATES


def now_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------- снимок
@dataclass(frozen=True)
class Snapshot:
    """Всё, что нужно для отрисовки экранов."""
    stats: dict[str, int]
    habits: list[Habit]
    activity: Activity
    names: dict[int, str]

    @property
    def metrics(self) -> PlayerMetrics:
        return build_metrics(self.stats, self.activity.completions, self.activity.best_streak)

    def habit(self, habit_id: int) -> Habit | None:
        return next((h for h in self.habits if h.id == habit_id), None)


async def load_snapshot(repo: Repository, user: User, now: datetime | None = None) -> Snapshot:
    logs = await repo.list_logs(user.tg_id)
    return Snapshot(
        stats=await repo.get_stats(user.tg_id),
        habits=await repo.list_habits(user.tg_id),
        activity=build_activity(logs, now or now_utc(), user.timezone),
        names=await repo.habit_names(user.tg_id),
    )


# ---------------------------------------------------------------- отметка
class CompletionStatus(Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    LIMIT_REACHED = "limit_reached"


@dataclass(frozen=True)
class CompletionResult:
    status: CompletionStatus
    habit: Habit | None = None
    done_today: int = 0
    outcome: RewardOutcome | None = None
    streak: int = 0
    achievements: list[Achievement] = field(default_factory=list)


async def complete_habit(
    repo: Repository, user: User, habit_id: int, now: datetime | None = None
) -> CompletionResult:
    now = now or now_utc()
    # Проверка лимита и запись — в одной транзакции, чтобы двойной тап не обошёл лимит.
    async with repo.db.transaction():
        habit = await repo.get_habit(user.tg_id, habit_id)
        if habit is None:
            return CompletionResult(CompletionStatus.NOT_FOUND)
        logs = await repo.list_logs(user.tg_id)
        before = build_activity(logs, now, user.timezone)
        done = before.today_counts.get(habit.id, 0)
        if not check_limit(done, habit.daily_limit).allowed:
            return CompletionResult(CompletionStatus.LIMIT_REACHED, habit, done)

        stats = await repo.get_stats(user.tg_id)
        outcome = apply_rewards(stats, habit.rewards)
        log = await repo.insert_log(user.tg_id, habit.id, now, outcome.gains)
        await repo.add_stats_xp(user.tg_id, outcome.gains)

    after = build_activity([*logs, log], now, user.timezone)
    achievements = newly_unlocked(
        build_metrics(stats, before.completions, before.best_streak),
        build_metrics(outcome.new_stats, after.completions, after.best_streak),
    )
    return CompletionResult(
        CompletionStatus.OK, habit, done + 1, outcome, after.habit_streak(habit.id), achievements
    )


# ---------------------------------------------------------------- отмена
@dataclass(frozen=True)
class UndoResult:
    habit_name: str
    losses: dict[str, int]


async def undo_last_today(repo: Repository, user: User, now: datetime | None = None) -> UndoResult | None:
    """Отменяет последнюю отметку за сегодняшний день пользователя."""
    start, end = day_bounds_utc(now or now_utc(), user.timezone)
    async with repo.db.transaction():
        log = await repo.last_log(user.tg_id, start, end)
        if log is None:
            return None
        # старые записи (до появления log_rewards) — откатываем по текущим наградам привычки
        losses = await repo.get_log_rewards(log.id) or await repo.get_habit_rewards(log.habit_id)
        await repo.delete_log(log.id)
        await repo.subtract_stats_xp(user.tg_id, losses)
    name = (await repo.habit_names(user.tg_id)).get(log.habit_id, "привычка")
    return UndoResult(name, losses)


# ---------------------------------------------------------------- шаблоны
async def add_templates(repo: Repository, user_id: int, indices: Iterable[int]) -> int:
    """Добавляет выбранные шаблоны, пропуская дубликаты и не превышая лимит привычек."""
    existing = {h.name.casefold() for h in await repo.list_habits(user_id)}
    free_slots = config.MAX_HABITS_PER_USER - len(existing)
    items = []
    for idx in sorted(set(indices)):
        if not 0 <= idx < len(TEMPLATES) or free_slots <= 0:
            continue
        tpl = TEMPLATES[idx]
        if tpl.name.casefold() in existing:
            continue
        items.append((tpl.name, tpl.daily_limit, dict(tpl.rewards)))
        existing.add(tpl.name.casefold())
        free_slots -= 1
    if not items:
        return 0
    return await repo.create_habits(user_id, items)
