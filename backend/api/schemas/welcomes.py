from ninja import Schema


class WelcomeOut(Schema):
    text: str
    id: int
