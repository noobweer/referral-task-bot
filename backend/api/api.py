from ninja import NinjaAPI

from .routers.profiles import router as profiles_router
from .routers.tasks import router as tasks_router
from .routers.welcomes import router as welcomes_router
from .routers.history import router as history_router
from .routers.pushes import router as pushes_router

api = NinjaAPI()

api.add_router("/profiles/", profiles_router)
api.add_router("/tasks/", tasks_router)
api.add_router("/welcomes/", welcomes_router)
api.add_router("/history", history_router)
api.add_router("/pushes/", pushes_router)