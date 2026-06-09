# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
"""
WSI package — F11 report and ranking routes.

Routes:
  GET /f11-report/{session_id}
  GET /ranking/{job_vacancy_id}
  GET /candidate/{candidate_id}/ranking/{job_vacancy_id}
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.cv_screening.constants.wsi_scale import (
    GATE_G3_THRESHOLD as _GATE_G3_THRESHOLD_CANONICAL,
)
from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    SENIORITY_WEIGHTS,
)

from ._shared import (
    AI_INTEGRATIONS_ANTHROPIC_API_KEY,
    AI_INTEGRATIONS_ANTHROPIC_BASE_URL,
    BLOOM_LEVELS,
    DREYFUS_LEVELS,
    WSI_CLASSIFICATION_MAP,
)
from app.shared.security.require_company_id import require_company_id
# Recovery #3 (2026-05-23) — imports restored para get_wsi_audit_trail
# (endpoint compliance EU AI Act Art. 12 / LGPD Art. 20 perdido no merge 02361f41c).
from app.auth.dependencies import (
    get_current_user_strict,
    require_role,
    validate_company_access,
)
from app.auth.models import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# F11 models, constants and helper functions
# ---------------------------------------------------------------------------

_GATE_G3_THRESHOLD = _GATE_G3_THRESHOLD_CANONICAL
_GATE_G4_THRESHOLD = 3.0   # /10 scale (audit P1-1 tail 2026-06-05)
_INJECTION_KEYWORDS = ["ignore", "esquece", "esqueça", "novo prompt", "sys:", "system:", "jailbreak", "prompt injection"]

_SENIORITY_WEIGHTS = SENIORITY_WEIGHTS


class CBIQuestion(BaseModel):
    question_number: int
    area: str
    competencia_label: str
    gap_focus: str
    question_text: str
    bloom_target: int
    bloom_label: str
    dreyfus_target: int
    dreyfus_label: str
    expected_evidence: str
    red_flags: str


class GateStatus(BaseModel):
    g1_elegibilidade: bool
    g1_detail: str
    g2_prompt_injection: bool
    g2_detail: str
    g3_wsi_tecnico: bool
    g3_detail: str
    g4_skill_critica: bool
    g4_detail: str
    g5_engajamento: bool
    g5_detail: str
    g6_inflacao: bool
    g6_detail: str
    all_passed: bool
    failed_gates: list[str]


class F11ReportResponse(BaseModel):
    session_id: str
    result_id: str | None
    candidate_name: str
    candidate_id: str
    job_title: str
    job_vacancy_id: str | None
    seniority: str | None
    mode: str
    screening_type: str
    duration_minutes: float | None
    started_at: str | None
    completed_at: str | None
    overall_wsi: float
    technical_wsi: float
    behavioral_wsi: float
    classification: str
    classification_label: str
    gates: GateStatus
    decision_result: str
    decision_confidence: str
    decision_reason: str | None
    human_review_required: bool = False
    already_generated: bool = False
    responses_hash: str
    response_analyses: list[dict[str, Any]]
    interview_questions: list[CBIQuestion]
    strengths: list[str]
    gaps: list[dict[str, Any]]
    question_count: int = 0
    seniority_weights: dict[str, float] | None = None
    attention_flags: list[str] = []
    generated_at: str
    methodology_version: str = "WSI v2.0"


def _get_seniority_weights(seniority: str | None) -> dict[str, float] | None:
    if not seniority:
        return None
    key = seniority.lower().strip().replace(" ", "_")
    return _SENIORITY_WEIGHTS.get(key)


def _build_attention_flags(analyses: list[dict], gates: GateStatus) -> list[str]:
    flags = []
    if gates.g1_elegibilidade is False:
        flags.append("Questão eliminatória reprovada (G1)")
    if gates.g2_prompt_injection is False:
        flags.append("Tentativa de prompt injection detectada (G2)")
    gap_count = sum(1 for a in analyses if a.get("gap_status") == "gap")
    if gap_count >= 3:
        flags.append(f"{gap_count} competências com gap identificado")
    low_star = sum(1 for a in analyses if sum(a.get("star", {}).values()) <= 1)
    if low_star >= 2:
        flags.append(f"{low_star} respostas com STAR incompleto")
    critical_gaps = [a for a in analyses if a.get("is_critical") and a.get("final_score", 10) < 6.0]
    if critical_gaps:
        flags.append(f"{len(critical_gaps)} competência(s) crítica(s) abaixo do esperado")
    return flags


def _compute_decision_confidence(
    overall_wsi: float,
    failed_gates: list[str],
    llm_fallback_count: int,
    score_variance: float,
) -> tuple:
    """F10-6 — Computa decision.confidence e human_review_required de forma determinística."""
    ambiguous_gates = {"G2", "G5", "G6"}
    clear_reject_gates = {"G1", "G3", "G4"}
    if (
        "G2" in failed_gates
        or llm_fallback_count >= 2
        or score_variance > 4.0
    ):
        return "baixa", True

    if overall_wsi >= 9.0 and not failed_gates:
        return "alta", False

    if failed_gates and clear_reject_gates.intersection(failed_gates) and not ambiguous_gates.intersection(failed_gates):
        return "alta", False

    if 6.0 <= overall_wsi < 7.5:
        return "media", True

    if 7.5 <= overall_wsi < 9.0 and not failed_gates:
        return "media", False

    if failed_gates and ambiguous_gates.issuperset(failed_gates):
        return "media", True

    return "media", overall_wsi < 7.5


def _f11_fallback_questions(gaps: list[dict[str, Any]]) -> list[CBIQuestion]:
    """Fallback determinístico quando LLM falha 3x. Spec 11.5 edge case."""
    result = []
    used_types: set = set()
    for i, gap in enumerate(gaps[:3]):
        area = gap.get("type", "technical")
        if area in used_types:
            area = "behavioral" if area == "technical" else "technical"
        used_types.add(area)
        competency = gap.get("competency", f"Competência {i+1}")
        result.append(CBIQuestion(
            question_number=i + 1,
            area=area,
            competencia_label=competency,
            gap_focus=f"Aprofundar evidências sobre {competency}",
            question_text=f"Descreva uma situação passada em que você precisou demonstrar {competency}. Qual foi a ação que tomou e qual foi o resultado?",
            bloom_target=3,
            bloom_label="Aplicar",
            dreyfus_target=3,
            dreyfus_label="Intermediário",
            expected_evidence=f"Situação concreta, ação clara e resultado mensurável em {competency}",
            red_flags=f"Resposta vaga ou hipotética sobre {competency}",
        ))
        if len(result) == 2:
            break

    while len(result) < 2:
        result.append(CBIQuestion(
            question_number=len(result) + 1,
            area="behavioral",
            competencia_label="Resolução de problemas",
            gap_focus="Avaliar capacidade geral de resolução de problemas",
            question_text="Descreva uma situação desafiadora que você enfrentou no trabalho. Qual foi a ação que tomou e qual foi o resultado?",
            bloom_target=4,
            bloom_label="Analisar",
            dreyfus_target=3,
            dreyfus_label="Intermediário",
            expected_evidence="Situação real, raciocínio estruturado, resultado concreto",
            red_flags="Resposta vaga, ausência de resultado ou situação hipotética",
        ))
    return result[:2]


async def _generate_cbi_questions_llm(
    gaps: list[dict[str, Any]],
    strengths: list[str],
    previous_questions: list[str],
    seniority: str,
    job_title: str,
) -> list[CBIQuestion]:
    """Gera 2 perguntas CBI via LLM (temp=0.6, max_tokens=600, retry≤3). Spec 11.5."""
    from app.shared.providers.llm_factory import get_provider_for_tenant

    gaps_formatted = "\n".join(
        f"[{g.get('severity','MÉDIO')}] {g.get('competency','')} ({g.get('type','técnico')}) — score {g.get('score',0):.1f}/10 — sinais ausentes: {g.get('missing_signals','n/a')}"
        for g in gaps[:3]
    ) or "Nenhum gap crítico identificado — perguntas de aprofundamento"

    strengths_formatted = "\n".join(f"✓ {s}" for s in strengths[:2]) or "N/A"
    prev_qs_formatted = "\n".join(f"- {q}" for q in previous_questions[:5]) or "Nenhuma"

    bloom_expected = max((g.get("bloom_target", 3) for g in gaps[:1]), default=3)
    dreyfus_expected = max((g.get("dreyfus_target", 3) for g in gaps[:1]), default=3)
    bloom_lbl = BLOOM_LEVELS.get(bloom_expected, BLOOM_LEVELS[3])["name_pt"]
    dreyfus_lbl = DREYFUS_LEVELS.get(dreyfus_expected, DREYFUS_LEVELS[3])["name_pt"]

    system_prompt = (
        "Você é um especialista em entrevistas comportamentais estruturadas (CBI).\n"
        "Gere EXATAMENTE 2 perguntas para entrevista presencial com base nos gaps identificados na triagem.\n\n"
        "REGRAS:\n"
        "- Pergunta 1: foco no gap de MAIOR severidade (técnico ou comportamental)\n"
        "- Pergunta 2: foco no segundo maior gap — de tipo DIFERENTE do primeiro\n"
        "- Formato CBI-STAR: pedir situação real passada + ação + resultado\n"
        "- Linguagem NEUTRA em gênero: 'a pessoa candidata', 'você', 'o time' — sem pronomes binários\n"
        "- Cenários exclusivamente profissionais\n"
        "- Não repetir perguntas da triagem\n"
        "- Retorne JSON válido sem texto adicional\n"
    )

    user_prompt = f"""Senioridade da vaga: {seniority or 'Não especificada'}
Cargo: {job_title}
Bloom esperado: {bloom_expected} — {bloom_lbl}
Dreyfus esperado: {dreyfus_expected} — {dreyfus_lbl}

Gaps identificados (ALTO→MÉDIO→BAIXO):
{gaps_formatted}

Pontos fortes (não perguntar sobre estes):
{strengths_formatted}

Perguntas JÁ feitas na triagem (não repetir):
{prev_qs_formatted}

Retorne JSON:
{{
  "interview_questions": [
    {{
      "question_number": 1,
      "area": "technical",
      "competencia_label": "nome da competência",
      "gap_focus": "descrição do gap em 1 frase",
      "question_text": "pergunta completa pronta para o consultor ler",
      "bloom_target": 1-6,
      "bloom_label": "label Bloom",
      "dreyfus_target": 1-5,
      "dreyfus_label": "label Dreyfus",
      "expected_evidence": "2-3 comportamentos/ações esperados",
      "red_flags": "2-3 sinais de que o gap persiste"
    }},
    {{
      "question_number": 2,
      "area": "behavioral",
      "competencia_label": "nome da competência",
      "gap_focus": "descrição do gap em 1 frase",
      "question_text": "pergunta completa pronta para o consultor ler",
      "bloom_target": 1-6,
      "bloom_label": "label Bloom",
      "dreyfus_target": 1-5,
      "dreyfus_label": "label Dreyfus",
      "expected_evidence": "2-3 comportamentos/ações esperados",
      "red_flags": "2-3 sinais de que o gap persiste"
    }}
  ]
}}"""

    container = get_provider_for_tenant()
    last_err = None

    for attempt in range(1, 4):
        try:
            raw = await container.generate_with_fallback(
                system_prompt + "\n\n" + user_prompt,
                    agent_type="WSIReportAgent",
                )
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            qs = data.get("interview_questions", [])
            if len(qs) >= 2:
                q1_area = qs[0].get("area", "technical")
                q2_area = qs[1].get("area", "behavioral")
                if q1_area == q2_area and attempt < 3:
                    logger.info(f"F11 CBI attempt {attempt}: both questions are '{q1_area}', retrying for type alternation")
                    continue
                result = []
                for q in qs[:2]:
                    result.append(CBIQuestion(
                        question_number=q.get("question_number", len(result) + 1),
                        area=q.get("area", "technical"),
                        competencia_label=q.get("competencia_label", ""),
                        gap_focus=q.get("gap_focus", ""),
                        question_text=q.get("question_text", ""),
                        bloom_target=int(q.get("bloom_target", 3)),
                        bloom_label=q.get("bloom_label", "Aplicar"),
                        dreyfus_target=int(q.get("dreyfus_target", 3)),
                        dreyfus_label=q.get("dreyfus_label", "Intermediário"),
                        expected_evidence=q.get("expected_evidence", ""),
                        red_flags=q.get("red_flags", ""),
                    ))
                return result
        except Exception as e:
            last_err = e
            logger.warning(f"F11 CBI generation attempt {attempt}/3 failed: {e}")

    logger.error(f"F11: All 3 LLM attempts failed ({last_err}) — returning deterministic fallback")
    return _f11_fallback_questions(gaps)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/f11-report/{session_id}", summary="F11 — Relatório completo do consultor WSI", response_model=None)
async def get_f11_report(session_id: str, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Gera o relatório completo F11 para uma sessão WSI concluída.

    Inclui: G1-G6 gates, SHA-256 das respostas brutas, 2 perguntas CBI para
    entrevista presencial (LLM temp=0.6, retry≤3) e decisão estruturada.
    Spec: WSI_METHODOLOGY_COMPLETE_v2.md sections 11.1–11.5.
    """
    try:
        # F11-3 — cache: lê o relatório pré-gerado se existir. A coluna
        # f11_report_json é criada pela migration 244 (o ALTER TABLE inline foi
        # REMOVIDO daqui: adquiria lock ACCESS EXCLUSIVE em wsi_results e, sob
        # leitura concorrente, falhava + derrubava o endpoint inteiro com 500).
        # Cache-read graceful: sem a migração, loga + rollback (limpa a transação
        # envenenada pelo UndefinedColumn) e regenera, em vez de 500.
        try:
            cache_r = await db.execute(text("""
                SELECT f11_report_json FROM wsi_results
                WHERE session_id = :sid AND f11_report_json IS NOT NULL
                ORDER BY created_at DESC LIMIT 1
            """), {"sid": session_id})
            cached = cache_r.fetchone()
            if cached and cached[0]:
                report = F11ReportResponse(**cached[0])
                report.already_generated = True
                return report
        except Exception as _cache_read_err:
            logger.warning(
                f"[F11] cache-read indisponível, regenerando: {_cache_read_err}"
            )
            await db.rollback()

        sess_r = await db.execute(text("""
            SELECT s.id, s.candidate_id, s.job_vacancy_id, s.screening_type, s.mode,
                   s.status, s.started_at, s.completed_at,
                   c.name AS candidate_name,
                   j.title AS job_title, j.seniority_level
            FROM wsi_sessions s
            LEFT JOIN candidates c ON c.id = s.candidate_id
            INNER JOIN job_vacancies j ON j.id = s.job_vacancy_id
            WHERE s.id = :sid
              AND j.company_id = :company_id
        """), {"sid": session_id, "company_id": company_id})
        session = sess_r.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão WSI não encontrada")

        (sid, cand_id, jv_id, screening_type, mode, status,
         started_at, completed_at, candidate_name, job_title, seniority) = session

        res_r = await db.execute(text("""
            SELECT id, technical_wsi, behavioral_wsi, overall_wsi, classification
            FROM wsi_results WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1
        """), {"sid": session_id})
        result_row = res_r.fetchone()

        if result_row:
            result_id, tech_wsi, behav_wsi, overall_wsi, classification = result_row
            result_id = str(result_id)
            tech_wsi = float(tech_wsi)
            behav_wsi = float(behav_wsi)
            overall_wsi = float(overall_wsi)
        else:
            result_id = None
            tech_wsi = behav_wsi = overall_wsi = 0.0
            classification = "regular"

        classification_label = WSI_CLASSIFICATION_MAP.get(classification, {}).get("label", classification)

        qs_r = await db.execute(text("""
            SELECT id, competency, framework, question_type, question_text, weight, sequence_order,
                   scoring_criteria
            FROM wsi_questions WHERE session_id = :sid ORDER BY sequence_order
        """), {"sid": session_id})
        questions = qs_r.fetchall()

        ana_r = await db.execute(text("""
            SELECT ra.id, ra.question_id, ra.competency, ra.response_text,
                   ra.autodeclaration_score, ra.context_score, ra.bloom_level, ra.dreyfus_level,
                   ra.evidences, ra.red_flags, ra.consistency_penalty, ra.final_score, ra.justification
            FROM wsi_response_analyses ra
            WHERE ra.session_id = :sid
        """), {"sid": session_id})
        analyses = ana_r.fetchall()

        responses_hash = hashlib.sha256(
            "".join(a[3] or "" for a in analyses).encode("utf-8")
        ).hexdigest()

        q_map = {str(q[0]): q for q in questions}

        analyses_list = []
        for a in analyses:
            (a_id, q_id, competency, resp_text, auto_score, ctx_score,
             bloom_lv, dreyfus_lv, evidences, red_flags, cons_pen, final_score, justification) = a
            q = q_map.get(str(q_id), None)
            bloom_info  = BLOOM_LEVELS.get(bloom_lv or 3, BLOOM_LEVELS[3])
            dreyfus_info = DREYFUS_LEVELS.get(dreyfus_lv or 3, DREYFUS_LEVELS[3])

            q_scoring = (q[7] if q and q[7] else {}) or {}
            if isinstance(q_scoring, str):
                import json as _json
                try:
                    q_scoring = _json.loads(q_scoring)
                except Exception:
                    q_scoring = {}
            q_bloom_expected = int(q_scoring.get("bloom_level", q_scoring.get("expected_bloom", bloom_lv or 3)))
            q_dreyfus_expected = int(q_scoring.get("dreyfus_level", q_scoring.get("expected_dreyfus", dreyfus_lv or 3)))
            if q and q_scoring.get("is_critical") is not None:
                q_is_critical = bool(q_scoring["is_critical"])
            else:
                # q[5] é o PESO da pergunta (CHECK 0-1) — NÃO expressa criticalidade
                # (o produtor grava weight=1.0 fixo; nenhum peso > 1.0 é possível, o
                # antigo `>= 1.5` era sempre-falso). Sem is_critical explícito no
                # scoring_criteria, não inferir crítico do peso: default False
                # (G4 só dispara em skill marcada crítica de forma explícita).
                q_is_critical = False

            bloom_exp_info = BLOOM_LEVELS.get(q_bloom_expected, BLOOM_LEVELS[3])
            dreyfus_exp_info = DREYFUS_LEVELS.get(q_dreyfus_expected, DREYFUS_LEVELS[3])

            demonstrated_bloom = bloom_lv or 3
            demonstrated_dreyfus = dreyfus_lv or 3
            if demonstrated_bloom > q_bloom_expected and demonstrated_dreyfus >= q_dreyfus_expected:
                gap_status = "acima"
            elif demonstrated_bloom < q_bloom_expected or demonstrated_dreyfus < q_dreyfus_expected:
                gap_status = "gap"
            else:
                gap_status = "ok"

            resp_lower = (resp_text or "").lower()
            star_s = any(kw in resp_lower for kw in ["contexto", "situação", "cenário", "quando", "empresa", "projeto"])
            star_t = any(kw in resp_lower for kw in ["objetivo", "tarefa", "desafio", "responsabilidade", "missão", "meta"])
            star_a = any(kw in resp_lower for kw in ["implementei", "desenvolvi", "criei", "resolvi", "apliquei", "fiz", "liderei"])
            star_r = any(kw in resp_lower for kw in ["resultado", "impacto", "melhoria", "redução", "aumento", "uptime", "%", "kpi"])

            analyses_list.append({
                "analysis_id": str(a_id),
                "question_id": str(q_id),
                "competency": competency,
                "question_text": q[4] if q else "",
                "question_type": q[3] if q else "technical",
                "framework": q[2] if q else "",
                "weight": float(q[5]) if q else 1.0,
                "is_critical": q_is_critical,
                "response_text": resp_text or "",
                "response_word_count": len((resp_text or "").split()),
                "autodeclaration_score": float(auto_score) if auto_score else 0.0,
                "context_score": float(ctx_score) if ctx_score else 0.0,
                "bloom_level": demonstrated_bloom,
                "bloom_label": bloom_info["name_pt"],
                "bloom_expected": q_bloom_expected,
                "bloom_expected_label": bloom_exp_info["name_pt"],
                "dreyfus_level": demonstrated_dreyfus,
                "dreyfus_label": dreyfus_info["name_pt"],
                "dreyfus_expected": q_dreyfus_expected,
                "dreyfus_expected_label": dreyfus_exp_info["name_pt"],
                "gap_status": gap_status,
                "star": {"S": star_s, "T": star_t, "A": star_a, "R": star_r},
                "evidences": evidences or [],
                "red_flags": red_flags or [],
                "consistency_penalty": float(cons_pen) if cons_pen else 0.0,
                "final_score": float(final_score) if final_score else 0.0,
                "justification": justification or "",
            })

        g1_failed = any(
            a["question_type"] == "eligibility" and a["final_score"] == 0.0
            for a in analyses_list
        )
        injection_count = sum(
            1 for a in analyses_list
            if any(kw in (a.get("response_text") or "").lower() for kw in _INJECTION_KEYWORDS)
        )
        g2_failed = injection_count >= 1

        g3_failed = tech_wsi < _GATE_G3_THRESHOLD and tech_wsi > 0.0

        g4_failed = any(
            a["final_score"] < _GATE_G4_THRESHOLD and a["final_score"] > 0.0
            and a.get("is_critical", False)
            for a in analyses_list
        )

        short_responses = sum(1 for a in analyses_list if a["response_word_count"] < 30)
        total_qs = len(analyses_list)
        g5_failed = (total_qs > 0) and (short_responses / total_qs >= 0.5)

        inflation_count = sum(
            1 for a in analyses_list
            if (
                (a.get("flags_structured") or {}).get("is_inflation", False)
                or any(
                    "inflação" in str(rf).lower() or "inflation" in str(rf).lower()
                    for rf in (a.get("red_flags") or [])
                )
            )
        )
        g6_failed = inflation_count >= 3

        failed_gates = []
        if g1_failed: failed_gates.append("G1")
        if g2_failed: failed_gates.append("G2")
        if g3_failed: failed_gates.append("G3")
        if g4_failed: failed_gates.append("G4")
        if g5_failed: failed_gates.append("G5")
        if g6_failed: failed_gates.append("G6")

        gates = GateStatus(
            g1_elegibilidade=not g1_failed,
            g1_detail="Elegibilidade confirmada" if not g1_failed else "Requisito de elegibilidade não atendido",
            g2_prompt_injection=not g2_failed,
            g2_detail=f"{injection_count} tentativa(s) de manipulação detectada(s)" if g2_failed else "Sem injeção de prompt detectada",
            g3_wsi_tecnico=not g3_failed,
            g3_detail=f"WSI Técnico {tech_wsi:.2f}/10 {'< limiar 4.0 — reprovado' if g3_failed else '≥ limiar 4.0 — aprovado'}",
            g4_skill_critica=not g4_failed,
            g4_detail="Skill crítica com score abaixo do mínimo absoluto" if g4_failed else "Nenhuma skill crítica abaixo do mínimo",
            g5_engajamento=not g5_failed,
            g5_detail=f"{short_responses}/{total_qs} respostas com < 30 palavras {'— engajamento insuficiente' if g5_failed else '— engajamento adequado'}",
            g6_inflacao=not g6_failed,
            g6_detail=f"{inflation_count} resposta(s) com inflação detectada" if g6_failed else "Sem padrão de inflação sistemática",
            all_passed=len(failed_gates) == 0,
            failed_gates=failed_gates,
        )

        all_scores = [a["final_score"] for a in analyses_list if a["final_score"] > 0]
        score_variance = (max(all_scores) - min(all_scores)) if len(all_scores) >= 2 else 0.0
        llm_fallback_count = sum(
            1 for a in analyses_list
            if (a.get("flags_structured") or {}).get("_llm_fallback", False)
        )

        gate_labels = {
            "G1": "elegibilidade", "G2": "injeção de prompt",
            "G3": "competência técnica mínima", "G4": "skill crítica",
            "G5": "engajamento insuficiente", "G6": "inflação sistemática",
        }
        if len(failed_gates) > 0:
            decision_result = "REPROVADO"
            gate_reasons = [gate_labels.get(g, g) for g in failed_gates]
            decision_reason = f"Gate(s) ativado(s): {', '.join(gate_reasons)}"
        elif overall_wsi >= 7.5:
            decision_result = "APROVADO"
            decision_reason = None
        elif overall_wsi >= 6.0:
            decision_result = "EM_AVALIACAO"
            decision_reason = f"Score WSI {overall_wsi:.2f}/10 requer revisão humana (faixa 6.0–7.49)"
        else:
            decision_result = "REPROVADO"
            decision_reason = f"Score WSI {overall_wsi:.2f}/10 abaixo do mínimo (< 6.0)"

        decision_confidence, human_review_required = _compute_decision_confidence(
            overall_wsi=overall_wsi,
            failed_gates=failed_gates,
            llm_fallback_count=llm_fallback_count,
            score_variance=score_variance,
        )

        sorted_analyses = sorted(analyses_list, key=lambda x: x["final_score"], reverse=True)
        strengths = [
            f"{a['competency']} — {a['final_score']:.1f}/10"
            for a in sorted_analyses[:3]
            if a["final_score"] >= 7.0
        ]

        gap_items = [
            a for a in sorted_analyses if a["final_score"] < 6.0 and a["final_score"] > 0.0
        ]
        gap_items.sort(key=lambda x: x["final_score"])
        gaps = []
        for a in gap_items[:3]:
            delta = 6.0 - a["final_score"]
            severity = "ALTO" if delta >= 3.0 else ("MÉDIO" if delta >= 1.5 else "BAIXO")
            gaps.append({
                "competency": a["competency"],
                "type": a["question_type"],
                "score": a["final_score"],
                "delta": round(delta, 2),
                "severity": severity,
                "missing_signals": ", ".join(str(rf) for rf in (a.get("red_flags") or [])[:2]) or "n/a",
                "bloom_target": a["bloom_level"],
                "dreyfus_target": a["dreyfus_level"],
            })

        previous_questions = [a["question_text"] for a in analyses_list if a["question_text"]]
        interview_questions = await _generate_cbi_questions_llm(
            gaps=gaps,
            strengths=strengths,
            previous_questions=previous_questions,
            seniority=str(seniority or ""),
            job_title=str(job_title or ""),
        )

        duration_minutes = None
        if started_at and completed_at:
            diff = (completed_at - started_at).total_seconds() / 60
            duration_minutes = round(diff, 1)

        report = F11ReportResponse(
            session_id=str(sid),
            result_id=result_id,
            candidate_name=candidate_name or "Candidato",
            candidate_id=str(cand_id),
            job_title=job_title or "Vaga",
            job_vacancy_id=str(jv_id) if jv_id else None,
            seniority=str(seniority) if seniority else None,
            mode=mode or "compact",
            screening_type=screening_type or "text",
            duration_minutes=duration_minutes,
            started_at=started_at.isoformat() if started_at else None,
            completed_at=completed_at.isoformat() if completed_at else None,
            overall_wsi=round(overall_wsi, 3),
            technical_wsi=round(tech_wsi, 3),
            behavioral_wsi=round(behav_wsi, 3),
            classification=classification,
            classification_label=classification_label,
            gates=gates,
            decision_result=decision_result,
            decision_confidence=decision_confidence,
            decision_reason=decision_reason,
            human_review_required=human_review_required,
            responses_hash=responses_hash,
            response_analyses=analyses_list,
            interview_questions=interview_questions,
            strengths=strengths,
            gaps=gaps,
            question_count=len(questions),
            seniority_weights=_get_seniority_weights(str(seniority) if seniority else None),
            attention_flags=_build_attention_flags(analyses_list, gates),
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        # F11-3 — persistir no cache para evitar re-geração
        if result_id:
            try:
                import json as _json
                await db.execute(text("""
                    UPDATE wsi_results SET f11_report_json = :payload
                    WHERE id = :rid
                """), {"rid": result_id, "payload": _json.dumps(report.model_dump())})
            except Exception as _cache_err:
                logger.warning(f"F11-3: falha ao persistir cache do relatório: {_cache_err}")
                await db.rollback()

        # Débito 3 — espelhar subset do relatório F11 no parecer WSI (score_breakdown),
        # para o card exibir o relatório completo. Sem SQL inline: via OpinionsRepository.
        try:
            from uuid import UUID as _UUID
            from app.repositories.opinions_repository import (
                OpinionsRepository,
            )
            _repo = OpinionsRepository(db)
            _cid = cand_id if isinstance(cand_id, _UUID) else _UUID(str(cand_id))
            _jv = str(jv_id) if jv_id else None
            _rd = report.model_dump()
            _subset = {
                k: _rd.get(k)
                for k in (
                    "classification", "classification_label", "gates",
                    "decision_result", "decision_confidence", "decision_reason",
                    "strengths", "gaps", "attention_flags", "generated_at",
                )
            }
            for _op in await _repo.get_current_by_candidate(_cid, company_id):
                _op_jv = str(_op.job_vacancy_id) if _op.job_vacancy_id else None
                if _op.opinion_type == "wsi" and _op_jv == _jv:
                    _sb = dict(_op.score_breakdown or {})
                    _sb["f11_report"] = _subset
                    _op.score_breakdown = _sb
                    await _repo.update(_op)
                    break
        except Exception as _fold_err:
            logger.warning(f"F11 fold into WSI opinion skipped: {_fold_err}")
            await db.rollback()

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"F11 report generation failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório F11: {str(e)}")


@router.get("/ranking/{job_vacancy_id}", summary="F11-6 — Ranking de candidatos por vaga", response_model=None)
async def get_vacancy_ranking(
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna o ranking completo de candidatos triados para uma vaga.

    Spec: WSI_METHODOLOGY_COMPLETE_v2.md §11.6.4 Tab 3.
    Ordena por overall_wsi DESC e calcula rank, percentil e médias do pool.
    """
    try:
        # Onda 4.2c-P0-4 (2026-05-23): tenant guard via INNER JOIN com job_vacancies.
        # Antes vazava ranking completo (candidate_name + scores) cross-tenant.
        rows_r = await db.execute(text("""
            SELECT
                r.id            AS result_id,
                r.candidate_id,
                COALESCE(c.name, 'Candidato') AS candidate_name,
                COALESCE(c.current_title, '') AS candidate_title,
                r.overall_wsi,
                r.technical_wsi,
                r.behavioral_wsi,
                r.classification,
                s.screening_type,
                r.created_at
            FROM wsi_results r
            LEFT JOIN wsi_sessions s ON s.id = r.session_id
            LEFT JOIN candidates c   ON c.id = r.candidate_id
            INNER JOIN job_vacancies jv ON jv.id = r.job_vacancy_id
            WHERE r.job_vacancy_id::text = :jv_id
              AND jv.company_id::text = :company_id
            ORDER BY r.overall_wsi DESC, r.created_at DESC
        """), {"jv_id": job_vacancy_id, "company_id": company_id})
        rows = rows_r.fetchall()

        if not rows:
            return {
                "job_vacancy_id": job_vacancy_id,
                "total_screened": 0,
                "averages": {"overall": 0.0, "technical": 0.0, "behavioral": 0.0},
                "ranking": [],
            }

        total = len(rows)
        overall_vals  = [float(r[4]) for r in rows]
        tech_vals     = [float(r[5]) for r in rows]
        behav_vals    = [float(r[6]) for r in rows]

        ranking = []
        for rank, row in enumerate(rows, start=1):
            score = float(row[4])
            below_or_eq = sum(1 for v in overall_vals if v <= score)
            percentile = round((below_or_eq / total) * 100)
            ranking.append({
                "rank": rank,
                "total": total,
                "result_id": str(row[0]),
                "candidate_id": str(row[1]),
                "candidate_name": row[2],
                "candidate_title": row[3],
                "overall_wsi": round(score, 2),
                "technical_wsi": round(float(row[5]), 2),
                "behavioral_wsi": round(float(row[6]), 2),
                "classification": row[7] or "regular",
                "percentile": percentile,
                "screening_type": row[8] or "text",
                "created_at": row[9].isoformat() if row[9] else None,
            })

        return {
            "job_vacancy_id": job_vacancy_id,
            "total_screened": total,
            "averages": {
                "overall":    round(sum(overall_vals) / total, 2),
                "technical":  round(sum(tech_vals) / total, 2),
                "behavioral": round(sum(behav_vals) / total, 2),
            },
            "ranking": ranking,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"F11-6 vacancy ranking failed for {job_vacancy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/candidate/{candidate_id}/ranking/{job_vacancy_id}",
    summary="F11-6 — Posição do candidato no ranking da vaga",
    response_model=None)
async def get_candidate_ranking(
    candidate_id: str,
    job_vacancy_id: str,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna a posição do candidato no ranking da vaga (rank #N de M).

    Spec: WSI_METHODOLOGY_COMPLETE_v2.md §11.6.4 Tab 3.
    """
    try:
        # Onda 4.2c-P0-5 (2026-05-23): tenant guard pre-check no job_vacancy.
        tenant_check = await db.execute(
            text("SELECT 1 FROM job_vacancies WHERE id = :jv_id AND company_id = :company_id"),
            {"jv_id": job_vacancy_id, "company_id": company_id},
        )
        if not tenant_check.scalar():
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        cand_r = await db.execute(text("""
            SELECT id, overall_wsi FROM wsi_results
            WHERE candidate_id::text = :cid AND job_vacancy_id::text = :jv_id
            ORDER BY created_at DESC LIMIT 1
        """), {"cid": candidate_id, "jv_id": job_vacancy_id})
        cand_row = cand_r.fetchone()

        if not cand_row:
            return {"candidate_id": candidate_id, "job_vacancy_id": job_vacancy_id, "ranked": False}

        cand_score = float(cand_row[1])

        total_r = await db.execute(text("""
            SELECT COUNT(*), SUM(CASE WHEN overall_wsi > :score THEN 1 ELSE 0 END)
            FROM wsi_results WHERE job_vacancy_id::text = :jv_id
        """), {"jv_id": job_vacancy_id, "score": cand_score})
        total_row = total_r.fetchone()
        total = int(total_row[0]) if total_row else 1
        above  = int(total_row[1] or 0) if total_row else 0
        rank   = above + 1

        return {
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "ranked": True,
            "rank": rank,
            "total": total,
            "overall_wsi": round(cand_score, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"F11-6 candidate ranking failed for {candidate_id}/{job_vacancy_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Recovery #3 (2026-05-23) — get_wsi_audit_trail restored.
#
# Endpoint perdido no merge commit 02361f41c em 2026-05-01. Implementação
# original Task #511 (round 3 fix com deny-by-default em sessions sem company).
#
# Compliance crítico: EU AI Act Art. 12 (record-keeping de IA high-risk) e
# LGPD Art. 20 (direito de explicação de decisão automatizada). Retorna a
# trilha imutável de respostas WSI + hashes SHA-256 + análise correlata.
#
# Acesso: admin (cross-tenant) ou dpo (escopado via validate_company_access).
# Deny-by-default quando session_company_id resolve None (job_vacancy órfão).
# ---------------------------------------------------------------------------
@router.get(
    "/reports/audit/{session_id}",
    summary="Audit trail WSI — EU AI Act Art. 12 / LGPD Art. 20",
    response_model=None,
    dependencies=[Depends(require_role([UserRole.admin, UserRole.wedotalent_admin]))],
)
async def get_wsi_audit_trail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_strict),
):
    """Retorna a trilha de auditoria imutável das respostas WSI da sessão.

    Acesso: ``admin`` (tenant admin — escopado à própria company via
    ``validate_company_access``) ou ``wedotalent_admin`` (staff WeDOTalent —
    cross-tenant). Recovery #3 (2026-05-23) substituiu o role legacy ``dpo``
    (deprecated no enum atual) por ``wedotalent_admin`` que tem mesmo papel
    de compliance cross-tenant.

    Inclui:
      - lista de respostas brutas + hash SHA-256 + timestamps (``wsi_responses``)
      - hashes correlatos da análise (``wsi_response_analyses.response_hash``)
      - metadados da sessão para correlação

    O hash permite verificar integridade sem reprocessar o texto e detectar
    duplicatas / adulterações posteriores.
    """
    # multi-tenancy: tenant-scoped via validate_company_access + deny-by-default
    # (Task #511 round 3). wedotalent_admin tem acesso cross-tenant INTENCIONAL
    # (EU AI Act Art. 12 — staff WeDOTalent responde regulador). Sensor false
    # positive: gate eh validate_company_access, nao require_company_id.
    # 1) Sessão existe? (join com job_vacancies para obter company_id)
    sess_row = (await db.execute(text(
        "SELECT s.id, s.status, s.candidate_id, s.job_vacancy_id, "
        "       s.created_at, s.completed_at, jv.company_id "
        "FROM wsi_sessions s "
        "LEFT JOIN job_vacancies jv ON jv.id = s.job_vacancy_id "
        "WHERE s.id = :sid"
    ), {"sid": session_id})).fetchone()
    if not sess_row:
        raise HTTPException(status_code=404, detail="WSI session not found")

    # 2) Tenant scoping (Task #511 round 3) — bloqueia IDOR cross-tenant.
    # - ``wedotalent_admin`` tem acesso cross-tenant explícito (staff WeDOTalent
    #   responde regulador europeu/ANPD).
    # - ``admin`` (tenant) só vê dados da própria company via
    #   ``validate_company_access`` (que usa ``user.can_access_company``).
    #
    # TODO follow-up cross-cutting: ``User.can_access_company`` em app/auth/models.py
    # ainda não reconhece ``wedotalent_admin`` como cross-tenant. Quando atualizar
    # (afeta vários endpoints), simplificar este path pra um único
    # ``validate_company_access`` call sem skip explícito.
    #
    # Round 3 fix (deny-by-default): se a sessão não resolve company
    # (job_vacancy ausente/órfão, dado legado, sessão sem job), apenas roles
    # cross-tenant (admin OR wedotalent_admin) podem acessar — sem company
    # resolvível não há como provar pertencimento ao tenant.
    session_company_id = sess_row[6]
    cross_tenant_roles = {UserRole.admin, UserRole.wedotalent_admin}
    if session_company_id is not None:
        if current_user.role != UserRole.wedotalent_admin:
            validate_company_access(current_user, str(session_company_id))
    else:
        if current_user.role not in cross_tenant_roles:
            logger.warning(
                "[WSI-AUDIT] deny: company unresolved for session=%s "
                "(role=%s, user=%s)",
                session_id, current_user.role, current_user.id,
            )
            raise HTTPException(
                status_code=403,
                detail="Cannot resolve session tenant; access denied",
            )

    responses_rows = (await db.execute(text(
        "SELECT id, question_id, raw_text, response_hash, candidate_id, created_at "
        "FROM wsi_responses WHERE session_id = :sid ORDER BY created_at ASC"
    ), {"sid": session_id})).fetchall()

    analyses_rows = (await db.execute(text(
        "SELECT question_id, competency, response_hash, final_score "
        "FROM wsi_response_analyses WHERE session_id = :sid"
    ), {"sid": session_id})).fetchall()

    logger.info(
        "[WSI-AUDIT] session=%s requested_by=%s role=%s items=%d",
        session_id, current_user.id, current_user.role, len(responses_rows),
    )

    return {
        "session_id": session_id,
        "session": {
            "status": sess_row[1],
            "candidate_id": sess_row[2],
            "job_vacancy_id": sess_row[3],
            "created_at": sess_row[4].isoformat() if sess_row[4] else None,
            "completed_at": sess_row[5].isoformat() if sess_row[5] else None,
        },
        "responses": [
            {
                "id": str(r[0]),
                "question_id": r[1],
                "raw_text": r[2],
                "response_hash": r[3],
                "candidate_id": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            }
            for r in responses_rows
        ],
        "analyses_hashes": [
            {
                "question_id": a[0],
                "competency": a[1],
                "response_hash": a[2],
                "final_score": float(a[3]) if a[3] is not None else None,
            }
            for a in analyses_rows
        ],
        "compliance": {
            "framework": "EU AI Act Art. 12 / LGPD Art. 20",
            "hash_algorithm": "SHA-256",
            "accessed_by": str(current_user.id),
            "accessed_at": datetime.utcnow().isoformat() + "Z",
        },
    }
