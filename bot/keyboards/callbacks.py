from aiogram.filters.callback_data import CallbackData


class MenuCb(CallbackData, prefix="m"):
    action: str  # main | mark | profile | stats | achievements | habits | add | settings | help


class MarkCb(CallbackData, prefix="mk"):
    habit_id: int


class UndoCb(CallbackData, prefix="u"):
    source: str  # mark | stats — какой экран обновить после отмены


class TplCb(CallbackData, prefix="tp"):
    action: str  # toggle | done | skip
    idx: int = -1


class HabitCb(CallbackData, prefix="h"):
    action: str  # open | templates | delete_ask | delete_yes | edit_name | edit_rewards | edit_limit
    habit_id: int = 0


class FormCb(CallbackData, prefix="f"):
    action: str  # stat | stats_done | xp | limit | save | restart | cancel
    value: str = ""


class SettingsCb(CallbackData, prefix="s"):
    action: str  # tz_menu | tz | rename | cancel
    idx: int = -1
