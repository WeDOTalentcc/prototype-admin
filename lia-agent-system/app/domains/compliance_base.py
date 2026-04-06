"""
ComplianceDomainPrompt — Camada intermediária de compliance obrigatória.

Todo domínio LIA DEVE herdar desta classe em vez de DomainPrompt diretamente.
Garante: FairnessGuard + PII Strip + PromptInjection + FactCheck + Audit por herança.

Padrão:
    class MeuDominio(ComplianceDomainPrompt):  # compliance automático
        ...

    class MeuDominio(DomainPrompt):  # rejeitado pelo DomainWorkflow (warning)
        ...

Referências legais:
    - LGPD Art. 12: minimização de dados pessoais
    - EU AI Act Art. 13: transparência em sistemas de IA de alto risco
    - CLT Art. 373-A / Lei 9.029/95: proibição de discriminação em recrutamento
"""
import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.domains.base import DomainContext, DomainPrompt, DomainResponse, IntentResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LIA-C07: StageContext — contexto de estágio de contratação
# ---------------------------------------------------------------------------

class HiringStage(str, Enum):
    SOURCING = "sourcing"
    SCREENING = "screening"
    SHORTLIST = "shortlist"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTION = "rejection"
    GENERAL = "general"


@dataclass
class StageContext:
    """Context about the current hiring stage — influences compliance strictness.

    LIA-C07: High-impact stages (shortlist, rejection, offer) require stricter
    FairnessGuard checks including Layer 3 (semantic LLM analysis).
    """
    stage: HiringStage = HiringStage.GENERAL
    job_id: str = ""
    candidate_id: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def is_high_impact(self) -> bool:
        """Shortlist, rejection and offer decisions are high-impact for bias."""
        return self.stage in (HiringStage.SHORTLIST, HiringStage.REJECTION, HiringStage.OFFER)

    @property
    def fairness_action_type(self) -> str:
        """Maps stage to FairnessGuard action_type for Layer 3 routing."""
        mapping = {
            HiringStage.SHORTLIST: "shortlist",
            HiringStage.REJECTION: "rejection",
            HiringStage.OFFER: "offer_extended",
            HiringStage.INTERVIEW: "interview_invite",
            HiringStage.SCREENING: "screening",
            HiringStage.SOURCING: "sourcing",
            HiringStage.GENERAL: "general",
        }
        return mapping.get(self.stage, "general")


class ComplianceDomainPrompt(DomainPrompt):
    """
    Camada intermediária que adiciona compliance automático a todos os domínios LIA.

    Subclasses DEVEM implementar os métodos abstratos de DomainPrompt.
    Os métodos pre_process e post_process são chamados automaticamente pelo
    DomainWorkflow quando o domínio herda desta classe.

    Layers de compliance aplicadas em pre_process:
        - Layer 1: FairnessGuard (bias explícito + implícito)
        - Layer 2: PII Strip (CPF, email, telefone, RG, CNPJ, quasi-identifiers)
        - Layer 3: PromptInjectionGuard (se disponível)

    Layers aplicadas em post_process:
        - FactChecker (verificação de claims numéricos na resposta)
        - Validadores de domínio customizados (via _domain_validators)
    """

    # Subclasses podem sobrescrever para customizar compliance por domínio
    _compliance_config: dict[str, Any] | None = None

    @property
    def compliance_config(self) -> dict[str, Any]:
        """
        Retorna configuração de compliance para este domínio.
        Subclasses podem sobrescrever _compliance_config para customizar.
        """
        defaults: dict[str, Any] = {
            "fairness_guard_enabled": True,
            "pii_strip_enabled": True,
            "prompt_injection_guard_enabled": True,
            "fact_checker_enabled": True,
            # Domínios marcados como high_impact ativam Layer 3 do FairnessGuard
            "high_impact": False,
            # action_type passado ao check_with_layer3 (ex: "rejection", "shortlist")
            "fairness_action_type": "general",
            # Setor para check_sector (ex: "tech", "financeiro", "saude")
            "sector": None,
        }
        if self._compliance_config:
            defaults.update(self._compliance_config)
        return defaults

    def get_compliance_config(self) -> dict[str, Any]:
        """Retorna a configuração de compliance deste domínio (API pública)."""
        return self.compliance_config

    def get_required_prompt_blocks(self) -> list[str]:
        """
        Retorna lista de blocos obrigatórios no system prompt deste domínio.
        Subclasses podem sobrescrever para adicionar blocos específicos.
        """
        return [
            "LGPD_COMPLIANCE",
            "NON_DISCRIMINATION",
            "DATA_MINIMIZATION",
        ]

    # ------------------------------------------------------------------
    # LIA-P02: get_system_prompt com auto-injeção de blocos de compliance
    # ------------------------------------------------------------------

    def get_system_prompt(self, base_prompt: str = "") -> str:
        """
        Retorna o system prompt do domínio com blocos de compliance injetados automaticamente.

        Blocos injetados:
        - LGPD_COMPLIANCE_BLOCK: informações sobre processamento de dados
        - NON_DISCRIMINATION_BLOCK: proibição de filtros discriminatórios
        - DEFENSIVE_BLOCK: defesa contra jailbreak/prompt injection
        - ANTI_SYCOPHANCY_BLOCK: prevenção de concordância acrítica

        LIA-P02: Auto-injeção garante que todos os domínios que herdam
        ComplianceDomainPrompt recebam blocos de compliance sem opt-in manual.
        Referência: EU AI Act Art. 13 — sistemas de alto risco devem ser
        transparentes sobre suas capacidades e limitações.
        """
        required_blocks = self.get_required_prompt_blocks()

        try:
            from app.shared.prompts.interaction_patterns import (
                ANTI_SYCOPHANCY_BLOCK,
                DEFENSIVE_BLOCK,
            )
        except ImportError:
            ANTI_SYCOPHANCY_BLOCK = ""
            DEFENSIVE_BLOCK = ""

        # Build LGPD compliance block text
        lgpd_block = (
            "\n[COMPLIANCE LGPD/EU AI Act]\n"
            "Este sistema processa dados pessoais em conformidade com a LGPD (Lei 13.709/2020) "
            "e o EU AI Act 2024. Não colete ou exponha dados pessoais desnecessariamente. "
            "Em decisões automatizadas de alto impacto, apresente explicação ao candidato (Art. 20 LGPD)."
        ) if "LGPD_COMPLIANCE" in required_blocks else ""

        non_discrim_block = (
            "\n[NÃO DISCRIMINAÇÃO]\n"
            "Decisões de recrutamento devem ser baseadas em competências e fit cultural. "
            "É proibido usar filtros de gênero, raça, cor, origem, religião ou idade "
            "(CLT Art. 373-A, Lei 9.029/95, EU AI Act Annex III item 4)."
        ) if "NON_DISCRIMINATION" in required_blocks else ""

        # Assemble prompt
        parts = []
        if base_prompt:
            parts.append(base_prompt)
        if lgpd_block:
            parts.append(lgpd_block)
        if non_discrim_block:
            parts.append(non_discrim_block)
        if DEFENSIVE_BLOCK:
            parts.append(f"\n{DEFENSIVE_BLOCK}")
        if ANTI_SYCOPHANCY_BLOCK:
            parts.append(f"\n{ANTI_SYCOPHANCY_BLOCK}")

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Pre-processing: chamado pelo DomainWorkflow ANTES de process_intent
    # ------------------------------------------------------------------

    async def pre_process(
        self,
        query: str,
        context: DomainContext,
        stage_context: Optional["StageContext"] = None,
    ) -> DomainResponse | None:
        """
        Executa checks de compliance antes do processamento do intent.

        Retorna DomainResponse de bloqueio se algo for detectado,
        ou None para continuar o fluxo normal.

        Ordem:
            1. FairnessGuard (viés discriminatório)
            2. PII Strip (remove PII do query antes de enviar ao LLM)
            3. PromptInjectionGuard
        """
        config = self.compliance_config

        # --- Layer 1: FairnessGuard ---
        if config.get("fairness_guard_enabled", True):
            blocked_response = await self._run_fairness_guard(query, context, stage_context)
            if blocked_response is not None:
                return blocked_response

        # --- Layer 2: PII Strip ---
        # Nota: strip_pii modifica apenas o que vai ao LLM internamente;
        # o query original fica em context para rastreabilidade.
        if config.get("pii_strip_enabled", True):
            stripped = self._strip_pii(query)
            if stripped != query:
                logger.info(
                    "[Compliance][%s] PII detectado e removido do query (len_orig=%d len_stripped=%d)",
                    self.domain_id, len(query), len(stripped),
                )
                # Armazena versão sanitizada no contexto para uso downstream
                context.metadata["pii_stripped_query"] = stripped
                context.metadata["pii_was_stripped"] = True

        # --- Layer 3: PromptInjection Guard ---
        if config.get("prompt_injection_guard_enabled", True):
            injection_blocked = await self._check_prompt_injection(query, context)
            if injection_blocked is not None:
                return injection_blocked

        return None

    # ------------------------------------------------------------------
    # Post-processing: chamado pelo DomainWorkflow APÓS format
    # ------------------------------------------------------------------

    async def post_process(
        self,
        response: DomainResponse,
        context: DomainContext,
    ) -> DomainResponse:
        """
        Executa validações de compliance na resposta já formatada.

        Aplica FactChecker e validadores de domínio customizados.
        Nunca bloqueia — apenas anota metadados de compliance.
        """
        config = self.compliance_config

        if config.get("fact_checker_enabled", True):
            response = await self._run_fact_checker(response, context)

        return response

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _run_fairness_guard(
        self,
        query: str,
        context: DomainContext,
        stage_context: Optional["StageContext"] = None,
    ) -> DomainResponse | None:
        """Executa FairnessGuard. Retorna DomainResponse de bloqueio ou None.

        LIA-C07: stage_context overrides config defaults — more specific wins.
        High-impact stages (shortlist, rejection, offer) trigger Layer 3 check.
        """
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard

            guard = FairnessGuard()
            config = self.compliance_config
            action_type = config.get("fairness_action_type", "general")
            high_impact = config.get("high_impact", False)

            # Stage context overrides config defaults (more specific wins)
            if stage_context is not None:
                action_type = stage_context.fairness_action_type
                high_impact = high_impact or stage_context.is_high_impact

            # Usa check_with_layer3 para domínios high_impact, check simples para demais
            if high_impact:
                result = await guard.check_with_layer3(
                    text=query,
                    action_type=action_type,
                    context=f"domain={self.domain_id}",
                )
            else:
                result = guard.check(query)

            if result.is_blocked:
                logger.warning(
                    "[Compliance][%s] FairnessGuard bloqueou query: category=%s terms=%s",
                    self.domain_id,
                    result.category,
                    result.blocked_terms,
                )
                return DomainResponse(
                    success=False,
                    message=result.educational_message or "",
                    metadata={
                        "blocked_by": "fairness_guard",
                        "block_category": result.category,
                        "blocked_terms": result.blocked_terms,
                        "confidence": result.confidence,
                        "original_query": result.original_query,
                        "compliance_layer": "pre_process",
                        "domain_id": self.domain_id,
                    },
                )

            # Registrar soft_warnings sem bloquear
            if result.soft_warnings:
                logger.info(
                    "[Compliance][%s] FairnessGuard soft warnings: %d avisos",
                    self.domain_id, len(result.soft_warnings),
                )
                context.metadata.setdefault("fairness_warnings", []).extend(
                    result.soft_warnings
                )

        except Exception as exc:
            # Fail-open: erro no guard não bloqueia o fluxo, mas é logado
            logger.error(
                "[Compliance][%s] FairnessGuard falhou (fail-open): %s",
                self.domain_id, exc, exc_info=True,
            )

        return None

    def _strip_pii(self, text: str) -> str:
        """
        Remove PII e quasi-identificadores do texto antes de enviar ao LLM.

        Aplica strip_pii_for_llm_prompt de app.shared.pii_masking.
        Fail-safe: retorna texto original em caso de erro.
        """
        try:
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            return strip_pii_for_llm_prompt(text)
        except Exception as exc:
            logger.warning(
                "[Compliance][%s] PII strip falhou (fail-safe): %s",
                self.domain_id, exc,
            )
            return text

    async def _check_prompt_injection(
        self, text: str, context: DomainContext
    ) -> DomainResponse | None:
        """
        Verifica prompt injection. Retorna DomainResponse de bloqueio ou None.

        Fail-safe: se PromptInjectionGuard não estiver disponível, retorna None.
        """
        try:
            from app.shared.compliance.prompt_injection_guard import PromptInjectionGuard

            guard = PromptInjectionGuard()
            result = guard.check(text)

            if result.is_blocked:
                logger.warning(
                    "[Compliance][%s] PromptInjectionGuard bloqueou query: reason=%s",
                    self.domain_id,
                    getattr(result, "reason", "unknown"),
                )
                return DomainResponse(
                    success=False,
                    message=(
                        getattr(result, "message", None)
                        or "Solicitação bloqueada por segurança."
                    ),
                    metadata={
                        "blocked_by": "prompt_injection_guard",
                        "compliance_layer": "pre_process",
                        "domain_id": self.domain_id,
                    },
                )

        except ImportError:
            # PromptInjectionGuard não disponível — silencioso
            logger.debug(
                "[Compliance][%s] PromptInjectionGuard não disponível (skipped)",
                self.domain_id,
            )
        except Exception as exc:
            # Fail-open: erro não bloqueia fluxo
            logger.warning(
                "[Compliance][%s] PromptInjectionGuard falhou (fail-open): %s",
                self.domain_id, exc,
            )

        return None

    async def _run_fact_checker(
        self, response: DomainResponse, context: DomainContext
    ) -> DomainResponse:
        """
        Executa FactChecker na resposta.

        Nunca bloqueia — apenas adiciona metadados de verificação.
        """
        try:
            from app.shared.compliance.fact_checker import FactChecker

            checker = FactChecker()
            context_data = context.current_data if context else {}
            result = checker.check_response(response.message, context_data)

            fact_check_metadata = result.to_metadata()
            if response.metadata is None:
                response.metadata = {}
            response.metadata.update(fact_check_metadata)

            if result.inaccurate_claims > 0:
                logger.warning(
                    "[Compliance][%s] FactChecker: %d claim(s) não verificado(s)",
                    self.domain_id, result.inaccurate_claims,
                )
                response.metadata["fact_check_warning"] = (
                    f"{result.inaccurate_claims} claim(s) could not be verified as accurate"
                )

        except Exception as exc:
            # Fail-open
            logger.warning(
                "[Compliance][%s] FactChecker falhou (fail-open): %s",
                self.domain_id, exc,
            )

        return response

    # ------------------------------------------------------------------
    # Garantir que os métodos abstratos de DomainPrompt ainda são abstratos
    # ------------------------------------------------------------------

    @abstractmethod
    def get_allowed_actions(self):
        ...

    @abstractmethod
    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        ...

    @abstractmethod
    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        ...

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} domain_id='{self.domain_id}' "
            f"compliance=True high_impact={self.compliance_config.get('high_impact', False)}>"
        )
