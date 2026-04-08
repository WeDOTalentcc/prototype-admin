# Z6-01: shim — fonte canônica em app.services.ats_clients.gupy
from app.services.ats_clients.gupy import *  # noqa: F401,F403
from app.services.ats_clients.gupy import GupyClient  # noqa: F401
from app.services.ats_clients.gupy import GUPY_CIRCUIT, circuit_breaker_decorator  # noqa: F401
