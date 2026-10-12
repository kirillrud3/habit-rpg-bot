from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.repository import Repository


class RepoMiddleware(BaseMiddleware):
    """Кладёт в data хендлера `repo` и `user` (User | None)."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["repo"] = self.repo
        tg_user = data.get("event_from_user")
        data["user"] = await self.repo.get_user(tg_user.id) if tg_user else None
        return await handler(event, data)
