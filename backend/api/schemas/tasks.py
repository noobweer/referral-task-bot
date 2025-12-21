from ninja import Schema
from typing import Optional

class TaskOut(Schema):
    id: int
    title: str
    description: str
    instruction: str
    link: str
    reward: int
    image: Optional[str] = None

class TaskStatusOut(Schema):
    task: TaskOut
    status: str

class TaskHistoryOut(Schema):
    id: int
    task_id: int
    title: str
    reward: int
    level: int
    status: str
    status_label: str
    admin_comment: Optional[str] = None
    proof_text: Optional[str] = None
    proof_image: Optional[str] = None