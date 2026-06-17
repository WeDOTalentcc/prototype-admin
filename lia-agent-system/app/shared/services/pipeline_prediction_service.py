"""
Pipeline Prediction Service — Sprint 3A.

Prevê probabilidade de fechamento de vagas ativas em X dias usando
dados já existentes — sem ML externo, sem migration.

Fórmula determinística com 5 fatores (total: 100 pts):
  - Velocidade          (30 pts): média de dias por etapa
  - Funil avançado      (25 pts): candidatos em etapas finais
  - Contribuição health (20 pts): health_score existente / 100 * 20
  - EWS risk            (15 pts): penalidade por candidatos em risco
  - Volume              (10 pts): total de candidatos ativos

Sem migration — usa dados existentes:
  vacancy_candidates (stage, stage_entered_at, status, lia_score)
  communication_logs (sent_at — último contato)
  job_vacancies (title, status, deadline, created_by, recruiter_email, company_id)
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "pipeline_prediction_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import asyncio
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.shared.services.early_warning_service import compute_ews_score, risk_level_for_score

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes de etapa — mapeamento para score de proximidade ao fechamento
# ---------------------------------------------------------------------------
_STAGE_CLOSURE_SCORE: dict[str, int] = {
    "offer": 25,
    "proposta": 25,
    "interview_final": 20,
    "interview_manager": 18,
    "interview_technical": 12,
    "entrevista_tecnica": 12,
    "interview_hr": 10,
    "entrevista_rh": 10,
    "screening": 6,
    "triagem": 6,
    "applied": 0,
    "novo": 0,
    "initial": 0,
}

_ADVANCED_STAGES = {
    "offer", "proposta",
    "interview_final", "interview_manager",
    "interview_technical", "entrevista_tecnica",
    "interview_hr", "entrevista_rh",
}

# Benchmarks de velocidade: dias esperados por etapa
_VELOCITY_BENCHMARK_DAYS = 5.0


# ---------------------------------------------------------------------------
# Funções puras (testáveis sem DB)
# ---------------------------------------------------------------------------

def compute_closure_probability(
    total_active: int,
    best_stage: str,
    avg_days_in_stage: float,
    advanced_count: int,
    critical_ews_count: int,
    high_ews_count: int,
    health_score: int,
) -> int:
    """
    Calcula probabilidade de fechamento (0–100) baseado nos 5 fatores.

    Args:
        total_active: Total de candidatos ativos no pipeline.
        best_stage: Etapa do candidato mais avançado.
        avg_days_in_stage: Média de dias na etapa atual entre todos os ativos.
        advanced_count: Candidatos em etapas avançadas (entrevista+).
        critical_ews_count: Candidatos com EWS score >= 1.0 (crítico).
        high_ews_count: Candidatos com EWS score >= 0.6 (alto).
        health_score: Health score da vaga 0–100 (do journey intelligence).

    Returns:
        Probabilidade inteira 0–100.
    """
    if total_active == 0:
        return 0

    score = 0

    # 1. Velocidade (0–30 pts): menor avg = melhor
    if avg_days_in_stage <= 0:
        score += 15  # sem dados = neutro
    elif avg_days_in_stage < 3:
        score += 30
    elif avg_days_in_stage < _VELOCITY_BENCHMARK_DAYS:
        score += 22
    elif avg_days_in_stage < 8:
        score += 14
    elif avg_days_in_stage < 14:
        score += 6
    # else: 0

    # 2. Funil avançado (0–25 pts): etapa do candidato mais avançado
    norm_best = (best_stage or "").lower()
    stage_score = _STAGE_CLOSURE_SCORE.get(norm_best, 0)
    # Normaliza para 0–22 pts + bônus de 3 pts se advanced_count >= 2
    advanced_pts = min(22, stage_score)
    if advanced_count >= 2:
        advanced_pts = min(25, advanced_pts + 3)
    score += advanced_pts

    # 3. Health score (0–20 pts)
    score += int(health_score / 100 * 20)

    # 4. EWS risk (0–15 pts base, penalidade por risco)
    ews_pts = 15
    ews_pts -= min(15, critical_ews_count * 5)
    ews_pts -= min(ews_pts, high_ews_count * 2)
    score += max(0, ews_pts)

    # 5. Volume (0–10 pts)
    if total_active >= 8:
        score += 10
    elif total_active >= 5:
        score += 8
    elif total_active >= 3:
        score += 5
    elif total_active >= 1:
        score += 2

    return min(100, max(0, score))


def estimate_days_to_close(
    best_stage: str,
    avg_days_in_stage: float,
    total_active: int,
) -> int | None:
    """
    Estima dias restantes até fechamento com base na etapa mais avançada.

    Returns:
        Estimativa em dias, ou None se pipeline estiver vazio.
    """
    if total_active == 0:
        return None

    norm = (best_stage or "").lower()

    if norm in ("offer", "proposta"):
        return max(2, int(avg_days_in_stage or 3))

    # Contar etapas restantes até offer
    _ORDERED = [
        "applied", "screening", "interview_hr",
        "interview_technical", "interview_manager",
        "interview_final", "offer",
    ]
    # Mapa de aliases para canonical
    _ALIAS = {
        "novo": "applied", "initial": "applied",
        "triagem": "screening",
        "entrevista_rh": "interview_hr",
        "entrevista_tecnica": "interview_technical",
        "proposta": "offer",
    }
    canonical = _ALIAS.get(norm, norm)
    try:
        current_idx = _ORDERED.index(canonical)
        stages_remaining = len(_ORDERED) - 1 - current_idx  # etapas até offer
    except ValueError:
        stages_remaining = 3  # estimativa conservadora para etapa desconhecida

    days_per_stage = max(2.0, avg_days_in_stage or _VELOCITY_BENCHMARK_DAYS)
    return min(90, max(1, int(stages_remaining * days_per_stage) + 2))


def get_confidence_level(
    total_active: int,
    health_score: int,
) -> str:
    """
    Determina nível de confiança da previsão.
    """
    if total_active >= 5 and health_score >= 60:
        return "high"
    if total_active <= 1 or health_score < 30:
        return "low"
    return "medium"


def build_factors(
    best_stage: str,
    avg_days_in_stage: float,
    advanced_count: int,
    critical_ews_count: int,
    high_ews_count: int,
    total_active: int,
    health_score: int,
) -> tuple[list[str], list[str]]:
    """
    Retorna (positive_factors, risk_factors) com base nos dados da vaga.
    """
    positives: list[str] = []
    risks: list[str] = []

    norm_best = (best_stage or "").lower()

    # Positivos
    if norm_best in ("offer", "proposta"):
        positives.append("candidate_in_offer_stage")
    elif norm_best in ("interview_final", "interview_manager"):
        positives.append("candidate_in_final_interview")

    if avg_days_in_stage > 0 and avg_days_in_stage < 3:
        positives.append("velocity_above_avg")

    if advanced_count >= 2:
        positives.append("multiple_advanced_candidates")
    elif advanced_count == 1:
        positives.append("one_advanced_candidate")

    if total_active >= 8:
        positives.append("strong_pipeline_volume")

    if health_score >= 70:
        positives.append("healthy_pipeline")

    # Riscos
    if critical_ews_count > 0:
        risks.append(f"ews_critical_count_{critical_ews_count}")

    if high_ews_count > 0:
        risks.append(f"ews_high_count_{high_ews_count}")

    if avg_days_in_stage >= 14:
        risks.append("very_slow_velocity")
    elif avg_days_in_stage >= 8:
        risks.append("slow_velocity")

    if total_active == 0:
        risks.append("empty_pipeline")
    elif total_active < 3:
        risks.append("low_pipeline_volume")

    if health_score < 30:
        risks.append("critical_health_score")
    elif health_score < 45:
        risks.append("warning_health_score")

    if advanced_count == 0 and total_active > 0:
        risks.append("no_advanced_candidates")

    return positives, risks


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class PipelinePredictionService:
    """
    Calcula probabilidade de fechamento de vagas usando dados operacionais
    já presentes no banco — sem ML externo, sem migration.
    """

    async def get_vacancy_prediction(
        self,
        vacancy_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Previsão individual para uma vaga.

        Faz 2 queries:
          1. Candidatos ativos (stage, stage_entered_at, lia_score, last_contact)
          2. Metadados da vaga (title, deadline)

        Returns:
            Dict com closure_probability, estimated_days_to_close, confidence_level,
            positive_factors, risk_factors, stage_of_best_candidate.
        """
        _managed = db is None
        if _managed:
            db = AsyncSessionLocal()

        try:
            # Query 1: candidatos ativos com dados de contato
            cand_result = await db.execute(
                text("""
                    SELECT
                        vc.stage,
                        vc.stage_entered_at,
                        vc.lia_score,
                        EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400
                            AS days_in_stage,
                        COALESCE(
                            EXTRACT(EPOCH FROM (NOW() - cl.last_sent)) / 86400,
                            EXTRACT(EPOCH FROM (NOW() - vc.stage_entered_at)) / 86400
                        ) AS days_since_contact
                    FROM vacancy_candidates vc
                    LEFT JOIN LATERAL (
                        SELECT MAX(sent_at) AS last_sent
                        FROM communication_logs
                        WHERE candidate_id = vc.candidate_id
                    ) cl ON true
                    WHERE vc.vacancy_id = :vid
                      AND vc.status IN ('active', 'pipeline')
                """),
                {"vid": vacancy_id},
            )
            candidates = cand_result.mappings().fetchall()

            # Query 2: metadados da vaga
            vac_result = await db.execute(
                text("""
                    SELECT title, deadline, created_at
                    FROM job_vacancies
                    WHERE id = :vid AND company_id = :cid
                """),
                {"vid": vacancy_id, "cid": company_id},
            )
            vac_row = vac_result.mappings().first()

        except Exception as e:
            logger.warning(f"[PipelinePrediction] DB error for vacancy {vacancy_id}: {e}")
            return self._empty_prediction(vacancy_id, company_id)
        finally:
            if _managed:
                await db.close()

        vacancy_title = vac_row["title"] if vac_row else "Vaga"
        deadline = vac_row["deadline"] if vac_row else None

        # --- Computar métricas a partir dos candidatos ---
        total_active = len(candidates)
        if total_active == 0:
            prob = compute_closure_probability(0, "", 0, 0, 0, 0, 0)
            return {
                "vacancy_id": vacancy_id,
                "company_id": company_id,
                "vacancy_title": vacancy_title,
                "closure_probability": prob,
                "estimated_days_to_close": None,
                "confidence_level": "low",
                "stage_of_best_candidate": None,
                "positive_factors": [],
                "risk_factors": ["empty_pipeline"],
                "deadline": deadline.isoformat() if deadline else None,
                "total_active": 0,
                "advanced_count": 0,
            }

        # Identificar melhor candidato (mais avançado pelo score de closure)
        best_stage = ""
        best_score = -1
        total_days = 0.0
        critical_ews = 0
        high_ews = 0
        advanced_count = 0

        for row in candidates:
            stage = (row["stage"] or "").lower()
            days_in_stage = float(row["days_in_stage"] or 0)
            days_since_contact = float(row["days_since_contact"] or days_in_stage)
            lia_score = float(row["lia_score"]) if row["lia_score"] is not None else None

            total_days += days_in_stage

            closure_s = _STAGE_CLOSURE_SCORE.get(stage, 0)
            if closure_s > best_score:
                best_score = closure_s
                best_stage = stage

            if stage in _ADVANCED_STAGES:
                advanced_count += 1

            ews = compute_ews_score(days_since_contact, stage, lia_score)
            level = risk_level_for_score(ews)
            if level == "critical":
                critical_ews += 1
            elif level == "high":
                high_ews += 1

        avg_days = total_days / total_active if total_active > 0 else 0.0

        # Health score: usamos cálculo simplificado inline para evitar chamada extra ao DB
        # (o health score completo requer dados de drop-off que não consultamos aqui)
        from app.shared.services.journey_intelligence_service import compute_health_score
        inline_health = compute_health_score(
            total_active=total_active,
            conversion_rate_overall=advanced_count / total_active if total_active > 0 else 0.0,
            avg_drop_off_rate=0.3,  # estimativa conservadora sem dados de drop-off
            candidates_in_advanced_stages=advanced_count,
            has_critical_ews=critical_ews > 0,
            days_since_last_movement=avg_days,
        )

        prob = compute_closure_probability(
            total_active=total_active,
            best_stage=best_stage,
            avg_days_in_stage=avg_days,
            advanced_count=advanced_count,
            critical_ews_count=critical_ews,
            high_ews_count=high_ews,
            health_score=inline_health,
        )

        estimated_days = estimate_days_to_close(best_stage, avg_days, total_active)
        confidence = get_confidence_level(total_active, inline_health)
        positives, risks = build_factors(
            best_stage, avg_days, advanced_count,
            critical_ews, high_ews, total_active, inline_health,
        )

        return {
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "vacancy_title": vacancy_title,
            "closure_probability": prob,
            "estimated_days_to_close": estimated_days,
            "confidence_level": confidence,
            "stage_of_best_candidate": best_stage or None,
            "positive_factors": positives,
            "risk_factors": risks,
            "deadline": deadline.isoformat() if deadline else None,
            "total_active": total_active,
            "advanced_count": advanced_count,
        }

    async def get_company_overview(
        self,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Previsão de todas as vagas ativas da empresa, ordenadas por
        closure_probability ascendente (mais em risco primeiro).

        Returns:
            Dict com lista de previsões + estatísticas agregadas.
        """
        _managed = db is None
        if _managed:
            db = AsyncSessionLocal()

        try:
            vac_result = await db.execute(
                text("""
                    SELECT DISTINCT id::text AS vacancy_id,
                           created_by, recruiter_email
                    FROM job_vacancies
                    WHERE company_id = :cid
                      AND status = 'active'
                    ORDER BY id
                    LIMIT 50
                """),
                {"cid": company_id},
            )
            rows = vac_result.fetchall()
        except Exception as e:
            logger.warning(f"[PipelinePrediction] company overview DB error: {e}")
            return {"company_id": company_id, "vacancies": [], "summary": {}}
        finally:
            if _managed:
                await db.close()

        if not rows:
            return {"company_id": company_id, "vacancies": [], "summary": {}}

        # Previsão em paralelo (nova sessão por vaga para segurança)
        tasks = [
            self.get_vacancy_prediction(row[0], company_id)
            for row in rows
        ]
        predictions: list[dict] = await asyncio.gather(*tasks, return_exceptions=True)

        valid: list[dict] = []
        for pred in predictions:
            if isinstance(pred, Exception):
                logger.debug(f"[PipelinePrediction] Prediction error: {pred}")
                continue
            # Injetar recruiter info
            for row in rows:
                if row[0] == pred.get("vacancy_id"):
                    pred["recruiter_email"] = row[2]
                    break
            valid.append(pred)

        # Ordenar por probability ASC (mais em risco primeiro)
        valid.sort(key=lambda x: x["closure_probability"])

        at_risk = [v for v in valid if v["closure_probability"] < 30]
        near_close = [v for v in valid if v["closure_probability"] >= 80]
        avg_prob = int(sum(v["closure_probability"] for v in valid) / len(valid)) if valid else 0

        return {
            "company_id": company_id,
            "vacancies": valid,
            "summary": {
                "total_active_vacancies": len(valid),
                "at_risk_count": len(at_risk),
                "near_closure_count": len(near_close),
                "avg_closure_probability": avg_prob,
            },
        }

    async def get_recruiter_vacancies_prediction(
        self,
        company_id: str,
        recruiter_id: str,
        db: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retorna previsões de fechamento apenas para vagas do recrutador indicado.
        Usado pelo ProactiveWorker para alertas dirigidos.
        """
        _managed = db is None
        if _managed:
            db = AsyncSessionLocal()

        try:
            result = await db.execute(
                text("""
                    SELECT DISTINCT id::text AS vacancy_id
                    FROM job_vacancies
                    WHERE company_id = :cid
                      AND status = 'active'
                      AND (
                          created_by = :uid
                          OR recruiter_email = (
                              SELECT email FROM users WHERE id = CAST(:uid AS uuid) LIMIT 1
                          )
                      )
                    LIMIT 20
                """),
                {"cid": company_id, "uid": recruiter_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.warning(f"[PipelinePrediction] recruiter overview error: {e}")
            return []
        finally:
            if _managed:
                await db.close()

        if not rows:
            return []

        tasks = [self.get_vacancy_prediction(row[0], company_id) for row in rows]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    def _empty_prediction(
        self, vacancy_id: str, company_id: str
    ) -> dict[str, Any]:
        return {
            "vacancy_id": vacancy_id,
            "company_id": company_id,
            "vacancy_title": "Vaga",
            "closure_probability": 0,
            "estimated_days_to_close": None,
            "confidence_level": "low",
            "stage_of_best_candidate": None,
            "positive_factors": [],
            "risk_factors": ["data_unavailable"],
            "deadline": None,
            "total_active": 0,
            "advanced_count": 0,
        }


# Singleton
pipeline_prediction_service = PipelinePredictionService()
