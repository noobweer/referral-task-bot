from typing import List

from ninja import Router
from ninja.files import UploadedFile
from ninja import File
from django.conf import settings
from ..models import Task
from ..services.tasks import (
    get_pending_tasks,
    get_available_tasks,
    get_task_by_id,
    start_task,
    complete_task,
)
from ..schemas.tasks import TaskOut, TaskStatusOut

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


