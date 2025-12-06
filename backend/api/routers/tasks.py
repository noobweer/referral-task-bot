from ninja import Router
from typing import List
from ..services.tasks import get_pending_tasks, get_available_tasks, get_task_by_id, start_task, complete_task
from ..schemas.tasks import TaskOut, TaskStatusOut

router = Router()


@router.get('/', response=List[TaskOut])
async def get_tasks(request, telegram_id: int, variant: str):
    if variant == "pending":
        return await get_pending_tasks(telegram_id)
    return await get_available_tasks(telegram_id)


@router.get('/{task_id}', response=TaskOut)
async def get_task(request, task_id: int):
    return await get_task_by_id(task_id)


@router.post('/{task_id}/start', response={201: TaskStatusOut, 200: TaskStatusOut})
async def post_start_task(request, task_id: int, telegram_id: int):
    task, is_created = await start_task(task_id, telegram_id)
    status_code = 201 if is_created else 200
    return status_code, task


@router.post('/{task_id}/complete', response=TaskStatusOut)
async def post_complete_task(request, task_id: int, telegram_id: int):
    return await complete_task(task_id, telegram_id)
