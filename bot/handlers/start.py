from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.handlers import views
from bot.handlers.templates import open_template_picker
from bot.keyboards.callbacks import MenuCb
from bot.keyboards.inline import back_kb
from bot.states import Registration
from bot.utils import show
from db.models import User
from db.repository import Repository
from game import config
from game.validation import ValidationError, validate_character_name

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, repo: Repository, user: User | None) -> None:
    await state.clear()
    if user is not None:
        text, kb = await views.main_menu(repo, user)
        await message.answer(text, reply_markup=kb)
        return
    await state.set_state(Registration.name)
    await message.answer(texts.ASK_NAME)


@router.message(Command("help"))
async def cmd_help(message: Message, user: User | None) -> None:
    await message.answer(texts.HELP, reply_markup=back_kb() if user else None)


@router.callback_query(MenuCb.filter(F.action == "help"))
async def cb_help(callback: CallbackQuery) -> None:
    await show(callback, texts.HELP, back_kb())
    await callback.answer()


@router.message(Registration.name, F.text)
async def registration_name(
    message: Message, state: FSMContext, repo: Repository, user: User | None
) -> None:
    if user is None:
        try:
            name = validate_character_name(message.text)
        except ValidationError as e:
            await message.answer(f"⚠️ {e}")
            return
        await repo.create_user(message.from_user.id, name, config.DEFAULT_TIMEZONE)
        user = await repo.get_user(message.from_user.id)
        await message.answer(texts.welcome(name))
    text, kb = await open_template_picker(state, repo, user, context="onboarding")
    await message.answer(text, reply_markup=kb)


@router.message(Registration.name)
async def registration_name_not_text(message: Message) -> None:
    await message.answer(texts.ASK_NAME_TEXT_ONLY)
