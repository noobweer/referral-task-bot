from ninja import NinjaAPI
from typing import List

from .services.profile import get_profile_telegram, create_or_update_profile
from .schemas.profile import ProfileIn, ProfileOut

from .services.task import get_available_tasks, get_pending_tasks, get_task_by_id, start_task, complete_task
from .schemas.task import TaskOut, TaskStatusOut

api = NinjaAPI()


@api.get("/profiles/{telegram_id}", response=ProfileOut)
def get_profile(request, telegram_id: int):
    return get_profile_telegram(telegram_id)


@api.post('/profiles/', response={201: ProfileOut, 200: ProfileOut})
def post_profile(request, payload: ProfileIn):
    profile, is_created = create_or_update_profile(payload)
    status_code = 201 if is_created else 200
    return status_code, profile


@api.get('/tasks/', response=List[TaskOut])
def get_tasks(request, telegram_id: int, variant: str):
    if variant == "pending":
        return get_pending_tasks(telegram_id)
    return get_available_tasks(telegram_id)


@api.get('/tasks/{task_id}', response=TaskOut)
def get_task(request, task_id: int):
    return get_task_by_id(task_id)


@api.post('/tasks/{task_id}/start', response={201: TaskStatusOut, 200: TaskStatusOut})
def post_start_task(request, task_id: int, telegram_id: int):
    task, is_created = start_task(task_id, telegram_id)
    status_code = 201 if is_created else 200
    return status_code, task


@api.post('/tasks/{task_id}/complete', response=TaskStatusOut)
def post_complete_task(request, task_id: int, telegram_id: int):
    return complete_task(task_id, telegram_id)

