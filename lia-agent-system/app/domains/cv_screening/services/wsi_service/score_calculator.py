"""
WSI Score Calculator — adaptador para o scorer canônico.

CONTEXTO HISTÓRICO (audit M13, Phase 2 — 2026-04-18)
=====================================================
Esta classe foi originalmente uma implementação **paralela** ao scorer
canônico ``wsi_deterministic_scorer.calculate_final_wsi_score``. A auditoria
WSI rev. 5 (achado M13) identificou 5 bugs independentes na implementação
original:

1. Operator-precedence bug (sem parênteses) na detecção de competências
   técnicas — ``in weights AND python OR javascript OR ...`` colapsava o
   ``in weights`` apenas para ``python``.
2. Lista hardcoded ``python|javascript|sql|docker|aws`` — vagas Java/Rust/Go
   caíam todas no fallback não-determinístico ``responses[:int(len*0.7)]``.
3. Não usava ``SENIORITY_WEIGHTS`` (8 níveis canônicos da spec §9.2),
   ignorando a calibração de peso por senioridade.
4. Fallback bizarro ``behavioral_wsi = technical_wsi * tech_weight`` quando
   não há respostas comportamentais — sem amparo na metodologia.
5. Tabela de classificação com 5 níveis divergente do canônico de 6 níveis
   (``classify_wsi_score`` em ``wsi_deterministic_scorer``).

A correção elegante é descontinuar esta classe. Como ela tem testes unitários
estáveis (``tests/e2e/test_wsi_call_flow_e2e.py::TestWSIScoreCalculator*``) e
2 callers em produção (``handlers_screening.py``, ``wsi_voice_orchestrator.py``),
optou-se por mantê-la como **fachada deprecada** que delega à fonte canônica.

Para código novo, prefira chamar diretamente
``wsi_deterministic_scorer.calculate_final_wsi_score`` com tuplas
``(name, score, weight)`` já segregadas por tipo (technical/behavioral),
que é o contrato real da metodologia.
"""
from __future__ import annotations

import logging

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    calculate_final_wsi_score,
    classify_wsi_score,
)

from .models import Competency, ResponseAnalysis, WSIResult

logger = logging.getLogger(__name__)


class WSIScoreCalculator:
    """Fachada deprecada — delega ao scorer canônico (audit M13).

    Para código novo, use diretamente
    ``wsi_deterministic_scorer.calculate_final_wsi_score`` com tuplas
    ``(name, score, weight)`` já segregadas por tipo.
    """

    def calculate(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        responses: list[ResponseAnalysis],
        weights: dict[str, float],
        tech_weight: float = 0.70,
        behav_weight: float = 0.30,
        competencies: list[Competency] | None = None,
        seniority: str | None = None,
    ) -> WSIResult:
        """Calcula WSI final delegando ao scorer canônico.

        Mudanças vs implementação histórica (audit M13):
        - O split tech/behav agora usa ``competencies`` (typed) quando fornecido.
          Sem esse hint, fallback DETERMINÍSTICO: ordena ``responses`` por
          ``weights[name]`` desc e classifica os primeiros ``len * tech_weight``
          como técnicos. Não há mais ``in keywords or javascript or ...``.
        - ``seniority`` (quando passado) ativa ``SENIORITY_WEIGHTS`` da spec
          §9.2; ``tech_weight``/``behav_weight`` viram fallback secundário.
        - Classificação usa ``classify_wsi_score`` (6 níveis canônicos),
          não a tabela local de 5 níveis.
        - Removido o fallback ``behavioral_wsi = technical_wsi * tech_weight``;
          ausência de respostas comportamentais agora replica a média técnica,
          que é o que ``calculate_final_wsi_score`` faz por construção.
        """
        type_by_name: dict[str, str] = {}
        if competencies:
            for c in competencies:
                type_by_name[c.name] = c.type

        technical_scores: list[tuple[str, float, float]] = []
        behavioral_scores: list[tuple[str, float, float]] = []

        unknown: list[ResponseAnalysis] = []
        for r in responses:
            weight = weights.get(r.competency, 0.10)
            # Audit task #498 — precedência de fonte da categoria:
            # 1) `r.category` populado pelo response_analyzer (framework da
            #    pergunta) — disponível em 100% dos fluxos via voz/chat;
            # 2) `competencies[name].type` quando o caller passou hint tipado;
            # 3) heurístico por peso (fallback histórico, último recurso).
            comp_type = r.category or type_by_name.get(r.competency)
            if comp_type == "technical":
                technical_scores.append((r.competency, r.final_score, weight))
            elif comp_type in ("behavioral", "cultural"):
                behavioral_scores.append((r.competency, r.final_score, weight))
            else:
                unknown.append(r)

        if unknown:
            unknown_sorted = sorted(
                unknown,
                key=lambda r: weights.get(r.competency, 0.10),
                reverse=True,
            )
            cutoff = max(1, int(round(len(unknown_sorted) * tech_weight)))
            for idx, r in enumerate(unknown_sorted):
                w = weights.get(r.competency, 0.10)
                if idx < cutoff:
                    technical_scores.append((r.competency, r.final_score, w))
                else:
                    behavioral_scores.append((r.competency, r.final_score, w))

        canonical = calculate_final_wsi_score(
            technical_scores=technical_scores,
            behavioral_scores=behavioral_scores,
            seniority=seniority,
            technical_weight=tech_weight if seniority is None else None,
            behavioral_weight=behav_weight if seniority is None else None,
        )

        breakdown = canonical["breakdown"]
        technical_wsi = round(breakdown["technical_average"], 2)
        behavioral_wsi = round(breakdown["behavioral_average"], 2)
        if behavioral_wsi == 0.0 and technical_wsi > 0.0:
            behavioral_wsi = technical_wsi
        overall_wsi = canonical["final_score"]
        classification = canonical.get("classification") or classify_wsi_score(overall_wsi)

        return WSIResult(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            technical_wsi=technical_wsi,
            behavioral_wsi=behavioral_wsi,
            overall_wsi=overall_wsi,
            classification=classification,
            percentile=None,
            response_analyses=responses,
        )

    def calculate_percentiles(
        self,
        results: list[WSIResult],
    ) -> list[WSIResult]:
        """Atribui percentis comparando candidatos entre si.

        Exemplo: candidato com WSI 4.2 que está no top 10% recebe percentile=90.
        Mantida pura (sem dependência do scorer); apenas ordenação.
        """
        if not results:
            return results

        sorted_results = sorted(results, key=lambda r: r.overall_wsi, reverse=True)
        total = len(sorted_results)

        for idx, result in enumerate(sorted_results):
            result.percentile = int(((total - idx) / total) * 100)

        return sorted_results
