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

Audit rev. 23 — gaps fechados nesta versão:
- G23-06: pós-processamento determinístico de `word_count_band` (Python
  conta palavras e sobrescreve o valor reportado pelo LLM).
- G23-07: helpers `purge_layer2_cache_entry` e `purge_layer2_cache_all`
  para atender DSR (LGPD Art. 18) sem aguardar evicção LRU natural.
- G23-08: integração com LangSmith via `@traceable("layer2_extraction")`
  para nomeação explícita do span em traces aninhados.
- G23-09: logs estruturados via `extra={...}` para facilitar query no
  Cloud Logging (campos: question_id, competency, confidence, hits, etc).
"""
import hashlib
import logging
import re
import threading
from collections import OrderedDict
from typing import Any

from app.domains.ai.services.llm import llm_service
from app.shared.prompts.loader import PromptLoader

from .models import Layer2Signals, WSIQuestion, safe_json_parse

# G23-08: LangSmith trace nomeado. Try-import como nos demais módulos
# (ver `app/shared/providers/llm_claude.py:13`).
try:
    from langsmith import traceable as _traceable  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - langsmith é opcional em dev
    def _traceable(**_kwargs):  # type: ignore[misc]
        def _decorator(fn):
            return fn
        return _decorator

logger = logging.getLogger(__name__)

# Cache LRU in-process compartilhado entre instâncias do extractor
# (módulo-level dict — singleton de fato). Audit rev. 22 follow-up.
# Key: sha256(question_id + response_text). Value: Layer2Signals.
# Cap N=500 entradas (esquece menos usadas). TTL implícito via processo.
#
# Thread-safety (audit rev. 22, achado architect): operações compostas
# get/move_to_end/popitem/set NÃO são atômicas no OrderedDict. Em ambiente
# multi-thread (FastAPI workers async + threadpools, gunicorn --threads,
# background tasks), corridas podem corromper a ordem LRU ou causar
# KeyError. Lock módulo-level garante atomicidade das seções críticas.
#
# Limitação conhecida (não resolvida nesta task): a key não inclui escopo
# de tenant. Hoje `question_id` é UUID gerado por `question_generator`
# (collision-resistant), então o risco prático é baixo, mas registrar:
# se no futuro ids passarem a ser determinísticos (slug, hash de prompt),
# adicionar tenant_id à composição da key para evitar cross-tenant hit.
_LAYER2_CACHE: OrderedDict[str, Layer2Signals] = OrderedDict()
_LAYER2_CACHE_MAX = 500
_LAYER2_CACHE_STATS = {"hits": 0, "misses": 0, "purges": 0}
_LAYER2_CACHE_LOCK = threading.Lock()


def _layer2_cache_key(question_id: str, response_text: str) -> str:
    h = hashlib.sha256()
    h.update(str(question_id).encode("utf-8"))
    h.update(b"|")
    h.update(response_text.encode("utf-8"))
    return h.hexdigest()


def get_layer2_cache_stats() -> dict[str, int]:
    """Telemetria do cache (hits/misses/size/purges). Útil para
    observabilidade. Exposto via endpoint admin (G23-05)."""
    with _LAYER2_CACHE_LOCK:
        return {**_LAYER2_CACHE_STATS, "size": len(_LAYER2_CACHE), "max": _LAYER2_CACHE_MAX}


def purge_layer2_cache_entry(question_id: str, response_text: str) -> bool:
    """G23-07 — DSR (LGPD Art. 18): remove uma entrada específica do
    cache antes da evicção LRU natural. Retorna True se a entrada existia.

    Use case: candidato exerce direito ao esquecimento; chamar este helper
    para cada (question_id, response_text) associado ao candidato."""
    key = _layer2_cache_key(question_id, response_text)
    with _LAYER2_CACHE_LOCK:
        existed = key in _LAYER2_CACHE
        if existed:
            del _LAYER2_CACHE[key]
            _LAYER2_CACHE_STATS["purges"] += 1
            logger.info(
                "Layer2 cache PURGE entry",
                extra={"event": "layer2_cache_purge_entry", "question_id": str(question_id)},
            )
        return existed


def purge_layer2_cache_all() -> int:
    """G23-07 — DSR/manutenção: limpa o cache inteiro. Retorna número
    de entradas removidas. Útil para deploys, testes e DSR amplo."""
    with _LAYER2_CACHE_LOCK:
        n = len(_LAYER2_CACHE)
        _LAYER2_CACHE.clear()
        _LAYER2_CACHE_STATS["purges"] += n
        logger.info(
            "Layer2 cache PURGE all",
            extra={"event": "layer2_cache_purge_all", "removed": n},
        )
        return n


# G23-06 — Word_count_band determinístico. O LLM erra contagem em ~12%
# dos casos (golden L2-002). Função pura; usa mesmo critério do prompt
# YAML (`split por espaços → descartar pontuação → contar`).
_WORD_BAND_BUCKETS = (
    (30, "<30"),
    (50, "30-50"),
    (150, "50-150"),
)


def compute_word_count_band(response_text: str) -> str:
    """Conta palavras de forma determinística e devolve o bucket canônico.

    Regra (mesma do prompt YAML): split por espaços, descarta tokens
    compostos só de pontuação. Retorna um dos 4 valores do enum
    `Layer2Signals.word_count_band`."""
    if not response_text:
        return "<30"
    tokens = [t for t in re.split(r"\s+", response_text.strip()) if re.search(r"\w", t)]
    n = len(tokens)
    for limit, label in _WORD_BAND_BUCKETS:
        if n < limit:
            return label
    return ">150"


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

    @_traceable(name="layer2_extraction", run_type="chain")
    async def extract(
        self,
        question: WSIQuestion,
        response_text: str,
        *,
        tracking_context: dict[str, Any] | None = None,
    ) -> Layer2Signals:
        """Invoca o LLM e retorna `Layer2Signals` validado.

        Args:
            question: pergunta WSI sendo avaliada.
            response_text: resposta bruta do candidato.
            tracking_context: opcional. Quando provido, as chaves
                `company_id` (UUID str, obrigatória), `user_id`,
                `candidate_id`, `vacancy_id` e `operation` são usadas para
                gravar o consumo de tokens em `AiConsumption` (via
                `TokenTrackingService.record_usage`). Audit task #532
                (G23-04). Quando ausente, nenhuma escrita de tracking
                acontece (preserva comportamento anterior).

        Raises:
            Layer2ExtractionError: LLM call failure, JSON parse failure,
                ou schema validation failure. Caller deve tratar e marcar
                `degraded_quality=True`.
        """
        if not response_text or not response_text.strip():
            raise Layer2ExtractionError("Empty response_text — cannot extract signals")

        # Cache lookup — evita re-chamar LLM para mesmo (question, response).
        # Custo típico ~$0.005/call; cache salva quando há retry/idempotência.
        cache_key = _layer2_cache_key(question.id, response_text)
        with _LAYER2_CACHE_LOCK:
            cached = _LAYER2_CACHE.get(cache_key)
            if cached is not None:
                _LAYER2_CACHE.move_to_end(cache_key)  # LRU touch
                _LAYER2_CACHE_STATS["hits"] += 1
                hits, misses, size = (
                    _LAYER2_CACHE_STATS["hits"],
                    _LAYER2_CACHE_STATS["misses"],
                    len(_LAYER2_CACHE),
                )
                logger.debug(
                    "Layer2 cache HIT",
                    extra={
                        "event": "layer2_cache_hit",
                        "question_id": str(question.id),
                        "size": size, "hits": hits, "misses": misses,
                    },
                )
                return cached
            _LAYER2_CACHE_STATS["misses"] += 1

        prompt = self._render_prompt(question, response_text)

        # Audit task #532 (G23-04) — token tracking opcional via callback.
        # Construímos o callback aqui (closure sobre `tracking_context` +
        # `question.id`) e o passamos para `safe_invoke`. O callback é
        # síncrono e fire-and-forget: se houver `tracking_context`,
        # agenda uma task assíncrona que abre uma `AsyncSessionLocal`
        # própria (NÃO compartilha a sessão do orquestrador para evitar
        # commits cruzados) e grava em `AiConsumption`. Falhas do
        # tracking nunca afetam a extração — apenas log.
        on_usage_cb = _build_layer2_usage_callback(
            tracking_context, question_id=question.id
        ) if tracking_context else None

        # PII masking acontece automaticamente dentro de safe_invoke.
        try:
            response = await self._llm.safe_invoke(
                prompt,
                temperature=self.DEFAULT_TEMPERATURE,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                on_usage=on_usage_cb,
            )
        except Exception as exc:
            logger.error(
                "Layer2 extraction LLM call failed",
                extra={
                    "event": "layer2_llm_failed",
                    "question_id": str(question.id),
                    "competency": question.competency,
                    "error": str(exc),
                },
            )
            raise Layer2ExtractionError(f"LLM call failed: {exc}") from exc

        # safe_invoke retorna objeto com .content (str). safe_json_parse
        # tolera markdown wrapper e devolve dict.
        content = getattr(response, "content", response)
        try:
            parsed = safe_json_parse(content, fallback=None)
        except Exception as exc:
            logger.error(
                "Layer2 extraction JSON parse failed",
                extra={
                    "event": "layer2_parse_failed",
                    "question_id": str(question.id),
                    "error": str(exc),
                },
            )
            raise Layer2ExtractionError(f"JSON parse failed: {exc}") from exc

        if not isinstance(parsed, dict):
            raise Layer2ExtractionError(
                f"LLM returned non-dict payload (got {type(parsed).__name__})"
            )

        # G23-06 — pós-processamento determinístico de word_count_band.
        # O LLM mis-counta em respostas curtas (golden L2-002, ~12% dos
        # casos). Sobrescrevemos com a contagem Python ANTES da validação
        # do schema para garantir consistência com `response_word_count`
        # usado no scorer determinístico (Camada 1).
        deterministic_band = compute_word_count_band(response_text)
        llm_band = parsed.get("word_count_band")
        if llm_band != deterministic_band:
            logger.info(
                "Layer2 word_count_band overridden (deterministic)",
                extra={
                    "event": "layer2_word_band_override",
                    "question_id": str(question.id),
                    "llm_band": llm_band,
                    "python_band": deterministic_band,
                },
            )
            parsed["word_count_band"] = deterministic_band

        try:
            signals = Layer2Signals(**parsed)
        except Exception as exc:
            logger.error(
                "Layer2 schema validation failed",
                extra={
                    "event": "layer2_schema_failed",
                    "question_id": str(question.id),
                    "error": str(exc),
                    "payload": parsed,
                },
            )
            raise Layer2ExtractionError(f"Schema validation failed: {exc}") from exc

        logger.info(
            "Layer2 extracted",
            extra={
                "event": "layer2_extracted",
                "question_id": str(question.id),
                "competency": question.competency,
                "confidence": signals.confidence,
                "trait_signals_count": signals.trait_signals_count,
                "semantic_inflation": signals.semantic_inflation,
                "prompt_injection_detected": signals.prompt_injection_detected,
            },
        )

        # Cache write + LRU eviction (FIFO da menor entrada).
        with _LAYER2_CACHE_LOCK:
            _LAYER2_CACHE[cache_key] = signals
            _LAYER2_CACHE.move_to_end(cache_key)  # garante MRU mesmo em re-write
            while len(_LAYER2_CACHE) > _LAYER2_CACHE_MAX:
                _LAYER2_CACHE.popitem(last=False)

        return signals


# ---------------------------------------------------------------------------
# Audit task #532 (G23-04) — token tracking helper
# ---------------------------------------------------------------------------
#
# A Camada 2 é hoje a etapa mais cara em tokens da plataforma. O scorer
# determinístico (Camada 1) não consome LLM. Este helper produz um
# callback síncrono compatível com `safe_invoke(on_usage=...)` que
# agenda gravação fire-and-forget em `AiConsumption` numa sessão de DB
# própria (não compartilha a transação do orquestrador).


def _build_layer2_usage_callback(
    tracking_context: dict[str, Any],
    *,
    question_id: Any,
):
    """Cria um callback `on_usage(usage_dict)` para `safe_invoke`.

    Audit task #545 — delega para o helper genérico
    `app.shared.observability.usage_tracking_callback.build_usage_callback`.
    O helper aplica o mesmo padrão (no-op sem `company_id`,
    `AsyncSessionLocal` própria, falhas não-bloqueantes) usado em todos
    os outros pontos da plataforma instrumentados com `on_usage`.
    """
    from app.shared.observability.usage_tracking_callback import (
        build_usage_callback,
    )

    cb = build_usage_callback(
        tracking_context,
        agent_type="wsi_layer2",
        default_operation="wsi_layer2_extract",
        extra={"question_id": str(question_id)},
    )
    # Mantém contrato anterior: sem company_id devolvia no-op (não None),
    # para evitar branches no caller.
    return cb if cb is not None else (lambda _usage: None)
