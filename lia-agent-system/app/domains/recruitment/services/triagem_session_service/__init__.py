"""
triagem_session_service package.

Sub-modules:
  _shared      - constants, prompts, shared helpers
  wsi_blocks   - block loading, building, and mapping
  scoring      - deterministic scoring and final score calculation
  conversation - intent classification, off-script/contextual question generation
  messaging    - process_message, _generate_lia_response, _pre_completion_response
  lifecycle    - create/start/complete/get_history session functions
  completion   - _trigger_post_completion, _persist_wsi_results
  voice        - TTS and phone call handling
  service      - TriagemSessionService facade + get_triagem_service factory
"""
from .service import TriagemSessionService, get_triagem_service, triagem_service

from .whatsapp_consent import TriagemWhatsAppConsentService, maybe_send_expiry_reminder

__all__ = [
    "TriagemSessionService",
    "get_triagem_service",
    "triagem_service",
    "TriagemWhatsAppConsentService",
    "maybe_send_expiry_reminder",
]
