"""Fallback-хендлеры и глобальный обработчик ошибок."""
import logging

from aiogram import Router
from aiogram.types import CallbackQuery, ErrorEvent, Message

from bot import texts
from bot.keyboards.inline import main_menu_kb
from db.models import User

logger = logging.getLogger(__name__)
router = Router(name="fallback")


@router.message()
async def unknown_message(message: Message, user: User | None = None) -> None:
    if user is None:
        await message.answer(texts.NEED_START)
    else:
        await message.answer(texts.UNKNOWN_INPUT, reply_markup=main_menu_kb())


@router.callback_query()
async def unknown_callback(callback: CallbackQuery, user: User | None = None) -> None:
    await callback.answer(texts.NEED_START if user is None else texts.STALE_BUTTON, show_alert=user is None)


async def on_error(event: ErrorEvent) -> bool:
    """Логирует любое исключение и сообщает пользователю, не роняя бота."""
    logger.exception("Ошибка при обработке апдейта %s", event.update.update_id, exc_info=event.exception)
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer(texts.ERROR, show_alert=True)
        elif event.update.message:
            await event.update.message.answer(texts.ERROR)
    except Exception:  # noqa: BLE001 — ответить не получилось, просто логируем
        logger.warning("Не удалось уведомить пользователя об ошибке", exc_info=True)
    return True
