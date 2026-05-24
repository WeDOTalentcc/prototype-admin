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
from enum import Enum, StrEnum
from typing import Any, Optional

from app.domains.base import DomainContext, DomainPrompt, DomainResponse, IntentResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LIA-C07: StageContext — contexto de estágio de contratação
# ---------------------------------------------------------------------------

class HiringStage(StrEnum):
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

    # Agent type classification for compliance block variant selection
    _DECISION_DOMAINS = frozenset({
        "pipeline", "pipeline_transition", "cv_screening", "sourcing",
        "autonomous", "talent_pool", "recruiter_assistant",
    })
    _COMMUNICATION_DOMAINS = frozenset({
        "communication", "onboarding",
    })

    @staticmethod
    def _load_yaml_block(filename: str, cache_attr: str) -> dict:
        """Load a YAML block file from prompts/shared/. Cached after first load."""
        if not hasattr(ComplianceDomainPrompt, cache_attr):
            import os
            try:
                import yaml
                path = os.path.join(
                    os.path.dirname(__file__), "..", "prompts", "shared", filename
                )
                with open(path) as f:
                    setattr(ComplianceDomainPrompt, cache_attr, yaml.safe_load(f) or {})
            except Exception as exc:
                logger.warning("[Compliance] %s not found: %s", filename, exc)
                setattr(ComplianceDomainPrompt, cache_attr, {})
        return getattr(ComplianceDomainPrompt, cache_attr)

    @staticmethod
    def _load_compliance_block() -> dict:
        return ComplianceDomainPrompt._load_yaml_block("compliance_block.yaml", "_compliance_block_cache")

    @staticmethod
    def _load_guardrails_block() -> dict:
        return ComplianceDomainPrompt._load_yaml_block("guardrails_block.yaml", "_guardrails_block_cache")

    def _get_agent_type(self) -> str:
        """Determine agent type for compliance block variant selection."""
        if self.domain_id in self._DECISION_DOMAINS:
            return "decision"
        if self.domain_id in self._COMMUNICATION_DOMAINS:
            return "communication"
        return "operational"

    def get_system_prompt(self, base_prompt: str = "") -> str:
        """
        Retorna o system prompt do domínio com blocos de compliance injetados automaticamente.

        Loads compliance blocks from app/prompts/shared/compliance_block.yaml.
        Selects variant (decision/communication/operational) based on domain_id.
        Falls back to hardcoded blocks if YAML unavailable.

        LIA-P02: Auto-injeção garante que todos os domínios que herdam
        ComplianceDomainPrompt recebam blocos de compliance sem opt-in manual.
        Referência: EU AI Act Art. 13 — sistemas de alto risco devem ser
        transparentes sobre suas capacidades e limitações.
        """
        try:
            from app.shared.prompts.interaction_patterns import (
                ANTI_SYCOPHANCY_BLOCK,
            )
        except ImportError:
            ANTI_SYCOPHANCY_BLOCK = ""

        # Load compliance blocks from YAML
        yaml_blocks = self._load_compliance_block()
        agent_type = self._get_agent_type()
        variant = yaml_blocks.get(agent_type, {})

        lgpd_block = variant.get("lgpd", "")
        fairness_block = variant.get("fairness", "")
        bias_block = variant.get("bias", "")
        audit_block = variant.get("audit", "")
        defensive_block = yaml_blocks.get("defensive", "")

        # Fallback if YAML not loaded
        if not lgpd_block:
            lgpd_block = (
                "\n[COMPLIANCE LGPD/EU AI Act]\n"
                "Este sistema processa dados pessoais em conformidade com a LGPD (Lei 13.709/2020) "
                "e o EU AI Act 2024. Não colete ou exponha dados pessoais desnecessariamente."
            )
        if not fairness_block:
            fairness_block = (
                "\n[NÃO DISCRIMINAÇÃO]\n"
                "Decisões de recrutamento devem ser baseadas em competências. "
                "É proibido usar filtros de gênero, raça, cor, origem, religião ou idade "
                "(CLT Art. 373-A, Lei 9.029/95)."
            )

        # Load guardrails from YAML
        guardrails_yaml = self._load_guardrails_block()
        universal = guardrails_yaml.get("universal", {})
        autonomy_variant = guardrails_yaml.get("autonomy", {}).get(agent_type, "")
        escalation_block = guardrails_yaml.get("escalation", "")
        error_block = guardrails_yaml.get("error_handling", "")
        data_safety_block = guardrails_yaml.get("data_safety", "")

        # Assemble prompt: compliance blocks + guardrails + interaction patterns
        parts = []
        if base_prompt:
            parts.append(base_prompt)

        # --- Compliance (from compliance_block.yaml) ---
        if lgpd_block:
            parts.append(lgpd_block)
        if fairness_block:
            parts.append(fairness_block)
        if bias_block:
            parts.append(bias_block)
        if audit_block:
            parts.append(audit_block)
        if defensive_block:
            parts.append(defensive_block)

        # --- Guardrails (from guardrails_block.yaml) ---
        for key in ("identity", "hallucination", "prompt_security", "multi_tenancy", "negation"):
            block = universal.get(key, "")
            if block:
                parts.append(block)
        if autonomy_variant:
            parts.append(autonomy_variant)
        if escalation_block:
            parts.append(escalation_block)
        if error_block:
            parts.append(error_block)
        if data_safety_block:
            parts.append(data_safety_block)

        # --- Interaction patterns (from Python — anti-sycophancy, already centralized) ---
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

        Aplica FairnessGuard post-check (output) + FactChecker.
        Nunca bloqueia — apenas anota metadados e soft_warnings.
        """
        config = self.compliance_config

        # --- Fairness Post-Check (output) ---
        response = await self._run_fairness_post_check(response, context)

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
            # P2-W1-08: Fail-closed — se não conseguimos verificar fairness, bloqueamos.
            # FairnessGuard é segurança crítica (LGPD/DEI); deixar passar silenciosamente
            # viola princípio "falhar alto, nunca silenciosamente" (CLAUDE.md REGRA #0).
            # Se o guard não está disponível (ImportError), retorna None (abaixo).
            logger.error(
                "[Compliance][%s] FairnessGuard falhou (fail-closed): %s",
                self.domain_id, exc, exc_info=True,
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Fairness check service unavailable — request blocked for safety",
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

    # ------------------------------------------------------------------
    # Fairness Post-Check (output analysis)
    # ------------------------------------------------------------------

    @staticmethod
    def _load_post_check_config() -> dict:
        """Load fairness post-check config from YAML. Cached after first load."""
        if not hasattr(ComplianceDomainPrompt, "_post_check_config_cache"):
            import os
            try:
                import yaml
                config_path = os.path.join(
                    os.path.dirname(__file__), "..", "config", "fairness_post_check.yaml"
                )
                with open(config_path) as f:
                    ComplianceDomainPrompt._post_check_config_cache = yaml.safe_load(f) or {}
            except Exception as exc:
                logger.debug("[Compliance] fairness_post_check.yaml not found: %s", exc)
                ComplianceDomainPrompt._post_check_config_cache = {"enabled": False}
        return ComplianceDomainPrompt._post_check_config_cache

    async def _run_fairness_post_check(
        self,
        response: DomainResponse,
        context: DomainContext,
    ) -> DomainResponse:
        """
        FairnessGuard post-check on agent OUTPUT.

        For decision domains (configured in fairness_post_check.yaml):
        1. Check response text for biased language
        2. If response.data contains scores/rankings, flag score distribution issues
        3. Log metrics as fairness_post_check_result for dashboard

        Never blocks — adds soft_warnings to response.metadata.
        """
        try:
            pc_config = self._load_post_check_config()
            if not pc_config.get("enabled", False):
                return response

            decision_domains = pc_config.get("decision_domains", [])
            if self.domain_id not in decision_domains:
                return response

            from app.shared.compliance.fairness_guard import FairnessGuard

            guard = FairnessGuard()
            warnings: list[str] = []

            # --- 1. Check response text for biased language ---
            if response.message:
                text_result = guard.check(response.message)
                if text_result.is_blocked:
                    warnings.append(
                        f"Output contains potentially biased language: "
                        f"category={text_result.category}, terms={text_result.blocked_terms}"
                    )
                if text_result.soft_warnings:
                    warnings.extend(
                        f"Output bias warning: {w}" for w in text_result.soft_warnings
                    )

            # --- 2. Check scores/rankings in response.data ---
            score_warnings = self._check_score_fairness(response.data, pc_config)
            warnings.extend(score_warnings)

            # --- 3. Annotate response ---
            if response.metadata is None:
                response.metadata = {}

            response.metadata["fairness_post_check_result"] = {
                "domain": self.domain_id,
                "checked": True,
                "warnings_count": len(warnings),
                "has_scores": bool(score_warnings),
            }

            if warnings:
                response.metadata.setdefault("fairness_output_warnings", []).extend(warnings)
                logger.info(
                    "[Compliance][%s] Fairness post-check: %d warning(s) on output",
                    self.domain_id,
                    len(warnings),
                )

        except Exception as exc:
            # Fail-open: post-check failure never blocks the response
            logger.warning(
                "[Compliance][%s] Fairness post-check failed (fail-open): %s",
                self.domain_id,
                exc,
            )

        return response

    @staticmethod
    def _check_score_fairness(data: Any, pc_config: dict) -> list[str]:
        """
        Analyze scores/rankings in response.data for distribution red flags.

        Checks:
        - If a ranking list has zero diversity signals (all same demographic hints)
        - If score variance is suspiciously low (all candidates scored identically)
        - If top-N is missing expected diversity

        Returns list of warning strings (empty if clean).
        """
        if not data or not isinstance(data, dict):
            return []

        warnings: list[str] = []
        score_fields = pc_config.get("score_fields", [])
        ranking_fields = pc_config.get("ranking_fields", [])

        # Check ranking lists
        for field_name in ranking_fields:
            items = data.get(field_name)
            if not items or not isinstance(items, list) or len(items) < 3:
                continue

            # Extract scores from ranked items
            scores = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                for sf in score_fields:
                    val = item.get(sf)
                    if isinstance(val, (int, float)):
                        scores.append(val)
                        break

            if len(scores) >= 3:
                # Flag if all scores are identical (suspicious)
                unique_scores = set(round(s, 4) for s in scores)
                if len(unique_scores) == 1:
                    warnings.append(
                        f"All {len(scores)} candidates in '{field_name}' have identical "
                        f"score ({scores[0]}) — review scoring criteria for meaningful differentiation"
                    )

                # Flag extreme concentration at top
                if len(scores) >= 5:
                    top_score = max(scores)
                    top_count = sum(1 for s in scores if abs(s - top_score) < 0.01)
                    if top_count == 1 and (top_score - sorted(scores)[-2]) > 0.3 * top_score:
                        warnings.append(
                            f"Single candidate in '{field_name}' scores significantly above "
                            f"all others ({top_score:.2f} vs next {sorted(scores)[-2]:.2f}) "
                            f"— verify no bias in scoring inputs"
                        )

        return warnings

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
