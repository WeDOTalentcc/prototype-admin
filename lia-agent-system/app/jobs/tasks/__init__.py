"""Celery tasks package (Fase 7)."""

from app.jobs.tasks.agents import *  # noqa: F401,F403
from app.jobs.tasks.agents_legacy import *  # noqa: F401,F403
from app.jobs.tasks.communication import *  # noqa: F401,F403
from app.jobs.tasks.compliance import *  # noqa: F401,F403
from app.jobs.tasks.feedback import *  # noqa: F401,F403
from app.jobs.tasks.followup import *  # noqa: F401,F403
from app.jobs.tasks.memory import *  # noqa: F401,F403
from app.jobs.tasks.ml import *  # noqa: F401,F403
from app.jobs.tasks.voice import *  # noqa: F401,F403
