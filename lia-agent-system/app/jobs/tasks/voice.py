"""Celery tasks: voice (Fase 7).

The OpenMic webhook → ``run_openmic_wsi_pipeline_task`` task was removed in
2026-04-18 (audit P0-4) along with the OpenMic.ai integration. Voice WSI
scoring is now handled inline by the canonical Twilio + Gemini Live pipeline
under ``app/domains/voice/services/``; no Celery task is required at this
boundary.
"""
__all__: list[str] = []
