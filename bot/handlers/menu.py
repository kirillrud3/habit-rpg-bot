from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.filters import Registered
from bot.handlers import views
from bot.keyboards.callbacks import MenuCb
from bot.utils import show
from db.models import User
from db.repository import Repository

router = Router(name="menu")
router.message.filter(Registered())
router.callback_query.filter(Registered())

# экран -> функция сборки
SCREENS = {
    "main": views.main_menu,
    "profile": views.profile,
    "stats": views.stats,
    "achievements": views.achievements,
}
COMMANDS = {"menu": "main", "profile": "profile", "stats": "stats", "achievements": "achievements"}


@router.message(Command(*COMMANDS))
async def cmd_screen(
    message: Message, command: CommandObject, state: FSMContext, repo: Repository, user: User
) -> None:
    await state.clear()
    text, kb = await SCREENS[COMMANDS[command.command.lower()]](repo, user)
    await message.answer(text, reply_markup=kb)


@router.callback_query(MenuCb.filter(F.action.in_(SCREENS)))
async def cb_screen(
    callback: CallbackQuery, callback_data: MenuCb, state: FSMContext, repo: Repository, user: User
) -> None:
    await state.clear()
    text, kb = await SCREENS[callback_data.action](repo, user)
    await show(callback, text, kb)
    await callback.answer()
