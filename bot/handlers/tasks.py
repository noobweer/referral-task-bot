from bot.utils.subscription import ensure_subscribed_message
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)
import httpx
from aiogram.types import BufferedInputFile
from bot.config.settings import SUPPORT_USERNAME

from bot.api_client.client import (
    fetch_available_tasks,
    fetch_pending_tasks,
    fetch_task_details,
    start_task,
    complete_task
)

router = Router()


def _format_task_text(task: dict) -> str:
    text = (
        f"📌 <b>{task['title']}</b>\n\n"
        f"📋 <b>Инструкция:</b>\n{task['instruction']}\n\n"
        f"💰 Награда: {task['reward']}₽"
    )
    if task.get("link"):
        text += f"\n🔗 <a href='{task['link']}'>[Нажми] Ссылка для выполнения</a>"
    return text


def _build_task_detail_keyboard(task_id: int, back_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить выполнение", callback_data=f"complete_task:{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=back_callback)]
    ])


def _build_list_keyboard(tasks: list, prefix: str) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(
            text=f"{t['title']} — {t['reward']}₽",
            callback_data=f"{prefix}:{t['id']}"
        )]
        for t in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(F.text == "📋 Выбрать задание")
async def show_available_tasks(message: Message):
    if not await ensure_subscribed_message(message):
        return
    telegram_id = message.from_user.id
    tasks = await fetch_available_tasks(telegram_id)
    if not tasks:
        await message.answer("Нет доступных заданий.")
        return
    keyboard = _build_list_keyboard(tasks, "task")
    await message.answer("📋 Доступные задания:", reply_markup=keyboard)


@router.message(F.text == "⏱️ Активные задания")
async def show_pending_tasks(message: Message):
    if not await ensure_subscribed_message(message):
        return
    telegram_id = message.from_user.id
    tasks = await fetch_pending_tasks(telegram_id)
    if not tasks:
        await message.answer("Нет активных заданий.")
        return
    keyboard = _build_list_keyboard(tasks, "pending_task")
    await message.answer("⏱️ Ваши активные задания:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("task:") | F.data.startswith("pending_task:"))
async def show_task_detail(callback: CallbackQuery):
    parts = callback.data.split(":")
    prefix, task_id = parts[0], int(parts[1])
    back_callback = "back_to_tasks" if prefix == "task" else "back_to_pending"

    task = await fetch_task_details(task_id)
    if not task:
        await callback.answer("Задание не найдено.", show_alert=True)
        return

    # 🔹 ВОЗВРАЩАЕМ старый формат текста, который точно работал
    text = _format_task_text(task)

    # Картинка (может быть None)
    image_url = task.get("image")

    # 🔹 Клавиатура — как раньше
    if prefix == "task":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Начать задание", callback_data=f"start_task:{task_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=back_callback)],
        ])
    else:
        keyboard = _build_task_detail_keyboard(task_id, back_callback)

    # 🔹 Пробуем отправить фото, НО текст не ломаем
        # Если картинка есть и это HTTPS-URL — качаем её сами и шлём как файл
        # Если картинка есть и это HTTPS-URL — качаем её сами и шлём как ОДНО сообщение (фото + текст)
    # Если картинка есть и это HTTPS-URL — качаем её сами
    if image_url and isinstance(image_url, str) and image_url.startswith("https://"):
        try:
            title = task.get("title", "")
            reward = task.get("reward", 0)

            # 1. Скачиваем картинку с твоего сервера
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url, timeout=10.0)
                resp.raise_for_status()
                image_bytes = resp.content

            # 2. Оборачиваем в файл для Telegram
            photo_input = BufferedInputFile(image_bytes, filename="task_image.jpg")

            # 3. СНАЧАЛА отправляем фото БЕЗ кнопок (только короткий caption)
            await callback.message.answer_photo(
                photo=photo_input,
                caption=f"📌 <b>{title}</b>\n\n💰 Награда: {reward}₽",
                parse_mode="HTML",
            )

            # 4. ПОТОМ отправляем текст с кнопками (как раньше)
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

        except Exception as e:
            print("ERROR SENDING PHOTO (download/upload):", e, "URL:", image_url)

            # Fallback: старое поведение — просто текст + кнопки
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
    else:
        # Картинки нет — ведём себя как раньше
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )



    await callback.answer()




@router.callback_query(F.data.startswith("start_task:"))
async def handle_start_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id

    if not await start_task(task_id, telegram_id):
        await callback.answer("Не удалось начать задание.", show_alert=True)
        return

    task = await fetch_task_details(task_id)
    if not task:
        await callback.answer("Ошибка: не удалось загрузить инструкцию.", show_alert=True)
        return

    text = _format_task_text(task)
    keyboard = _build_task_detail_keyboard(task_id, "back_to_tasks")
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=False
    )
    await callback.answer("Задание начато! ✅")


@router.callback_query(F.data.startswith("complete_task:"))
async def handle_complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id

    if not await complete_task(task_id, telegram_id):
        await callback.answer("Не удалось отправить подтверждение.", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ Вы подтвердили выполнение задания!\n\n"
        "⏳ Деньги поступят в течение нескольких дней.\n"
        f"Если у вас возникли проблемы: @{SUPPORT_USERNAME}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_tasks")]
        ])
    )
    await callback.answer("Выполнено! Спасибо!")


@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    tasks = await fetch_available_tasks(telegram_id)
    if not tasks:
        await callback.message.edit_text("Нет доступных заданий.")
        await callback.answer()
        return

    keyboard = _build_list_keyboard(tasks, "task")
    await callback.message.edit_text("📋 Доступные задания:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_pending")
async def back_to_pending(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    tasks = await fetch_pending_tasks(telegram_id)
    if not tasks:
        await callback.message.edit_text("Нет активных заданий.")
        await callback.answer()
        return

    keyboard = _build_list_keyboard(tasks, "pending_task")
    await callback.message.edit_text("⏱️ Ваши активные задания:", reply_markup=keyboard)
    await callback.answer()
