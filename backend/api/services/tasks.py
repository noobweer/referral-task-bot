from api.models import Task, Completed, TelegramUser
from django.db.models import OuterRef, Exists
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from asgiref.sync import sync_to_async

from .profiles import _get_profile_telegram


@sync_to_async
def get_available_tasks(telegram_id: int):
    user = _get_profile_telegram(telegram_id)

    completed_tasks = Completed.objects.filter(
        user=user,
        task=OuterRef('pk')
    )

    return list(Task.objects.filter(is_active=True).exclude(
        Exists(completed_tasks)
    ))


@sync_to_async
def get_pending_tasks(telegram_id: int):
    user = _get_profile_telegram(telegram_id)
    if not user:
        return []
    return list(
        Task.objects.filter(
            completed__user=user,
            completed__status=Completed.STATUS_PENDING
        )
    )


def _get_task_by_id(task_id: int):
    return get_object_or_404(Task, pk=task_id)


@sync_to_async
def get_task_by_id(task_id: int):
    return get_object_or_404(Task, pk=task_id)


@sync_to_async
def start_task(task_id: int, telegram_id: int):
    user = _get_profile_telegram(telegram_id)
    if not user:
        raise HttpError(404, "User with this telegram_id not found")

    task = _get_task_by_id(task_id)
    if not task:
        raise HttpError(404, "Task not found")

    try:
        # 🔥 Добавь select_related здесь
        completed = Completed.objects.select_related('task', 'user').get(
            user=user,
            task=task
        )
        if completed.status == Completed.STATUS_DONE:
            raise HttpError(400, "Task already completed and cannot be restarted")
        return completed, False
    except Completed.DoesNotExist:
        completed = Completed.objects.create(
            user=user,
            task=task,
            status=Completed.STATUS_PENDING
        )
        return Completed.objects.select_related('task', 'user').get(pk=completed.pk), True


@sync_to_async
def complete_task(task_id: int, telegram_id: int, proof_text: str | None = None):
    user = _get_profile_telegram(telegram_id)
    if not user:
        raise HttpError(404, "User with this telegram_id not found")

    task = _get_task_by_id(task_id)
    if not task:
        raise HttpError(404, "Task not found")

    try:
        completed = Completed.objects.select_related('task', 'user').get(
            user=user,
            task=task
        )
    except Completed.DoesNotExist:
        raise HttpError(404, "Task not started")

    # если уже принято — нельзя снова
    if completed.status == Completed.STATUS_DONE:
        raise HttpError(400, "Task already approved")

    # ✅ отправляем на проверку
    completed.status = Completed.STATUS_REVIEW

    if proof_text:
        completed.proof_text = proof_text

    completed.save(update_fields=['status', 'proof_text'])

    # ❌ ВАЖНО: здесь больше НЕТ начисления баллов
    return completed
