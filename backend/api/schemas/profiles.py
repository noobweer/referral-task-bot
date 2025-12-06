from datetime import datetime
from typing import Optional
from ninja import Schema
from pydantic import field_serializer


class ProfileIn(Schema):
    telegram_id: int
    username: str


class ProfileOut(Schema):
    username: Optional[str] = None
    date_joined_bot: datetime
    last_activity: datetime
    tasks_done: int

    @field_serializer('date_joined_bot', 'last_activity')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.strftime("%d.%m.%Y – %H:%M")
