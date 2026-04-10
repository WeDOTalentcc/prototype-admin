"""
Sprint 1A.1 — Supervisor routing para job_creation domain.

ONDE APLICAR: app/hub/supervisor_graph.py (ou equivalente)
AÇÃO: Adicionar job_creation ao DOMAIN_DESCRIPTIONS e ROUTING_KEYWORDS.

Buscar a seção de DOMAIN_DESCRIPTIONS e adicionar o bloco abaixo.
Buscar a seção de ROUTING_KEYWORDS e adicionar os patterns.
"""

# --- ADICIONAR ao DOMAIN_DESCRIPTIONS ---
# Encontre o dict DOMAIN_DESCRIPTIONS e adicione:

JOB_CREATION_DESCRIPTION = {
    "job_creation": {
        "description": (
            "Criação de vagas com metodologia WSI (Web-based Structured Interviews). "
            "Inclui: enriquecimento de JD, perfil Big Five, competências, "
            "geração de perguntas de triagem (CBI/Bloom/Dreyfus), "
            "elegibilidade, revisão, publicação, calibração e handoff. "
            "Use quando o recrutador quer criar, publicar ou configurar uma nova vaga."
        ),
        "capabilities": [
            "criar vaga com JD enriquecido",
            "gerar perguntas de triagem WSI",
            "definir critérios de elegibilidade",
            "configurar screening automático",
            "publicar vaga em plataformas",
            "calibrar threshold de candidatos",
        ],
    }
}

# --- ADICIONAR ao ROUTING_KEYWORDS ---
# Encontre o dict ROUTING_KEYWORDS e adicione:

JOB_CREATION_KEYWORDS = {
    "job_creation": [
        r"\b(criar|nova|abrir|publicar|configurar)\s+(vaga|posicao|cargo)\b",
        r"\bcriar\s+vaga\b",
        r"\bnova\s+vaga\b",
        r"\bpublicar\s+vaga\b",
        r"\b(job\s+description|jd)\b",
        r"\b(perguntas|questoes)\s+(de\s+)?(triagem|screening|wsi)\b",
        r"\b(enriquecer|melhorar)\s+(jd|descricao)\b",
        r"\bcalibr(ar|acao)\b",
        r"\bwsi\b",
    ],
}

# --- ADICIONAR ao domain registry ---
# Em app/domains/registry.py (ou __init__.py), registrar:
#
# from app.domains.job_creation.domain import JobCreationDomain
# register_domain("job_creation", JobCreationDomain)
#
# Se usar @register_domain decorator:
# Verificar que job_creation/domain.py tem o decorator

# --- FEATURE FLAG ---
# No supervisor, antes de rotear para job_creation, verificar:
#
# import os
# ENABLE_UNIFIED_WIZARD = os.getenv("ENABLE_UNIFIED_WIZARD", "false").lower() == "true"
#
# No routing logic:
# if matched_domain == "job_creation" and not ENABLE_UNIFIED_WIZARD:
#     matched_domain = "jobs"  # fallback para domain legado
