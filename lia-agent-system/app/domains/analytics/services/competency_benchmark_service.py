"""Competency Benchmark Service — Fase 2 (espelho do MarketBenchmarkService).

Sugere competências técnicas + comportamentais por (título + senioridade +
departamento + modo de triagem), dimensionado pelo modo via SCREENING_MODE_CONFIG.

Consumido pela Fase 3 (intake_gate confirmação assistida). Serviço standalone —
não é wired no grafo ainda; o intake_gate o chamará para sugerir competências
que o recrutador confirma/edita (recognition > recall).

Disciplina canônica:
  - Multi-tenancy: company_id participa da cache key (nunca enviado ao LLM).
  - LGPD: nenhum atributo protegido na sugestão (idade/gênero/raça/etc.).
  - Fairness: cada competência sugerida passa por FairnessGuard.check (WSI P7);
    sugestões bloqueadas são filtradas (fail-closed na sugestão individual).
  - Fail-open no serviço: LLM down/garbage → fallback determinístico por
    família de cargo (NUNCA silencioso — is_estimate=True + confidence=low +
    log explícito; segue REGRA 4 anti-silent-fallback do CLAUDE.md).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.domains.ai.services.llm import llm_service
from app.domains.job_creation.helpers.screening_mode_config import (
    SCREENING_MODE_CONFIG,
)
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)

VALID_BIG_FIVE_TRAITS = {
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "stability",
}
_DEFAULT_TRAIT = "conscientiousness"

# Variantes comuns que o LLM pode retornar → normalização canônica.
_TRAIT_ALIASES = {
    "emotional_stability": "stability",
    "estabilidade": "stability",
    "estabilidade_emocional": "stability",
    "neuroticism": "stability",
    "neuroticismo": "stability",
    "abertura": "openness",
    "openness_to_experience": "openness",
    "conscienciosidade": "conscientiousness",
    "conscientiousness_": "conscientiousness",
    "extroversao": "extraversion",
    "extroversão": "extraversion",
    "extroversion": "extraversion",
    "amabilidade": "agreeableness",
    "agradabilidade": "agreeableness",
}

_TECH_ROLE_KEYWORDS = (
    "desenvolvedor", "developer", "engenheiro", "engineer", "data",
    "machine learning", "devops", "cloud", "arquiteto", "programador",
    "software", "backend", "frontend", "fullstack", "sre", "qa",
)


@dataclass
class CacheEntry:
    data: dict[str, Any]
    created_at: datetime
    ttl_seconds: int = 86400

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)


class TTLCache:
    def __init__(self, default_ttl: int = 86400):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._cache[key]
            return None
        return entry.data

    def set(self, key: str, data: dict[str, Any], ttl: int | None = None) -> None:
        self._cache[key] = CacheEntry(
            data=data,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl or self.default_ttl,
        )

    def clear(self) -> None:
        self._cache.clear()

    def cleanup_expired(self) -> int:
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired:
            del self._cache[k]
        return len(expired)


class CompetencyBenchmarkService:
    """Sugere competências técnicas + comportamentais (espelho do salary benchmark).

    Features (paralelo ao MarketBenchmarkService):
      - Cache TTL in-memory (24h) com company_id na key (isolamento multi-tenant)
      - Parse LLM com grounding WSI + few-shot por família de cargo
      - FairnessGuard em cada sugestão (filtra blocked)
      - Fallback determinístico quando LLM falha
      - Dimensionamento pelo modo (SCREENING_MODE_CONFIG)
    """

    DISCLAIMER = "Sugestão assistida por IA + benchmark. Revise e ajuste conforme a vaga."
    CACHE_TTL_HOURS = 24

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = TTLCache(default_ttl=self.CACHE_TTL_HOURS * 3600)

    # ── cache key (company_id incluso) ──────────────────────────────────────
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{str(v).lower()}")
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    # ── dimensionamento pelo modo ───────────────────────────────────────────
    def _target_counts(
        self, screening_mode: str, seniority: str | None = None
    ) -> tuple[int, int]:
        # Per-senioridade (YAML canonical) -- audit 2026-06-05 #3. Antes usava
        # SCREENING_MODE_CONFIG (por modo: full=8+4), divergindo do validador
        # (por senioridade: full/senior=7+5) -> causava a 13a pergunta.
        from app.domains.job_creation.helpers.wsi_distribution import (
            block_distribution,
        )
        dist = block_distribution(screening_mode, seniority or "pleno")
        return dist["technical"], dist["behavioral"]

    # ── prompt WSI-grounded ─────────────────────────────────────────────────
    def _build_prompt(
        self,
        title: str,
        seniority: str | None,
        department: str | None,
        n_tech: int,
        n_behav: int,
    ) -> str:
        seniority_txt = seniority or "(não informada)"
        department_txt = department or "(não informado)"
        return f"""Você é um especialista em recrutamento usando a metodologia WSI (Work Sample Inference).
Sugira as competências mais relevantes para a seguinte vaga, dimensionadas para uma triagem objetiva.

CARGO: {title}
SENIORIDADE: {seniority_txt}
DEPARTAMENTO: {department_txt}

Sugira EXATAMENTE {n_tech} competências TÉCNICAS (hard skills, ferramentas, conhecimentos)
e {n_behav} competências COMPORTAMENTAIS (soft skills), priorizando as mais discriminantes
para o cargo e a senioridade.

REGRAS DE FAIRNESS (LGPD + WSI P7 — OBRIGATÓRIO):
- NÃO inclua nada relacionado a idade, gênero, raça, etnia, religião, estado civil, aparência ou saúde.
- NÃO use proxies de viés ("jovem e dinâmico", "fit cultural", "boa aparência", "ele deve").
- Foque APENAS em capacidades observáveis e relevantes para o trabalho.

Cada competência comportamental DEVE ser classificada por um trait Big Five:
openness, conscientiousness, extraversion, agreeableness, stability.

Responda APENAS com JSON válido (sem markdown, sem explicações):
{{
  "technical": [
    {{"skill": "nome da competência técnica", "contexto": "como é usada no cargo (1 frase)"}}
  ],
  "behavioral": [
    {{"competencia": "nome da soft skill", "contexto": "como se manifesta no cargo (1 frase)", "trait_big_five": "conscientiousness"}}
  ]
}}"""

    # ── parse robusto ───────────────────────────────────────────────────────
    @staticmethod
    def _extract_json(response: str) -> dict[str, Any] | None:
        if not response:
            return None
        # strip markdown fences se houver
        text = response.strip()
        if "```" in text:
            text = re.sub(r"```(?:json)?", "", text)
        # primeiro { até último } (cobre nested arrays/objects)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except (json.JSONDecodeError, ValueError):
            return None

    @classmethod
    def _normalize_trait(cls, raw: Any) -> str:
        if not isinstance(raw, str):
            return _DEFAULT_TRAIT
        key = raw.strip().lower()
        if key in VALID_BIG_FIVE_TRAITS:
            return key
        return _TRAIT_ALIASES.get(key, _DEFAULT_TRAIT)

    def _parse(
        self, response: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
        parsed = self._extract_json(response)
        if not isinstance(parsed, dict):
            return None
        raw_tech = parsed.get("technical") or []
        raw_behav = parsed.get("behavioral") or []
        if not isinstance(raw_tech, list) or not isinstance(raw_behav, list):
            return None

        technical: list[dict[str, Any]] = []
        for item in raw_tech:
            if not isinstance(item, dict):
                continue
            skill = (item.get("skill") or "").strip()
            if not skill:
                continue
            technical.append({"skill": skill, "contexto": (item.get("contexto") or "").strip()})

        behavioral: list[dict[str, Any]] = []
        for item in raw_behav:
            if not isinstance(item, dict):
                continue
            comp = (item.get("competencia") or item.get("competency") or "").strip()
            if not comp:
                continue
            behavioral.append({
                "competencia": comp,
                "contexto": (item.get("contexto") or "").strip(),
                "trait_big_five": self._normalize_trait(item.get("trait_big_five")),
            })

        if not technical and not behavioral:
            return None
        return technical, behavioral

    # ── fairness filter (P7) ────────────────────────────────────────────────
    def _apply_fairness_filter(
        self,
        technical: list[dict[str, Any]],
        behavioral: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        """Filtra sugestões cujo texto é bloqueado pelo FairnessGuard.

        Fail-open para regressão do guard (não derruba sugestão por bug do guard),
        mas fail-closed por-item quando o guard explicitamente bloqueia.
        """
        dropped: list[str] = []
        try:
            guard = FairnessGuard(strict=False)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "[CompetencyBenchmark] FairnessGuard init failed (fail-open): %s", exc,
            )
            return technical, behavioral, dropped

        def _ok(text: str) -> bool:
            try:
                return not guard.check(text).is_blocked
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "[CompetencyBenchmark] FairnessGuard check failed (fail-open): %s", exc,
                )
                return True

        clean_tech = []
        for t in technical:
            if _ok(f"{t.get('skill', '')} {t.get('contexto', '')}"):
                clean_tech.append(t)
            else:
                dropped.append(t.get("skill", ""))

        clean_behav = []
        for b in behavioral:
            if _ok(f"{b.get('competencia', '')} {b.get('contexto', '')}"):
                clean_behav.append(b)
            else:
                dropped.append(b.get("competencia", ""))

        if dropped:
            self.logger.info(
                "[CompetencyBenchmark] FairnessGuard filtered %d suggestion(s): %s",
                len(dropped), dropped,
            )
        return clean_tech, clean_behav, dropped

    # ── fallback determinístico ─────────────────────────────────────────────
    def _get_default_competencies(
        self, title: str, seniority: str | None, n_tech: int, n_behav: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        is_tech = any(kw in (title or "").lower() for kw in _TECH_ROLE_KEYWORDS)

        if is_tech:
            tech_pool = [
                ("Lógica de programação", "resolver problemas com algoritmos no dia a dia"),
                ("Versionamento (Git)", "colaborar em código com controle de versão"),
                ("Testes automatizados", "garantir qualidade do que entrega"),
                ("Banco de dados (SQL)", "modelar e consultar dados do produto"),
                ("APIs e integrações", "conectar serviços e sistemas"),
                ("Boas práticas de código", "escrever código legível e sustentável"),
                ("Cloud / infraestrutura", "operar aplicações em ambiente de nuvem"),
                ("Depuração e troubleshooting", "investigar e resolver incidentes"),
            ]
        else:
            tech_pool = [
                ("Domínio técnico da função", "executar as atividades centrais do cargo"),
                ("Ferramentas da área", "operar os sistemas usados na rotina"),
                ("Análise de dados", "tomar decisões baseadas em indicadores"),
                ("Organização e processos", "seguir e melhorar fluxos de trabalho"),
                ("Documentação", "registrar e comunicar informações com clareza"),
                ("Gestão de prioridades", "equilibrar demandas concorrentes"),
                ("Conhecimento do negócio", "entender o contexto e os objetivos da área"),
                ("Atenção a detalhes", "garantir precisão nas entregas"),
            ]

        behav_pool = [
            ("Comunicação", "explicar ideias com clareza a diferentes públicos", "extraversion"),
            ("Colaboração", "trabalhar bem em equipe rumo a um objetivo comum", "agreeableness"),
            ("Resolução de problemas", "abordar desafios de forma estruturada", "openness"),
            ("Adaptabilidade", "lidar bem com mudanças e ambiguidade", "stability"),
            ("Responsabilidade", "assumir compromissos e cumprir prazos", "conscientiousness"),
            ("Proatividade", "antecipar necessidades e agir sem ser solicitado", "conscientiousness"),
        ]

        technical = [
            {"skill": s, "contexto": c} for s, c in tech_pool[:n_tech]
        ]
        behavioral = [
            {"competencia": comp, "contexto": ctx, "trait_big_five": trait}
            for comp, ctx, trait in behav_pool[:n_behav]
        ]
        return technical, behavioral

    # ── API pública ─────────────────────────────────────────────────────────
    async def suggest_competencies(
        self,
        title: str,
        seniority: str | None = None,
        department: str | None = None,
        screening_mode: str = "compact",
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """Sugere competências técnicas + comportamentais dimensionadas pelo modo.

        Args:
            title: título do cargo (ex.: "Engenheiro de Software")
            seniority: senioridade (júnior/pleno/sênior/...)
            department: departamento (opcional, melhora a sugestão)
            screening_mode: "compact" | "full" — dimensiona nº de competências
            company_id: tenant — participa da cache key (isolamento multi-tenant)

        Returns:
            {
              "technical":  [{"skill", "contexto"}],
              "behavioral": [{"competencia", "contexto", "trait_big_five"}],
              "sources": [...], "confidence": "high|medium|low",
              "disclaimer": "...", "screening_mode": "...",
              "is_estimate": bool, "filtered_count": int,
            }
        """
        n_tech, n_behav = self._target_counts(screening_mode, seniority)

        cache_key = self._generate_cache_key(
            "competency",
            title=title,
            seniority=seniority,
            department=department,
            screening_mode=screening_mode,
            company_id=company_id,
        )
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info("[CompetencyBenchmark] cache hit: %s (%s)", title, screening_mode)
            return cached

        technical: list[dict[str, Any]] = []
        behavioral: list[dict[str, Any]] = []
        is_estimate = False
        confidence = "medium"

        try:
            prompt = self._build_prompt(title, seniority, department, n_tech, n_behav)
            # Provider canonical = claude (async ainvoke). gemini usa o SDK
            # nativo SINCRONO que quebra o credit-gate seam quando chamado de
            # dentro de event loop (_enforce_credit_gate_sync called from
            # running event loop) -> caia sempre no fallback generico em
            # contexto async (orquestrador/intake_gate). Fix 2026-05-31.
            import os as _os
            _provider = _os.environ.get("LIA_COMPETENCY_BENCHMARK_PROVIDER", "claude")
            response = await llm_service.generate(prompt, provider=_provider)
            parsed = self._parse(response)
            if parsed is None:
                self.logger.warning(
                    "[CompetencyBenchmark] LLM parse failed for %s — fallback", title,
                )
                technical, behavioral = self._get_default_competencies(
                    title, seniority, n_tech, n_behav,
                )
                is_estimate = True
                confidence = "low"
            else:
                technical, behavioral = parsed
        except Exception as exc:  # noqa: BLE001 — fail-open com flag explícita (não silencioso)
            self.logger.warning(
                "[CompetencyBenchmark] LLM call failed for %s (fallback): %s", title, exc,
            )
            technical, behavioral = self._get_default_competencies(
                title, seniority, n_tech, n_behav,
            )
            is_estimate = True
            confidence = "low"

        # Fairness P7 — filtra sugestões bloqueadas
        technical, behavioral, dropped = self._apply_fairness_filter(technical, behavioral)

        # Se o filtro esvaziou uma das listas, recompõe pelo fallback (defesa em profundidade)
        if not technical:
            fb_tech, _ = self._get_default_competencies(title, seniority, n_tech, 0)
            technical = fb_tech
            is_estimate = True
        if not behavioral:
            _, fb_behav = self._get_default_competencies(title, seniority, 0, n_behav)
            behavioral = fb_behav
            is_estimate = True

        # Dimensiona pelo modo (corta excesso do LLM)
        technical = technical[:n_tech]
        behavioral = behavioral[:n_behav]

        result = {
            "technical": technical,
            "behavioral": behavioral,
            "sources": ["benchmark interno", "WSI methodology"],
            "confidence": confidence,
            "disclaimer": self.DISCLAIMER,
            "screening_mode": screening_mode,
            "search_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "is_estimate": is_estimate,
            "filtered_count": len(dropped),
        }
        self.cache.set(cache_key, result)
        return result

    def clear_cache(self) -> None:
        self.cache.clear()
        self.logger.info("Competency benchmark cache cleared")

    def cleanup_expired_cache(self) -> int:
        removed = self.cache.cleanup_expired()
        self.logger.info("Removed %d expired competency cache entries", removed)
        return removed


competency_benchmark_service = CompetencyBenchmarkService()


def get_competency_benchmark_service() -> "CompetencyBenchmarkService":
    return competency_benchmark_service
