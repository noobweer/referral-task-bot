from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from bot.config.settings import REQUIRED_CHANNEL_USERNAME
from bot.keyboards.subscribe import get_subscribe_keyboard
from bot.api_client.client import notify_locker_passed

async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    """
    Проверяем через Telegram API, подписан ли пользователь на канал.
    """
    # Если канал не задан — считаем, что проверка выключена
    if not REQUIRED_CHANNEL_USERNAME:
        return True

    chat_id = "@" + REQUIRED_CHANNEL_USERNAME  # например, @cassh_lab

    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        # Подходящие статусы: обычный участник или админ/создатель
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest:
        # Ошибки типа "чат не найден" или пользователь не найден — считаем, что НЕ подписан
        return False


async def ensure_subscribed_message(message: Message) -> bool:
    """
    Используем в обработчиках сообщений:
    - если подписан → True и продолжаем работу
    - если НЕ подписан → показываем клавиатуру "подпишись", возвращаем False
    """
    bot = message.bot
    user_id = message.from_user.id

    if await is_user_subscribed(bot, user_id):
        await notify_locker_passed(user_id)
        return True

    await message.answer(
        "❗️ Чтобы пользоваться ботом, нужно подписаться на наш канал.\n\n"
        "1️⃣ Нажми «✅ Подписаться на канал»\n"
        "2️⃣ Вернись в бот и жми «🔁 Проверить подписку»",
        reply_markup=get_subscribe_keyboard(),
    )
    return False
