"""
IntentClassifierService - Classifies user input into intent categories using Claude.

Supports 4 intent types:
- DATA_INPUT: User providing job information
- QUESTION: User asking a question
- CORRECTION: User correcting previous info
- DEVIATION: User wants to change topic or skip step
"""
import json
import logging
import re
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)


class IntentType(StrEnum):
    DATA_INPUT = "DATA_INPUT"
    QUESTION = "QUESTION"
    CORRECTION = "CORRECTION"
    DEVIATION = "DEVIATION"
    REUSE_VACANCY = "REUSE_VACANCY"  # User wants to reuse/copy a previous vacancy


class ClassificationResult(BaseModel):
    """Result of intent classification."""
    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    original_text: str
    reasoning: str | None = None


class IntentClassifierService:
    """
    Service for classifying user input into intent categories.
    Uses Claude for fast, accurate classification in Portuguese.
    """

    CLASSIFICATION_PROMPT = """Classifique a intenção do usuário em uma das 5 categorias:

DATA_INPUT - Usuário fornecendo informações (cargo, salário, local, skills, requisitos)
QUESTION - Usuário fazendo pergunta (começa com "qual", "como", "quanto", "por que", "?")
CORRECTION - Usuário corrigindo info anterior ("na verdade", "não é", "errei", "corrijo")
DEVIATION - Usuário quer mudar tema ou pular etapa ("pula", "voltar", "próximo", "ignora")
REUSE_VACANCY - Usuário quer reaproveitar/copiar/clonar uma vaga anterior ("aproveitar vaga", "reutilizar vaga", "fast track", "copiar de uma vaga", "vaga anterior")

Contexto atual: {stage_context}

Mensagem: "{user_input}"

Responda APENAS em JSON:
{{"intent": "TIPO", "confidence": 0.0-1.0, "entities": {{}}, "reasoning": "breve"}}"""

    ENTITY_PATTERNS = {
        "salary": [
            r"(\d+(?:\.\d+)?)\s*[kK]",
            r"R\$?\s*(\d+(?:\.\d{3})*(?:,\d{2})?)",
            r"(\d+)\s*(?:mil|reais)",
        ],
        "work_model": [
            r"\b(remoto|híbrido|presencial|home\s*office)\b",
        ],
        "location": [
            r"\b(?:em|de)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)*)\b",
            r"\b(SP|RJ|MG|RS|PR|SC|BA|PE|CE|DF)\b",
        ],
        "seniority": [
            r"\b(júnior|junior|pleno|sênior|senior|lead|staff|principal)\b",
        ],
        "skills": [
            r"\b(Python|Java|JavaScript|TypeScript|React|Node|Angular|Vue|Go|Rust|AWS|Azure|GCP|Docker|Kubernetes|SQL|NoSQL|MongoDB|PostgreSQL|Redis|Kafka)\b",
        ],
    }

    CORRECTION_INDICATORS = [
        "na verdade", "não é", "errei", "corrijo", "correção",
        "esqueci", "mudou", "alterou", "desculpa", "ops",
        "não era", "não são", "deixa eu corrigir"
    ]

    DEVIATION_INDICATORS = [
        "pula", "próximo", "voltar", "anterior", "ignora",
        "skip", "next", "back", "muda", "outro assunto",
        "deixa pra lá", "depois", "outra hora", "me explica"
    ]

    QUESTION_INDICATORS = [
        "?", "qual", "como", "quanto", "quando", "onde",
        "por que", "porque", "quem", "o que", "poderia",
        "seria", "existe", "tem como"
    ]

    REUSE_VACANCY_INDICATORS = [
        "aproveitar vaga", "reutilizar vaga", "copiar vaga",
        "usar como base", "vaga anterior", "vaga passada",
        "mesma vaga", "igual a vaga", "baseado na vaga",
        "reaproveitar", "duplicar vaga", "clonar vaga",
        "vaga que já fiz", "vaga que criei", "vaga do ano passado",
        "fast track", "fasttrack", "vaga similar", "mesmos requisitos",
        "aproveitar uma vaga", "reutilizar uma vaga", "copiar de uma vaga",
        # Query-style indicators for vacancy search
        "ultimas vagas", "últimas vagas", "vagas criadas", "vagas anteriores",
        "buscar vaga", "buscar vagas", "pesquisar vaga", "pesquisar vagas",
        "listar vagas", "mostrar vagas", "ver vagas", "quais vagas",
        "vagas que criamos", "vagas que fizemos", "vagas recentes",
        "vagas do mês", "vagas do ano", "histórico de vagas",
        "vagas existentes", "vagas abertas", "vagas fechadas",
        "vagas preenchidas", "vagas contratadas", "busca de vagas"
    ]

    def __init__(self):
        self._llm_service = llm_service

    def _quick_classify(self, text: str) -> IntentType | None:
        """
        Quick rule-based pre-classification for obvious cases.
        Returns None if LLM classification is needed.
        """
        text_lower = text.lower().strip()

        if any(ind in text_lower for ind in self.CORRECTION_INDICATORS):
            return IntentType.CORRECTION

        if any(ind in text_lower for ind in self.REUSE_VACANCY_INDICATORS):
            return IntentType.REUSE_VACANCY

        if any(ind in text_lower for ind in self.DEVIATION_INDICATORS):
            if not text_lower.endswith("?"):
                return IntentType.DEVIATION

        if text.strip().endswith("?") or any(
            text_lower.startswith(q) for q in ["qual", "como", "quanto", "quando", "onde", "por que", "porque", "quem", "o que"]
        ):
            return IntentType.QUESTION

        return None

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """Extract entities from text using regex patterns."""
        entities: dict[str, Any] = {}

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if entity_type == "skills":
                        entities[entity_type] = list(set(matches))
                    elif entity_type == "salary":
                        raw_value = matches[0]
                        if isinstance(raw_value, str):
                            clean_value = raw_value.replace(".", "").replace(",", ".")
                            try:
                                entities[entity_type] = float(clean_value)
                            except ValueError:
                                entities[entity_type] = raw_value
                    else:
                        entities[entity_type] = matches[0] if len(matches) == 1 else matches
                    break

        return entities

    async def classify(
        self,
        user_input: str,
        stage_context: str | None = None,
        use_llm: bool = True
    ) -> ClassificationResult:
        """
        Classify user input into an intent category.

        Args:
            user_input: The user's message to classify
            stage_context: Current wizard stage for context (e.g., "salary", "competencies")
            use_llm: Whether to use LLM for classification (False for rule-based only)

        Returns:
            ClassificationResult with intent_type, confidence, entities, and original text
        """
        if not user_input or not user_input.strip():
            return ClassificationResult(
                intent_type=IntentType.DATA_INPUT,
                confidence=0.0,
                extracted_entities={},
                original_text=user_input or "",
                reasoning="Empty input"
            )

        entities = self._extract_entities(user_input)
        quick_intent = self._quick_classify(user_input)

        if quick_intent and not use_llm:
            return ClassificationResult(
                intent_type=quick_intent,
                confidence=0.85,
                extracted_entities=entities,
                original_text=user_input,
                reasoning="Rule-based classification"
            )

        if quick_intent and quick_intent in [IntentType.CORRECTION, IntentType.DEVIATION]:
            return ClassificationResult(
                intent_type=quick_intent,
                confidence=0.9,
                extracted_entities=entities,
                original_text=user_input,
                reasoning="Strong indicator match"
            )

        if use_llm:
            try:
                result = await self._classify_with_llm(user_input, stage_context, entities)
                return result
            except Exception as e:
                logger.warning(f"LLM classification failed, falling back to rules: {e}")

        if quick_intent:
            return ClassificationResult(
                intent_type=quick_intent,
                confidence=0.75,
                extracted_entities=entities,
                original_text=user_input,
                reasoning="Fallback to rule-based"
            )

        if entities:
            return ClassificationResult(
                intent_type=IntentType.DATA_INPUT,
                confidence=0.7,
                extracted_entities=entities,
                original_text=user_input,
                reasoning="Entities detected, assuming data input"
            )

        return ClassificationResult(
            intent_type=IntentType.DATA_INPUT,
            confidence=0.5,
            extracted_entities=entities,
            original_text=user_input,
            reasoning="Default classification"
        )

    async def _classify_with_llm(
        self,
        user_input: str,
        stage_context: str | None,
        pre_extracted_entities: dict[str, Any]
    ) -> ClassificationResult:
        """Use Claude for intent classification."""
        prompt = self.CLASSIFICATION_PROMPT.format(
            stage_context=stage_context or "geral",
            user_input=user_input[:500]
        )

        response = await self._llm_service.generate(prompt)

        json_match = re.search(r'\{[\s\S]*?\}', response)
        if not json_match:
            raise ValueError("No JSON found in LLM response")

        data = json.loads(json_match.group())

        intent_str = data.get("intent", "DATA_INPUT").upper()
        try:
            intent_type = IntentType(intent_str)
        except ValueError:
            intent_type = IntentType.DATA_INPUT

        confidence = float(data.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))

        llm_entities = data.get("entities", {})
        merged_entities = {**pre_extracted_entities, **llm_entities}

        return ClassificationResult(
            intent_type=intent_type,
            confidence=confidence,
            extracted_entities=merged_entities,
            original_text=user_input,
            reasoning=data.get("reasoning")
        )

    async def classify_batch(
        self,
        inputs: list[str],
        stage_context: str | None = None
    ) -> list[ClassificationResult]:
        """Classify multiple inputs (uses rule-based for speed)."""
        results = []
        for user_input in inputs:
            result = await self.classify(user_input, stage_context, use_llm=False)
            results.append(result)
        return results


intent_classifier_service = IntentClassifierService()


# ---------------------------------------------------------------------------
# UC-P3-10: Tier-filtered IntentClassifier factory
# ---------------------------------------------------------------------------
# Different subscription tiers expose different intent subsets to prevent
# basic-tier tenants from accidentally triggering enterprise-only workflows.
#
# basic:        core job creation/editing intents only
# professional: full set minus autonomous multi-step planning
# enterprise:   all intents (default behavior, same as IntentClassifierService)

_ENTERPRISE_ONLY_INTENTS: frozenset[IntentType] = frozenset([
    # REUSE_VACANCY triggers deep vacancy search + fast-track planning;
    # restrict to professional+ to avoid unintended autonomous workflows
    # on basic plans that lack the downstream agents.
    IntentType.REUSE_VACANCY,
])

_BASIC_ALLOWED_INTENTS: frozenset[IntentType] = frozenset([
    IntentType.DATA_INPUT,
    IntentType.QUESTION,
    IntentType.CORRECTION,
    IntentType.DEVIATION,
])

_PROFESSIONAL_ALLOWED_INTENTS: frozenset[IntentType] = frozenset(
    [i for i in IntentType if i not in _ENTERPRISE_ONLY_INTENTS]
)


class TierFilteredIntentClassifierService(IntentClassifierService):
    """IntentClassifierService with a subset of intents enabled based on plan tier.

    When the classified intent is not in the allowed set for the tenant's tier,
    falls back to DATA_INPUT with reduced confidence — safe default that routes
    to the standard chat pipeline instead of an enterprise workflow.
    """

    def __init__(self, allowed_intents: frozenset[IntentType]) -> None:
        super().__init__()
        self._allowed_intents = allowed_intents

    async def classify(
        self,
        user_input: str,
        stage_context: str | None = None,
        use_llm: bool = True,
    ) -> ClassificationResult:
        result = await super().classify(user_input, stage_context, use_llm)
        if result.intent_type not in self._allowed_intents:
            return ClassificationResult(
                intent_type=IntentType.DATA_INPUT,
                confidence=0.5,
                extracted_entities=result.extracted_entities,
                original_text=result.original_text,
                reasoning=(
                    f"Intent {result.intent_type.value} not available on current plan tier; "
                    "downgraded to DATA_INPUT."
                ),
            )
        return result


def get_classifier_for_tier(tier: str) -> IntentClassifierService:
    """Factory: return the appropriate IntentClassifierService for a subscription tier.

    Args:
        tier: "basic", "professional", or "enterprise" (case-insensitive).
              Unknown tiers default to "basic" (fail-safe).

    Returns:
        IntentClassifierService (or TierFilteredIntentClassifierService subclass)
        configured for the given tier.

    Examples:
        classifier = get_classifier_for_tier(company_plan)
        result = await classifier.classify(user_message)

    Tier capabilities:
        basic:        DATA_INPUT, QUESTION, CORRECTION, DEVIATION
        professional: above + REUSE_VACANCY minus autonomous planning intents
        enterprise:   all intents (full IntentClassifierService)
    """
    normalized = (tier or "basic").lower().strip()
    if normalized == "enterprise":
        return intent_classifier_service  # singleton — full set
    if normalized == "professional":
        return TierFilteredIntentClassifierService(_PROFESSIONAL_ALLOWED_INTENTS)
    # "basic" or unknown — most restrictive
    return TierFilteredIntentClassifierService(_BASIC_ALLOWED_INTENTS)
