from aiogram import Router, F
from bot.api_client.client import fetch_profile, fetch_create_profile
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote
from bot.utils.subscription import ensure_subscribed_message
from bot.config.settings import SUPPORT_USERNAME

router = Router()


def get_level_title(level: int) -> str:
    return {
        0: "Новичок",
        1: "Активный",
        2: "Продвинутый",
        3: "Премиум",
    }.get(level, "Новичок")


@router.message(F.text == "👤 Профиль")
async def show_available_tasks(message: Message):
    # 🔒 Проверяем подписку
    if not await ensure_subscribed_message(message):
        return
    telegram_id = message.from_user.id
    profile = await fetch_profile(telegram_id)

    if not profile:
        # пробуем создать профиль
        await fetch_create_profile(telegram_id, message.from_user.username)
        profile = await fetch_profile(telegram_id)

    if not profile:
        await message.answer("Профиль временно недоступен. Попробуй ещё раз через минуту 🙏")
        return

    username = profile.get("username") or "—"
    points = profile.get("points", 0)
    tasks_done = profile.get("tasks_done", 0)
    date_joined = profile.get("date_joined_bot", "")
    last_activity = profile.get("last_activity", "")
    level = profile.get("level", 0)
    level_title = get_level_title(level)

    await message.answer(
        f"👤 Профиль пользователя: <b>{username}</b>\n\n"
        f"🆔 ID: <code>{profile.get('telegram_id', telegram_id)}</code>\n"
        f"⭐ Уровень: <b>Level {level} — {level_title}</b>\n"
        f"💰 Баланс: <b>{profile.get('points', 0)}</b> баллов\n"
        f"✅ Выполнено заданий: <b>{profile.get('tasks_done', 0)}</b>\n",
        parse_mode="HTML"
    )

@router.message(F.text == "💸 Выплата")
async def payout_info(message: Message):
    if not await ensure_subscribed_message(message):
        return

    telegram_id = message.from_user.id
    profile = await fetch_profile(telegram_id)

    if not profile:
        await message.answer("Профиль временно недоступен. Попробуй позже 🙏")
        return

    balance = profile.get("points", 0)
    username = profile.get("username") or (message.from_user.username or "")

    text = (
        "💸 <b>Выплата</b>\n\n"
        f"💰 Твой баланс: <b>{balance}</b>\n\n"
        "<b>Минимальная сумма вывода 1000</b>\n"
        "Чтобы получить выплату — напиши менеджеру.\n"
        "Сообщение уже будет заполнено автоматически 👇"
    )

    prefill_text = (
        f"Привет! Хочу получить выплату.\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"Username: @{username}\n"
    )

    url = f"https://t.me/{SUPPORT_USERNAME}?text={quote(prefill_text)}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Написать менеджеру", url=url)]
        ]
    )

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
