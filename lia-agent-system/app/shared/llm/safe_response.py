"""
safe_llm_with_flag — shim de retrocompatibilidade.

EXTRACTED TO: libs/lia-llm/lia_llm/safe_response.py
Este arquivo é shim — remover quando todos os consumers migrarem para:
    from lia_llm.safe_response import safe_llm_with_flag, LLMResponseEnvelope
    from lia_llm import safe_llm_with_flag
"""
# ruff: noqa: F401, F403
from lia_llm.safe_response import *  # noqa: F401, F403
from lia_llm.safe_response import (  # noqa: F401 — re-export explícito para IDEs
    LLMFailureMode,
    LLMResponseEnvelope,
    safe_llm_with_flag,
    safe_llm_with_flag_async,
)
