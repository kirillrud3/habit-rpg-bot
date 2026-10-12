from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot import services, texts
from bot.filters import Registered
from bot.handlers import views
from bot.keyboards.callbacks import MarkCb, MenuCb, UndoCb
from bot.services import CompletionStatus
from bot.utils import drop_keyboard, send, show
from db.models import User
from db.repository import Repository
from game.formatting import format_completion, format_level_ups, format_new_achievements, format_undo

router = Router(name="checkin")
router.callback_query.filter(Registered())


@router.callback_query(MenuCb.filter(F.action == "mark"))
async def show_mark_list(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    await state.clear()
    text, kb = await views.mark_list(repo, user)
    await show(callback, text, kb)
    await callback.answer()


@router.callback_query(MarkCb.filter())
async def mark_habit(callback: CallbackQuery, callback_data: MarkCb, repo: Repository, user: User) -> None:
    result = await services.complete_habit(repo, user, callback_data.habit_id)

    if result.status is CompletionStatus.NOT_FOUND:
        await callback.answer(texts.HABIT_NOT_FOUND, show_alert=True)
        text, kb = await views.mark_list(repo, user)
        await show(callback, text, kb)
        return

    if result.status is CompletionStatus.LIMIT_REACHED:
        await callback.answer(
            texts.LIMIT_REACHED.format(done=result.done_today, limit=result.habit.daily_limit),
            show_alert=True,
        )
        return

    await callback.answer("✅")
    habit, outcome = result.habit, result.outcome
    messages = [
        format_completion(habit.name, outcome.gains, result.done_today, habit.daily_limit, result.streak),
        format_level_ups(outcome),
        format_new_achievements(result.achievements),
    ]
    messages = [m for m in messages if m]
    # Ответы приходят новыми сообщениями, а список кнопок переезжает под последний —
    # так история остаётся в чате.
    await drop_keyboard(callback)
    _, mark_kb = await views.mark_list(repo, user)
    for i, text in enumerate(messages):
        await send(callback, text, mark_kb if i == len(messages) - 1 else None)


@router.callback_query(UndoCb.filter())
async def undo_last(callback: CallbackQuery, callback_data: UndoCb, repo: Repository, user: User) -> None:
    result = await services.undo_last_today(repo, user)
    if result is None:
        await callback.answer(texts.NOTHING_TO_UNDO, show_alert=True)
    else:
        await callback.answer(format_undo(result.habit_name, result.losses), show_alert=True)
    build = views.stats if callback_data.source == "stats" else views.mark_list
    text, kb = await build(repo, user)
    await show(callback, text, kb)
