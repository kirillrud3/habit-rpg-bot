from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot import services, texts
from bot.filters import Registered
from bot.handlers import views
from bot.keyboards.callbacks import HabitCb, TplCb
from bot.keyboards.inline import templates_kb
from bot.states import TemplateSelect
from bot.utils import show
from db.models import User
from db.repository import Repository
from game.templates import TEMPLATES

router = Router(name="templates")
router.callback_query.filter(Registered())
router.message.filter(Registered())


async def open_template_picker(
    state: FSMContext, repo: Repository, user: User, context: str
) -> tuple[str, InlineKeyboardMarkup]:
    """Переводит в состояние выбора шаблонов и возвращает экран."""
    existing = {h.name.casefold() for h in await repo.list_habits(user.tg_id)}
    available = [i for i, t in enumerate(TEMPLATES) if t.name.casefold() not in existing]
    if not available:
        await state.clear()
        return await views.habits_menu(repo, user, texts.TEMPLATES_ALL_ADDED)
    await state.set_state(TemplateSelect.choosing)
    await state.update_data(tpl_available=available, tpl_selected=[], tpl_context=context)
    return texts.TEMPLATES_INTRO, templates_kb(TEMPLATES, available, set())


@router.callback_query(HabitCb.filter(F.action == "templates"))
async def from_habits(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    text, kb = await open_template_picker(state, repo, user, context="habits")
    await show(callback, text, kb)
    await callback.answer()


@router.callback_query(TemplateSelect.choosing, TplCb.filter(F.action == "toggle"))
async def toggle_template(callback: CallbackQuery, callback_data: TplCb, state: FSMContext) -> None:
    data = await state.get_data()
    available: list[int] = data.get("tpl_available", [])
    selected: list[int] = data.get("tpl_selected", [])
    if callback_data.idx not in available:
        await callback.answer(texts.STALE_BUTTON)
        return
    if callback_data.idx in selected:
        selected.remove(callback_data.idx)
    else:
        selected.append(callback_data.idx)
    await state.update_data(tpl_selected=selected)
    await show(callback, texts.TEMPLATES_INTRO, templates_kb(TEMPLATES, available, set(selected)))
    await callback.answer()


@router.callback_query(TemplateSelect.choosing, TplCb.filter(F.action.in_({"done", "skip"})))
async def finish_templates(
    callback: CallbackQuery, callback_data: TplCb, state: FSMContext, repo: Repository, user: User
) -> None:
    data = await state.get_data()
    await state.clear()
    added = 0
    if callback_data.action == "done":
        added = await services.add_templates(repo, user.tg_id, data.get("tpl_selected", []))
    note = f"✨ Добавлено привычек: <b>{added}</b>" if added else None

    if data.get("tpl_context") == "habits":
        text, kb = await views.habits_menu(repo, user, note)
    else:
        text, kb = await views.main_menu(repo, user, note)
    await show(callback, text, kb)
    await callback.answer()


@router.message(TemplateSelect.choosing)
async def templates_text(message: Message) -> None:
    await message.answer(texts.USE_BUTTONS)
