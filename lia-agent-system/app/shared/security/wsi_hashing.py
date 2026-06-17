"""WSI response hashing — EU AI Act / LGPD compliance (Task #511).

Provê SHA-256 determinístico sobre respostas WSI para:
  - audit trail imutável em `wsi_responses`
  - detecção de duplicatas / integridade
  - cross-reference em logs sem expor texto bruto

Determinismo:
  - mesma resposta + mesma sessão + mesma pergunta → mesmo hash (idempotente)
  - mesma resposta em sessão/pergunta diferente → hash diferente
    (impede correlação cruzada acidental e respeita escopo de cada interação)

Texto normalizado: lowercase + espaços colapsados (whitespace runs → 1 espaço,
trim nas pontas). Preserva semântica enquanto torna o hash robusto a ruídos
de transcrição e variações de capitalização.
"""
from __future__ import annotations

import hashlib
import re

__all__ = ["hash_response", "normalize_text", "EU_AI_ACT_DISCLAIMER"]


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(raw: str | None) -> str:
    """Normaliza texto para hashing: lowercase + collapse whitespace + trim."""
    if not raw:
        return ""
    return _WHITESPACE_RE.sub(" ", raw.strip().lower())


def hash_response(raw_text: str | None, session_id: str, question_id: str) -> str:
    """Retorna SHA-256 hex (64 chars) da tupla (session_id, question_id, texto normalizado).

    Args:
        raw_text: resposta bruta do candidato (pode ser vazia).
        session_id: ID da sessão WSI (escopo).
        question_id: ID da pergunta (escopo).

    Returns:
        Hex string SHA-256 — 64 caracteres lowercase.
    """
    payload = f"{session_id}:{question_id}:{normalize_text(raw_text)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


EU_AI_ACT_DISCLAIMER = (
    "AVISO DE TRANSPARÊNCIA — EU AI Act Art. 13 / LGPD Art. 20\n"
    "Este parecer foi gerado por sistema automatizado de IA classificado como "
    "Alto Risco (recrutamento e seleção). Os scores e recomendações são "
    "auxiliares à decisão humana e não substituem o julgamento do recrutador. "
    "O candidato tem direito a revisão humana, explicação dos critérios e "
    "contestação da análise (LGPD Art. 20 §1º). Trilha de auditoria imutável "
    "disponível via endpoint /api/v1/wsi/reports/audit/{session_id}."
)
