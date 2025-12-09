from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from bot.api_client.client import fetch_welcome_messages, fetch_create_profile
from bot.keyboards.main_menu import main_menu
from bot.keyboards.subscribe import get_subscribe_keyboard
from bot.utils.subscription import is_user_subscribed

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    bot = message.bot
    user = message.from_user
    telegram_id = user.id
    username = user.username

    # 🔒 1. Сначала проверяем подписку
    if not await is_user_subscribed(bot, telegram_id):
        await message.answer(
            "👋 Привет! Чтобы пользоваться ботом, сначала подпишись на наш канал:",
            reply_markup=get_subscribe_keyboard(),
        )
        return  # дальше бота не пускаем

    # ✅ 2. Пользователь подписан — создаём профиль и показываем приветствие
    await fetch_create_profile(telegram_id, username)
    welcomes = await fetch_welcome_messages()

    if welcomes:
        for welcome in welcomes:
            text = welcome.get("text") if isinstance(welcome, dict) else str(welcome)
            await message.answer(text)

    # Показываем главное меню
    await message.answer("Выберите действие:", reply_markup=main_menu)


# 🔁 Обработчик кнопки "Проверить подписку"
@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    bot = callback.message.bot
    user_id = callback.from_user.id

    if await is_user_subscribed(bot, user_id):
        await callback.message.answer(
            "✅ Спасибо за подписку! Теперь бот полностью доступен.",
            reply_markup=main_menu,
        )
    else:
        await callback.answer(
            "❗️ Вы ещё не подписались на канал.",
            show_alert=True
        )
