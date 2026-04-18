"""
WSI Layer 2 Extractor — LLM-based semantic signal extraction (spec §F8.3).

Audit rev. 18 (M01): a Camada 2 produz `Layer2Signals` (sinais estruturais
e semânticos) que alimentam as penalidades semânticas (M04), bônus
(M05) e detecção semântica de inflação (M06) na Camada 1 determinística.

Padrão canônico do projeto:
- LLM via `llm_service.safe_invoke` (PII masking automático em `app/domains/ai/services/llm.py:855`).
- Prompt YAML carregado via `PromptLoader` (cache).
- JSON parsing via `safe_json_parse` (tolerante a markdown).
- Validação de schema via Pydantic `Layer2Signals`.
- Falhas explícitas via `Layer2ExtractionError` (NUNCA fallback silencioso —
  ver lição M12/rev. 15 em `question_generator.py::OceanExtractionError`).
"""
import logging
from typing import Any

from app.domains.ai.services.llm import llm_service
from app.shared.prompts.loader import PromptLoader

from .models import Layer2Signals, WSIQuestion, safe_json_parse

logger = logging.getLogger(__name__)


class Layer2ExtractionError(RuntimeError):
    """Raised when Camada 2 extraction fails (LLM call, JSON parse, schema
    validation). Caller MUST handle by setting `degraded_quality=True` and
    falling back to Camada 1 — never returning a fabricated payload."""


class WSILayer2Extractor:
    """Extrator de sinais semânticos via LLM (spec §F8.3).

    Stateless. Carrega o prompt uma vez (cache do `PromptLoader`).
    """

    PROMPT_PATH = "domains/wsi_layer2_extraction"
    PROMPT_KEY = "extraction_prompt"

    DEFAULT_MAX_TOKENS = 700
    DEFAULT_TEMPERATURE = 0.1  # extração estruturada — não criação

    def __init__(self, llm: Any | None = None) -> None:
        """`llm` opcional — quando None, usa o singleton `llm_service`
        (padrão canônico). Permite injeção em testes (mock).
        """
        self._llm = llm or llm_service

    def _render_prompt(self, question: WSIQuestion, response_text: str) -> str:
        data = PromptLoader.load(self.PROMPT_PATH)
        template = data.get(self.PROMPT_KEY)
        if not template:
            raise Layer2ExtractionError(
                f"Prompt YAML missing key '{self.PROMPT_KEY}' at {self.PROMPT_PATH}"
            )
        return template.format(
            framework=question.framework,
            competency=question.competency,
            question_text=question.question_text,
            response_text=response_text,
        )

    async def extract(
        self,
        question: WSIQuestion,
        response_text: str,
    ) -> Layer2Signals:
        """Invoca o LLM e retorna `Layer2Signals` validado.

        Raises:
            Layer2ExtractionError: LLM call failure, JSON parse failure,
                ou schema validation failure. Caller deve tratar e marcar
                `degraded_quality=True`.
        """
        if not response_text or not response_text.strip():
            raise Layer2ExtractionError("Empty response_text — cannot extract signals")

        prompt = self._render_prompt(question, response_text)

        # PII masking acontece automaticamente dentro de safe_invoke.
        try:
            response = await self._llm.safe_invoke(
                prompt,
                temperature=self.DEFAULT_TEMPERATURE,
                max_tokens=self.DEFAULT_MAX_TOKENS,
            )
        except Exception as exc:
            logger.error(
                "Layer2 extraction LLM call failed for q=%s competency=%s: %s",
                question.id, question.competency, exc,
            )
            raise Layer2ExtractionError(f"LLM call failed: {exc}") from exc

        # safe_invoke retorna objeto com .content (str). safe_json_parse
        # tolera markdown wrapper e devolve dict.
        content = getattr(response, "content", response)
        try:
            parsed = safe_json_parse(content, fallback=None)
        except Exception as exc:
            logger.error(
                "Layer2 extraction JSON parse failed for q=%s: %s",
                question.id, exc,
            )
            raise Layer2ExtractionError(f"JSON parse failed: {exc}") from exc

        if not isinstance(parsed, dict):
            raise Layer2ExtractionError(
                f"LLM returned non-dict payload (got {type(parsed).__name__})"
            )

        try:
            signals = Layer2Signals(**parsed)
        except Exception as exc:
            logger.error(
                "Layer2 schema validation failed for q=%s: %s | payload=%s",
                question.id, exc, parsed,
            )
            raise Layer2ExtractionError(f"Schema validation failed: {exc}") from exc

        logger.info(
            "Layer2 extracted for q=%s competency=%s confidence=%.2f traits=%d",
            question.id, question.competency,
            signals.confidence, signals.trait_signals_count,
        )
        return signals
