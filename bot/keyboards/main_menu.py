from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Выбрать задание")],
        [KeyboardButton(text="⏱️ Активные задания")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💸 Выплата")],
        [KeyboardButton(text="📜 История заданий")],
        [KeyboardButton(text="💼 Поддержка")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)