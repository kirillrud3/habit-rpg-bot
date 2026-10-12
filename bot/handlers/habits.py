"""Список привычек, карточка привычки, создание и редактирование (FSM)."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot import texts
from bot.filters import Registered
from bot.handlers import views
from bot.keyboards.callbacks import FormCb, HabitCb, MenuCb
from bot.keyboards.inline import (
    cancel_kb,
    confirm_kb,
    delete_confirm_kb,
    limit_select_kb,
    stats_select_kb,
    xp_select_kb,
)
from bot.states import HabitForm
from bot.utils import show
from db.models import User
from db.repository import Repository
from game import config
from game.formatting import esc, format_habit_preview
from game.validation import (
    ValidationError,
    parse_int,
    validate_daily_limit,
    validate_habit_name,
    validate_rewards,
)

router = Router(name="habits")
router.message.filter(Registered())
router.callback_query.filter(Registered())

Event = Message | CallbackQuery
EDIT_ACTIONS = {"edit_name", "edit_rewards", "edit_limit"}


async def reply(event: Event, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    """Колбэк — редактируем экран, сообщение — отвечаем новым."""
    if isinstance(event, CallbackQuery):
        await show(event, text, kb)
    else:
        await event.answer(text, reply_markup=kb)


async def show_card(event: Event, repo: Repository, user: User, habit_id: int, note: str | None = None) -> None:
    screen = await views.habit_card(repo, user, habit_id, note)
    if screen is None:
        screen = await views.habits_menu(repo, user, texts.HABIT_NOT_FOUND)
    await reply(event, *screen)


# ------------------------------------------------------------ экраны формы
def _step(data: dict, n: int) -> str:
    return texts.FORM_STEP_ADD.format(n=n) if data.get("f_mode") == "add" else texts.FORM_STEP_EDIT


def _pending(data: dict) -> list[str]:
    """Выбранные статы в порядке конфига — в этом порядке спрашиваем XP."""
    return [k for k in config.STAT_KEYS if k in data.get("f_stats", [])]


def stats_screen(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    text = texts.FORM_ASK_STATS.format(step=_step(data, 2), name=esc(data["f_name"]))
    return text, stats_select_kb(set(data.get("f_stats", [])))


def xp_screen(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    pending, i = _pending(data), len(data.get("f_rewards", {}))
    text = texts.FORM_ASK_XP.format(
        step=_step(data, 3), name=esc(data["f_name"]), stat=config.STATS_BY_KEY[pending[i]].label,
        i=i + 1, n=len(pending), max_xp=config.MAX_XP_PER_STAT,
    )
    return text, xp_select_kb()


def limit_screen(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    text = texts.FORM_ASK_LIMIT.format(
        step=_step(data, 4), name=esc(data["f_name"]), lo=config.MIN_DAILY_LIMIT, hi=config.MAX_DAILY_LIMIT
    )
    return text, limit_select_kb(data.get("f_limit"))


def confirm_screen(data: dict) -> tuple[str, InlineKeyboardMarkup]:
    rewards = {k: data["f_rewards"][k] for k in _pending(data)}
    return format_habit_preview(data["f_name"], rewards, data["f_limit"]), confirm_kb()


# ------------------------------------------------------------ список / карточка
@router.callback_query(MenuCb.filter(F.action == "habits"))
async def habits_menu(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    await state.clear()
    await show(callback, *await views.habits_menu(repo, user))
    await callback.answer()


@router.callback_query(HabitCb.filter(F.action == "open"))
async def open_card(
    callback: CallbackQuery, callback_data: HabitCb, state: FSMContext, repo: Repository, user: User
) -> None:
    await state.clear()
    await show_card(callback, repo, user, callback_data.habit_id)
    await callback.answer()


@router.callback_query(HabitCb.filter(F.action == "delete_ask"))
async def delete_ask(callback: CallbackQuery, callback_data: HabitCb, repo: Repository, user: User) -> None:
    habit = await repo.get_habit(user.tg_id, callback_data.habit_id)
    if habit is None:
        await callback.answer(texts.HABIT_NOT_FOUND, show_alert=True)
        return
    await show(callback, texts.DELETE_CONFIRM.format(name=esc(habit.name)), delete_confirm_kb(habit.id))
    await callback.answer()


@router.callback_query(HabitCb.filter(F.action == "delete_yes"))
async def delete_yes(callback: CallbackQuery, callback_data: HabitCb, repo: Repository, user: User) -> None:
    habit = await repo.get_habit(user.tg_id, callback_data.habit_id)
    if habit is None or not await repo.deactivate_habit(user.tg_id, habit.id):
        await callback.answer(texts.HABIT_NOT_FOUND, show_alert=True)
        note = None
    else:
        await callback.answer("🗑")
        note = texts.DELETED.format(name=esc(habit.name))
    await show(callback, *await views.habits_menu(repo, user, note))


# ------------------------------------------------------------ старт формы
async def start_add(event: Event, state: FSMContext, repo: Repository, user: User) -> None:
    if await repo.count_active_habits(user.tg_id) >= config.MAX_HABITS_PER_USER:
        warning = texts.FORM_TOO_MANY.format(n=config.MAX_HABITS_PER_USER)
        if isinstance(event, CallbackQuery):
            await event.answer(warning, show_alert=True)
        else:
            await event.answer(warning)
        return
    await state.clear()
    await state.set_state(HabitForm.name)
    await state.update_data(f_mode="add", f_stats=[], f_rewards={}, f_limit=config.DEFAULT_DAILY_LIMIT)
    await reply(event, texts.FORM_ASK_NAME, cancel_kb())


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext, repo: Repository, user: User) -> None:
    await start_add(message, state, repo, user)


@router.callback_query(MenuCb.filter(F.action == "add"))
async def cb_add(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    await start_add(callback, state, repo, user)
    await callback.answer()


@router.callback_query(HabitCb.filter(F.action.in_(EDIT_ACTIONS)))
async def start_edit(
    callback: CallbackQuery, callback_data: HabitCb, state: FSMContext, repo: Repository, user: User
) -> None:
    habit = await repo.get_habit(user.tg_id, callback_data.habit_id)
    if habit is None:
        await callback.answer(texts.HABIT_NOT_FOUND, show_alert=True)
        await show(callback, *await views.habits_menu(repo, user))
        return
    await state.clear()
    await state.update_data(
        f_mode=callback_data.action, f_habit_id=habit.id, f_name=habit.name,
        f_stats=list(habit.rewards), f_rewards={}, f_limit=habit.daily_limit,
    )
    data = await state.get_data()
    if callback_data.action == "edit_name":
        await state.set_state(HabitForm.name)
        await show(callback, texts.FORM_ASK_NEW_NAME.format(name=esc(habit.name)), cancel_kb())
    elif callback_data.action == "edit_rewards":
        await state.set_state(HabitForm.stats)
        await show(callback, *stats_screen(data))
    else:
        await state.set_state(HabitForm.limit)
        await show(callback, *limit_screen(data))
    await callback.answer()


# ------------------------------------------------------------ шаг: название
@router.message(HabitForm.name, F.text)
async def form_name(message: Message, state: FSMContext, repo: Repository, user: User) -> None:
    data = await state.get_data()
    habit_id = data.get("f_habit_id")
    existing = [h.name for h in await repo.list_habits(user.tg_id) if h.id != habit_id]
    try:
        name = validate_habit_name(message.text, existing)
    except ValidationError as e:
        await message.answer(f"⚠️ {esc(str(e))}\nПопробуй другое название.", reply_markup=cancel_kb())
        return

    if data.get("f_mode") == "edit_name":
        await repo.update_habit_name(user.tg_id, habit_id, name)
        await state.clear()
        await show_card(message, repo, user, habit_id, texts.FORM_UPDATED)
        return

    await state.update_data(f_name=name)
    await state.set_state(HabitForm.stats)
    await reply(message, *stats_screen(await state.get_data()))


@router.message(HabitForm.name)
async def form_name_not_text(message: Message) -> None:
    await message.answer(texts.FORM_NAME_TEXT_ONLY, reply_markup=cancel_kb())


# ------------------------------------------------------------ шаг: характеристики
@router.callback_query(HabitForm.stats, FormCb.filter(F.action == "stat"))
async def form_toggle_stat(callback: CallbackQuery, callback_data: FormCb, state: FSMContext) -> None:
    if callback_data.value not in config.STATS_BY_KEY:
        await callback.answer(texts.STALE_BUTTON)
        return
    data = await state.get_data()
    selected: list[str] = data.get("f_stats", [])
    if callback_data.value in selected:
        selected.remove(callback_data.value)
    else:
        selected.append(callback_data.value)
    await state.update_data(f_stats=selected)
    await show(callback, *stats_screen(await state.get_data()))
    await callback.answer()


@router.callback_query(HabitForm.stats, FormCb.filter(F.action == "stats_done"))
async def form_stats_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not _pending(data):
        await callback.answer(texts.FORM_NEED_STAT, show_alert=True)
        return
    await state.update_data(f_rewards={})
    await state.set_state(HabitForm.xp)
    await show(callback, *xp_screen(await state.get_data()))
    await callback.answer()


# ------------------------------------------------------------ шаг: XP
async def apply_xp(event: Event, xp: int, state: FSMContext, repo: Repository, user: User) -> None:
    data = await state.get_data()
    pending = _pending(data)
    rewards: dict[str, int] = dict(data.get("f_rewards", {}))
    if len(rewards) >= len(pending):
        return
    rewards[pending[len(rewards)]] = xp
    await state.update_data(f_rewards=rewards)
    data = await state.get_data()

    if len(rewards) < len(pending):
        await reply(event, *xp_screen(data))
        return
    if data.get("f_mode") == "edit_rewards":
        await repo.replace_habit_rewards(user.tg_id, data["f_habit_id"], validate_rewards(rewards))
        await state.clear()
        await show_card(event, repo, user, data["f_habit_id"], texts.FORM_UPDATED)
        return
    await state.set_state(HabitForm.limit)
    await reply(event, *limit_screen(data))


@router.callback_query(HabitForm.xp, FormCb.filter(F.action == "xp"))
async def form_xp_button(
    callback: CallbackQuery, callback_data: FormCb, state: FSMContext, repo: Repository, user: User
) -> None:
    if not callback_data.value.isdigit() or int(callback_data.value) not in config.XP_CHOICES:
        await callback.answer(texts.STALE_BUTTON)
        return
    await apply_xp(callback, int(callback_data.value), state, repo, user)
    await callback.answer()


@router.message(HabitForm.xp, F.text)
async def form_xp_text(message: Message, state: FSMContext, repo: Repository, user: User) -> None:
    try:
        xp = parse_int(message.text, 1, config.MAX_XP_PER_STAT)
    except ValidationError as e:
        await message.answer(f"⚠️ {e}")
        return
    await apply_xp(message, xp, state, repo, user)


# ------------------------------------------------------------ шаг: лимит
async def apply_limit(event: Event, limit: int, state: FSMContext, repo: Repository, user: User) -> None:
    data = await state.get_data()
    if data.get("f_mode") == "edit_limit":
        await repo.update_habit_limit(user.tg_id, data["f_habit_id"], limit)
        await state.clear()
        await show_card(event, repo, user, data["f_habit_id"], texts.FORM_UPDATED)
        return
    await state.update_data(f_limit=limit)
    await state.set_state(HabitForm.confirm)
    await reply(event, *confirm_screen(await state.get_data()))


@router.callback_query(HabitForm.limit, FormCb.filter(F.action == "limit"))
async def form_limit_button(
    callback: CallbackQuery, callback_data: FormCb, state: FSMContext, repo: Repository, user: User
) -> None:
    if not callback_data.value.isdigit() or int(callback_data.value) not in config.DAILY_LIMIT_CHOICES:
        await callback.answer(texts.STALE_BUTTON)
        return
    await apply_limit(callback, int(callback_data.value), state, repo, user)
    await callback.answer()


@router.message(HabitForm.limit, F.text)
async def form_limit_text(message: Message, state: FSMContext, repo: Repository, user: User) -> None:
    try:
        limit = parse_int(message.text, config.MIN_DAILY_LIMIT, config.MAX_DAILY_LIMIT)
    except ValidationError as e:
        await message.answer(f"⚠️ {e}")
        return
    await apply_limit(message, limit, state, repo, user)


# ------------------------------------------------------------ шаг: подтверждение
@router.callback_query(HabitForm.confirm, FormCb.filter(F.action == "save"))
async def form_save(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    data = await state.get_data()
    await state.clear()
    try:
        existing = [h.name for h in await repo.list_habits(user.tg_id)]
        if len(existing) >= config.MAX_HABITS_PER_USER:
            raise ValidationError(texts.FORM_TOO_MANY.format(n=config.MAX_HABITS_PER_USER))
        name = validate_habit_name(data.get("f_name"), existing)
        rewards = validate_rewards(data.get("f_rewards", {}))
        limit = validate_daily_limit(data.get("f_limit", config.DEFAULT_DAILY_LIMIT))
    except ValidationError as e:
        await callback.answer(f"⚠️ {e}", show_alert=True)
        await show(callback, *await views.habits_menu(repo, user))
        return
    habit_id = await repo.create_habit(user.tg_id, name, limit, rewards)
    await show_card(callback, repo, user, habit_id, texts.FORM_CREATED)
    await callback.answer("✨")


@router.callback_query(HabitForm.confirm, FormCb.filter(F.action == "restart"))
async def form_restart(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    await start_add(callback, state, repo, user)
    await callback.answer()


@router.callback_query(FormCb.filter(F.action == "cancel"))
async def form_cancel(callback: CallbackQuery, state: FSMContext, repo: Repository, user: User) -> None:
    data = await state.get_data()
    await state.clear()
    if data.get("f_mode") in EDIT_ACTIONS and data.get("f_habit_id"):
        await show_card(callback, repo, user, data["f_habit_id"])
    else:
        await show(callback, *await views.habits_menu(repo, user))
    await callback.answer("Отменено")


@router.message(HabitForm.stats)
@router.message(HabitForm.xp)
@router.message(HabitForm.limit)
@router.message(HabitForm.confirm)
async def form_use_buttons(message: Message) -> None:
    await message.answer(texts.USE_BUTTONS)
