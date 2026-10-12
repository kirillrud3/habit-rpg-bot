import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

from bot.handlers import get_routers
from bot.handlers.errors import on_error
from bot.middlewares import RepoMiddleware, RetryOnNetworkError
from db import Database, Repository


async def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit("BOT_TOKEN не задан. Скопируй .env.example в .env и впиши токен.")

    db = Database(os.getenv("DB_PATH", "data/bot.db"))
    await db.connect()
    await db.init_schema()
    repo = Repository(db)

    # PROXY_URL — если Telegram API недоступен напрямую (http://, socks5://)
    session = AiohttpSession(proxy=os.getenv("PROXY_URL") or None)
    session.middleware(RetryOnNetworkError())
    bot = Bot(token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(RepoMiddleware(repo))
    dp.include_routers(*get_routers())
    dp.errors.register(on_error)

    await bot.set_my_commands([
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="add", description="Добавить свою привычку"),
        BotCommand(command="profile", description="Профиль персонажа"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="achievements", description="Достижения"),
        BotCommand(command="help", description="Как играть"),
        BotCommand(command="start", description="Начать заново / меню"),
    ])
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        if isinstance(e, SystemExit) and e.code not in (None, 0):
            raise
