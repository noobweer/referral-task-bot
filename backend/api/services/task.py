from api.models import Task, Completed, TelegramUser
from django.db.models import OuterRef, Exists
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from .profile import get_profile_telegram


def get_available_tasks(telegram_id: int):
    user = get_profile_telegram(telegram_id)

    completed_tasks = Completed.objects.filter(
        user=user,
        task=OuterRef('pk')
    )

    return Task.objects.filter(is_active=True).exclude(
        Exists(completed_tasks)
    )


def get_pending_tasks(telegram_id: int):
    user = get_profile_telegram(telegram_id)
    return Completed.objects.filter(user=user, status='PE') if user else None


def get_task_by_id(task_id: int):
    return get_object_or_404(Task, pk=task_id)


def start_task(task_id: int, telegram_id: int):
    user = get_profile_telegram(telegram_id)
    if not user:
        raise HttpError(404, "User with this telegram_id not found")

    task = get_task_by_id(task_id)
    if not task:
        raise HttpError(404, "Task not found")

    try:
        completed = Completed.objects.get(user=user, task=task)
        if completed.status == Completed.STATUS_DONE:
            raise HttpError(400, "Task already completed and cannot be restarted")
        return completed, False
    except Completed.DoesNotExist:
        completed = Completed.objects.create(
            user=user,
            task=task,
            status=Completed.STATUS_PENDING
        )
        return completed, True


def complete_task(task_id: int, telegram_id: int):
    user = get_profile_telegram(telegram_id)
    if not user:
        raise HttpError(404, "User with this telegram_id not found")

    task = get_task_by_id(task_id)
    if not task:
        raise HttpError(404, "Task not found")

    try:
        completed = Completed.objects.get(user=user, task=task)
    except Completed.DoesNotExist:
        raise HttpError(404, "Task not started")

    if completed.status == Completed.STATUS_DONE:
        raise HttpError(400, "Task already completed")

    completed.status = Completed.STATUS_DONE
    completed.save(update_fields=['status'])
    return completed
