"""
Sprint 1A.9 — Reutilizar serviços de cv_screening ao invés de duplicar.

ONDE APLICAR: app/domains/job_creation/services/
AÇÃO: Substituir imports locais por imports de cv_screening.

Buscar e substituir padrões como:
  from ..services.jd_enrichment import JdEnrichmentService
Por:
  from app.domains.cv_screening.services.jd_enrichment_service import JdEnrichmentService

Lista completa de serviços a reutilizar:
"""

# --- IMPORTS QUE DEVEM SER USADOS ---
# (substituir qualquer versão local por estes)

SERVICE_IMPORTS = {
    "JdEnrichmentService": "from app.domains.cv_screening.services.jd_enrichment_service import JdEnrichmentService",
    "WSIQuestionGenerator": "from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator, WSIService",
    "WSIScreeningPipeline": "from app.domains.cv_screening.services.wsi_screening_pipeline import WSIScreeningPipeline",
    "seniority_resolver": "from app.domains.cv_screening.services.seniority_resolver import resolve_seniority_full",
    "wsi_deterministic_scorer": "from app.domains.cv_screening.services.wsi_deterministic_scorer import calculate_wsi_deterministic, detect_red_flags",
    "PersonalizedFeedbackService": "from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService",
    "FairnessGuard": "from app.shared.compliance.fairness_guard import FairnessGuard",
    "AuditService": "from app.shared.compliance.audit_service import AuditService",
}

# --- VERIFICAÇÃO ---
# Após substituir, buscar por arquivos em job_creation/services/ que duplicam lógica:
#
# grep -r "class JdEnrichmentService" app/domains/job_creation/
# grep -r "class WSIQuestionGenerator" app/domains/job_creation/
#
# Se encontrar duplicatas, remover e usar os imports acima.

# --- ARQUIVOS CANDIDATOS A REMOÇÃO (se duplicam cv_screening) ---
# app/domains/job_creation/services/jd_enrichment.py  → usar cv_screening
# app/domains/job_creation/services/wsi_questions.py   → usar cv_screening
# app/domains/job_creation/services/scoring.py         → usar cv_screening
