"""PII Masking — shim de retrocompatibilidade.

EXTRACTED TO: libs/lia-pii/lia_pii/masking.py  (G10-pii, 2026-06-13)

Todo código real vive agora em lia-pii. Este módulo re-exporta tudo para
que os ~50 consumers existentes no monolito não precisem ser migrados
imediatamente (strangler fig). Migrar consumers para:

    from lia_pii import mask_pii, PIIMaskingFilter, ...
    # ou
    from lia_pii.masking import mask_pii, ...

Remover este shim quando todos os consumers migrarem para lia-pii.
"""
# noqa: F401, F403  (re-export shim — wildcard + explicit exports intencional)
from lia_pii.masking import *  # noqa: F401, F403
from lia_pii.masking import (
    CPF_PATTERN,
    EMAIL_PATTERN,
    PHONE_BR_PATTERN,
    PII_PATTERNS,
    PIIMaskingFilter,
    _CNPJ_PATTERN,
    _LLM_PROMPT_PII_PATTERNS,
    _LLM_PROMPT_PII_STRIPPING_ENABLED,
    _PRESIDIO_ENABLED,
    _PRESIDIO_ENTITIES,
    _PRESIDIO_LANG,
    _PRESIDIO_SPACY_MODEL,
    _RECRUITER_CHAT_MASK_PII,
    _RG_PATTERN_STRICT,
    _UUID_V4_PATTERN,
    _chat_pii_mask_identity,
    chat_should_mask_identity,
    get_masked_logger,
    install_global_pii_masking,
    mask_phone_preserve_tail,
    mask_pii,
    mask_pii_outbound,
    reset_chat_pii_mask_identity,
    reset_skip_llm_input_pii_strip,
    set_chat_pii_mask_identity,
    set_skip_llm_input_pii_strip,
    strip_pii_for_llm_prompt,
    strip_pii_for_llm_prompt_async,
)

__all__ = [
    "CPF_PATTERN",
    "EMAIL_PATTERN",
    "PHONE_BR_PATTERN",
    "PII_PATTERNS",
    "PIIMaskingFilter",
    "chat_should_mask_identity",
    "get_masked_logger",
    "install_global_pii_masking",
    "mask_phone_preserve_tail",
    "mask_pii",
    "mask_pii_outbound",
    "reset_chat_pii_mask_identity",
    "reset_skip_llm_input_pii_strip",
    "set_chat_pii_mask_identity",
    "set_skip_llm_input_pii_strip",
    "strip_pii_for_llm_prompt",
]
