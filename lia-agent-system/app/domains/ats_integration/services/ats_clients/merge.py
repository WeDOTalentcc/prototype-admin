# Z6-01: shim — fonte canônica em app.services.ats_clients.merge
from app.services.ats_clients.merge import *  # noqa: F401,F403
from app.services.ats_clients.merge import MergeClient  # noqa: F401
from app.services.ats_clients.merge import MERGE_CIRCUIT, circuit_breaker_decorator  # noqa: F401
