import httpx
from ..config.settings import API_BASE_URL


async def fetch_profile(telegram_id: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/profiles/{telegram_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error: {e}")
            return None


async def fetch_create_profile(telegram_id: int, username: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE_URL}/profiles/",
                json={"telegram_id": telegram_id, "username": username or ""}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error: {e}")
            return None


async def fetch_welcome_messages():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/welcomes/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"API error: {e}")
            return []


async def fetch_available_tasks(telegram_id):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/tasks/",
                params={"telegram_id": telegram_id, "variant": "available"}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error: {e}")
            return []


async def fetch_pending_tasks(telegram_id: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/tasks/",
                params={"telegram_id": telegram_id, "variant": "pending"}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error fetching pending tasks: {e}")
            return []


async def fetch_task_details(task_id):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/tasks/{task_id}",
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"API error: {e}")
            return None


async def start_task(task_id: int, telegram_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE_URL}/tasks/{task_id}/start",
                params={"telegram_id": telegram_id}
            )
            return True if resp.status_code in (200, 201) else False
        except Exception as e:
            print(f"Ошибка начала задания {task_id}: {e}")
            return False


async def complete_task(task_id: int, telegram_id: int, proof_text: str = "") -> bool:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE_URL}/tasks/{task_id}/complete",
                params={"telegram_id": telegram_id, "proof_text": proof_text}
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Ошибка отправки на проверку {task_id}: {e}")
            return False

