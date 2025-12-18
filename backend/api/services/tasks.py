from api.models import Task, Completed, TelegramUser
from django.db.models import OuterRef, Exists
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from ninja.errors import HttpError
from asgiref.sync import sync_to_async

from .profiles import _get_profile_telegram

def calc_level(tasks_done: int) -> int:
    if tasks_done >= 30:
        return 3
    if tasks_done >= 15:
        return 2
    if tasks_done >= 5:
        return 1
    return 0


def get_user_level(user: TelegramUser) -> int:
    return calc_level(int(user.tasks_done or 0))


@sync_to_async
def get_available_tasks(telegram_id: int, level: int | None = None):
    user = _get_profile_telegram(telegram_id)
    if not user:
        return []

    user_level = get_user_level(user)

    # если клиент запросил level выше — запрещаем
    if level is not None and int(level) > user_level:
        raise HttpError(403, "Level not available")

    completed_tasks = Completed.objects.filter(
        user=user,
        task=OuterRef("pk"),
    ).exclude(status=Completed.STATUS_REJECTED)  # ✅ rejected НЕ блокирует повтор

    qs = Task.objects.filter(is_active=True)

    # показываем только задания доступных уровней
    qs = qs.filter(level__lte=user_level)

    # если выбран конкретный раздел — только этот level
    if level is not None:
        qs = qs.filter(level=int(level))

    return list(qs.exclude(Exists(completed_tasks)))




@sync_to_async
def get_pending_tasks(telegram_id: int):
    user = _get_profile_telegram(telegram_id)
    if not user:
        return []
    return list(
        Task.objects.filter(
            completed__user=user,
            completed__status__in=[Completed.STATUS_PENDING, Completed.STATUS_REVIEW]
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

    # ✅ запрет на старт заданий выше уровня пользователя
    user_level = get_user_level(user)
    if hasattr(task, "level") and int(task.level or 0) > user_level:
        raise HttpError(403, "Task level is not доступен")

    try:
        completed = Completed.objects.select_related('task', 'user').get(
            user=user,
            task=task
        )

        # если уже принято — нельзя заново
        if completed.status == Completed.STATUS_DONE:
            raise HttpError(400, "Task already completed and cannot be restarted")

        # ✅ если было отклонено — сбрасываем и даём начать заново
        if completed.status == Completed.STATUS_REJECTED:
            completed.status = Completed.STATUS_PENDING
            completed.rewarded = False

            # если есть поля proof_text / proof_image — чистим
            if hasattr(completed, "proof_text"):
                completed.proof_text = ""
            if hasattr(completed, "proof_image"):
                completed.proof_image = None

            completed.save()
            return Completed.objects.select_related('task', 'user').get(pk=completed.pk), False

        return completed, False

    except Completed.DoesNotExist:
        completed = Completed.objects.create(
            user=user,
            task=task,
            status=Completed.STATUS_PENDING
        )
        return Completed.objects.select_related('task', 'user').get(pk=completed.pk), True



@sync_to_async
def complete_task(task_id: int, telegram_id: int, proof_text: str | None = None, proof_image=None):
    user = _get_profile_telegram(telegram_id)
    if not user:
        raise HttpError(404, "User with this telegram_id not found")

    task = _get_task_by_id(task_id)
    if not task:
        raise HttpError(404, "Task not found")

    try:
        completed = Completed.objects.select_related('task', 'user').get(user=user, task=task)
    except Completed.DoesNotExist:
        raise HttpError(404, "Task not started")

    # если уже принято — нельзя снова
    if completed.status == Completed.STATUS_DONE:
        raise HttpError(400, "Task already approved")

    completed.status = Completed.STATUS_REVIEW

    if proof_text:
        completed.proof_text = proof_text

    if proof_image is not None:
        # UploadedFile -> читаем байты и сохраняем в ImageField
        filename = proof_image.name or "proof.jpg"
        completed.proof_image.save(filename, ContentFile(proof_image.read()), save=False)

    completed.save()
    return completed
