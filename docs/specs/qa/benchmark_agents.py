#!/usr/bin/env python3
"""
benchmark_agents.py — Benchmark de Agentes de Processo de IA
Plataforma LIA — Testa agentes de backend que atuam em processos automatizados.

Uso:
  python benchmark_agents.py --base-url http://localhost:3000 --token SEU_TOKEN
  python benchmark_agents.py --agent wsi --base-url ... --token ...
  python benchmark_agents.py --dry-run
  LIA_TOKEN=xxx python benchmark_agents.py --base-url ...

Diferença do benchmark_prompts.py: este script testa AGENTES DE PROCESSO
(WSI scoring, CV matching, salary benchmark, pipeline analysis),
não componentes de chat/UI.
"""

import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Tenta importar httpx (async); cai para requests (sync) se não disponível
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    try:
        import requests
    except ImportError:
        print("❌ Nenhuma biblioteca HTTP encontrada. Instale httpx ou requests:")
        print("   pip install httpx  (recomendado)")
        print("   pip install requests  (alternativa)")
        sys.exit(1)

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES GLOBAIS
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:3000"
DEFAULT_TIMEOUT = 60  # segundos (agentes de processo podem ser mais lentos)
DEFAULT_OUTPUT_DIR = "."

BENCHMARK_USER_ID = "benchmark_agent_user"
BENCHMARK_JOB_ID = "benchmark_job_001"

# ---------------------------------------------------------------------------
# HELPERS DE DETECÇÃO / VALIDAÇÃO
# ---------------------------------------------------------------------------


def extract_brl_values(text: str) -> list:
    """Extract BRL salary values from text. e.g. 'R$ 15.000' -> 15000.0"""
    pattern = r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    matches = re.findall(pattern, text)
    return [float(m.replace(".", "").replace(",", ".")) for m in matches]


def check_star_in_answer(answer: str) -> dict:
    """Detect STAR elements in a candidate answer."""
    return {
        "situacao": any(
            w in answer.lower()
            for w in ["situação", "contexto", "cenário", "quando", "em 2"]
        ),
        "tarefa": any(
            w in answer.lower()
            for w in ["tarefa", "objetivo", "responsável", "precisava", "designado"]
        ),
        "acao": any(
            w in answer.lower()
            for w in ["ação", "fiz", "implementei", "desenvolvi", "criei", "dividi"]
        ),
        "resultado": any(
            w in answer.lower()
            for w in ["resultado", "consegui", "entregamos", "reduzi", "%", "entregue"]
        ),
    }


def contains_portuguese(text: str) -> bool:
    """Check whether a text contains Portuguese indicators."""
    pt_words = [
        "de", "com", "para", "que", "uma", "não", "você", "mais", "está",
        "são", "ser", "ter", "por", "isso", "mas", "bem", "olá", "sim",
        "posso", "ajudar", "entendo", "claro", "aqui", "também", "sobre",
        "candidato", "vaga", "recrutamento", "seleção", "entrevista",
        "habilidades", "experiência", "salário", "faixa",
    ]
    lower = text.lower()
    return sum(1 for w in pt_words if w in lower) >= 3


def mentions_pipeline_stages(text: str) -> bool:
    """Check if text mentions typical recruitment pipeline stages."""
    stage_words = [
        "triagem", "entrevista", "oferta", "etapa", "funil", "pipeline",
        "aprovado", "reprovado", "candidato", "processo", "seleção",
        "tempo", "prazo", "dias", "semana", "gargalo", "bottleneck",
    ]
    lower = text.lower()
    return sum(1 for w in stage_words if w in lower) >= 2


def get_text_from_response(data: Any, paths: list) -> str:
    """Try multiple key paths to extract text from a response dict."""
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return str(data)
    for path in paths:
        keys = path.split(".") if isinstance(path, str) else path
        val = data
        try:
            for k in keys:
                if isinstance(val, dict):
                    val = val[k]
                elif isinstance(val, list) and k.isdigit():
                    val = val[int(k)]
                else:
                    val = None
                    break
            if val is not None:
                return str(val)
        except (KeyError, IndexError, TypeError):
            continue
    return ""


# ---------------------------------------------------------------------------
# GOLDEN TEST CASES — AGENTES DE PROCESSO
# ---------------------------------------------------------------------------

GOLDEN_CASES = [
    # =========================================================================
    # 1. WSI SCORING
    # =========================================================================
    {
        "id": "wsi_001",
        "agent": "wsi",
        "name": "WSI — Resposta STAR completa (deve score >= 7)",
        "endpoint": "http://localhost:8000/api/v1/wsi/analyze-response",
        "method": "POST",
        "body": {
            "session_id": f"benchmark-wsi-{BENCHMARK_JOB_ID}",
            "question_id": "q-benchmark-001",
            "candidate_id": "candidate-benchmark-001",
            "job_vacancy_id": BENCHMARK_JOB_ID,
            "question_text": "Descreva uma situação em que você liderou um projeto complexo de dados",
            "response_text": ("\nSituação: Em 2023, nossa empresa precisava migrar 500GB de dados legados "
                "para um novo data warehouse em 3 meses.\n"
                "Tarefa: Fui designado como tech lead do projeto, responsável pela arquitetura e execução.\n"
                "Ação: Dividi o projeto em 4 sprints, criei pipelines ETL com Python e Airflow, "
                "implementei testes automatizados de qualidade de dados.\n"
                "Resultado: Entregamos em 2,5 meses com 99.8% de integridade dos dados "
                "e redução de 40% no tempo de queries.\n"),
            "competency": "lideranca_tecnica",
            "framework": "STAR",
        },
        "description": "Resposta STAR completa deve receber score alto (>=7) com star_completeness >= 0.8",
        "quality_checks": {
            "score_min": 7.0,
            "score_max": 10.0,
            "star_completeness_min": 0.8,
            "check_feedback_portuguese": True,
        },
        "star_elements_expected": ["situacao", "tarefa", "acao", "resultado"],
    },
    {
        "id": "wsi_002",
        "agent": "wsi",
        "name": "WSI — Resposta vaga (deve score <= 4)",
        "endpoint": "http://localhost:8000/api/v1/wsi/analyze-response",
        "method": "POST",
        "body": {
            "session_id": f"benchmark-wsi-{BENCHMARK_JOB_ID}",
            "question_id": "q-benchmark-001",
            "candidate_id": "candidate-benchmark-001",
            "job_vacancy_id": BENCHMARK_JOB_ID,
            "question_text": "Descreva uma situação em que você liderou um projeto complexo de dados",
            "response_text": ("Sim, já trabalhei com projetos de dados. "
                "Foi uma experiência muito boa e aprendi bastante."),
            "competency": "lideranca_tecnica",
            "framework": "STAR",
        },
        "description": "Resposta vaga deve receber score baixo (<=4) sem elementos STAR claros",
        "quality_checks": {
            "score_min": 0.0,
            "score_max": 4.0,
            "check_feedback_portuguese": True,
        },
        "star_elements_expected": [],
    },
    {
        "id": "wsi_003",
        "agent": "wsi",
        "name": "WSI — Resposta parcial STAR (deve score 4-7)",
        "endpoint": "http://localhost:8000/api/v1/wsi/analyze-response",
        "method": "POST",
        "body": {
            "session_id": f"benchmark-wsi-{BENCHMARK_JOB_ID}",
            "question_id": "q-benchmark-001",
            "candidate_id": "candidate-benchmark-001",
            "job_vacancy_id": BENCHMARK_JOB_ID,
            "question_text": "Descreva uma situação em que você liderou um projeto complexo de dados",
            "response_text": ("Trabalhei num projeto de migração de dados onde precisávamos mover o banco da empresa. "
                "Fiz o ETL com Python e o projeto foi concluído com sucesso."),
            "competency": "lideranca_tecnica",
            "framework": "STAR",
        },
        "description": "Resposta parcial deve receber score médio (4-7) com alguns elementos STAR",
        "quality_checks": {
            "score_min": 4.0,
            "score_max": 7.0,
            "check_feedback_portuguese": True,
        },
        "star_elements_expected": ["tarefa", "acao"],
    },
    {
        "id": "wsi_004",
        "agent": "wsi",
        "name": "WSI — Resposta irrelevante/off-topic (deve score <= 3)",
        "endpoint": "http://localhost:8000/api/v1/wsi/analyze-response",
        "method": "POST",
        "body": {
            "session_id": f"benchmark-wsi-{BENCHMARK_JOB_ID}",
            "question_id": "q-benchmark-001",
            "candidate_id": "candidate-benchmark-001",
            "job_vacancy_id": BENCHMARK_JOB_ID,
            "question_text": "Descreva uma situação em que você liderou um projeto complexo de dados",
            "response_text": ("Eu gosto muito de trabalhar em equipe e sempre fui muito dedicado "
                "nos meus trabalhos anteriores."),
            "competency": "lideranca_tecnica",
            "framework": "STAR",
        },
        "description": "Resposta off-topic deve receber score muito baixo (<=3)",
        "quality_checks": {
            "score_min": 0.0,
            "score_max": 3.0,
            "check_feedback_portuguese": True,
        },
        "star_elements_expected": [],
    },

    # =========================================================================
    # 2. CV MATCHING
    # =========================================================================
    {
        "id": "cv_001",
        "agent": "cv_match",
        "name": "CV Match — Match forte (deve match_score > 80)",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "endpoint_fallback": "/api/lia/api/cv-match",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": (
                "Analise o match entre a vaga e o CV. "
                "Vaga: Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos. "
                "CV: 10 anos de experiência com Python, Apache Spark, AWS Glue, Redshift, ETL, SQL avançado."
            ),
            "context_type": "cv_match",
            "context_id": BENCHMARK_JOB_ID,
        },
        "body_fallback": {
            "job_description": "Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos",
            "cv_text": "10 anos de experiência com Python, Apache Spark, AWS Glue, Redshift, ETL, SQL avançado",
        },
        "description": "CV sênior Python/Spark vs vaga Python/Spark deve ter match alto (>80)",
        "quality_checks": {
            "match_score_min": 80.0,
            "match_score_max": 100.0,
            "check_matched_skills_present": True,
        },
    },
    {
        "id": "cv_002",
        "agent": "cv_match",
        "name": "CV Match — Match fraco (deve match_score < 30)",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "endpoint_fallback": "/api/lia/api/cv-match",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": (
                "Analise o match entre a vaga e o CV. "
                "Vaga: Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos. "
                "CV: UX Designer com 8 anos em Figma, pesquisa de usuário, prototipagem, design system."
            ),
            "context_type": "cv_match",
            "context_id": BENCHMARK_JOB_ID,
        },
        "body_fallback": {
            "job_description": "Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos",
            "cv_text": "UX Designer com 8 anos em Figma, pesquisa de usuário, prototipagem, design system",
        },
        "description": "CV de designer vs vaga de dados deve ter match baixo (<30)",
        "quality_checks": {
            "match_score_min": 0.0,
            "match_score_max": 30.0,
            "check_missing_skills_present": True,
        },
    },
    {
        "id": "cv_003",
        "agent": "cv_match",
        "name": "CV Match — Match parcial (deve match_score 40-70)",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "endpoint_fallback": "/api/lia/api/cv-match",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": (
                "Analise o match entre a vaga e o CV. "
                "Vaga: Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos. "
                "CV: 2 anos Python, conhecimento básico de SQL, experiência com pandas."
            ),
            "context_type": "cv_match",
            "context_id": BENCHMARK_JOB_ID,
        },
        "body_fallback": {
            "job_description": "Engenheiro de Dados Sênior - Python, Spark, AWS, 5+ anos",
            "cv_text": "2 anos Python, conhecimento básico de SQL, experiência com pandas",
        },
        "description": "CV júnior Python vs vaga sênior deve ter match médio (40-70)",
        "quality_checks": {
            "match_score_min": 40.0,
            "match_score_max": 70.0,
        },
    },

    # =========================================================================
    # 3. SALARY BENCHMARK
    # =========================================================================
    {
        "id": "salary_001",
        "agent": "salary",
        "name": "Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k)",
        "endpoint": "/api/backend-proxy/lia/conversational/",
        "method": "POST",
        "body": {
            "message": (
                "Qual a faixa salarial para Engenheiro de Dados Sênior em São Paulo, "
                "trabalho remoto?"
            ),
            "mode": "salary_benchmark",
        },
        "description": "Consulta de salário senior deve retornar faixa BRL plausível (R$ 12.000-25.000)",
        "quality_checks": {
            "brl_values_count_min": 1,
            "brl_min_expected": 8000.0,
            "brl_max_expected": 35000.0,
            "check_response_portuguese": True,
        },
    },
    {
        "id": "salary_002",
        "agent": "salary",
        "name": "Salary — Analista de Dados Júnior BH (R$ 3k-6k)",
        "endpoint": "/api/backend-proxy/lia/conversational/",
        "method": "POST",
        "body": {
            "message": (
                "Qual a faixa salarial para Analista de Dados Júnior em Belo Horizonte, "
                "presencial?"
            ),
            "mode": "salary_benchmark",
        },
        "description": "Consulta júnior deve retornar faixa menor que sênior (R$ 3.000-6.000)",
        "quality_checks": {
            "brl_values_count_min": 1,
            "brl_min_expected": 1500.0,
            "brl_max_expected": 10000.0,
            "brl_max_ceiling": 12000.0,  # valores devem ser menores que senior
            "check_response_portuguese": True,
        },
    },

    # =========================================================================
    # 4. PIPELINE ANALYSIS
    # =========================================================================
    {
        "id": "pipeline_001",
        "agent": "pipeline",
        "name": "Pipeline — Saúde geral do funil",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": "Analise a saúde geral do nosso funil de recrutamento",
            "context_type": "pipeline_analysis",
        },
        "description": "Análise de saúde deve mencionar etapas do pipeline e identificar gargalos",
        "quality_checks": {
            "check_pipeline_stages": True,
            "check_response_portuguese": True,
            "min_length": 30,
        },
    },
    {
        "id": "pipeline_002",
        "agent": "pipeline",
        "name": "Pipeline — Tempo médio de contratação tech",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": "Qual é o tempo médio de contratação nas nossas vagas de tecnologia?",
            "context_type": "pipeline_analysis",
        },
        "description": "Consulta de time-to-hire deve mencionar métricas de tempo e sugestões",
        "quality_checks": {
            "check_pipeline_stages": True,
            "check_response_portuguese": True,
            "min_length": 30,
        },
    },

    # =========================================================================
    # 5. CANDIDATE SEARCH
    # =========================================================================
    {
        "id": "search_001",
        "agent": "candidate_search",
        "name": "Candidate Search — Engenheiro Python Sênior",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": "Busque candidatos com perfil de Engenheiro Python Sênior com experiência em AWS",
            "context_type": "candidate_search",
        },
        "description": "Busca de candidatos deve retornar lista ou indicação de candidatos relevantes",
        "quality_checks": {
            "check_response_portuguese": True,
            "min_length": 20,
        },
    },
    {
        "id": "search_002",
        "agent": "candidate_search",
        "name": "Candidate Search — Product Manager",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": BENCHMARK_USER_ID,
            "message": "Encontre candidatos para Product Manager com experiência em metodologias ágeis",
            "context_type": "candidate_search",
        },
        "description": "Busca PM deve retornar candidatos ou diagnóstico útil",
        "quality_checks": {
            "check_response_portuguese": True,
            "min_length": 20,
        },
    },
]

# ---------------------------------------------------------------------------
# AVALIAÇÃO DE QUALIDADE POR AGENTE
# ---------------------------------------------------------------------------


def evaluate_wsi_response(
    case: dict, data: Any, response_text: str, verbose: bool = False
) -> tuple:
    """
    Evaluate a WSI scoring response. Returns (score_0_100, issues, details).
    """
    issues = []
    details = {}
    score = 0

    checks = case.get("quality_checks", {})

    # Extrai campos esperados da resposta
    score_val = None
    feedback = ""
    star_completeness = None

    if isinstance(data, dict):
        # Tenta extrair score
        for key in ["score", "wsi_score", "total_score", "evaluation_score"]:
            if key in data and data[key] is not None:
                try:
                    score_val = float(data[key])
                except (ValueError, TypeError):
                    pass
                break

        # Tenta extrair feedback
        for key in ["feedback", "comments", "evaluation", "avaliacao", "observacoes"]:
            if key in data and data[key]:
                feedback = str(data[key])
                break

        # Tenta extrair star_completeness
        for key in ["star_completeness", "star_score", "completeness"]:
            if key in data and data[key] is not None:
                try:
                    star_completeness = float(data[key])
                except (ValueError, TypeError):
                    pass
                break

    details["score_raw"] = score_val
    details["star_completeness_raw"] = star_completeness
    details["feedback_snippet"] = feedback[:120] if feedback else ""

    # --- Validação do score ---
    if score_val is None:
        issues.append("Campo 'score' ausente ou não numérico na resposta")
    else:
        if not (0.0 <= score_val <= 10.0):
            issues.append(f"Score {score_val} fora do intervalo 0-10")
        else:
            score += 30  # score presente e válido

        score_min = checks.get("score_min", 0.0)
        score_max = checks.get("score_max", 10.0)
        if score_min <= score_val <= score_max:
            score += 40  # score dentro do intervalo esperado
            details["score_range_ok"] = True
        else:
            issues.append(
                f"Score {score_val:.1f} fora do intervalo esperado [{score_min}, {score_max}]"
            )
            details["score_range_ok"] = False

    # --- Validação do star_completeness ---
    star_min = checks.get("star_completeness_min")
    if star_min is not None:
        if star_completeness is None:
            issues.append("Campo 'star_completeness' ausente")
        elif star_completeness < star_min:
            issues.append(
                f"star_completeness {star_completeness:.2f} abaixo do mínimo {star_min}"
            )
        else:
            score += 15
            details["star_completeness_ok"] = True

    # --- Validação do feedback em português ---
    if checks.get("check_feedback_portuguese"):
        text_to_check = feedback or response_text
        if contains_portuguese(text_to_check):
            score += 15
            details["feedback_portuguese"] = True
        else:
            issues.append("Feedback não parece estar em português")
            details["feedback_portuguese"] = False

    return min(score, 100), issues, details


def evaluate_cv_match_response(
    case: dict, data: Any, response_text: str, verbose: bool = False
) -> tuple:
    """
    Evaluate a CV matching response. Returns (score_0_100, issues, details).
    """
    issues = []
    details = {}
    score = 0

    checks = case.get("quality_checks", {})

    match_score = None
    matched_skills = []
    missing_skills = []

    if isinstance(data, dict):
        for key in ["match_score", "score", "compatibility_score", "similarity"]:
            if key in data and data[key] is not None:
                try:
                    match_score = float(data[key])
                except (ValueError, TypeError):
                    pass
                break

        for key in ["matched_skills", "matching_skills", "skills_match", "skills"]:
            if key in data and isinstance(data[key], list):
                matched_skills = data[key]
                break

        for key in ["missing_skills", "gaps", "skill_gaps", "unmatched_skills"]:
            if key in data and isinstance(data[key], list):
                missing_skills = data[key]
                break

        # Se não encontrou score diretamente, tenta dentro de sub-dicts
        if match_score is None:
            for subkey in data:
                if isinstance(data[subkey], dict):
                    for k in ["match_score", "score", "compatibility"]:
                        if k in data[subkey]:
                            try:
                                match_score = float(data[subkey][k])
                            except (ValueError, TypeError):
                                pass

    # Se ainda não encontrou, tenta extrair do texto
    if match_score is None and response_text:
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", response_text)
        if pct_match:
            match_score = float(pct_match.group(1))

    details["match_score_raw"] = match_score
    details["matched_skills_count"] = len(matched_skills)
    details["missing_skills_count"] = len(missing_skills)

    # --- Validação do match_score ---
    if match_score is None:
        issues.append("Campo 'match_score' ausente ou não numérico")
    else:
        if not (0.0 <= match_score <= 100.0):
            issues.append(f"match_score {match_score} fora do intervalo 0-100")
        else:
            score += 30

        score_min = checks.get("match_score_min", 0.0)
        score_max = checks.get("match_score_max", 100.0)
        if score_min <= match_score <= score_max:
            score += 40
            details["score_range_ok"] = True
        else:
            issues.append(
                f"match_score {match_score:.1f} fora do intervalo esperado [{score_min}, {score_max}]"
            )
            details["score_range_ok"] = False

    # --- Validação de listas de habilidades ---
    if checks.get("check_matched_skills_present"):
        if matched_skills:
            score += 15
            details["matched_skills_present"] = True
        else:
            issues.append("Lista 'matched_skills' ausente ou vazia")
            details["matched_skills_present"] = False

    if checks.get("check_missing_skills_present"):
        if missing_skills:
            score += 15
            details["missing_skills_present"] = True
        else:
            issues.append("Lista 'missing_skills' ausente ou vazia")
            details["missing_skills_present"] = False

    # Bônus por ter pelo menos uma lista de skills
    if not checks.get("check_matched_skills_present") and not checks.get("check_missing_skills_present"):
        if matched_skills or missing_skills:
            score += 15

    return min(score, 100), issues, details


def evaluate_salary_response(
    case: dict, data: Any, response_text: str, verbose: bool = False
) -> tuple:
    """
    Evaluate a salary benchmark response. Returns (score_0_100, issues, details).
    """
    issues = []
    details = {}
    score = 0

    checks = case.get("quality_checks", {})

    # Extrai texto da resposta
    text = response_text
    if isinstance(data, dict):
        for key in ["response", "message", "content", "salary_range", "result"]:
            if key in data and data[key]:
                text = str(data[key])
                break

    brl_values = extract_brl_values(text)
    details["brl_values_found"] = brl_values

    min_count = checks.get("brl_values_count_min", 1)
    if len(brl_values) >= min_count:
        score += 40
        details["brl_values_ok"] = True
    else:
        issues.append(
            f"Esperado >= {min_count} valor(es) BRL na resposta, encontrado {len(brl_values)}"
        )
        details["brl_values_ok"] = False

    # Verifica se os valores são plausíveis para o mercado brasileiro
    brl_min = checks.get("brl_min_expected", 1000.0)
    brl_max = checks.get("brl_max_expected", 50000.0)
    brl_ceiling = checks.get("brl_max_ceiling")

    if brl_values:
        plausible = [v for v in brl_values if brl_min <= v <= brl_max]
        if plausible:
            score += 30
            details["brl_plausible"] = True
            details["brl_plausible_values"] = plausible
        else:
            issues.append(
                f"Valores BRL {brl_values} fora do range plausível [{brl_min:.0f}, {brl_max:.0f}]"
            )
            details["brl_plausible"] = False

        if brl_ceiling is not None:
            above_ceiling = [v for v in brl_values if v > brl_ceiling]
            if above_ceiling:
                issues.append(
                    f"Valores {above_ceiling} acima do teto esperado {brl_ceiling:.0f} "
                    f"(resposta de júnior não deve superar sênior)"
                )
            else:
                score += 10

    # Verifica português
    if checks.get("check_response_portuguese"):
        if contains_portuguese(text):
            score += 20
            details["portuguese_ok"] = True
        else:
            issues.append("Resposta não parece estar em português")
            details["portuguese_ok"] = False

    return min(score, 100), issues, details


def evaluate_pipeline_response(
    case: dict, data: Any, response_text: str, verbose: bool = False
) -> tuple:
    """
    Evaluate a pipeline analysis response. Returns (score_0_100, issues, details).
    """
    issues = []
    details = {}
    score = 0

    checks = case.get("quality_checks", {})

    text = response_text
    if isinstance(data, dict):
        for key in ["message", "response", "content", "analysis", "result"]:
            if key in data and data[key]:
                text = str(data[key])
                break

    min_length = checks.get("min_length", 20)
    details["response_length"] = len(text)

    if len(text) >= min_length:
        score += 20
        details["length_ok"] = True
    else:
        issues.append(f"Resposta muito curta ({len(text)} chars), esperado >= {min_length}")
        details["length_ok"] = False

    if checks.get("check_pipeline_stages"):
        if mentions_pipeline_stages(text):
            score += 50
            details["pipeline_stages_mentioned"] = True
        else:
            issues.append("Resposta não menciona etapas do pipeline (triagem, entrevista, oferta, etc.)")
            details["pipeline_stages_mentioned"] = False

    if checks.get("check_response_portuguese"):
        if contains_portuguese(text):
            score += 30
            details["portuguese_ok"] = True
        else:
            issues.append("Resposta não parece estar em português")
            details["portuguese_ok"] = False

    return min(score, 100), issues, details


def evaluate_candidate_search_response(
    case: dict, data: Any, response_text: str, verbose: bool = False
) -> tuple:
    """
    Evaluate a candidate search response. Returns (score_0_100, issues, details).
    """
    issues = []
    details = {}
    score = 0

    checks = case.get("quality_checks", {})

    text = response_text
    if isinstance(data, dict):
        for key in ["message", "response", "content", "candidates", "result"]:
            if key in data and data[key]:
                if isinstance(data[key], list):
                    text = json.dumps(data[key], ensure_ascii=False)
                else:
                    text = str(data[key])
                break

    min_length = checks.get("min_length", 20)
    details["response_length"] = len(text)

    if len(text) >= min_length:
        score += 40
        details["length_ok"] = True
    else:
        issues.append(f"Resposta muito curta ({len(text)} chars), esperado >= {min_length}")

    if checks.get("check_response_portuguese"):
        if contains_portuguese(text):
            score += 30
            details["portuguese_ok"] = True
        else:
            issues.append("Resposta não parece estar em português")
            details["portuguese_ok"] = False

    # Bônus se mencionar candidatos, perfis ou habilidades
    candidate_words = ["candidato", "perfil", "habilidade", "experiência", "encontr", "result"]
    lower = text.lower()
    if any(w in lower for w in candidate_words):
        score += 30
        details["candidate_content_ok"] = True
    else:
        issues.append("Resposta não menciona candidatos ou perfis relevantes")

    return min(score, 100), issues, details


EVALUATORS = {
    "wsi": evaluate_wsi_response,
    "cv_match": evaluate_cv_match_response,
    "salary": evaluate_salary_response,
    "pipeline": evaluate_pipeline_response,
    "candidate_search": evaluate_candidate_search_response,
}

# ---------------------------------------------------------------------------
# HTTP CLIENT — async httpx + fallback sync requests
# ---------------------------------------------------------------------------


async def post_async(url: str, payload: dict, headers: dict, timeout: int) -> tuple:
    """POST via httpx (async). Returns (status_code, data_dict, elapsed_ms)."""
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
    elapsed = (time.monotonic() - start) * 1000
    try:
        data = resp.json()
    except Exception:
        data = {"_raw": resp.text}
    return resp.status_code, data, elapsed


def post_sync(url: str, payload: dict, headers: dict, timeout: int) -> tuple:
    """POST via requests (sync). Returns (status_code, data_dict, elapsed_ms)."""
    import requests as req_lib
    start = time.monotonic()
    resp = req_lib.post(url, json=payload, headers=headers, timeout=timeout)
    elapsed = (time.monotonic() - start) * 1000
    try:
        data = resp.json()
    except Exception:
        data = {"_raw": resp.text}
    return resp.status_code, data, elapsed


async def call_endpoint(
    base_url: str,
    endpoint: str,
    payload: dict,
    headers: dict,
    timeout: int,
    fallback_endpoint: str = None,
    fallback_payload: dict = None,
) -> tuple:
    """
    Call endpoint (primary, then optional fallback). Returns (status, data, elapsed_ms, used_endpoint).
    """
    # Support absolute endpoint URLs (e.g., for direct backend access)
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url = endpoint
    else:
        url = base_url.rstrip("/") + endpoint
    try:
        if HAS_HTTPX:
            status, data, elapsed = await post_async(url, payload, headers, timeout)
        else:
            status, data, elapsed = post_sync(url, payload, headers, timeout)
    except Exception as exc:
        if fallback_endpoint:
            fallback_url = fallback_endpoint if fallback_endpoint.startswith("http") else base_url.rstrip("/") + fallback_endpoint
            fb_payload = fallback_payload or payload
            try:
                if HAS_HTTPX:
                    status, data, elapsed = await post_async(
                        fallback_url, fb_payload, headers, timeout
                    )
                else:
                    status, data, elapsed = post_sync(
                        fallback_url, fb_payload, headers, timeout
                    )
                return status, data, elapsed, fallback_endpoint
            except Exception as exc2:
                return 0, {"error": str(exc2)}, 0, fallback_endpoint
        return 0, {"error": str(exc)}, 0, endpoint

    # Se primário retornou 4xx/5xx e há fallback, tenta fallback
    if status >= 400 and fallback_endpoint:
        fallback_url = fallback_endpoint if fallback_endpoint.startswith("http") else base_url.rstrip("/") + fallback_endpoint
        fb_payload = fallback_payload or payload
        try:
            if HAS_HTTPX:
                status2, data2, elapsed2 = await post_async(
                    fallback_url, fb_payload, headers, timeout
                )
            else:
                status2, data2, elapsed2 = post_sync(
                    fallback_url, fb_payload, headers, timeout
                )
            if status2 < 400:
                return status2, data2, elapsed2, fallback_endpoint
        except Exception:
            pass  # mantém resultado primário

    return status, data, elapsed, endpoint


# ---------------------------------------------------------------------------
# EXECUÇÃO DE UM CASO DE TESTE
# ---------------------------------------------------------------------------


async def run_case(
    case: dict,
    base_url: str,
    headers: dict,
    timeout: int,
    verbose: bool = False,
) -> dict:
    """Run a single benchmark test case. Returns a result dict."""
    agent = case["agent"]
    evaluator = EVALUATORS.get(agent)

    status, data, elapsed_ms, used_endpoint = await call_endpoint(
        base_url=base_url,
        endpoint=case["endpoint"],
        payload=case["body"],
        headers=headers,
        timeout=timeout,
        fallback_endpoint=case.get("endpoint_fallback"),
        fallback_payload=case.get("body_fallback"),
    )

    # Extrai texto legível da resposta
    response_text = get_text_from_response(
        data,
        [
            "message", "response", "content", "result",
            "message.content", "data.response", "data.message",
        ],
    )
    if not response_text and isinstance(data, dict):
        response_text = json.dumps(data, ensure_ascii=False)

    # Avalia qualidade
    if status == 0:
        quality_score = 0
        issues = [f"Falha de conexão: {data.get('error', 'desconhecido')}"]
        details = {}
        passed = False
    elif status >= 400:
        quality_score = 0
        issues = [f"HTTP {status}: {response_text[:200]}"]
        details = {}
        passed = False
    elif evaluator:
        quality_score, issues, details = evaluator(case, data, response_text, verbose)
        passed = quality_score >= 60 and len([i for i in issues if "fora do intervalo esperado" in i or "ausente" in i or "não parece" in i or "curta" in i or "não menciona" in i]) == 0
    else:
        quality_score = 50
        issues = ["Sem avaliador específico para este agente"]
        details = {}
        passed = True

    return {
        "id": case["id"],
        "agent": agent,
        "name": case["name"],
        "endpoint": used_endpoint,
        "http_status": status,
        "elapsed_ms": round(elapsed_ms, 1),
        "quality_score": quality_score,
        "passed": passed,
        "issues": issues,
        "details": details,
        "response_snippet": response_text[:300] if response_text else "",
        "response_raw": data,
        "description": case.get("description", ""),
    }


# ---------------------------------------------------------------------------
# DRY-RUN
# ---------------------------------------------------------------------------


def dry_run(cases: list, base_url: str) -> None:
    """Print all endpoints and payloads without calling them."""
    print(f"\n{'=' * 70}")
    print(f"  DRY-RUN — benchmark_agents.py")
    print(f"  Base URL: {base_url}")
    print(f"  Total de casos: {len(cases)}")
    print(f"{'=' * 70}\n")

    agents_seen = set()
    for case in cases:
        agent = case["agent"]
        if agent not in agents_seen:
            print(f"\n{'─' * 60}")
            print(f"  AGENTE: {agent.upper()}")
            print(f"{'─' * 60}")
            agents_seen.add(agent)

        url = base_url.rstrip("/") + case["endpoint"]
        print(f"\n[{case['id']}] {case['name']}")
        print(f"  URL     : POST {url}")
        if case.get("endpoint_fallback"):
            fallback_url = base_url.rstrip("/") + case["endpoint_fallback"]
            print(f"  FALLBACK: POST {fallback_url}")
        print(f"  Payload :")
        payload_str = json.dumps(case["body"], ensure_ascii=False, indent=4)
        for line in payload_str.splitlines():
            print(f"    {line}")
        checks = case.get("quality_checks", {})
        if checks:
            print(f"  Checks  : {json.dumps(checks, ensure_ascii=False)}")
        print(f"  Desc    : {case.get('description', '')}")


# ---------------------------------------------------------------------------
# EXPORTAÇÃO
# ---------------------------------------------------------------------------


def export_results(
    results: list,
    output_dir: str,
    timestamp: str,
    base_url: str,
    agent_filter: Optional[str],
) -> dict:
    """Export results to CSV, JSON and Markdown. Returns paths dict."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    base_name = f"agents_benchmark_{timestamp}"
    json_path = out / f"{base_name}.json"
    csv_path = out / f"{base_name}.csv"
    md_path = out / f"{base_name}.md"

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    avg_quality = sum(r["quality_score"] for r in results) / total if total else 0
    avg_elapsed = sum(r["elapsed_ms"] for r in results) / total if total else 0

    # --- JSON ---
    json_data = {
        "benchmark": "benchmark_agents.py",
        "timestamp": timestamp,
        "base_url": base_url,
        "agent_filter": agent_filter,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "avg_quality_score": round(avg_quality, 1),
            "avg_elapsed_ms": round(avg_elapsed, 1),
        },
        "results": results,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)

    # --- CSV ---
    fieldnames = [
        "id", "agent", "name", "endpoint", "http_status",
        "elapsed_ms", "quality_score", "passed", "issues", "description",
        "response_snippet",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["issues"] = " | ".join(r.get("issues", []))
            writer.writerow(row)

    # --- Markdown ---
    lines = [
        f"# Benchmark de Agentes de Processo — Plataforma LIA",
        f"",
        f"**Gerado em:** {timestamp}  ",
        f"**Base URL:** `{base_url}`  ",
        f"**Agente filtrado:** `{agent_filter or 'todos'}`  ",
        f"",
        f"## Resumo",
        f"",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Total de casos | {total} |",
        f"| Aprovados | {passed} |",
        f"| Reprovados | {failed} |",
        f"| Score médio | {avg_quality:.1f}/100 |",
        f"| Latência média | {avg_elapsed:.0f}ms |",
        f"",
        f"## Resultados por Caso",
        f"",
    ]

    agent_groups: dict = {}
    for r in results:
        agent_groups.setdefault(r["agent"], []).append(r)

    for agent, agent_results in agent_groups.items():
        lines.append(f"### Agente: `{agent.upper()}`")
        lines.append("")
        lines.append("| ID | Nome | Status | Score | Latência | Issues |")
        lines.append("|----|------|--------|-------|----------|--------|")
        for r in agent_results:
            status_icon = "✅" if r["passed"] else "❌"
            issues_str = "; ".join(r["issues"]) if r["issues"] else "—"
            lines.append(
                f"| {r['id']} | {r['name']} | {status_icon} HTTP {r['http_status']} "
                f"| {r['quality_score']}/100 | {r['elapsed_ms']}ms | {issues_str} |"
            )
        lines.append("")

    lines += [
        "## Detalhes dos Casos Reprovados",
        "",
    ]
    failed_cases = [r for r in results if not r["passed"]]
    if not failed_cases:
        lines.append("_Nenhum caso reprovado._")
    else:
        for r in failed_cases:
            lines.append(f"### {r['id']} — {r['name']}")
            lines.append(f"- **Agente:** {r['agent']}")
            lines.append(f"- **Endpoint:** `{r['endpoint']}`")
            lines.append(f"- **HTTP Status:** {r['http_status']}")
            lines.append(f"- **Score:** {r['quality_score']}/100")
            lines.append(f"- **Issues:**")
            for issue in r.get("issues", []):
                lines.append(f"  - {issue}")
            if r.get("response_snippet"):
                lines.append(f"- **Resposta (trecho):**")
                lines.append(f"  ```")
                lines.append(f"  {r['response_snippet'][:200]}")
                lines.append(f"  ```")
            lines.append("")

    lines += [
        "---",
        "",
        f"_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  ",
        f"_Para testar componentes de chat/UI, use `benchmark_prompts.py`._",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "markdown": str(md_path),
    }


# ---------------------------------------------------------------------------
# TERMINAL OUTPUT
# ---------------------------------------------------------------------------


def color(text: str, code: str) -> str:
    """Wrap text in ANSI color code."""
    return f"\033[{code}m{text}\033[0m"


def print_result(result: dict, verbose: bool = False) -> None:
    """Print a single test result to terminal."""
    passed = result["passed"]
    icon = "✅" if passed else "❌"
    score_color = "32" if result["quality_score"] >= 80 else ("33" if result["quality_score"] >= 50 else "31")

    print(
        f"  {icon} [{result['id']}] {result['name']}"
        f"  {color(str(result['quality_score']) + '/100', score_color)}"
        f"  HTTP {result['http_status']}"
        f"  {result['elapsed_ms']}ms"
    )

    if result["issues"]:
        for issue in result["issues"]:
            print(f"       ⚠️  {color(issue, '33')}")

    if verbose and result.get("details"):
        print(f"       📊 {result['details']}")
        if result.get("response_snippet"):
            snippet = result["response_snippet"][:150].replace("\n", " ")
            print(f"       💬 {color(snippet, '36')}")


def print_summary(results: list, paths: dict) -> None:
    """Print final summary to terminal."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    avg_quality = sum(r["quality_score"] for r in results) / total if total else 0
    avg_elapsed = sum(r["elapsed_ms"] for r in results) / total if total else 0

    print(f"\n{'=' * 60}")
    print(f"  RESUMO FINAL — Benchmark Agentes de Processo")
    print(f"{'=' * 60}")
    print(f"  Total de casos : {total}")
    print(f"  ✅ Aprovados   : {color(str(passed), '32')}")
    print(f"  ❌ Reprovados  : {color(str(failed), '31' if failed > 0 else '32')}")
    print(f"  Score médio    : {color(f'{avg_quality:.1f}/100', '32' if avg_quality >= 70 else '33')}")
    print(f"  Latência média : {avg_elapsed:.0f}ms")
    print(f"\n  Arquivos gerados:")
    for fmt, path in paths.items():
        print(f"    {fmt.upper():8s} → {path}")
    print(f"{'=' * 60}\n")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark de Agentes de Processo de IA — Plataforma LIA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Agentes disponíveis:
  wsi              WSI Scoring (avalia respostas de candidatos STAR)
  cv_match         CV Matching (compatibilidade CV x vaga)
  salary           Salary Benchmark (faixas salariais BRL)
  pipeline         Pipeline Analysis (análise do funil de recrutamento)
  candidate_search Candidate Search (busca de candidatos)

Exemplos:
  python benchmark_agents.py --base-url http://localhost:3000 --token abc123
  python benchmark_agents.py --agent wsi --base-url http://localhost:3000 --token abc123
  python benchmark_agents.py --dry-run
  LIA_TOKEN=abc123 python benchmark_agents.py --base-url http://localhost:3000
        """,
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL base da API (padrão: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("LIA_TOKEN", ""),
        help="Token de autenticação Bearer (ou defina LIA_TOKEN no ambiente)",
    )
    parser.add_argument(
        "--agent",
        choices=["wsi", "cv_match", "salary", "pipeline", "candidate_search"],
        default=None,
        help="Filtrar por agente específico (padrão: todos)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Diretório de saída para os relatórios (padrão: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibir detalhes extras de cada caso (payload, resposta bruta)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Imprime endpoints e payloads sem chamar a API",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout em segundos por requisição (padrão: {DEFAULT_TIMEOUT})",
    )
    return parser.parse_args()


async def main_async(args: argparse.Namespace) -> int:
    # Filtra casos por agente, se solicitado
    cases = GOLDEN_CASES
    if args.agent:
        cases = [c for c in cases if c["agent"] == args.agent]
        if not cases:
            print(f"❌ Nenhum caso encontrado para o agente '{args.agent}'")
            return 1

    if args.dry_run:
        dry_run(cases, args.base_url)
        return 0

    # Valida token
    token = args.token
    if not token:
        print("⚠️  Aviso: nenhum token fornecido. Requisições podem falhar com 401.")
        print("   Use --token SEU_TOKEN ou defina a variável LIA_TOKEN.")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'=' * 60}")
    print(f"  benchmark_agents.py — Agentes de Processo de IA")
    print(f"  Base URL : {args.base_url}")
    print(f"  Agente   : {args.agent or 'todos'}")
    print(f"  Casos    : {len(cases)}")
    print(f"  Timeout  : {args.timeout}s")
    print(f"{'=' * 60}\n")

    results = []
    current_agent = None

    for case in cases:
        if case["agent"] != current_agent:
            current_agent = case["agent"]
            print(f"\n  {'─' * 50}")
            print(f"  Agente: {color(current_agent.upper(), '34;1')}")
            print(f"  {'─' * 50}")

        result = await run_case(
            case=case,
            base_url=args.base_url,
            headers=headers,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        results.append(result)
        print_result(result, verbose=args.verbose)

    print()

    # Exporta resultados
    paths = export_results(
        results=results,
        output_dir=args.output,
        timestamp=timestamp,
        base_url=args.base_url,
        agent_filter=args.agent,
    )

    print_summary(results, paths)

    # Exit code 1 se qualquer caso falhou
    return 1 if any(not r["passed"] for r in results) else 0


def main() -> None:
    args = parse_args()

    if HAS_HTTPX:
        exit_code = asyncio.run(main_async(args))
    else:
        # Fallback síncrono — cria event loop manual
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            exit_code = loop.run_until_complete(main_async(args))
        finally:
            loop.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
