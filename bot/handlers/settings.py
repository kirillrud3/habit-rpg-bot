from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.filters import Registered
from bot.handlers import views
from bot.keyboards.callbacks import MenuCb, SettingsCb
from bot.keyboards.inline import settings_cancel_kb, timezones_kb
from bot.states import SettingsForm
from bot.utils import show
from db.models import User
from db.repository import Repository
from game import config
from game.formatting import esc
from game.validation import ValidationError, validate_character_name

router = Router(name="settings")
router.message.filter(Registered())
router.callback_query.filter(Registered())


@router.callback_query(MenuCb.filter(F.action == "settings"))
@router.callback_query(SettingsCb.filter(F.action == "cancel"))
async def settings_screen(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    await state.clear()
    await show(callback, *views.settings(user))
    await callback.answer()


@router.callback_query(SettingsCb.filter(F.action == "tz_menu"))
async def tz_menu(callback: CallbackQuery, user: User) -> None:
    await show(callback, texts.SETTINGS_TZ_TITLE, timezones_kb(user.timezone))
    await callback.answer()


@router.callback_query(SettingsCb.filter(F.action == "tz"))
async def tz_set(callback: CallbackQuery, callback_data: SettingsCb, repo: Repository, user: User) -> None:
    if not 0 <= callback_data.idx < len(config.TIMEZONE_CHOICES):
        await callback.answer(texts.STALE_BUTTON)
        return
    tz = config.TIMEZONE_CHOICES[callback_data.idx][0]
    await repo.update_timezone(user.tg_id, tz)
    user = await repo.get_user(user.tg_id)
    await show(callback, *views.settings(user, f"✅ Часовой пояс: <b>{views.timezone_label(tz)}</b>"))
    await callback.answer()


@router.callback_query(SettingsCb.filter(F.action == "rename"))
async def rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.rename)
    await show(callback, texts.SETTINGS_ASK_NAME, settings_cancel_kb())
    await callback.answer()


@router.message(SettingsForm.rename, F.text)
async def rename_finish(message: Message, state: FSMContext, repo: Repository, user: User) -> None:
    try:
        name = validate_character_name(message.text)
    except ValidationError as e:
        await message.answer(f"⚠️ {esc(str(e))}", reply_markup=settings_cancel_kb())
        return
    await repo.update_character_name(user.tg_id, name)
    await state.clear()
    user = await repo.get_user(user.tg_id)
    text, kb = views.settings(user, f"✅ Теперь героя зовут <b>{esc(name)}</b>")
    await message.answer(text, reply_markup=kb)


@router.message(SettingsForm.rename)
async def rename_not_text(message: Message) -> None:
    await message.answer(texts.ASK_NAME_TEXT_ONLY, reply_markup=settings_cancel_kb())
