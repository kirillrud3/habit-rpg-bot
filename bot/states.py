from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()


class TemplateSelect(StatesGroup):
    choosing = State()


class HabitForm(StatesGroup):
    """Создание и редактирование привычки (режим хранится в данных FSM)."""
    name = State()
    stats = State()
    xp = State()
    limit = State()
    confirm = State()


class SettingsForm(StatesGroup):
    rename = State()
