from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from db.models import User


class Registered(BaseFilter):
    """Пропускает только пользователей, у которых уже создан персонаж."""

    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return user is not None
