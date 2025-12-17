from bot.utils.subscription import ensure_subscribed_message
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import httpx
from aiogram.types import BufferedInputFile
from bot.config.settings import SUPPORT_USERNAME
from bot.api_client.client import fetch_profile

from bot.api_client.client import (
    fetch_available_tasks,
    fetch_pending_tasks,
    fetch_task_details,
    start_task,
    complete_task
)
from typing import Dict

LAST_TASK_PHOTO: Dict[int, int] = {}

PROOF_SENT_TEXT = (
    "✅ Доказательство отправлено на проверку!\n\n"
    "Баллы начислятся после подтверждения админом."
)


router = Router()

def _needed_tasks_for_level(level: int) -> int:
    # пороги должны совпадать с backend calc_level()
    return {0: 0, 1: 5, 2: 15, 3: 30}.get(level, 0)


def _build_levels_keyboard(user_level: int, tasks_done: int) -> InlineKeyboardMarkup:
    levels = [
        (0, "Level 0 — минимальные"),
        (1, "Level 1 — HR / простые финансы"),
        (2, "Level 2 — МФО / гайды"),
        (3, "Level 3 — премиум"),
    ]

    rows = []
    for lvl, title in levels:
        if lvl <= user_level:
            # доступно
            rows.append([InlineKeyboardButton(text=f"✅ {title}", callback_data=f"level_select:{lvl}")])
        else:
            need = _needed_tasks_for_level(lvl)
            left = max(0, need - tasks_done)
            rows.append([InlineKeyboardButton(text=f"🔒 {title} (ещё {left})", callback_data=f"level_locked:{lvl}")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


LEVEL_SECTIONS = {
    0: "Level 0 — минимальные",
    1: "Level 1 — HR / простые финансы",
    2: "Level 2 — МФО / гайды",
    3: "Level 3 — премиум",
}

def _build_sections_keyboard(user_level: int) -> InlineKeyboardMarkup:
    kb = []
    for lvl in range(4):
        title = LEVEL_SECTIONS[lvl]
        lock = " 🔒" if user_level < lvl else ""
        kb.append([InlineKeyboardButton(text=f"{title}{lock}", callback_data=f"section:{lvl}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


class ProofState(StatesGroup):
    waiting_proof_text = State()


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

    # Берём профиль, чтобы понять какой уровень доступен
    from bot.api_client.client import fetch_profile
    profile = await fetch_profile(telegram_id)

    if not profile:
        await message.answer("Профиль временно недоступен. Попробуй ещё раз через минуту 🙏")
        return

    user_level = int(profile.get("level", 0) or 0)
    tasks_done = int(profile.get("tasks_done", 0) or 0)

    keyboard = _build_levels_keyboard(user_level=user_level, tasks_done=tasks_done)
    await message.answer("📚 Выбери раздел заданий:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("section:"))
async def open_section(callback: CallbackQuery):
    if not await ensure_subscribed_message(callback.message):
        return

    telegram_id = callback.from_user.id
    level = int(callback.data.split(":")[1])

    # тянем задания выбранного уровня
    tasks = await fetch_available_tasks(telegram_id, level=level)

    if not tasks:
        await callback.message.edit_text(
            "В этом разделе пока нет доступных заданий 🙂",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад к разделам", callback_data="back_to_sections")]
            ])
        )
        await callback.answer()
        return

    keyboard = _build_list_keyboard(tasks, "task")
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="⬅️ Назад к разделам", callback_data="back_to_sections")]
    )

    await callback.message.edit_text(
        f"📋 Задания раздела Level {level}:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_sections")
async def back_to_sections(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    profile = await fetch_profile(telegram_id) or {}
    user_level = int(profile.get("level", 0) or 0)

    keyboard = _build_sections_keyboard(user_level)
    await callback.message.edit_text("📂 Выбери раздел заданий:", reply_markup=keyboard)
    await callback.answer()


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

async def _delete_last_task_photo(callback: CallbackQuery):
    """Удаляет последнюю картинку задания в этом чате, если она есть."""
    chat_id = callback.message.chat.id
    msg_id = LAST_TASK_PHOTO.pop(chat_id, None)
    if msg_id is None:
        return

    try:
        await callback.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception as e:
        print("ERROR DELETING TASK PHOTO:", e)

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
        # Если картинка есть и это HTTPS-URL
        # Если картинка есть и это HTTPS-URL
    if image_url and isinstance(image_url, str) and image_url.startswith("https://"):
        try:
            # 0. Удаляем предыдущую картинку (если была)
            await _delete_last_task_photo(callback)

            # 1. Скачиваем картинку с твоего сервера
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url, timeout=10.0)
                resp.raise_for_status()
                image_bytes = resp.content

            # 2. Оборачиваем в файл для Telegram
            photo_input = BufferedInputFile(image_bytes, filename="task_image.jpg")

            # 3. Отправляем чистое фото (без подписи и кнопок)
            photo_msg = await callback.message.answer_photo(
                photo=photo_input,
            )

            # 4. Запоминаем id картинки для этого чата
            LAST_TASK_PHOTO[callback.message.chat.id] = photo_msg.message_id

            # 5. Отдельным сообщением отправляем текст с кнопками
            await callback.message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

        except Exception as e:
            print("ERROR SENDING PHOTO (download/upload):", e, "URL:", image_url)

            # Fallback: просто текст + кнопки
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
    else:
        # Картинки нет — старое поведение
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
async def handle_complete_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])

    await _delete_last_task_photo(callback)

    # запоминаем task_id и ждём доказательство
    await state.set_state(ProofState.waiting_proof_text)
    await state.update_data(task_id=task_id)

    await callback.message.edit_text(
        "📸 Отправь СКРИН выполнения задания.\n\n"
        "Если по какой-то причине скрина нет — можешь написать доказательство текстом.\n\n"
        "После этого я отправлю задание на проверку ✅",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_proof")]
        ])
    )
    await callback.answer()

@router.message(ProofState.waiting_proof_text, F.photo)
async def handle_proof_photo(message: Message, state: FSMContext):
    if not await ensure_subscribed_message(message):
        return

    data = await state.get_data()
    task_id = data.get("task_id")
    telegram_id = message.from_user.id

    # Берём фото максимального размера
    photo = message.photo[-1]

    # Получаем файл из Telegram
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    image_bytes = file_bytes.read()

    ok = await complete_task(
        task_id=task_id,
        telegram_id=telegram_id,
        proof_text="",  # можно оставить пустым
        proof_image_bytes=image_bytes,
        filename="proof.jpg",
        mime_type="image/jpeg",
    )

    if not ok:
        await message.answer("❌ Не удалось отправить скрин. Попробуй ещё раз.")
        return

    await state.clear()

    await message.answer(PROOF_SENT_TEXT)


@router.message(ProofState.waiting_proof_text)
async def handle_proof_text(message: Message, state: FSMContext):
    if not await ensure_subscribed_message(message):
        return

    data = await state.get_data()
    task_id = data.get("task_id")
    telegram_id = message.from_user.id

    proof_text = (message.text or "").strip()
    if not proof_text:
        await message.answer("Пришли доказательство текстом 🙏")
        return

    ok = await complete_task(task_id, telegram_id, proof_text=proof_text)
    if not ok:
        await message.answer("Не удалось отправить на проверку. Попробуй ещё раз.")
        return

    await state.clear()

    await message.answer(PROOF_SENT_TEXT)




@router.callback_query(F.data == "cancel_proof")
async def cancel_proof(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Окей, отменил отправку ✅")
    await callback.answer()



@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    tasks = await fetch_available_tasks(telegram_id)
    
    await _delete_last_task_photo(callback)

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
    
    await _delete_last_task_photo(callback)

    if not tasks:
        await callback.message.edit_text("Нет активных заданий.")
        await callback.answer()
        return

    keyboard = _build_list_keyboard(tasks, "pending_task")
    await callback.message.edit_text("⏱️ Ваши активные задания:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("level_locked:"))
async def level_locked(callback: CallbackQuery):
    lvl = int(callback.data.split(":")[1])
    need = _needed_tasks_for_level(lvl)
    await callback.answer(
        f"🔒 Этот уровень пока закрыт.\nНужно выполнить минимум {need} заданий.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("level_select:"))
async def level_select(callback: CallbackQuery):
    lvl = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id

    # получаем задания только выбранного уровня
    tasks = await fetch_available_tasks(telegram_id, level=lvl)

    if not tasks:
        await callback.message.edit_text("Нет доступных заданий в этом разделе.")
        await callback.answer()
        return

    keyboard = _build_list_keyboard(tasks, "task")
    await callback.message.edit_text(f"📋 Задания из раздела Level {lvl}:", reply_markup=keyboard)
    await callback.answer()
