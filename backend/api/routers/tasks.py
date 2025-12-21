from typing import List

from ninja import Router
from ninja.files import UploadedFile
from ninja import File
from django.conf import settings
from ..models import Task
from ..models import Completed
from ..services.tasks import (
    get_pending_tasks,
    get_available_tasks,
    get_task_history,
    get_task_by_id,
    start_task,
    complete_task,
)
from ..schemas.tasks import TaskOut, TaskStatusOut, TaskHistoryOut

router = Router()


def _serialize_task(request, task: Task) -> TaskOut:
    
    image_url = None
    if getattr(task, "image", None):
        # task.image.url -> "/media/task_images/..."
        # build_absolute_uri -> "http://127.0.0.1:8000/media/task_images/..."
        image_url = f"{settings.PUBLIC_BASE_URL}{task.image.url}"

    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        instruction=task.instruction,
        link=task.link,
        reward=task.reward,
        image=image_url,
    )


@router.get("/", response=List[TaskOut])
async def get_tasks(request, telegram_id: int, variant: str, level: int | None = None):
    if variant == "pending":
        tasks = await get_pending_tasks(telegram_id)
    else:
        tasks = await get_available_tasks(telegram_id, level=level)

    return [_serialize_task(request, task) for task in tasks]


@router.get("/{task_id}", response=TaskOut)
async def get_task(request, task_id: int):
    task = await get_task_by_id(task_id)
    return _serialize_task(request, task)


@router.post("/{task_id}/start", response={201: TaskStatusOut, 200: TaskStatusOut})
async def post_start_task(request, task_id: int, telegram_id: int):
    task_status, is_created = await start_task(task_id, telegram_id)
    status_code = 201 if is_created else 200
    return status_code, task_status


@router.post("/{task_id}/complete", response=TaskStatusOut)
async def post_complete_task(
    request,
    task_id: int,
    telegram_id: int,
    proof_text: str = "",
    proof_image: UploadedFile | None = File(None),
):
    return await complete_task(
        task_id,
        telegram_id,
        proof_text=proof_text,
        proof_image=proof_image
    )


def _serialize_history_item(item: Completed) -> TaskHistoryOut:
    proof_image_url = None
    if getattr(item, "proof_image", None):
        proof_image_url = f"{settings.PUBLIC_BASE_URL}{item.proof_image.url}"

    return TaskHistoryOut(
        id=item.id,
        task_id=item.task_id,
        title=item.task.title,
        reward=item.task.reward,
        level=getattr(item.task, "level", 0) or 0,
        status=item.status,
        status_label=item.get_status_display(),
        admin_comment=item.admin_comment,
        proof_text=item.proof_text,
        proof_image=proof_image_url,
    )


@router.get("/history", response=List[TaskHistoryOut])
async def get_history(request, telegram_id: int, limit: int = 20):
    items = await get_task_history(telegram_id, limit=limit)
    return [_serialize_history_item(x) for x in items]

