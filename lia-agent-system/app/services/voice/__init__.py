"""Legacy voice services package.

The OpenMic.ai and Deepgram providers were removed in 2026-04-18 (audit
P0-4). The canonical voice stack is now Twilio Programmable Voice (PSTN /
WhatsApp) plus Gemini Live Audio (web VoIP), implemented under
``app/domains/voice/services/``.
"""
__all__: list[str] = []
