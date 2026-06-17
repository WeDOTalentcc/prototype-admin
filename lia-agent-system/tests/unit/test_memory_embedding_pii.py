"""LGPD sensor B2 (audit 2026-06-06): memory_service (conversa) embeda com
mask_names=True -> nomes de candidato sao redigidos (Presidio) antes de ir pro
provedor. Conversa e a superficie de PII mais sensivel. Store e query usam o
MESMO nivel -> recall consistente.
"""
from __future__ import annotations

import inspect


def test_memory_service_masks_names_on_all_embed_calls():
    from app.domains.recruiter_assistant.services import memory_service as m

    src = inspect.getsource(m)
    assert src.count("mask_names=True") >= 4, (
        "memory_service deixou de mascarar nomes em alguma chamada de embedding "
        "-> conversa com nome de candidato vazaria pro provedor (LGPD)."
    )
