import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


async def show(callback: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    """Показать экран: отредактировать сообщение с кнопкой, а если нельзя — прислать новое."""
    msg = callback.message
    if isinstance(msg, Message):
        try:
            await msg.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return
            logger.debug("Не удалось отредактировать сообщение: %s", e)
    await send(callback, text, kb)


async def send(callback: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> Message:
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    return await callback.bot.send_message(chat_id, text, reply_markup=kb)


async def drop_keyboard(callback: CallbackQuery) -> None:
    """Убрать кнопки со старого сообщения (ошибки игнорируем)."""
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
