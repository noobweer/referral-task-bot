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
