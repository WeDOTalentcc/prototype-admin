"""Backwards-compatibility shim — real implementation in app/domains/voice/services."""
from app.domains.voice.services.gemini_voice_service import *  # noqa: F401,F403
# R-056: dependency already lazily imported in canonical (app/domains/voice/services/gemini_voice_service.py) -- OK
