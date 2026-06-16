#!/usr/bin/env python3
"""
benchmark_prompts.py — Benchmark de Qualidade dos Prompts de IA
Plataforma LIA — plataforma-lia

Testa a qualidade das respostas da IA chamando os endpoints reais da API
e gera relatórios detalhados em CSV, JSON e Markdown.

Uso:
  python benchmark_prompts.py --base-url http://localhost:3000 --token SEU_TOKEN
  python benchmark_prompts.py --base-url https://app.wedotalent.com --token SEU_TOKEN --output results/
  python benchmark_prompts.py --component wizard --base-url http://localhost:3000 --token SEU_TOKEN
  python benchmark_prompts.py --dry-run

Saída:
  benchmark_results_YYYYMMDD_HHMMSS.json  — resultados completos com respostas brutas
  benchmark_results_YYYYMMDD_HHMMSS.csv   — planilha para análise no Excel/Sheets
  benchmark_summary_YYYYMMDD_HHMMSS.md    — relatório legível em Markdown
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
DEFAULT_TIMEOUT = 30  # segundos
DEFAULT_OUTPUT_DIR = "."

# Palavras-chave em português para detectar idioma
PORTUGUESE_KEYWORDS = [
    "candidato", "vaga", "processo", "seletivo", "entrevista", "empresa",
    "perfil", "experiência", "habilidade", "competência", "recrutamento",
    "contratação", "currículo", "triagem", "pipeline", "etapa", "feedback",
    "aprovado", "reprovado", "engenheiro", "desenvolvedor", "plataforma",
    "como", "que", "para", "com", "uma", "você", "não", "mais", "está",
    "são", "ser", "ter", "por", "isso", "mas", "bem", "olá", "sim", "não",
    "posso", "ajudar", "entendo", "claro", "aqui", "também", "sobre",
]

# Palavras relacionadas a recrutamento
RECRUITMENT_KEYWORDS = [
    "candidato", "vaga", "recrutamento", "seleção", "entrevista", "currículo",
    "processo seletivo", "contratação", "pipeline", "triagem", "job", "hiring",
    "candidate", "position", "recruitment", "selection", "screening", "onboarding",
    "engenheiro", "desenvolvedor", "analista", "gerente", "product manager",
    "empresa", "equipe", "time", "profissional", "experiência", "habilidade",
    "silver medalist", "feedback", "etapa", "aprovado", "reprovado", "wizard",
    "plataforma", "lia", "wedotalent",
]

# ---------------------------------------------------------------------------
# GOLDEN PROMPTS — Casos de teste por componente
# ---------------------------------------------------------------------------

GOLDEN_PROMPTS = [
    # -------------------------------------------------------------------------
    # 1. LIA FLOAT / GENERAL CHAT
    # -------------------------------------------------------------------------
    {
        "id": "chat_001",
        "component": "chat",
        "name": "Consulta candidatos triagem",
        "endpoint": "/api/backend-proxy/chat/",
        "method": "POST",
        "body": {
            "content": "Quantos candidatos estão no estágio de triagem essa semana?",
            "conversation_id": None,
            "user_id": "benchmark_user",
        },
        "response_path": ["message", "content"],  # caminho para extrair texto da resposta
        "expected_keywords": ["candidato", "triagem", "semana", "etapa", "pipeline"],
        "must_not_contain": ["error", "undefined", "null", "exception"],
        "min_length": 20,
        "description": "LIA deve entender consulta sobre candidatos na triagem",
    },
    {
        "id": "chat_002",
        "component": "chat",
        "name": "Pipeline travado",
        "endpoint": "/api/backend-proxy/chat/",
        "method": "POST",
        "body": {
            "content": "Quais vagas estão com pipeline travado há mais de 5 dias?",
            "conversation_id": None,
            "user_id": "benchmark_user",
        },
        "response_path": ["message", "content"],
        "expected_keywords": ["vaga", "pipeline", "dias", "candidato"],
        "must_not_contain": ["error", "undefined", "null"],
        "min_length": 20,
        "description": "LIA deve identificar vagas com pipeline parado",
    },
    {
        "id": "chat_003",
        "component": "chat",
        "name": "Relatório processos seletivos",
        "endpoint": "/api/backend-proxy/chat/",
        "method": "POST",
        "body": {
            "content": "Preciso de um relatório dos processos seletivos do mês passado",
            "conversation_id": None,
            "user_id": "benchmark_user",
        },
        "response_path": ["message", "content"],
        "expected_keywords": ["relatório", "processo", "seletivo", "mês"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 30,
        "description": "LIA deve entender pedido de relatório mensal",
    },
    {
        "id": "chat_004",
        "component": "chat",
        "name": "Candidatos vaga backend",
        "endpoint": "/api/backend-proxy/chat/",
        "method": "POST",
        "body": {
            "content": "Me mostra os candidatos que aplicaram para a vaga de backend",
            "conversation_id": None,
            "user_id": "benchmark_user",
        },
        "response_path": ["message", "content"],
        "expected_keywords": ["candidato", "vaga", "backend", "aplicar"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 20,
        "description": "LIA deve listar candidatos de uma vaga específica",
    },
    {
        "id": "chat_005",
        "component": "chat",
        "name": "Silver medalist Product Manager",
        "endpoint": "/api/backend-proxy/chat/",
        "method": "POST",
        "body": {
            "content": "Existe algum silver medalist para a vaga de Product Manager?",
            "conversation_id": None,
            "user_id": "benchmark_user",
        },
        "response_path": ["message", "content"],
        "expected_keywords": ["silver", "medalist", "candidato", "vaga", "product manager"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 20,
        "description": "LIA deve entender conceito de silver medalist",
    },

    # -------------------------------------------------------------------------
    # 2. ORCHESTRATOR / CONTEXT-AWARE
    # -------------------------------------------------------------------------
    {
        "id": "orch_001",
        "component": "orchestrator",
        "name": "Mover candidato próxima etapa",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": "benchmark_user",
            "message": "Mover o candidato João Silva para a próxima etapa",
            "context_type": "pipeline",
            "context_id": None,
        },
        "response_path": ["message"],  # ou pode ser response raiz
        "expected_keywords": ["candidato", "etapa", "mover", "pipeline", "joão", "silva"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Orquestrador deve entender ação de mover candidato no pipeline",
    },
    {
        "id": "orch_002",
        "component": "orchestrator",
        "name": "Agendar entrevista",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": "benchmark_user",
            "message": "Agendar entrevista para amanhã às 14h",
            "context_type": "pipeline",
            "context_id": None,
        },
        "response_path": ["message"],
        "expected_keywords": ["entrevista", "agenda", "amanhã", "14", "horário"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Orquestrador deve entender agendamento de entrevista",
    },
    {
        "id": "orch_003",
        "component": "orchestrator",
        "name": "Email feedback reprovados",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": "benchmark_user",
            "message": "Enviar email de feedback para os candidatos reprovados",
            "context_type": "pipeline",
            "context_id": None,
        },
        "response_path": ["message"],
        "expected_keywords": ["email", "feedback", "candidato", "reprovado", "enviar"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Orquestrador deve entender envio de emails em massa",
    },
    {
        "id": "orch_004",
        "component": "orchestrator",
        "name": "Criar vaga engenheiro dados",
        "endpoint": "/api/backend-proxy/orchestrator/process/",
        "method": "POST",
        "body": {
            "user_id": "benchmark_user",
            "message": "Criar uma nova vaga para engenheiro de dados sênior",
            "context_type": "general",
            "context_id": None,
        },
        "response_path": ["message"],
        "expected_keywords": ["vaga", "engenheiro", "dados", "sênior", "criar"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Orquestrador deve iniciar fluxo de criação de vaga",
    },

    # -------------------------------------------------------------------------
    # 3. WIZARD / JOB CREATION
    # -------------------------------------------------------------------------
    {
        "id": "wizard_001",
        "component": "wizard",
        "name": "Wizard info básica Python fintech",
        "endpoint": "/api/backend-proxy/lia/job-wizard/interpret/",
        "method": "POST",
        "body": {
            "message": "Preciso de um engenheiro Python sênior, remoto, para fintech",
            "current_stage": "info_basica",
            "context": {},
        },
        "response_path": ["lia_response"],
        "expected_keywords": ["python", "sênior", "remoto", "fintech", "engenheiro"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Wizard deve interpretar info básica da vaga corretamente",
        "extra_checks": ["action", "confidence", "should_advance"],  # campos esperados na resposta
    },
    {
        "id": "wizard_002",
        "component": "wizard",
        "name": "Wizard requisitos Python Spark AWS",
        "endpoint": "/api/backend-proxy/lia/job-wizard/interpret/",
        "method": "POST",
        "body": {
            "message": "5 anos de experiência, Python e Spark obrigatórios, AWS desejável",
            "current_stage": "requisitos",
            "context": {},
        },
        "response_path": ["lia_response"],
        "expected_keywords": ["python", "spark", "aws", "experiência", "requisito"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Wizard deve extrair requisitos técnicos da vaga",
        "extra_checks": ["action", "confidence", "should_advance"],
    },
    {
        "id": "wizard_003",
        "component": "wizard",
        "name": "Wizard competências raciocínio equipe",
        "endpoint": "/api/backend-proxy/lia/job-wizard/interpret/",
        "method": "POST",
        "body": {
            "message": "Quero avaliar raciocínio lógico e trabalho em equipe",
            "current_stage": "competencias",
            "context": {},
        },
        "response_path": ["lia_response"],
        "expected_keywords": ["raciocínio", "equipe", "competência", "avaliar", "habilidade"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 10,
        "description": "Wizard deve capturar competências comportamentais",
        "extra_checks": ["action", "confidence", "should_advance"],
    },
    {
        "id": "wizard_004",
        "component": "wizard",
        "name": "Wizard revisão publicar vaga",
        "endpoint": "/api/backend-proxy/lia/job-wizard/interpret/",
        "method": "POST",
        "body": {
            "message": "Pode publicar a vaga",
            "current_stage": "revisao",
            "context": {},
        },
        "response_path": ["lia_response"],
        "expected_keywords": ["publicar", "vaga", "confirm", "ok", "publicada", "pronto"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 5,
        "description": "Wizard deve confirmar publicação da vaga na etapa de revisão",
        "extra_checks": ["action", "confidence", "should_advance"],
    },

    # -------------------------------------------------------------------------
    # 4. CONVERSATIONAL / LIA GENERAL
    # -------------------------------------------------------------------------
    {
        "id": "conv_001",
        "component": "conversational",
        "name": "Olá como funciona plataforma",
        "endpoint": "/api/backend-proxy/lia/conversational/",
        "method": "POST",
        "body": {
            "message": "Olá, como funciona a plataforma?",
            "context": None,
            "mode": None,
        },
        "response_path": ["response"],
        "expected_keywords": ["plataforma", "recrutamento", "ajudar", "vaga", "candidato", "funciona"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 30,
        "description": "LIA conversacional deve apresentar a plataforma",
        "extra_checks": ["understood_intent", "can_help"],
    },
    {
        "id": "conv_002",
        "component": "conversational",
        "name": "Quero criar nova vaga",
        "endpoint": "/api/backend-proxy/lia/conversational/",
        "method": "POST",
        "body": {
            "message": "Quero criar uma nova vaga",
            "context": None,
            "mode": None,
        },
        "response_path": ["response"],
        "expected_keywords": ["vaga", "criar", "wizard", "informação", "ajudar"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 20,
        "description": "LIA deve direcionar para criação de vaga",
        "extra_checks": ["understood_intent", "can_help"],
    },
    {
        "id": "conv_003",
        "component": "conversational",
        "name": "Ajuda processo seletivo",
        "endpoint": "/api/backend-proxy/lia/conversational/",
        "method": "POST",
        "body": {
            "message": "Preciso de ajuda com o processo seletivo",
            "context": None,
            "mode": None,
        },
        "response_path": ["response"],
        "expected_keywords": ["processo", "seletivo", "ajudar", "candidato", "etapa"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 20,
        "description": "LIA deve oferecer ajuda com processo seletivo",
        "extra_checks": ["understood_intent", "can_help"],
    },

    # -------------------------------------------------------------------------
    # 5. WSI / SCREENING QUESTIONS
    # -------------------------------------------------------------------------
    {
        "id": "wsi_001",
        "component": "wsi",
        "name": "Perguntas triagem Python Sênior",
        "endpoint": "/api/lia/api/wsi/generate-job-screening-questions/",
        "method": "POST",
        "body": {
            "job_title": "Engenheiro Python Sênior",
            "technical_skills": ["python", "django", "aws"],
            "seniority_level": "senior",
            "count": 5,
        },
        "response_path": ["questions"],  # lista de perguntas
        "expected_keywords": ["python", "django", "aws", "experiência", "desenvolveu", "arquitetura"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 50,  # total de caracteres das perguntas concatenadas
        "description": "WSI deve gerar perguntas de triagem técnicas para Python Sênior",
        "extra_checks": ["total_generated"],
    },
    {
        "id": "wsi_002",
        "component": "wsi",
        "name": "Perguntas triagem Product Manager",
        "endpoint": "/api/lia/api/wsi/generate-job-screening-questions/",
        "method": "POST",
        "body": {
            "job_title": "Product Manager",
            "technical_skills": [],
            "seniority_level": "pleno",
            "count": 5,
        },
        "response_path": ["questions"],
        "expected_keywords": ["produto", "roadmap", "stakeholder", "prioridade", "métrica", "produto", "manager"],
        "must_not_contain": ["error", "undefined"],
        "min_length": 50,
        "description": "WSI deve gerar perguntas de triagem para Product Manager",
        "extra_checks": ["total_generated"],
    },
]


# ---------------------------------------------------------------------------
# FUNÇÕES DE AVALIAÇÃO DE QUALIDADE
# ---------------------------------------------------------------------------

def extract_response_text(data: Any, path: list) -> str:
    """
    Extrai o texto da resposta seguindo o caminho de chaves fornecido.
    Se o caminho levar a uma lista, concatena todos os elementos.
    """
    if not data or not path:
        return ""

    current = data
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit():
            idx = int(key)
            current = current[idx] if idx < len(current) else None
        else:
            return ""
        if current is None:
            return ""

    # Se for lista (ex: questions), converte para string
    if isinstance(current, list):
        parts = []
        for item in current:
            if isinstance(item, dict):
                # Tenta extrair texto de campos comuns
                text = (
                    item.get("question") or item.get("text") or
                    item.get("content") or str(item)
                )
                parts.append(str(text))
            else:
                parts.append(str(item))
        return " | ".join(parts)

    return str(current) if current is not None else ""


def has_portuguese_content(text: str) -> bool:
    """
    Verifica se o texto contém palavras em português.
    Heurística simples: conta quantas palavras-chave PT-BR existem.
    """
    if not text:
        return False
    text_lower = text.lower()
    matches = sum(1 for kw in PORTUGUESE_KEYWORDS if kw in text_lower)
    return matches >= 2  # precisa de pelo menos 2 palavras PT


def is_recruitment_relevant(text: str) -> bool:
    """
    Verifica se a resposta menciona contexto de recrutamento/RH.
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in RECRUITMENT_KEYWORDS)


def has_hallucination_risk(prompt: str, response: str) -> bool:
    """
    Detecta risco de alucinação: resposta menciona números específicos ou
    nomes próprios que NÃO estavam no prompt original.

    Heurística: procura por números com contexto de dados concretos
    (ex: "23 candidatos", "R$ 5.000") que não vieram do prompt.
    """
    if not response:
        return False

    # Padrões suspeitos: números seguidos de substantivos de dados
    suspicious_patterns = [
        r"\b\d+\s+candidatos?\b",
        r"\b\d+\s+vagas?\b",
        r"\b\d+\s+dias?\b",
        r"\bR\$\s*[\d.,]+\b",
        r"\b\d{1,3}%\b",  # percentuais específicos
    ]

    # Verifica se os números no prompt justificam os números na resposta
    prompt_numbers = set(re.findall(r"\b\d+\b", prompt))
    response_lower = response.lower()

    for pattern in suspicious_patterns:
        matches = re.findall(pattern, response_lower)
        if matches:
            # Extrai números dos matches
            for match in matches:
                nums_in_match = set(re.findall(r"\b\d+\b", match))
                # Se há números na resposta que não estavam no prompt
                if nums_in_match - prompt_numbers:
                    return True

    return False


def evaluate_response(
    prompt_config: dict,
    raw_response: Any,
    response_text: str,
    latency_ms: int,
    error: Optional[str] = None,
    http_status: Optional[int] = None,
) -> dict:
    """
    Avalia a qualidade de uma resposta da IA.

    Retorna um dicionário com todas as métricas de qualidade.
    """
    prompt_text = (
        prompt_config.get("body", {}).get("content") or
        prompt_config.get("body", {}).get("message") or
        str(prompt_config.get("body", ""))
    )

    # Verificações básicas
    response_received = bool(response_text) and not error
    response_length = len(response_text) if response_text else 0

    # Verificações de qualidade
    portuguese_ok = has_portuguese_content(response_text) if response_text else False
    relevant_ok = is_recruitment_relevant(response_text) if response_text else False
    hallucination_risk = has_hallucination_risk(prompt_text, response_text) if response_text else False

    # Verifica palavras esperadas
    expected_found = []
    expected_missing = []
    if response_text:
        resp_lower = response_text.lower()
        for kw in prompt_config.get("expected_keywords", []):
            if kw.lower() in resp_lower:
                expected_found.append(kw)
            else:
                expected_missing.append(kw)

    keywords_coverage = (
        len(expected_found) / len(prompt_config.get("expected_keywords", [1]))
        if prompt_config.get("expected_keywords")
        else 1.0
    )

    # Verifica palavras proibidas
    forbidden_found = []
    if response_text:
        resp_lower = response_text.lower()
        for kw in prompt_config.get("must_not_contain", []):
            if kw.lower() in resp_lower:
                forbidden_found.append(kw)

    # Verifica tamanho mínimo
    min_length = prompt_config.get("min_length", 10)
    length_ok = response_length >= min_length

    # Verifica campos extras esperados na resposta JSON
    extra_checks_ok = {}
    if prompt_config.get("extra_checks") and isinstance(raw_response, dict):
        for field in prompt_config["extra_checks"]:
            extra_checks_ok[field] = field in raw_response

    # Calcula score geral (0-100)
    score_factors = [
        (response_received, 30),        # 30 pts: recebeu resposta
        (length_ok, 15),                # 15 pts: tamanho adequado
        (portuguese_ok, 20),            # 20 pts: resposta em português
        (relevant_ok, 20),              # 20 pts: contexto de recrutamento
        (keywords_coverage >= 0.5, 10), # 10 pts: palavras esperadas encontradas
        (not forbidden_found, 5),       # 5 pts: sem palavras proibidas
    ]
    score = sum(pts for ok, pts in score_factors if ok)

    # Status geral do teste
    passed = (
        response_received and
        length_ok and
        not forbidden_found and
        http_status not in [401, 403, 500, 502, 503]
    )

    return {
        "id": prompt_config["id"],
        "component": prompt_config["component"],
        "name": prompt_config["name"],
        "endpoint": prompt_config["endpoint"],
        "description": prompt_config.get("description", ""),
        "latency_ms": latency_ms,
        "http_status": http_status,
        "response_received": response_received,
        "response_length": response_length,
        "has_portuguese": portuguese_ok,
        "is_relevant": relevant_ok,
        "has_hallucination_risk": hallucination_risk,
        "length_ok": length_ok,
        "min_length": min_length,
        "keywords_coverage": round(keywords_coverage, 2),
        "expected_found": expected_found,
        "expected_missing": expected_missing,
        "forbidden_found": forbidden_found,
        "extra_checks": extra_checks_ok,
        "score": score,
        "passed": passed,
        "error": error,
        "response_text": response_text[:500] if response_text else "",  # primeiros 500 chars
        "raw_response": raw_response,
    }


# ---------------------------------------------------------------------------
# FUNÇÕES DE CHAMADA DE API (ASYNC com httpx / SYNC com requests fallback)
# ---------------------------------------------------------------------------

def build_headers(token: str) -> dict:
    """Constrói os headers de autenticação."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Benchmark-Run": "true",  # identifica chamadas do benchmark
    }


async def call_endpoint_async(
    base_url: str,
    token: str,
    prompt_config: dict,
    verbose: bool = False,
) -> tuple[Any, int, Optional[str], int]:
    """
    Chama um endpoint de forma assíncrona usando httpx.

    Retorna: (raw_response, http_status, error_message, latency_ms)
    """
    url = f"{base_url.rstrip('/')}{prompt_config['endpoint']}"
    headers = build_headers(token)
    body = prompt_config["body"]

    # Remove None values do body para não enviar campos nulos desnecessários
    clean_body = {k: v for k, v in body.items() if v is not None}

    if verbose:
        print(f"    → POST {url}")
        print(f"    → Body: {json.dumps(clean_body, ensure_ascii=False)[:200]}")

    start_time = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=clean_body, headers=headers)
            latency_ms = int((time.monotonic() - start_time) * 1000)

            http_status = response.status_code

            # Trata erros HTTP conhecidos
            if http_status == 401:
                return None, http_status, "Erro de autenticação (401): token inválido ou expirado", latency_ms
            elif http_status == 403:
                return None, http_status, "Acesso proibido (403): sem permissão para este endpoint", latency_ms
            elif http_status == 404:
                return None, http_status, f"Endpoint não encontrado (404): {url}", latency_ms
            elif http_status >= 500:
                body_text = response.text[:200] if response.text else ""
                return None, http_status, f"Erro do servidor ({http_status}): {body_text}", latency_ms

            # Tenta decodificar JSON
            try:
                data = response.json()
                return data, http_status, None, latency_ms
            except Exception:
                text = response.text
                if not text:
                    return None, http_status, "Resposta vazia (sem conteúdo)", latency_ms
                return {"_raw_text": text}, http_status, None, latency_ms

    except httpx.ConnectError as e:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        return None, None, f"Erro de conexão: servidor inacessível em {base_url}", latency_ms
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        return None, None, f"Timeout após {DEFAULT_TIMEOUT}s", latency_ms
    except Exception as e:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        return None, None, f"Erro inesperado: {type(e).__name__}: {str(e)}", latency_ms


def call_endpoint_sync(
    base_url: str,
    token: str,
    prompt_config: dict,
    verbose: bool = False,
) -> tuple[Any, int, Optional[str], int]:
    """
    Chama um endpoint de forma síncrona usando requests (fallback).

    Retorna: (raw_response, http_status, error_message, latency_ms)
    """
    import requests as req

    url = f"{base_url.rstrip('/')}{prompt_config['endpoint']}"
    headers = build_headers(token)
    body = prompt_config["body"]

    clean_body = {k: v for k, v in body.items() if v is not None}

    if verbose:
        print(f"    → POST {url}")
        print(f"    → Body: {json.dumps(clean_body, ensure_ascii=False)[:200]}")

    start_time = time.monotonic()
    try:
        response = req.post(url, json=clean_body, headers=headers, timeout=DEFAULT_TIMEOUT)
        latency_ms = int((time.monotonic() - start_time) * 1000)

        http_status = response.status_code

        if http_status == 401:
            return None, http_status, "Erro de autenticação (401): token inválido ou expirado", latency_ms
        elif http_status == 403:
            return None, http_status, "Acesso proibido (403): sem permissão para este endpoint", latency_ms
        elif http_status == 404:
            return None, http_status, f"Endpoint não encontrado (404): {url}", latency_ms
        elif http_status >= 500:
            body_text = response.text[:200] if response.text else ""
            return None, http_status, f"Erro do servidor ({http_status}): {body_text}", latency_ms

        try:
            data = response.json()
            return data, http_status, None, latency_ms
        except Exception:
            text = response.text
            if not text:
                return None, http_status, "Resposta vazia (sem conteúdo)", latency_ms
            return {"_raw_text": text}, http_status, None, latency_ms

    except Exception as e:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        err_type = type(e).__name__
        if "ConnectionError" in err_type or "ConnectError" in err_type:
            return None, None, f"Erro de conexão: servidor inacessível em {base_url}", latency_ms
        elif "Timeout" in err_type:
            return None, None, f"Timeout após {DEFAULT_TIMEOUT}s", latency_ms
        return None, None, f"Erro inesperado: {err_type}: {str(e)}", latency_ms


# ---------------------------------------------------------------------------
# RUNNER PRINCIPAL
# ---------------------------------------------------------------------------

async def run_benchmark_async(
    base_url: str,
    token: str,
    prompts: list,
    verbose: bool = False,
) -> list:
    """Executa todos os benchmarks de forma assíncrona."""
    results = []

    for i, prompt_config in enumerate(prompts, 1):
        component = prompt_config["component"]
        name = prompt_config["name"]
        test_id = prompt_config["id"]

        print(f"\n  [{i:02d}/{len(prompts):02d}] [{component.upper()}] {name}")

        raw_response, http_status, error, latency_ms = await call_endpoint_async(
            base_url, token, prompt_config, verbose
        )

        # Extrai texto da resposta
        response_text = ""
        if raw_response and not error:
            if isinstance(raw_response, dict) and "_raw_text" in raw_response:
                response_text = raw_response["_raw_text"]
            else:
                response_text = extract_response_text(
                    raw_response,
                    prompt_config.get("response_path", [])
                )

        # Avalia qualidade
        result = evaluate_response(
            prompt_config, raw_response, response_text,
            latency_ms, error, http_status
        )

        results.append(result)

        # Output colorido
        status_icon = "✅" if result["passed"] else "❌"
        score_str = f"score={result['score']}/100"
        latency_str = f"{latency_ms}ms"
        status_str = f"HTTP {http_status}" if http_status else "CONN_ERR"

        if result["passed"]:
            print(f"    {status_icon} PASS | {status_str} | {latency_str} | {score_str} | {response_text[:80]!r}")
        else:
            print(f"    {status_icon} FAIL | {status_str} | {latency_str} | {score_str}")
            if error:
                print(f"    ⚠️  Erro: {error}")
            if result["expected_missing"]:
                print(f"    ⚠️  Keywords não encontradas: {result['expected_missing']}")
            if result["forbidden_found"]:
                print(f"    ⚠️  Palavras proibidas encontradas: {result['forbidden_found']}")

        if verbose and response_text:
            print(f"    📝 Resposta: {response_text[:200]!r}")

    return results


def run_benchmark_sync(
    base_url: str,
    token: str,
    prompts: list,
    verbose: bool = False,
) -> list:
    """Executa todos os benchmarks de forma síncrona (fallback sem httpx)."""
    results = []

    for i, prompt_config in enumerate(prompts, 1):
        component = prompt_config["component"]
        name = prompt_config["name"]

        print(f"\n  [{i:02d}/{len(prompts):02d}] [{component.upper()}] {name}")

        raw_response, http_status, error, latency_ms = call_endpoint_sync(
            base_url, token, prompt_config, verbose
        )

        response_text = ""
        if raw_response and not error:
            if isinstance(raw_response, dict) and "_raw_text" in raw_response:
                response_text = raw_response["_raw_text"]
            else:
                response_text = extract_response_text(
                    raw_response,
                    prompt_config.get("response_path", [])
                )

        result = evaluate_response(
            prompt_config, raw_response, response_text,
            latency_ms, error, http_status
        )

        results.append(result)

        status_icon = "✅" if result["passed"] else "❌"
        score_str = f"score={result['score']}/100"
        latency_str = f"{latency_ms}ms"
        status_str = f"HTTP {http_status}" if http_status else "CONN_ERR"

        if result["passed"]:
            print(f"    {status_icon} PASS | {status_str} | {latency_str} | {score_str} | {response_text[:80]!r}")
        else:
            print(f"    {status_icon} FAIL | {status_str} | {latency_str} | {score_str}")
            if error:
                print(f"    ⚠️  Erro: {error}")
            if result["expected_missing"]:
                print(f"    ⚠️  Keywords não encontradas: {result['expected_missing']}")
            if result["forbidden_found"]:
                print(f"    ⚠️  Palavras proibidas encontradas: {result['forbidden_found']}")

        if verbose and response_text:
            print(f"    📝 Resposta: {response_text[:200]!r}")

    return results


# ---------------------------------------------------------------------------
# EXPORTAÇÃO DE RELATÓRIOS
# ---------------------------------------------------------------------------

def export_json(results: list, output_path: str, metadata: dict) -> str:
    """Exporta resultados completos em JSON."""
    output = {
        "metadata": metadata,
        "summary": compute_summary(results),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    return output_path


def export_csv(results: list, output_path: str) -> str:
    """Exporta resultados em CSV para análise em planilha."""
    if not results:
        return output_path

    # Colunas do CSV
    fieldnames = [
        "id", "component", "name", "endpoint",
        "passed", "score", "http_status", "latency_ms",
        "response_received", "response_length", "length_ok", "min_length",
        "has_portuguese", "is_relevant", "has_hallucination_risk",
        "keywords_coverage", "expected_missing", "forbidden_found",
        "error", "response_text",
    ]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            row = dict(result)
            # Converte listas para strings legíveis
            row["expected_missing"] = ", ".join(result.get("expected_missing", []))
            row["forbidden_found"] = ", ".join(result.get("forbidden_found", []))
            writer.writerow(row)

    return output_path


def compute_summary(results: list) -> dict:
    """Calcula estatísticas gerais do benchmark."""
    if not results:
        return {}

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    latencies = [r["latency_ms"] for r in results if r["latency_ms"] is not None]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0

    scores = [r["score"] for r in results]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Por componente
    by_component = {}
    for result in results:
        comp = result["component"]
        if comp not in by_component:
            by_component[comp] = {"total": 0, "passed": 0, "scores": [], "latencies": []}
        by_component[comp]["total"] += 1
        if result["passed"]:
            by_component[comp]["passed"] += 1
        by_component[comp]["scores"].append(result["score"])
        if result["latency_ms"]:
            by_component[comp]["latencies"].append(result["latency_ms"])

    component_summary = {}
    for comp, data in by_component.items():
        component_summary[comp] = {
            "total": data["total"],
            "passed": data["passed"],
            "failed": data["total"] - data["passed"],
            "pass_rate": f"{(data['passed'] / data['total'] * 100):.0f}%",
            "avg_score": round(sum(data["scores"]) / len(data["scores"]), 1),
            "avg_latency_ms": int(sum(data["latencies"]) / len(data["latencies"])) if data["latencies"] else 0,
        }

    # Problemas de qualidade encontrados
    quality_issues = []
    for r in results:
        if r.get("has_hallucination_risk"):
            quality_issues.append(f"[{r['id']}] Risco de alucinação detectado")
        if not r.get("has_portuguese") and r.get("response_received"):
            quality_issues.append(f"[{r['id']}] Resposta não está em português")
        if not r.get("is_relevant") and r.get("response_received"):
            quality_issues.append(f"[{r['id']}] Resposta não menciona contexto de recrutamento")
        if r.get("expected_missing"):
            quality_issues.append(f"[{r['id']}] Keywords ausentes: {r['expected_missing']}")

    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{(passed / total * 100):.1f}%",
        "avg_score": avg_score,
        "avg_latency_ms": avg_latency,
        "max_latency_ms": max_latency,
        "min_latency_ms": min_latency,
        "by_component": component_summary,
        "quality_issues": quality_issues,
        "hallucination_risks": sum(1 for r in results if r.get("has_hallucination_risk")),
        "non_portuguese": sum(1 for r in results if not r.get("has_portuguese") and r.get("response_received")),
    }


def export_markdown(results: list, output_path: str, metadata: dict) -> str:
    """Exporta relatório legível em Markdown."""
    summary = compute_summary(results)
    now_str = metadata.get("timestamp", datetime.now().isoformat())
    base_url = metadata.get("base_url", "N/A")

    lines = [
        "# 📊 Benchmark de Qualidade — Plataforma LIA",
        "",
        f"**Data:** {now_str}  ",
        f"**Ambiente:** {base_url}  ",
        f"**Total de testes:** {summary.get('total_tests', 0)}  ",
        "",
        "---",
        "",
        "## 📈 Resumo Geral",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| ✅ Passou | **{summary.get('passed', 0)}** de {summary.get('total_tests', 0)} ({summary.get('pass_rate', '0%')}) |",
        f"| ❌ Falhou | **{summary.get('failed', 0)}** |",
        f"| 🎯 Score médio | **{summary.get('avg_score', 0)}/100** |",
        f"| ⏱️ Latência média | **{summary.get('avg_latency_ms', 0)}ms** |",
        f"| ⏱️ Latência máxima | **{summary.get('max_latency_ms', 0)}ms** |",
        f"| ⏱️ Latência mínima | **{summary.get('min_latency_ms', 0)}ms** |",
        f"| ⚠️ Riscos de alucinação | **{summary.get('hallucination_risks', 0)}** |",
        f"| 🌐 Respostas não em PT-BR | **{summary.get('non_portuguese', 0)}** |",
        "",
        "---",
        "",
        "## 🔍 Resultados por Componente",
        "",
    ]

    # Tabela por componente
    by_comp = summary.get("by_component", {})
    if by_comp:
        lines += [
            "| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |",
            "|-----------|-------|--------|--------|------|-------------|----------------|",
        ]
        for comp, data in by_comp.items():
            pass_icon = "🟢" if int(data["pass_rate"].rstrip("%")) >= 80 else "🟡" if int(data["pass_rate"].rstrip("%")) >= 50 else "🔴"
            lines.append(
                f"| {pass_icon} `{comp}` | {data['total']} | {data['passed']} | {data['failed']} | "
                f"{data['pass_rate']} | {data['avg_score']}/100 | {data['avg_latency_ms']}ms |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## 📋 Resultados Detalhados",
        "",
    ]

    # Resultados por teste
    for result in results:
        icon = "✅" if result["passed"] else "❌"
        lines += [
            f"### {icon} [{result['id']}] {result['name']}",
            "",
            f"- **Componente:** `{result['component']}`",
            f"- **Endpoint:** `{result['endpoint']}`",
            f"- **Status HTTP:** `{result.get('http_status', 'N/A')}`",
            f"- **Latência:** `{result['latency_ms']}ms`",
            f"- **Score:** `{result['score']}/100`",
            f"- **Em português:** {'✅' if result['has_portuguese'] else '❌'}",
            f"- **Relevante para RH:** {'✅' if result['is_relevant'] else '❌'}",
            f"- **Risco de alucinação:** {'⚠️ SIM' if result['has_hallucination_risk'] else '✅ Não'}",
            f"- **Cobertura de keywords:** `{result['keywords_coverage'] * 100:.0f}%`",
        ]

        if result.get("expected_missing"):
            lines.append(f"- **Keywords ausentes:** `{', '.join(result['expected_missing'])}`")
        if result.get("forbidden_found"):
            lines.append(f"- **⚠️ Palavras proibidas:** `{', '.join(result['forbidden_found'])}`")
        if result.get("error"):
            lines.append(f"- **❌ Erro:** `{result['error']}`")
        if result.get("response_text"):
            preview = result["response_text"][:300].replace("\n", " ")
            lines += ["", f"> **Resposta (preview):** {preview}"]

        lines.append("")

    # Problemas de qualidade
    quality_issues = summary.get("quality_issues", [])
    if quality_issues:
        lines += [
            "---",
            "",
            "## ⚠️ Problemas de Qualidade Encontrados",
            "",
        ]
        for issue in quality_issues:
            lines.append(f"- {issue}")
        lines.append("")

    # Rodapé
    lines += [
        "---",
        "",
        "*Relatório gerado automaticamente por `benchmark_prompts.py`*  ",
        f"*Plataforma LIA — plataforma-lia — {now_str}*",
        "",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


# ---------------------------------------------------------------------------
# DRY RUN
# ---------------------------------------------------------------------------

def dry_run(prompts: list, base_url: str):
    """Imprime o que seria chamado sem fazer requisições reais."""
    print("\n🔍 DRY RUN — Chamadas que seriam feitas:\n")
    print(f"  Base URL: {base_url}")
    print(f"  Total de testes: {len(prompts)}\n")

    by_component = {}
    for p in prompts:
        comp = p["component"]
        if comp not in by_component:
            by_component[comp] = []
        by_component[comp].append(p)

    for comp, comp_prompts in by_component.items():
        print(f"  📦 Componente: {comp.upper()} ({len(comp_prompts)} testes)")
        for p in comp_prompts:
            url = f"{base_url.rstrip('/')}{p['endpoint']}"
            body_preview = json.dumps(p["body"], ensure_ascii=False)[:120]
            print(f"    [{p['id']}] {p['name']}")
            print(f"           POST {url}")
            print(f"           Body: {body_preview}")
            print(f"           Esperado: {p.get('expected_keywords', [])[:3]}")
            print()


# ---------------------------------------------------------------------------
# ARGPARSE E MAIN
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark de Qualidade dos Prompts de IA — Plataforma LIA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Benchmark completo em localhost
  python benchmark_prompts.py --base-url http://localhost:3000 --token SEU_TOKEN

  # Apenas o componente wizard em produção
  python benchmark_prompts.py --base-url https://app.wedotalent.com --token SEU_TOKEN --component wizard

  # Ver o que seria chamado sem fazer requisições
  python benchmark_prompts.py --dry-run

  # Com output em pasta específica e verbose
  python benchmark_prompts.py --base-url http://localhost:3000 --token SEU_TOKEN --output ./results --verbose

Componentes disponíveis: chat, orchestrator, wizard, conversational, wsi
        """
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"URL base da API (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("LIA_TOKEN", ""),
        help="Token de autenticação Bearer (ou use env LIA_TOKEN)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Diretório de saída para os relatórios (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--component",
        choices=["chat", "orchestrator", "wizard", "conversational", "wsi"],
        default=None,
        help="Filtrar por componente específico (default: todos)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibir corpo das requisições e respostas completas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas exibir o que seria chamado, sem fazer requisições reais",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout em segundos para cada requisição (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Não gerar o relatório Markdown (apenas JSON e CSV)",
    )

    return parser.parse_args()


async def async_main(args):
    """Ponto de entrada assíncrono (usado com httpx)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Filtra prompts por componente se necessário
    prompts = GOLDEN_PROMPTS
    if args.component:
        prompts = [p for p in GOLDEN_PROMPTS if p["component"] == args.component]
        if not prompts:
            print(f"❌ Nenhum teste encontrado para o componente: {args.component}")
            sys.exit(1)

    # Dry run
    if args.dry_run:
        dry_run(prompts, args.base_url)
        return

    # Valida token
    if not args.token:
        print("❌ Token de autenticação não fornecido.")
        print("   Use --token SEU_TOKEN ou defina a variável de ambiente LIA_TOKEN")
        sys.exit(1)

    # Cria diretório de output se necessário
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("🚀 BENCHMARK DE QUALIDADE — PLATAFORMA LIA")
    print("=" * 60)
    print(f"  🌐 Base URL: {args.base_url}")
    print(f"  📦 Componente: {args.component or 'todos'}")
    print(f"  🧪 Total de testes: {len(prompts)}")
    print(f"  📁 Output: {output_dir.resolve()}")
    print(f"  ⏱️  Timeout: {args.timeout}s")
    print(f"  🔧 HTTP lib: {'httpx (async)' if HAS_HTTPX else 'requests (sync)'}")
    print("=" * 60)
    print("\n▶️  Executando testes...\n")

    # Executa benchmark
    start_total = time.monotonic()
    results = await run_benchmark_async(args.base_url, args.token, prompts, args.verbose)
    total_time = int((time.monotonic() - start_total) * 1000)

    # Metadados do run
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "base_url": args.base_url,
        "component_filter": args.component,
        "total_tests": len(prompts),
        "total_time_ms": total_time,
        "http_library": "httpx" if HAS_HTTPX else "requests",
        "timeout_s": args.timeout,
        "benchmark_version": "1.0.0",
    }

    # Exporta relatórios
    base_name = f"benchmark_results_{timestamp}"
    json_path = output_dir / f"{base_name}.json"
    csv_path = output_dir / f"{base_name}.csv"
    md_path = output_dir / f"benchmark_summary_{timestamp}.md"

    print("\n\n" + "=" * 60)
    print("📊 RESULTADOS FINAIS")
    print("=" * 60)

    summary = compute_summary(results)
    passed = summary.get("passed", 0)
    total = summary.get("total_tests", 0)
    failed = summary.get("failed", 0)
    pass_rate = summary.get("pass_rate", "0%")
    avg_score = summary.get("avg_score", 0)
    avg_latency = summary.get("avg_latency_ms", 0)

    overall_icon = "✅" if passed == total else "⚠️" if passed >= total * 0.7 else "❌"

    print(f"\n  {overall_icon} PASSOU: {passed}/{total} ({pass_rate})")
    print(f"  ❌ FALHOU: {failed}/{total}")
    print(f"  🎯 Score médio: {avg_score}/100")
    print(f"  ⏱️  Latência média: {avg_latency}ms")
    print(f"  ⏱️  Tempo total: {total_time}ms")

    # Resumo por componente
    print("\n  Por componente:")
    for comp, data in summary.get("by_component", {}).items():
        comp_icon = "✅" if data["passed"] == data["total"] else "⚠️" if data["passed"] > 0 else "❌"
        print(
            f"    {comp_icon} {comp:20s} {data['passed']}/{data['total']} "
            f"({data['pass_rate']}) | score: {data['avg_score']}/100 | "
            f"latência: {data['avg_latency_ms']}ms"
        )

    # Problemas de qualidade
    quality_issues = summary.get("quality_issues", [])
    if quality_issues:
        print(f"\n  ⚠️  Problemas de qualidade encontrados ({len(quality_issues)}):")
        for issue in quality_issues[:10]:  # exibe só os primeiros 10
            print(f"     • {issue}")
        if len(quality_issues) > 10:
            print(f"     ... e mais {len(quality_issues) - 10} (ver relatório completo)")

    # Salva arquivos
    print("\n" + "-" * 60)
    print("💾 Salvando relatórios...")

    export_json(results, str(json_path), metadata)
    print(f"  📄 JSON: {json_path.resolve()}")

    export_csv(results, str(csv_path))
    print(f"  📊 CSV:  {csv_path.resolve()}")

    if not args.no_markdown:
        export_markdown(results, str(md_path), metadata)
        print(f"  📝 MD:   {md_path.resolve()}")

    print("\n" + "=" * 60)
    print("✅ Benchmark concluído!")
    print("=" * 60 + "\n")

    # Exit code baseado nos resultados
    sys.exit(0 if passed == total else 1)


def sync_main(args):
    """Ponto de entrada síncrono (usado com requests como fallback)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    prompts = GOLDEN_PROMPTS
    if args.component:
        prompts = [p for p in GOLDEN_PROMPTS if p["component"] == args.component]
        if not prompts:
            print(f"❌ Nenhum teste encontrado para o componente: {args.component}")
            sys.exit(1)

    if args.dry_run:
        dry_run(prompts, args.base_url)
        return

    if not args.token:
        print("❌ Token de autenticação não fornecido.")
        print("   Use --token SEU_TOKEN ou defina a variável de ambiente LIA_TOKEN")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("🚀 BENCHMARK DE QUALIDADE — PLATAFORMA LIA")
    print("=" * 60)
    print(f"  🌐 Base URL: {args.base_url}")
    print(f"  📦 Componente: {args.component or 'todos'}")
    print(f"  🧪 Total de testes: {len(prompts)}")
    print(f"  📁 Output: {output_dir.resolve()}")
    print(f"  ⏱️  Timeout: {args.timeout}s")
    print(f"  🔧 HTTP lib: requests (sync)")
    print("=" * 60)
    print("\n▶️  Executando testes...\n")

    start_total = time.monotonic()
    results = run_benchmark_sync(args.base_url, args.token, prompts, args.verbose)
    total_time = int((time.monotonic() - start_total) * 1000)

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "base_url": args.base_url,
        "component_filter": args.component,
        "total_tests": len(prompts),
        "total_time_ms": total_time,
        "http_library": "requests",
        "timeout_s": args.timeout,
        "benchmark_version": "1.0.0",
    }

    base_name = f"benchmark_results_{timestamp}"
    json_path = output_dir / f"{base_name}.json"
    csv_path = output_dir / f"{base_name}.csv"
    md_path = output_dir / f"benchmark_summary_{timestamp}.md"

    print("\n\n" + "=" * 60)
    print("📊 RESULTADOS FINAIS")
    print("=" * 60)

    summary = compute_summary(results)
    passed = summary.get("passed", 0)
    total = summary.get("total_tests", 0)
    failed = summary.get("failed", 0)
    pass_rate = summary.get("pass_rate", "0%")
    avg_score = summary.get("avg_score", 0)
    avg_latency = summary.get("avg_latency_ms", 0)

    overall_icon = "✅" if passed == total else "⚠️" if passed >= total * 0.7 else "❌"

    print(f"\n  {overall_icon} PASSOU: {passed}/{total} ({pass_rate})")
    print(f"  ❌ FALHOU: {failed}/{total}")
    print(f"  🎯 Score médio: {avg_score}/100")
    print(f"  ⏱️  Latência média: {avg_latency}ms")
    print(f"  ⏱️  Tempo total: {total_time}ms")

    print("\n  Por componente:")
    for comp, data in summary.get("by_component", {}).items():
        comp_icon = "✅" if data["passed"] == data["total"] else "⚠️" if data["passed"] > 0 else "❌"
        print(
            f"    {comp_icon} {comp:20s} {data['passed']}/{data['total']} "
            f"({data['pass_rate']}) | score: {data['avg_score']}/100 | "
            f"latência: {data['avg_latency_ms']}ms"
        )

    quality_issues = summary.get("quality_issues", [])
    if quality_issues:
        print(f"\n  ⚠️  Problemas de qualidade encontrados ({len(quality_issues)}):")
        for issue in quality_issues[:10]:
            print(f"     • {issue}")

    print("\n" + "-" * 60)
    print("💾 Salvando relatórios...")

    export_json(results, str(json_path), metadata)
    print(f"  📄 JSON: {json_path.resolve()}")

    export_csv(results, str(csv_path))
    print(f"  📊 CSV:  {csv_path.resolve()}")

    if not args.no_markdown:
        export_markdown(results, str(md_path), metadata)
        print(f"  📝 MD:   {md_path.resolve()}")

    print("\n" + "=" * 60)
    print("✅ Benchmark concluído!")
    print("=" * 60 + "\n")

    sys.exit(0 if passed == total else 1)


def main():
    args = parse_args()

    # Aplica timeout global
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = args.timeout

    if HAS_HTTPX:
        # Usa asyncio com httpx para melhor performance
        asyncio.run(async_main(args))
    else:
        # Fallback para requests síncrono
        print("ℹ️  httpx não encontrado, usando requests (síncrono). Para melhor performance: pip install httpx")
        sync_main(args)


if __name__ == "__main__":
    main()
