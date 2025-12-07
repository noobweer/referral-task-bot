from aiogram import Router, types
from aiogram.filters import Command
from bot.api_client.client import fetch_welcome_messages, fetch_create_profile
from bot.keyboards.main_menu import main_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    telegram_id = user.id
    username = user.username
    await fetch_create_profile(telegram_id, username)
    welcomes = await fetch_welcome_messages()

    if not welcomes:
        await message.answer("Добро пожаловать!", reply_markup=main_menu)
    else:
        for i, msg in enumerate(welcomes):
            text = msg["text"]
            if i == len(welcomes) - 1:
                await message.answer(text, reply_markup=main_menu)
            else:
                await message.answer(text)
