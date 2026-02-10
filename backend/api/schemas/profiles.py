from datetime import datetime
from typing import Optional
from ninja import Schema
from pydantic import field_serializer
from typing import Any


class ProfileIn(Schema):
    telegram_id: int
    username: str


class ProfileOut(Schema):
    telegram_id: int
    username: Optional[str]
    date_joined_bot: Optional[str]
    last_activity: Optional[str]
    tasks_done: int
    points: int
    level: int

    @field_serializer('date_joined_bot', 'last_activity')
    def serialize_datetime(self, dt: Any):
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt
        return dt.strftime("%d.%m.%Y – %H:%M")
