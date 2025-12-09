from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config.settings import REQUIRED_CHANNEL_USERNAME


def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура:
    - 'Подписаться на канал' — ведёт в канал
    - 'Проверить подписку' — бот снова проверит статус
    """
    if not REQUIRED_CHANNEL_USERNAME:
        # Если канал не указан в .env — не показываем кнопки
        return InlineKeyboardMarkup(inline_keyboard=[])

    url = f"https://t.me/{REQUIRED_CHANNEL_USERNAME}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подписаться на канал",
                    url=url
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔁 Проверить подписку",
                    callback_data="check_subscription"
                )
            ]
        ]
    )
    return keyboard
