from ninja import Schema


class TaskOut(Schema):
    id: int
    title: str
    description: str
    instruction: str
    link: str
    reward: int


class TaskStatusOut(Schema):
    task: TaskOut
    status: str
