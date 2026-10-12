from aiogram import Router

from bot.handlers import checkin, errors, habits, menu, settings, start, templates


def get_routers() -> list[Router]:
    # Порядок важен: команды (/start, /menu) раньше FSM-ввода, fallback — последним.
    return [
        start.router,
        menu.router,
        settings.router,
        templates.router,
        checkin.router,
        habits.router,
        errors.router,
    ]
