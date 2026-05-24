"""SuggestionClickEvent model — P1-3 Fase 2 (Onda 4-Fase8 2026-05-24).

Captura eventos de clique do usuário em sugestões da LIA (ChatSuggestionsPanel
lâmpada, dynamic cards de /lia/suggestions, ChatWorkflowReels, settings_chips).

Por que tabela separada (não extend InteractionFeedback):
- InteractionFeedback = feedback SOBRE mensagem da LIA (thumbs, rating, correction)
- SuggestionClickEvent = ação PROATIVA do usuário (clique em sugestão)
- Single responsibility — semânticas diferentes não devem misturar

Multi-tenancy: company_id obrigatório (vem do JWT, NUNCA do payload).
LGPD: sem PII direto — só metadata + suggestion_id/text (sem candidato).

Fase 2 (esta migration): logging puro.
Fase 3 (próxima sprint, requer ~1 semana de tráfego):
  - Repository agregado top_suggestions_for_company(company_id, page_context, days)
  - Wire ranqueamento em /lia/suggestions endpoint (Bayesian smoothing)
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


# Allowlist canonical de fontes (validate no endpoint pra evitar values bagunçados)
SUGGESTION_SOURCES = {
    "panel_static",    # ChatSuggestionsPanel q1-q33 (legacy estáticas)
    "panel_dynamic",   # /lia/suggestions endpoint (dynamic cards)
    "reel_card",       # ChatWorkflowReels (22 cards canonical)
    "chip_settings",   # UnifiedChatEmptyState SETTINGS_CHIPS
    "smart_prompt",    # PromptSuggestionsPanel getSmartSuggestions (candidate context)
    "reel_action",     # ChatWorkflowReels RAIL_A_SUGGESTIONS actions
}


class SuggestionClickEvent(Base):
    """
    Captura cliques em sugestões pra alimentar pipeline de aprendizado.

    Tabela append-only (sem UPDATE). Cada clique = 1 row.
    Retenção LGPD: dados não-PII; cleanup canonical via lgpd_cleanup_service
    rule futura (atualmente sem TTL, será adicionado quando tabela > 100k rows).
    """
    __tablename__ = "suggestion_click_events"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Multi-tenancy canonical (REGRA E1)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)

    # Suggestion identification
    suggestion_id = Column(String(100), nullable=False, index=True)
    # ex: "q1".."q33" pra panel_static, hash do title pra panel_dynamic,
    # node id pra reel_card ("triagem", "entrevista", etc.)
    suggestion_text = Column(String(500), nullable=False)
    # Conteúdo textual da sugestão (até 500 chars — protege contra prompt injection)
    suggestion_source = Column(String(50), nullable=False, index=True)
    # Um dos SUGGESTION_SOURCES (enforced no endpoint, NOT NULL no DB)

    # Context para Fase 3 ranqueamento
    page_context = Column(String(100), nullable=True)
    # ex: "candidato_detalhe", "kanban", "agent_studio", "home"
    chat_mode = Column(String(20), nullable=True)
    # "sidebar" | "floating" | "fullscreen" | "minimized"

    click_metadata = Column(JSON, default=dict)
    # Free-form: domain_hint, intent_hint, category, etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Onda 4-Fase8: extend_existing=True canonical pro projeto (QW1) — evita
    # reload conflict. Composite indexes são criados via migration SQL raw
    # (190_suggestion_clicks_feedback_check.py) — model não precisa replicar.
    __table_args__ = {"extend_existing": True}

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "user_id": self.user_id,
            "suggestion_id": self.suggestion_id,
            "suggestion_text": self.suggestion_text,
            "suggestion_source": self.suggestion_source,
            "page_context": self.page_context,
            "chat_mode": self.chat_mode,
            "click_metadata": self.click_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
