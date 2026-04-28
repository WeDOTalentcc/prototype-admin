"""
Stage 4 — Salary & Benefits handler for the wizard step service.

F.3 (Onda 25 cross-reference) — `pick_canonical` agora considera 3 fontes:
  1. history  — padrões salariais internos (vagas anteriores na plataforma)
  2. market   — benchmark externo (combined_recommendation)
  3. ats_history — vagas similares vindas dos ATSs conectados (Gupy/Pandapé/Merge)

A 3ª fonte é fail-open: se `ats_job_history_service.get_similar_jobs` falhar
ou retornar lista vazia (empresa sem ATS conectado, primeira vaga, etc.), o
pipeline mantém o comportamento de 2 fontes. LGPD: descartamos vagas com
`closed_at` ou `created_at` mais antigo que 12 meses para não usar referências
salariais defasadas.
"""
import logging
import statistics
from datetime import datetime, timedelta

from ._shared import get_historical_salary_patterns
from app.shared.wizard_suggestion_priority import WizardSuggestion, pick_canonical
from app.domains.job_management.services.ats_job_history_service import (
    ats_job_history_service,
)

logger = logging.getLogger(__name__)

# LGPD / qualidade: descartar vagas ATS com mais de 12 meses
_ATS_HISTORY_CUTOFF_DAYS = 365


async def handle_salary(
    db,
    company_id: str,
    job_draft: dict,
    company_benefits: list,
    benchmarks: dict,
    field_origins: dict,
    suggestions_data: dict,
) -> tuple[str, dict, dict]:
    """
    Handle stage 4: salary and benefits.

    Returns:
        (lia_message, suggestions_data, field_origins)
    """
    benefits_list = ""
    if company_benefits:
        benefits_list = "\n\n✅ **Benefícios cadastrados da empresa:**\n" + "\n".join(
            [f"• {b['name']}" for b in company_benefits[:10]]
        )
    else:
        benefits_list = (
            "\n\n⚠️ *Nenhum benefício cadastrado. "
            "Você pode adicionar benefícios em Configurações → Benefícios.*"
        )

    salary_info = ""
    learning_info = ""
    historical_salary_info = ""
    internal_salary = benchmarks.get("internal_salary", {})
    market_salary = benchmarks.get("market_salary", {})
    combined = benchmarks.get("combined_recommendation", {})
    learning_adjustments = benchmarks.get("learning_adjustments", {})

    job_title_for_salary = job_draft.get('cargo') or job_draft.get('job_title') or ''
    seniority_for_salary = job_draft.get('senioridade') or job_draft.get('seniority') or 'Pleno'

    salary_patterns = {'has_data': False}
    try:
        salary_patterns = await get_historical_salary_patterns(
            db, company_id, job_title_for_salary, seniority_for_salary
        )
        if salary_patterns.get('has_data'):
            avg_min = salary_patterns['avg_min']
            avg_max = salary_patterns['avg_max']
            sample = salary_patterns['sample_size']
            historical_salary_info = (
                f"\n\n💰 **Referência histórica** ({sample} vagas similares): "
                f"R$ {avg_min:,.0f} - R$ {avg_max:,.0f}"
            )
            job_draft['salary_suggestion'] = historical_salary_info

            field_origins['salary_historical'] = {
                'source': 'historical_pattern',
                'confidence': min(0.85, 0.5 + (sample * 0.05)),
                'avg_min': avg_min,
                'avg_max': avg_max,
                'sample_size': sample,
            }

            if not job_draft.get('salary_min') and not job_draft.get('salario'):
                job_draft['salary_min'] = avg_min
                job_draft['salary_max'] = avg_max
                job_draft['salary_suggested'] = True
                logger.info(f"Pre-filled salary from historical patterns: R$ {avg_min:,.0f} - R$ {avg_max:,.0f}")
    except Exception as e:
        logger.warning(f"Could not get historical salary patterns: {e}")

    if internal_salary.get("sample_size", 0) > 0 or market_salary.get("min"):
        salary_info = "\n\n💰 **Sugestão de faixa salarial:**"

        if combined.get("recommended_min"):
            salary_info += (
                f"\n• Recomendado: R$ {combined.get('recommended_min', 0):,.0f} "
                f"- R$ {combined.get('recommended_max', 0):,.0f}"
            )
        elif internal_salary.get("median"):
            salary_info += f"\n• Mediana interna: R$ {internal_salary['median']:,.0f}"
        elif market_salary.get("median"):
            salary_info += f"\n• Mediana de mercado: R$ {market_salary['median']:,.0f}"

        if internal_salary.get("trend") == "increasing":
            salary_info += "\n• 📈 Tendência de alta nos últimos meses"
        elif internal_salary.get("trend") == "decreasing":
            salary_info += "\n• 📉 Tendência de queda nos últimos meses"

    if "salary_range" in learning_adjustments:
        salary_adj = learning_adjustments["salary_range"]
        adjustment_pct = salary_adj.get("adjustment_pct", 0)

        if adjustment_pct and abs(adjustment_pct) > 5:
            if combined.get("recommended_min") and not job_draft.get("salary_min"):
                job_draft["salary_min"] = combined.get("recommended_min")
                job_draft["salary_max"] = combined.get("recommended_max", combined.get("recommended_min"))

            field_origins["salary_range"] = {
                "source": "learning_adjusted",
                "original_min": combined.get("original_recommended_min"),
                "original_max": combined.get("original_recommended_max"),
                "adjusted_min": combined.get("recommended_min"),
                "adjusted_max": combined.get("recommended_max"),
                "adjustment_pct": adjustment_pct,
                "confidence": salary_adj.get("confidence", "low"),
                "sample_size": salary_adj.get("sample_size", 0),
            }

            direction_text = "para cima" if adjustment_pct > 0 else "para baixo"
            confidence_emoji = (
                "🟢" if salary_adj.get("confidence") == "high"
                else "🟡" if salary_adj.get("confidence") == "medium"
                else "🔴"
            )
            learning_info = (
                f"\n\n🧠 **Ajuste baseado em aprendizado:** Com base no histórico de correções da sua empresa, "
                f"ajustei a faixa salarial em **{adjustment_pct:+.0f}%** {direction_text}. "
                f"{confidence_emoji} Confiança: {salary_adj.get('confidence', 'low')}"
            )
            logger.info(
                f"Learning adjustment applied in benchmarks: {adjustment_pct:+.1f}% "
                f"for role {job_draft.get('cargo') or job_draft.get('job_title')}"
            )

    lia_message = f"""Perfeito! Vamos definir a **Remuneração**. 💰

📊 **Minha análise de mercado:**
{historical_salary_info}{salary_info}{learning_info}
{benefits_list}

**O que precisamos definir:**
• Faixa salarial (mínimo - máximo)
• Bônus ou PLR (se aplicável)
• Benefícios oferecidos nesta vaga

💡 *Os benefícios da empresa já estão pré-selecionados no painel. Ajuste conforme necessário.*

---

✅ **Próximo passo:** Após confirmar a remuneração, vamos definir as **competências** técnicas e comportamentais.

❓ *Quer saber mais sobre salários de mercado para este cargo? Pergunte!*"""

    suggestions_data = {
        "benefits": [{"name": b["name"], "selected": True} for b in company_benefits] if company_benefits else [],
        "salary_benchmark": combined,
        "learning_adjustments": learning_adjustments,
        "historical_salary": salary_patterns if salary_patterns.get('has_data') else None,
    }

    # ---- pick_canonical salary suggestion --------------------------------
    _hist_suggestion = None
    _mkt_suggestion = None
    _ats_suggestion = None
    _sources_used: list[str] = []

    if salary_patterns.get("has_data"):
        _hist_suggestion = WizardSuggestion(
            source="history",
            recommended_min=salary_patterns.get("avg_min"),
            recommended_max=salary_patterns.get("avg_max"),
            confidence=(
                "high" if salary_patterns.get("sample_size", 0) >= 10
                else "medium" if salary_patterns.get("sample_size", 0) >= 3
                else "low"
            ),
            sample_size=salary_patterns.get("sample_size", 0),
            metadata={"source_detail": "historical_pattern"},
        )
        _sources_used.append("history")

    if combined.get("recommended_min"):
        _mkt_suggestion = WizardSuggestion(
            source="market",
            recommended_min=combined.get("recommended_min"),
            recommended_max=combined.get("recommended_max"),
            confidence=combined.get("confidence", "low"),
            sample_size=combined.get("sample_size", 0),
            metadata={"source_detail": "benchmark_market"},
        )
        _sources_used.append("market")

    # ---- F.3: 3rd source — ATS job history (fail-open) -------------------
    # Vagas similares no histórico dos ATSs conectados (Gupy/Pandapé/Merge).
    # Pode falhar por: empresa sem ATS conectado, sem vagas similares, erro
    # de rede no ATS. Em todos os casos, mantemos o pipeline com 2 fontes.
    try:
        if db is not None and company_id and job_title_for_salary:
            similar_ats_jobs = await ats_job_history_service.get_similar_jobs(
                company_id=company_id,
                role=job_title_for_salary,
                seniority=seniority_for_salary,
                limit=20,
            )

            # Cutoff temporal LGPD: descarta vagas > 12 meses
            cutoff = datetime.utcnow() - timedelta(days=_ATS_HISTORY_CUTOFF_DAYS)
            ats_mins: list[float] = []
            ats_maxs: list[float] = []
            for j in similar_ats_jobs or []:
                ref_date = j.closed_at or j.created_at
                if ref_date is not None and ref_date < cutoff:
                    continue
                if j.salary_min and j.salary_max and j.salary_min > 0 and j.salary_max > 0:
                    ats_mins.append(float(j.salary_min))
                    ats_maxs.append(float(j.salary_max))

            if ats_mins and ats_maxs:
                ats_sample = len(ats_mins)
                ats_min_median = statistics.median(ats_mins)
                ats_max_median = statistics.median(ats_maxs)
                _ats_suggestion = WizardSuggestion(
                    source="ats_history",
                    recommended_min=ats_min_median,
                    recommended_max=ats_max_median,
                    confidence=(
                        "high" if ats_sample >= 10
                        else "medium" if ats_sample >= 3
                        else "low"
                    ),
                    sample_size=ats_sample,
                    metadata={"source_detail": "ats_similar_jobs"},
                )
                _sources_used.append("ats_history")
                logger.info(
                    f"ATS history suggestion: {ats_sample} similar jobs "
                    f"R$ {ats_min_median:,.0f} - R$ {ats_max_median:,.0f}"
                )
    except Exception as e:
        # FAIL-OPEN: ATS opcional, pipeline continua com 2 fontes
        logger.warning(f"Could not fetch ATS history salary signal (fail-open): {e}")

    # `pick_canonical` aceita apenas (history, market). Fundimos as duas fontes
    # de "histórico" (interno + ATS) em uma única — escolhendo a que tiver
    # MAIOR confiança / sample_size, com prioridade ao histórico interno em
    # caso de empate (mais auditável e LGPD-clean).
    _merged_history = _hist_suggestion
    if _ats_suggestion is not None:
        if _merged_history is None:
            _merged_history = _ats_suggestion
        else:
            _CONF_RANK = {"high": 3, "medium": 2, "low": 1}
            hist_rank = _CONF_RANK.get(_merged_history.confidence, 0)
            ats_rank = _CONF_RANK.get(_ats_suggestion.confidence, 0)
            # ATS só prevalece se ranking ESTRITAMENTE maior, ou ranking igual
            # com sample_size estritamente maior — interno tem prioridade no empate
            if ats_rank > hist_rank or (
                ats_rank == hist_rank
                and _ats_suggestion.sample_size > _merged_history.sample_size
            ):
                _merged_history = _ats_suggestion

    _canonical = pick_canonical(history=_merged_history, market=_mkt_suggestion)
    if _canonical:
        suggestions_data["canonical_salary_suggestion"] = {
            "source": _canonical.source,
            "recommended_min": _canonical.recommended_min,
            "recommended_max": _canonical.recommended_max,
            "confidence": _canonical.confidence,
            "sample_size": _canonical.sample_size,
            "sources_used": _sources_used,  # auditoria F.3
        }
    # -----------------------------------------------------------------------

    return lia_message, suggestions_data, field_origins
