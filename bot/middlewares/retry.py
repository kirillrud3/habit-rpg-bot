import asyncio
import logging

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import GetUpdates, TelegramMethod
from aiogram.methods.base import TelegramType

logger = logging.getLogger(__name__)


class RetryOnNetworkError(BaseRequestMiddleware):
    """Повторяет запрос к Telegram API при обрыве соединения.

    getUpdates не трогаем — polling сам переподключается.
    """

    def __init__(self, attempts: int = 4, base_delay: float = 0.5) -> None:
        self.attempts = attempts
        self.base_delay = base_delay

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> TelegramType:
        if isinstance(method, GetUpdates):
            return await make_request(bot, method)
        for attempt in range(1, self.attempts + 1):
            try:
                return await make_request(bot, method)
            except TelegramNetworkError as e:
                if attempt == self.attempts:
                    raise
                logger.warning(
                    "Сетевая ошибка в %s (попытка %d/%d): %s",
                    type(method).__name__, attempt, self.attempts, e,
                )
                await asyncio.sleep(self.base_delay * attempt)
        raise AssertionError("unreachable")
