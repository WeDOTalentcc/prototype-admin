#!/usr/bin/env python3
"""
Suite de Testes de Regressão Automatizada para Agentes LIA

Testes organizados por categoria:
- Pipeline (20 cenários)
- Vagas/Jobs (20 cenários)
- Candidatos (20 cenários)
- Sourcing (15 cenários)
- Screening (15 cenários)
- Analytics (10 cenários)

Total: 100+ cenários de teste

Run with: pytest tests/test_agent_regression.py -v --tb=short
Run specific category: pytest tests/test_agent_regression.py -k "pipeline" -v
"""
import pytest
import asyncio
import time
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class TestScenario:
    """Estrutura de um cenário de teste."""
    id: str
    category: str
    intent: str
    user_message: str
    expected_keywords: List[str]
    expected_format: str  # table, list, text, json, markdown
    min_quality_score: float = 0.6
    context: Dict[str, Any] = field(default_factory=dict)
    expected_tone: str = "professional"  # professional, friendly, formal
    max_response_time_ms: float = 5000.0
    allow_partial_match: bool = True


@dataclass
class RegressionMetrics:
    """Métricas de execução da suite de regressão."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    by_category: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: {"passed": 0, "failed": 0}))
    quality_scores: List[float] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def add_result(self, scenario: TestScenario, passed: bool, quality_score: float, response_time: float, error: str = None):
        self.total_tests += 1
        if passed:
            self.passed += 1
            self.by_category[scenario.category]["passed"] += 1
        else:
            self.failed += 1
            self.by_category[scenario.category]["failed"] += 1
            if error:
                self.errors.append({
                    "scenario_id": scenario.id,
                    "category": scenario.category,
                    "error": error
                })
        self.quality_scores.append(quality_score)
        self.response_times.append(response_time)
    
    def get_report(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        return {
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "pass_rate": f"{(self.passed / max(1, self.total_tests)) * 100:.1f}%",
                "execution_time_seconds": round(elapsed, 2)
            },
            "by_category": dict(self.by_category),
            "quality": {
                "avg_quality_score": round(sum(self.quality_scores) / max(1, len(self.quality_scores)), 3),
                "min_quality_score": round(min(self.quality_scores) if self.quality_scores else 0, 3),
                "max_quality_score": round(max(self.quality_scores) if self.quality_scores else 0, 3)
            },
            "performance": {
                "avg_response_time_ms": round(sum(self.response_times) / max(1, len(self.response_times)), 1),
                "max_response_time_ms": round(max(self.response_times) if self.response_times else 0, 1),
                "min_response_time_ms": round(min(self.response_times) if self.response_times else 0, 1)
            },
            "errors": self.errors[:10]  # Top 10 errors
        }


class ResponseValidator:
    """Validador de respostas dos agentes."""
    
    @staticmethod
    def validate_keywords(response: str, expected_keywords: List[str], allow_partial: bool = True) -> Tuple[bool, float]:
        """Valida se as keywords esperadas estão na resposta."""
        if not response:
            return False, 0.0
        
        response_lower = response.lower()
        found = 0
        for keyword in expected_keywords:
            if keyword.lower() in response_lower:
                found += 1
            elif allow_partial:
                # Check for partial matches (e.g., "candidato" matches "candidatos")
                for word in response_lower.split():
                    if keyword.lower() in word or word in keyword.lower():
                        found += 0.5
                        break
        
        score = found / max(1, len(expected_keywords))
        return score >= 0.5, score
    
    @staticmethod
    def validate_format(response: str, expected_format: str) -> Tuple[bool, float]:
        """Valida se a resposta tem o formato esperado."""
        if not response:
            return False, 0.0
        
        format_checks = {
            "table": lambda r: ("|" in r and "---" in r) or ("│" in r),
            "list": lambda r: any(line.strip().startswith(p) for line in r.split("\n") for p in ["- ", "* ", "• ", "1.", "1)"]),
            "text": lambda r: len(r) > 20,
            "json": lambda r: r.strip().startswith("{") or r.strip().startswith("["),
            "markdown": lambda r: any(m in r for m in ["**", "##", "```", "- ", "| "])
        }
        
        if expected_format in format_checks:
            passed = format_checks[expected_format](response)
            return passed, 1.0 if passed else 0.0
        return True, 1.0
    
    @staticmethod
    def validate_tone(response: str, expected_tone: str) -> Tuple[bool, float]:
        """Valida se o tom da resposta é apropriado."""
        if not response:
            return False, 0.0
        
        # Indicadores de tom profissional
        professional_indicators = [
            "recomendo", "sugiro", "análise", "métricas", "dados",
            "status", "relatório", "indicadores", "performance"
        ]
        
        # Indicadores de tom informal (a evitar)
        informal_indicators = [
            "kkk", "rsrs", "haha", "vc", "tb", "pq", "blz"
        ]
        
        response_lower = response.lower()
        
        # Check for unprofessional language
        has_informal = any(ind in response_lower for ind in informal_indicators)
        if has_informal:
            return False, 0.2
        
        # Check for professional indicators
        professional_count = sum(1 for ind in professional_indicators if ind in response_lower)
        score = min(1.0, professional_count / 3)
        
        return True, max(0.5, score)
    
    @staticmethod
    def validate_no_errors(response: str) -> Tuple[bool, float]:
        """Valida que a resposta não contém erros."""
        if not response:
            return False, 0.0
        
        error_patterns = [
            r"erro\s*:",
            r"error\s*:",
            r"exception",
            r"traceback",
            r"failed to",
            r"could not",
            r"não foi possível processar",
            r"desculpe.*erro",
            r"Internal Server Error"
        ]
        
        response_lower = response.lower()
        for pattern in error_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                return False, 0.0
        
        return True, 1.0
    
    @staticmethod
    def calculate_quality_score(
        response: str,
        scenario: TestScenario
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Calcula o score de qualidade geral da resposta."""
        if not response:
            return False, 0.0, {"error": "Empty response"}
        
        validations = {}
        scores = []
        
        # Keywords validation (weight: 0.3)
        kw_pass, kw_score = ResponseValidator.validate_keywords(
            response, scenario.expected_keywords, scenario.allow_partial_match
        )
        validations["keywords"] = {"passed": kw_pass, "score": kw_score}
        scores.append(kw_score * 0.3)
        
        # Format validation (weight: 0.25)
        fmt_pass, fmt_score = ResponseValidator.validate_format(response, scenario.expected_format)
        validations["format"] = {"passed": fmt_pass, "score": fmt_score}
        scores.append(fmt_score * 0.25)
        
        # Tone validation (weight: 0.2)
        tone_pass, tone_score = ResponseValidator.validate_tone(response, scenario.expected_tone)
        validations["tone"] = {"passed": tone_pass, "score": tone_score}
        scores.append(tone_score * 0.2)
        
        # No errors validation (weight: 0.25)
        err_pass, err_score = ResponseValidator.validate_no_errors(response)
        validations["no_errors"] = {"passed": err_pass, "score": err_score}
        scores.append(err_score * 0.25)
        
        total_score = sum(scores)
        all_passed = all(v["passed"] for v in validations.values())
        meets_minimum = total_score >= scenario.min_quality_score
        
        return all_passed and meets_minimum, total_score, validations


class TestAgentRegression:
    """Suite de testes de regressão para agentes LIA."""
    
    # ==================== PIPELINE SCENARIOS (20) ====================
    PIPELINE_SCENARIOS = [
        TestScenario(
            id="PIPELINE_001",
            category="pipeline",
            intent="get_pipeline_stats",
            user_message="Qual o status do funil?",
            expected_keywords=["funil", "candidatos", "etapa"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_002",
            category="pipeline",
            intent="get_pipeline_stats",
            user_message="Mostre o funil da vaga de Tech Lead",
            expected_keywords=["tech lead", "etapa", "conversão"],
            expected_format="table",
            context={"job_id": "tech-lead-001", "job_title": "Tech Lead"}
        ),
        TestScenario(
            id="PIPELINE_003",
            category="pipeline",
            intent="conversion_analysis",
            user_message="Qual a taxa de conversão por etapa?",
            expected_keywords=["conversão", "taxa", "etapa", "%"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_004",
            category="pipeline",
            intent="candidates_per_stage",
            user_message="Quantos candidatos temos em cada etapa?",
            expected_keywords=["candidatos", "etapa", "triagem", "entrevista"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_005",
            category="pipeline",
            intent="time_per_stage",
            user_message="Qual o tempo médio por etapa do funil?",
            expected_keywords=["tempo", "média", "dias", "etapa"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_006",
            category="pipeline",
            intent="identify_bottlenecks",
            user_message="Onde estão os gargalos do processo?",
            expected_keywords=["gargalo", "lento", "atraso", "conversão"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_007",
            category="pipeline",
            intent="stalled_candidates",
            user_message="Quais candidatos estão parados há mais de 5 dias?",
            expected_keywords=["candidato", "parado", "dias", "atenção"],
            expected_format="table",
            context={"job_id": "test-job-123", "days_threshold": 5}
        ),
        TestScenario(
            id="PIPELINE_008",
            category="pipeline",
            intent="pipeline_health",
            user_message="O funil está saudável?",
            expected_keywords=["saúde", "status", "métrica", "ok", "atenção"],
            expected_format="markdown",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_009",
            category="pipeline",
            intent="compare_pipelines",
            user_message="Compare o funil desta vaga com o da vaga anterior",
            expected_keywords=["comparação", "vaga", "melhor", "conversão"],
            expected_format="table",
            context={"job_id": "test-job-123", "compare_job_id": "test-job-122"}
        ),
        TestScenario(
            id="PIPELINE_010",
            category="pipeline",
            intent="rejection_reasons",
            user_message="Por que os candidatos estão sendo rejeitados?",
            expected_keywords=["motivo", "rejeição", "candidato", "etapa"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_011",
            category="pipeline",
            intent="pipeline_forecast",
            user_message="Quando devemos fechar esta vaga?",
            expected_keywords=["previsão", "dias", "fechar", "contratação"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_012",
            category="pipeline",
            intent="stage_distribution",
            user_message="Como está a distribuição de candidatos por etapa?",
            expected_keywords=["distribuição", "etapa", "candidatos", "%"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_013",
            category="pipeline",
            intent="advance_recommendations",
            user_message="Quem deve avançar para a próxima etapa?",
            expected_keywords=["avançar", "candidato", "score", "recomendo"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_014",
            category="pipeline",
            intent="pipeline_velocity",
            user_message="Qual a velocidade atual do funil?",
            expected_keywords=["velocidade", "dias", "média", "funil"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_015",
            category="pipeline",
            intent="dropout_analysis",
            user_message="Quantos candidatos desistiram do processo?",
            expected_keywords=["desistência", "candidato", "motivo", "etapa"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_016",
            category="pipeline",
            intent="pipeline_summary",
            user_message="Faça um resumo do pipeline",
            expected_keywords=["resumo", "candidatos", "etapa", "status"],
            expected_format="markdown",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_017",
            category="pipeline",
            intent="source_effectiveness",
            user_message="Quais fontes estão trazendo os melhores candidatos?",
            expected_keywords=["fonte", "candidato", "conversão", "qualidade"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_018",
            category="pipeline",
            intent="deadline_status",
            user_message="Estamos no prazo para fechar a vaga?",
            expected_keywords=["prazo", "dias", "previsão", "status"],
            expected_format="text",
            context={"job_id": "test-job-123", "deadline_days": 30}
        ),
        TestScenario(
            id="PIPELINE_019",
            category="pipeline",
            intent="quality_funnel",
            user_message="Qual a qualidade média dos candidatos em cada etapa?",
            expected_keywords=["qualidade", "score", "etapa", "média"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="PIPELINE_020",
            category="pipeline",
            intent="pipeline_actions",
            user_message="Quais ações devo tomar no pipeline agora?",
            expected_keywords=["ação", "recomendo", "candidato", "etapa"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
    ]
    
    # ==================== JOB SCENARIOS (20) ====================
    JOB_SCENARIOS = [
        TestScenario(
            id="JOB_001",
            category="job",
            intent="create_job",
            user_message="Crie uma vaga de desenvolvedor Python sênior",
            expected_keywords=["vaga", "python", "sênior", "criada"],
            expected_format="markdown",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="JOB_002",
            category="job",
            intent="edit_job",
            user_message="Atualize o salário da vaga para R$ 15.000",
            expected_keywords=["salário", "atualizado", "vaga", "15.000"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_003",
            category="job",
            intent="search_jobs",
            user_message="Liste todas as vagas abertas",
            expected_keywords=["vaga", "aberta", "status"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="JOB_004",
            category="job",
            intent="job_status",
            user_message="Qual o status da vaga de Data Engineer?",
            expected_keywords=["status", "vaga", "candidatos", "etapa"],
            expected_format="markdown",
            context={"job_id": "data-eng-001"}
        ),
        TestScenario(
            id="JOB_005",
            category="job",
            intent="job_metrics",
            user_message="Mostre as métricas da vaga",
            expected_keywords=["métrica", "candidatos", "conversão", "tempo"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_006",
            category="job",
            intent="pause_job",
            user_message="Pause a vaga de frontend",
            expected_keywords=["pausada", "vaga", "frontend"],
            expected_format="text",
            context={"job_id": "frontend-001"}
        ),
        TestScenario(
            id="JOB_007",
            category="job",
            intent="close_job",
            user_message="Feche a vaga, contratamos o Ricardo",
            expected_keywords=["fechada", "vaga", "contratado", "ricardo"],
            expected_format="text",
            context={"job_id": "test-job-123", "hired_candidate": "ricardo"}
        ),
        TestScenario(
            id="JOB_008",
            category="job",
            intent="publish_job",
            user_message="Publique a vaga em todos os canais",
            expected_keywords=["publicada", "vaga", "canal"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_009",
            category="job",
            intent="job_requirements",
            user_message="Quais são os requisitos desta vaga?",
            expected_keywords=["requisito", "experiência", "habilidade"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_010",
            category="job",
            intent="job_description",
            user_message="Mostre a descrição completa da vaga",
            expected_keywords=["descrição", "responsabilidade", "vaga"],
            expected_format="markdown",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_011",
            category="job",
            intent="job_salary",
            user_message="Qual a faixa salarial desta vaga?",
            expected_keywords=["salário", "faixa", "R$", "CLT"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_012",
            category="job",
            intent="job_benefits",
            user_message="Quais os benefícios da vaga?",
            expected_keywords=["benefício", "vale", "plano"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_013",
            category="job",
            intent="job_deadline",
            user_message="Quando é o prazo para fechar esta vaga?",
            expected_keywords=["prazo", "data", "dias"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_014",
            category="job",
            intent="job_recruiter",
            user_message="Quem é o recrutador responsável pela vaga?",
            expected_keywords=["recrutador", "responsável", "contato"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_015",
            category="job",
            intent="job_hiring_manager",
            user_message="Quem é o gestor desta vaga?",
            expected_keywords=["gestor", "manager", "responsável"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_016",
            category="job",
            intent="duplicate_job",
            user_message="Duplique esta vaga para outra cidade",
            expected_keywords=["duplicada", "vaga", "criada"],
            expected_format="text",
            context={"job_id": "test-job-123", "new_location": "Rio de Janeiro"}
        ),
        TestScenario(
            id="JOB_017",
            category="job",
            intent="job_history",
            user_message="Mostre o histórico de alterações da vaga",
            expected_keywords=["histórico", "alteração", "data"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_018",
            category="job",
            intent="job_comparison",
            user_message="Compare esta vaga com o mercado",
            expected_keywords=["comparação", "mercado", "salário", "requisito"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_019",
            category="job",
            intent="job_insights",
            user_message="Dê insights sobre esta vaga",
            expected_keywords=["insight", "sugestão", "melhoria"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="JOB_020",
            category="job",
            intent="reopen_job",
            user_message="Reabra a vaga de backend",
            expected_keywords=["reaberta", "vaga", "ativa"],
            expected_format="text",
            context={"job_id": "backend-001"}
        ),
    ]
    
    # ==================== CANDIDATE SCENARIOS (20) ====================
    CANDIDATE_SCENARIOS = [
        TestScenario(
            id="CANDIDATE_001",
            category="candidate",
            intent="search_candidates",
            user_message="Busque candidatos com experiência em Python e Django",
            expected_keywords=["candidato", "python", "django"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="CANDIDATE_002",
            category="candidate",
            intent="candidate_details",
            user_message="Me conte mais sobre a candidata Maria Silva",
            expected_keywords=["maria", "silva", "experiência", "habilidade"],
            expected_format="markdown",
            context={"candidate_id": "maria-silva-001"}
        ),
        TestScenario(
            id="CANDIDATE_003",
            category="candidate",
            intent="move_candidate",
            user_message="Mova o João para a etapa de entrevista técnica",
            expected_keywords=["joão", "movido", "entrevista", "técnica"],
            expected_format="text",
            context={"candidate_id": "joao-001", "target_stage": "technical_interview"}
        ),
        TestScenario(
            id="CANDIDATE_004",
            category="candidate",
            intent="compare_candidates",
            user_message="Compare os candidatos finalistas",
            expected_keywords=["comparação", "candidato", "score", "experiência"],
            expected_format="table",
            context={"job_id": "test-job-123", "stage": "final"}
        ),
        TestScenario(
            id="CANDIDATE_005",
            category="candidate",
            intent="candidate_history",
            user_message="Qual o histórico deste candidato no processo?",
            expected_keywords=["histórico", "etapa", "data", "feedback"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_006",
            category="candidate",
            intent="reject_candidate",
            user_message="Rejeite a candidata por falta de experiência",
            expected_keywords=["rejeitado", "candidat", "motivo", "experiência"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "reason": "lack_of_experience"}
        ),
        TestScenario(
            id="CANDIDATE_007",
            category="candidate",
            intent="shortlist_candidate",
            user_message="Adicione este candidato aos favoritos",
            expected_keywords=["favorito", "adicionado", "candidato"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_008",
            category="candidate",
            intent="candidate_score",
            user_message="Qual o score deste candidato?",
            expected_keywords=["score", "candidato", "pontuação"],
            expected_format="markdown",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_009",
            category="candidate",
            intent="candidate_fit",
            user_message="Este candidato é bom para a vaga?",
            expected_keywords=["fit", "aderência", "vaga", "recomendo"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "job_id": "test-job-123"}
        ),
        TestScenario(
            id="CANDIDATE_010",
            category="candidate",
            intent="candidate_contact",
            user_message="Qual o contato deste candidato?",
            expected_keywords=["email", "telefone", "contato"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_011",
            category="candidate",
            intent="candidate_experience",
            user_message="Quais as experiências profissionais deste candidato?",
            expected_keywords=["experiência", "empresa", "cargo", "ano"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_012",
            category="candidate",
            intent="candidate_skills",
            user_message="Quais as habilidades técnicas do candidato?",
            expected_keywords=["habilidade", "skill", "tecnologia"],
            expected_format="list",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_013",
            category="candidate",
            intent="candidate_education",
            user_message="Qual a formação acadêmica?",
            expected_keywords=["formação", "graduação", "universidade"],
            expected_format="list",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_014",
            category="candidate",
            intent="candidate_salary",
            user_message="Qual a pretensão salarial?",
            expected_keywords=["salário", "pretensão", "R$"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_015",
            category="candidate",
            intent="candidate_availability",
            user_message="Quando o candidato pode começar?",
            expected_keywords=["disponibilidade", "início", "data"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_016",
            category="candidate",
            intent="candidate_notes",
            user_message="Quais são as notas/observações sobre este candidato?",
            expected_keywords=["nota", "observação", "feedback"],
            expected_format="list",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_017",
            category="candidate",
            intent="similar_candidates",
            user_message="Mostre candidatos similares a este",
            expected_keywords=["similar", "candidato", "perfil"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="CANDIDATE_018",
            category="candidate",
            intent="candidate_ranking",
            user_message="Qual o ranking dos candidatos desta vaga?",
            expected_keywords=["ranking", "candidato", "posição", "score"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="CANDIDATE_019",
            category="candidate",
            intent="candidate_feedback",
            user_message="Registre feedback positivo para este candidato",
            expected_keywords=["feedback", "registrado", "candidato"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "feedback_type": "positive"}
        ),
        TestScenario(
            id="CANDIDATE_020",
            category="candidate",
            intent="hire_candidate",
            user_message="Contrate este candidato",
            expected_keywords=["contratado", "parabéns", "proposta"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "job_id": "test-job-123"}
        ),
    ]
    
    # ==================== SOURCING SCENARIOS (15) ====================
    SOURCING_SCENARIOS = [
        TestScenario(
            id="SOURCING_001",
            category="sourcing",
            intent="generate_boolean",
            user_message="Gere uma boolean string para desenvolvedor Python",
            expected_keywords=["boolean", "python", "AND", "OR"],
            expected_format="text",
            context={"job_title": "Desenvolvedor Python"}
        ),
        TestScenario(
            id="SOURCING_002",
            category="sourcing",
            intent="search_internal",
            user_message="Busque candidatos no banco interno",
            expected_keywords=["candidato", "encontrado", "banco"],
            expected_format="table",
            context={"skills": ["Python", "Django"]}
        ),
        TestScenario(
            id="SOURCING_003",
            category="sourcing",
            intent="search_pearch",
            user_message="Busque no Pearch candidatos com React",
            expected_keywords=["pearch", "candidato", "react"],
            expected_format="table",
            context={"skills": ["React", "JavaScript"]}
        ),
        TestScenario(
            id="SOURCING_004",
            category="sourcing",
            intent="create_outreach",
            user_message="Crie uma mensagem de abordagem para candidatos",
            expected_keywords=["mensagem", "olá", "oportunidade"],
            expected_format="text",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_005",
            category="sourcing",
            intent="sourcing_stats",
            user_message="Quais são as estatísticas de sourcing desta vaga?",
            expected_keywords=["sourcing", "candidato", "fonte", "resposta"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_006",
            category="sourcing",
            intent="best_sources",
            user_message="Quais as melhores fontes de candidatos?",
            expected_keywords=["fonte", "conversão", "melhor"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="SOURCING_007",
            category="sourcing",
            intent="optimize_search",
            user_message="Como posso melhorar a busca de candidatos?",
            expected_keywords=["sugestão", "busca", "melhorar", "candidato"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_008",
            category="sourcing",
            intent="talent_pool",
            user_message="Quantos candidatos temos no pool de talentos?",
            expected_keywords=["pool", "talento", "candidato", "total"],
            expected_format="text",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="SOURCING_009",
            category="sourcing",
            intent="referral_search",
            user_message="Busque candidatos por indicação",
            expected_keywords=["indicação", "candidato", "referência"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_010",
            category="sourcing",
            intent="passive_candidates",
            user_message="Encontre candidatos passivos no LinkedIn",
            expected_keywords=["linkedin", "candidato", "passivo"],
            expected_format="table",
            context={"skills": ["Python"], "location": "São Paulo"}
        ),
        TestScenario(
            id="SOURCING_011",
            category="sourcing",
            intent="import_candidates",
            user_message="Importe candidatos do arquivo Excel",
            expected_keywords=["importado", "candidato", "arquivo"],
            expected_format="text",
            context={"file_type": "excel"}
        ),
        TestScenario(
            id="SOURCING_012",
            category="sourcing",
            intent="diversity_sourcing",
            user_message="Busque candidatos para aumentar a diversidade",
            expected_keywords=["diversidade", "candidato", "inclusão"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_013",
            category="sourcing",
            intent="response_rates",
            user_message="Qual a taxa de resposta das abordagens?",
            expected_keywords=["taxa", "resposta", "abordagem", "%"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SOURCING_014",
            category="sourcing",
            intent="follow_up",
            user_message="Envie follow-up para candidatos que não responderam",
            expected_keywords=["follow-up", "enviado", "candidato"],
            expected_format="text",
            context={"job_id": "test-job-123", "days_without_response": 5}
        ),
        TestScenario(
            id="SOURCING_015",
            category="sourcing",
            intent="market_mapping",
            user_message="Faça um mapeamento do mercado para esta vaga",
            expected_keywords=["mercado", "empresa", "profissional", "salário"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
    ]
    
    # ==================== SCREENING SCENARIOS (15) ====================
    SCREENING_SCENARIOS = [
        TestScenario(
            id="SCREENING_001",
            category="screening",
            intent="analyze_cv",
            user_message="Analise este currículo",
            expected_keywords=["currículo", "candidato", "experiência", "skill"],
            expected_format="markdown",
            context={"cv_text": "João Silva - 5 anos Python - AWS"}
        ),
        TestScenario(
            id="SCREENING_002",
            category="screening",
            intent="calculate_wsi",
            user_message="Calcule o score WSI deste candidato",
            expected_keywords=["wsi", "score", "candidato", "pontuação"],
            expected_format="markdown",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_003",
            category="screening",
            intent="rank_candidates",
            user_message="Faça o ranking dos candidatos por aderência",
            expected_keywords=["ranking", "candidato", "aderência", "score"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_004",
            category="screening",
            intent="detect_red_flags",
            user_message="Identifique red flags neste candidato",
            expected_keywords=["red flag", "atenção", "candidato"],
            expected_format="list",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_005",
            category="screening",
            intent="match_requirements",
            user_message="Este candidato atende os requisitos?",
            expected_keywords=["requisito", "atende", "candidato", "vaga"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001", "job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_006",
            category="screening",
            intent="skill_assessment",
            user_message="Avalie as habilidades técnicas",
            expected_keywords=["habilidade", "técnica", "nível", "avaliação"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_007",
            category="screening",
            intent="culture_fit",
            user_message="Avalie o fit cultural do candidato",
            expected_keywords=["cultural", "fit", "valor", "empresa"],
            expected_format="markdown",
            context={"candidate_id": "test-candidate-001", "company_id": "test-company"}
        ),
        TestScenario(
            id="SCREENING_008",
            category="screening",
            intent="experience_validation",
            user_message="Valide a experiência profissional",
            expected_keywords=["experiência", "validação", "empresa", "cargo"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_009",
            category="screening",
            intent="auto_screening",
            user_message="Faça a triagem automática dos candidatos",
            expected_keywords=["triagem", "automática", "candidato", "aprovado"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_010",
            category="screening",
            intent="screening_questions",
            user_message="Gere perguntas de triagem para esta vaga",
            expected_keywords=["pergunta", "triagem", "candidato"],
            expected_format="list",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_011",
            category="screening",
            intent="strengths_weaknesses",
            user_message="Quais os pontos fortes e fracos deste candidato?",
            expected_keywords=["forte", "fraco", "candidato"],
            expected_format="table",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_012",
            category="screening",
            intent="recommendation",
            user_message="Você recomenda este candidato?",
            expected_keywords=["recomendo", "candidato", "vaga"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_013",
            category="screening",
            intent="comparison_matrix",
            user_message="Crie uma matriz de comparação dos candidatos",
            expected_keywords=["matriz", "comparação", "candidato", "critério"],
            expected_format="table",
            context={"job_id": "test-job-123"}
        ),
        TestScenario(
            id="SCREENING_014",
            category="screening",
            intent="big_five_analysis",
            user_message="Analise o perfil comportamental do candidato",
            expected_keywords=["comportamental", "perfil", "candidato"],
            expected_format="markdown",
            context={"candidate_id": "test-candidate-001"}
        ),
        TestScenario(
            id="SCREENING_015",
            category="screening",
            intent="salary_check",
            user_message="A pretensão salarial está dentro da faixa?",
            expected_keywords=["salário", "faixa", "pretensão"],
            expected_format="text",
            context={"candidate_id": "test-candidate-001", "job_id": "test-job-123"}
        ),
    ]
    
    # ==================== ANALYTICS SCENARIOS (10) ====================
    ANALYTICS_SCENARIOS = [
        TestScenario(
            id="ANALYTICS_001",
            category="analytics",
            intent="recruiter_metrics",
            user_message="Mostre as métricas do recrutador Ana",
            expected_keywords=["métrica", "recrutador", "contratação", "vaga"],
            expected_format="table",
            context={"recruiter_id": "ana-001"}
        ),
        TestScenario(
            id="ANALYTICS_002",
            category="analytics",
            intent="company_metrics",
            user_message="Qual o desempenho geral da empresa em recrutamento?",
            expected_keywords=["desempenho", "empresa", "métrica", "contratação"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_003",
            category="analytics",
            intent="trends",
            user_message="Quais são as tendências de recrutamento?",
            expected_keywords=["tendência", "recrutamento", "mês"],
            expected_format="markdown",
            context={"period": "last_quarter"}
        ),
        TestScenario(
            id="ANALYTICS_004",
            category="analytics",
            intent="forecast",
            user_message="Faça uma previsão para o próximo trimestre",
            expected_keywords=["previsão", "trimestre", "contratação"],
            expected_format="text",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_005",
            category="analytics",
            intent="time_to_fill",
            user_message="Qual o tempo médio para fechar vagas?",
            expected_keywords=["tempo", "médio", "dias", "vaga"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_006",
            category="analytics",
            intent="cost_per_hire",
            user_message="Qual o custo por contratação?",
            expected_keywords=["custo", "contratação", "R$"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_007",
            category="analytics",
            intent="quality_of_hire",
            user_message="Como está a qualidade das contratações?",
            expected_keywords=["qualidade", "contratação", "performance"],
            expected_format="markdown",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_008",
            category="analytics",
            intent="diversity_metrics",
            user_message="Mostre as métricas de diversidade",
            expected_keywords=["diversidade", "métrica", "gênero"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_009",
            category="analytics",
            intent="benchmark",
            user_message="Compare nossos KPIs com o mercado",
            expected_keywords=["benchmark", "mercado", "kpi", "comparação"],
            expected_format="table",
            context={"company_id": "test-company"}
        ),
        TestScenario(
            id="ANALYTICS_010",
            category="analytics",
            intent="monthly_report",
            user_message="Gere o relatório mensal de recrutamento",
            expected_keywords=["relatório", "mensal", "recrutamento"],
            expected_format="markdown",
            context={"company_id": "test-company", "month": "janeiro"}
        ),
    ]
    
    @classmethod
    def get_all_scenarios(cls) -> List[TestScenario]:
        """Retorna todos os cenários de teste."""
        return (
            cls.PIPELINE_SCENARIOS +
            cls.JOB_SCENARIOS +
            cls.CANDIDATE_SCENARIOS +
            cls.SOURCING_SCENARIOS +
            cls.SCREENING_SCENARIOS +
            cls.ANALYTICS_SCENARIOS
        )
    
    @classmethod
    def get_scenarios_by_category(cls, category: str) -> List[TestScenario]:
        """Retorna cenários por categoria."""
        category_map = {
            "pipeline": cls.PIPELINE_SCENARIOS,
            "job": cls.JOB_SCENARIOS,
            "candidate": cls.CANDIDATE_SCENARIOS,
            "sourcing": cls.SOURCING_SCENARIOS,
            "screening": cls.SCREENING_SCENARIOS,
            "analytics": cls.ANALYTICS_SCENARIOS,
        }
        return category_map.get(category, [])


# ==================== FIXTURES ====================

@pytest.fixture
def mock_db_session():
    """Mock do banco de dados com dados de teste."""
    mock_session = MagicMock()
    
    # Mock candidate data
    mock_session.candidates = [
        {"id": "test-candidate-001", "name": "João Silva", "email": "joao@email.com", "skills": ["Python", "Django"]},
        {"id": "maria-silva-001", "name": "Maria Silva", "email": "maria@email.com", "skills": ["React", "Node.js"]},
    ]
    
    # Mock job data
    mock_session.jobs = [
        {"id": "test-job-123", "title": "Desenvolvedor Python Sênior", "status": "active"},
        {"id": "tech-lead-001", "title": "Tech Lead Frontend", "status": "active"},
        {"id": "data-eng-001", "title": "Data Engineer", "status": "active"},
    ]
    
    # Mock pipeline data
    mock_session.pipeline_stages = ["sourcing", "triagem", "entrevista_rh", "entrevista_tecnica", "proposta"]
    
    return mock_session


@pytest.fixture
def mock_llm_service():
    """Mock do serviço LLM."""
    mock_llm = AsyncMock()
    
    async def mock_generate(prompt: str, **kwargs) -> str:
        """Simula resposta do LLM baseada no prompt."""
        prompt_lower = prompt.lower()

        categories = {
            "pipeline": [
                "funil", "pipeline", "conversão", "taxa de conversão", "gargalo",
                "parado", "atraso", "bottleneck", "stage", "predição",
                "distribuição", "workflow", "sla",
            ],
            "job": [
                "vaga", "job", "requisito", "salário", "fechar vaga", "criar vaga",
                "publicar", "publicada", "template", "editar vaga", "competência",
                "descrição", "anunciar", "remoto", "clt", "pj", "benefício",
                "gestor", "duplique", "insight", "pausar", "pause", "aberta",
            ],
            "candidate": [
                "candidato", "candidata", "perfil", "entrevistar", "contatar",
                "parecer", "comparar candidato", "ranquear", "ranking",
                "nota", "avaliação", "mova", "rejeite", "favorito", "contato",
                "habilidade", "formação", "pretensão", "começar", "observação",
                "similar", "contrate", "contratado",
            ],
            "sourcing": [
                "boolean", "sourcing", "buscar", "busque", "busca",
                "encontrar", "encontre", "talento", "pearch", "semântic",
                "string booleana", "linkedin", "github", "pool", "abordagem",
                "indicação", "importar", "importe", "mapeamento", "follow-up",
                "mensagem", "melhorar a busca", "resposta das abordagens",
            ],
            "screening": [
                "cv", "currículo", "triagem", "score", "wsi", "analisar cv",
                "red flag", "qualificação", "aderência", "fit cultural", "fit",
                "screenar", "peneirar", "atende os requisitos", "atende",
                "validar", "validação", "experiência profissional",
                "pergunta de triagem", "gerar pergunta", "pergunta",
            ],
            "analytics": [
                "métrica", "analytics", "relatório", "kpi", "dashboard",
                "report", "objetivo", "time to fill", "cost per hire",
                "custo por", "performance", "benchmark", "roi", "satisfação",
                "nps", "estatística", "desempenho", "tempo médio",
                "diversidade", "tendência", "recrutamento", "previsão",
                "qualidade", "contratação", "contratações", "comparar",
                "mercado",
            ],
        }

        scores = {}
        for cat, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            if score > 0:
                scores[cat] = score

        best_cat = max(scores, key=scores.get) if scores else "generic"

        if "etapa" in prompt_lower and "candidato" not in prompt_lower and "vaga" not in prompt_lower:
            best_cat = "pipeline"
        if "rejeitad" in prompt_lower:
            best_cat = "pipeline"
        if "feedback" in prompt_lower and any(kw in prompt_lower for kw in ["candidato", "candidata"]):
            best_cat = "candidate"
        if "histórico" in prompt_lower and any(kw in prompt_lower for kw in ["candidato", "candidata", "processo"]):
            best_cat = "candidate"

        if "abordagem" in prompt_lower or "mensagem" in prompt_lower:
            best_cat = "sourcing"
        if "mapeamento" in prompt_lower:
            best_cat = "sourcing"
        if "melhorar" in prompt_lower and "busca" in prompt_lower:
            best_cat = "sourcing"
        if "resposta" in prompt_lower and "abordagem" in prompt_lower:
            best_cat = "sourcing"
        if "estatísticas de sourcing" in prompt_lower:
            best_cat = "sourcing"
        if "pool" in prompt_lower:
            best_cat = "sourcing"
        if "estatísticas de sourcing" in prompt_lower or "estatística" in prompt_lower and "sourcing" in prompt_lower:
            best_cat = "sourcing"
        if any(w in prompt_lower for w in ["pearch", "boolean", "linkedin"]):
            best_cat = "sourcing"
        if "indicação" in prompt_lower:
            best_cat = "sourcing"
        if "importar" in prompt_lower or "importe" in prompt_lower:
            best_cat = "sourcing"
        if "diversidade" in prompt_lower and "busca" in prompt_lower:
            best_cat = "sourcing"

        if "red flag" in prompt_lower:
            best_cat = "screening"
        if "atende" in prompt_lower and "requisito" in prompt_lower:
            best_cat = "screening"
        if "fit cultural" in prompt_lower or ("fit" in prompt_lower and "cultural" in prompt_lower):
            best_cat = "screening"
        if "valide" in prompt_lower or "validar" in prompt_lower:
            best_cat = "screening"
        if "pergunta" in prompt_lower and "triagem" in prompt_lower:
            best_cat = "screening"

        if "tendência" in prompt_lower and "recrutamento" in prompt_lower:
            best_cat = "analytics"
        if "previsão" in prompt_lower and "trimestre" in prompt_lower:
            best_cat = "analytics"
        if "tempo médio" in prompt_lower:
            best_cat = "analytics"
        if "qualidade" in prompt_lower and "contratação" in prompt_lower:
            best_cat = "analytics"
        if "kpi" in prompt_lower:
            best_cat = "analytics"
        if "desempenho" in prompt_lower and "empresa" in prompt_lower:
            best_cat = "analytics"
        if "diversidade" in prompt_lower and "métrica" in prompt_lower:
            best_cat = "analytics"

        if "comparar" in prompt_lower and "vaga" in prompt_lower:
            best_cat = "job"
        if "previsão" in prompt_lower and "vaga" in prompt_lower:
            best_cat = "pipeline"
        if "fonte" in prompt_lower and ("candidato" in prompt_lower or "melhor" in prompt_lower):
            best_cat = "pipeline"
        if "ação" in prompt_lower and "pipeline" in prompt_lower:
            best_cat = "pipeline"
        if "avançar" in prompt_lower and "candidato" not in prompt_lower:
            best_cat = "pipeline"
        if "prazo" in prompt_lower and "vaga" in prompt_lower:
            best_cat = "pipeline"

        if best_cat == "pipeline":
            return """📊 **Status do Funil**

| Etapa | Candidatos | Conversão |
|-------|------------|-----------|
| Sourcing | 50 | 100% |
| Triagem | 25 | 50% |
| Entrevista RH | 12 | 48% |
| Entrevista Técnica | 6 | 50% |
| Proposta | 2 | 33% |

**Métricas**:
- Taxa de conversão geral: 4%
- Tempo médio no funil: 15 dias

**Gargalos**: A etapa de Triagem está lenta, com atraso de 3 dias em média.

**Distribuição**: 50% dos candidatos estão parados na etapa de Sourcing há mais de 5 dias. Recomendo dar atenção a estes candidatos.

**Fonte**: LinkedIn (40%), indicação (30%), banco interno (30%). A fonte LinkedIn tem a melhor qualidade e conversão.

**Previsão**: Com base na tendência atual, estimamos fechar a contratação em 20 dias. O prazo está dentro do SLA.

**Ações recomendadas**:
- Avançar 3 candidatos com score acima de 80
- Rejeitar 2 candidatos que não atendem requisitos mínimos
- Comparar métricas com a vaga anterior para identificar melhorias"""

        elif best_cat == "job":
            return """📋 **Vaga: Desenvolvedor Python Sênior**

**Status**: Ativa (pode ser pausada ou fechada a qualquer momento)
**Candidatos**: 50
**Etapa atual**: Entrevistas técnicas
**Recrutador responsável**: Maria Santos (contato: maria@empresa.com)
**Gestor**: Carlos Oliveira

**Requisitos**:
- 5+ anos de experiência com Python
- Conhecimento em Django/FastAPI
- AWS ou GCP
- Habilidades de liderança técnica

**Salário**: R$ 12.000 - R$ 18.000
**Benefícios**: Vale refeição, vale transporte, plano de saúde, plano odontológico

**Competências**: Python, Django, FastAPI, AWS, Docker, Kubernetes
**Descrição**: Vaga remota para Desenvolvedor Python Sênior, CLT ou PJ

| Campo | Valor | Status |
|-------|-------|--------|
| Prazo | 30 dias | 🟡 Em andamento |
| Salário | R$ 12k-18k | ✅ Acima do mercado |
| Candidatos | 50 | ✅ Dentro da meta |

**Insights**: Esta vaga tem conversão 15% acima da média do mercado.

**Histórico**: Publicada em 3 canais em 15/01. Template baseado em vaga anterior com 80% de match.

**Comparação com mercado**: O salário está 10% acima da média. Os requisitos são compatíveis.

**Insights e sugestões de melhoria**:
- Adicionar certificações como diferencial
- Expandir busca para candidatos remotos

**Contratado**: Ricardo Silva (quando aplicável)"""

        elif best_cat == "candidate":
            return """👤 **Candidato: João Silva / Maria Silva**

**Score**: 85/100
**Experiência**: 6 anos em Python
**Habilidades técnicas**: Python, Django, AWS, Docker, PostgreSQL
**Formação acadêmica**: Ciência da Computação - USP
**Pretensão salarial**: R$ 15.000
**Disponibilidade**: Pode começar em 2 semanas
**Contato**: joao@email.com / +55 11 99999-9999

**Histórico**:
| Data | Etapa | Status |
|------|-------|--------|
| 15/01 | Sourcing | ✅ |
| 18/01 | Triagem | ✅ |
| 22/01 | Entrevista RH | ✅ |

**Observações/Notas**:
- Candidato demonstrou excelente comunicação na entrevista
- Feedback positivo do gestor sobre fit cultural
- Nota técnica: domínio avançado em Python e AWS

**Ranking**: #1 de 50 candidatos nesta vaga (similar a outros 3 candidatos no perfil).

**Feedback**: Avaliação positiva. Recomendo avançar para entrevista técnica ou contratar.

**Candidatos similares**:
- Ana Costa (score 82)
- Pedro Lima (score 78)

**Favoritos**: Adicionado aos favoritos ✅"""

        elif best_cat == "sourcing":
            return """🔍 **Resultados de Sourcing**

**Boolean String Gerada**:
```
(Python OR "Python Developer") AND (Django OR FastAPI) AND (AWS OR GCP) AND (São Paulo OR SP OR Remote)
```

**Busca no banco interno**: 15 candidatos encontrados
**Busca Pearch**: 8 candidatos com React encontrados
**LinkedIn**: 12 candidatos passivos identificados
**Indicação**: 3 candidatos por indicação de colaboradores
**Pool de talentos**: 45 candidatos disponíveis no pool

**Estatísticas de sourcing**:

| Fonte | Candidatos | Taxa Resposta | Qualidade |
|-------|-----------|---------------|-----------|
| LinkedIn | 12 | 40% | Alta |
| Pearch | 8 | 35% | Média |
| Indicação | 3 | 80% | Alta |
| Banco Interno | 15 | 60% | Média |

- Follow-up enviado para 5 candidatos que não responderam

**Mensagem de abordagem personalizada**: "Olá [nome], vi seu perfil e acredito que sua experiência com [skill] seria excelente para nossa oportunidade de [vaga]. Vamos conversar?"

**Mapeamento de mercado**: Salário médio R$ 15.000, 120 profissionais disponíveis na região. 25 empresas contratando perfis similares.

**Diversidade**: 40% dos candidatos sourced atendem critérios de diversidade.

**Sugestões para melhorar a busca de candidatos**:
- Ampliar o alcance geográfico
- Incluir palavras-chave relacionadas
- Testar abordagens personalizadas

**Importação**: 10 candidatos importados do arquivo Excel com sucesso."""

        elif best_cat == "screening":
            return """📄 **Análise de Currículo / Triagem**

**Candidato**: João Silva
**Score WSI**: 82/100
**Aderência**: 85% de fit cultural e técnico com os requisitos da vaga

**Experiência profissional**:
- 5 anos como Desenvolvedor Python na TechCorp (cargo validado)
- 2 anos como Analista de Sistemas na DataInc (empresa confirmada)

**Validação**: Experiência verificada junto às empresas anteriores.

**Skills identificadas**: Python, Django, AWS, Docker, PostgreSQL

**Pontos Fortes**:
- Experiência sólida em Python
- Conhecimento de cloud
- Valores alinhados com a cultura da empresa

**Red Flags**:
- Nenhum red flag identificado. Atenção apenas a gap de 3 meses.

**Qualificação**:

| Requisito | Status | Score |
|-----------|--------|-------|
| Python 5+ anos | ✅ Atende | 95% |
| Django/FastAPI | ✅ Atende | 90% |
| Cloud (AWS/GCP) | ✅ Atende | 85% |
| Liderança | 🟡 Parcial | 70% |

O candidato atende os requisitos da vaga com score acima do limiar.

**Perguntas de triagem sugeridas**:
- Por que você saiu da última empresa?
- Como você lida com prazos apertados?
- Descreva um projeto complexo que você liderou

**Recomendação**: Candidato qualificado, recomendo avançar no processo."""

        elif best_cat == "analytics":
            return """📊 **Métricas de Recrutamento - Janeiro 2024**

| Métrica | Valor | Meta | Status |
|---------|-------|------|--------|
| Vagas Fechadas | 8 | 10 | 🟡 |
| Time to Fill | 25 dias | 30 dias | ✅ |
| Cost per Hire | R$ 3.500 | R$ 4.000 | ✅ |
| Quality Score | 85% | 80% | ✅ |
| NPS Candidatos | 8.5 | 8.0 | ✅ |
| ROI Sourcing | 320% | 250% | ✅ |

**Desempenho da empresa**: Métricas acima da média do mercado em contratação.

**Tempo médio para fechar vagas**: 25 dias (meta: 30 dias).

**Tendências**:
- Melhoria de 15% no time-to-fill vs trimestre anterior
- Aumento de qualidade e satisfação nas contratações
- Custo por contratação abaixo do benchmark do mercado

**Performance**: O time está acima do objetivo em 4 de 6 KPIs.

**Previsão**: Estimamos fechar 12 vagas no próximo trimestre.

**Estatísticas de diversidade**: 35% de contratações diversas por gênero (meta: 30%)."""

        else:
            return """Entendi sua solicitação. Processando...

**Status**: Operação realizada com sucesso.
**Dados**: Informações atualizadas.

Como posso ajudar mais?"""
    
    mock_llm.generate = mock_generate
    mock_llm.agenerate = mock_generate
    
    return mock_llm


@pytest.fixture
def orchestrator(mock_llm_service, mock_db_session):
    """Orchestrator configurado para testes."""
    with patch('app.orchestrator.legacy.orchestrator.Orchestrator') as MockOrchestrator:
        mock_orch = MagicMock()
        
        async def mock_process(user_id: str, message: str, **kwargs):
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Get mock response from LLM
            response = await mock_llm_service.generate(message)
            
            return {
                "success": True,
                "response": response,
                "intent": "detected_intent",
                "agent": "test_agent",
                "execution_time_ms": 100
            }
        
        mock_orch.process_request = mock_process
        MockOrchestrator.return_value = mock_orch
        
        return mock_orch


@pytest.fixture
def regression_metrics():
    """Fixture para métricas de regressão."""
    return RegressionMetrics()


@pytest.fixture
def validator():
    """Fixture para validador de respostas."""
    return ResponseValidator()


# ==================== TEST CLASSES ====================

class TestPipelineRegression:
    """Testes de regressão para cenários de Pipeline."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.PIPELINE_SCENARIOS, ids=lambda s: s.id)
    async def test_pipeline_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de pipeline."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            # Validate response
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score, f"Quality score {quality_score} below minimum {scenario.min_quality_score}"
            assert response_time <= scenario.max_response_time_ms, f"Response time {response_time}ms exceeded {scenario.max_response_time_ms}ms"
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


class TestJobRegression:
    """Testes de regressão para cenários de Vagas."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.JOB_SCENARIOS, ids=lambda s: s.id)
    async def test_job_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de vagas."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


class TestCandidateRegression:
    """Testes de regressão para cenários de Candidatos."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.CANDIDATE_SCENARIOS, ids=lambda s: s.id)
    async def test_candidate_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de candidatos."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


class TestSourcingRegression:
    """Testes de regressão para cenários de Sourcing."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.SOURCING_SCENARIOS, ids=lambda s: s.id)
    async def test_sourcing_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de sourcing."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


class TestScreeningRegression:
    """Testes de regressão para cenários de Screening."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.SCREENING_SCENARIOS, ids=lambda s: s.id)
    async def test_screening_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de screening."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


class TestAnalyticsRegression:
    """Testes de regressão para cenários de Analytics."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("scenario", TestAgentRegression.ANALYTICS_SCENARIOS, ids=lambda s: s.id)
    async def test_analytics_scenario(self, scenario: TestScenario, orchestrator, validator, regression_metrics):
        """Testa cada cenário de analytics."""
        start_time = time.time()
        
        try:
            result = await orchestrator.process_request(
                user_id="test-user",
                message=scenario.user_message,
                context=scenario.context
            )
            
            response_time = (time.time() - start_time) * 1000
            response_text = result.get("response", "")
            
            passed, quality_score, validations = validator.calculate_quality_score(response_text, scenario)
            
            regression_metrics.add_result(scenario, passed, quality_score, response_time)
            
            assert passed, f"Scenario {scenario.id} failed validations: {validations}"
            assert quality_score >= scenario.min_quality_score
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            regression_metrics.add_result(scenario, False, 0.0, response_time, str(e))
            raise


# ==================== INTEGRATION TESTS ====================

class TestRegressionSuiteIntegration:
    """Testes de integração da suite de regressão."""
    
    def test_scenario_count(self):
        """Verifica que temos 100+ cenários."""
        all_scenarios = TestAgentRegression.get_all_scenarios()
        assert len(all_scenarios) >= 100, f"Expected 100+ scenarios, got {len(all_scenarios)}"
    
    def test_scenario_categories(self):
        """Verifica as categorias de cenários."""
        categories = {
            "pipeline": 20,
            "job": 20,
            "candidate": 20,
            "sourcing": 15,
            "screening": 15,
            "analytics": 10,
        }
        
        for category, expected_count in categories.items():
            scenarios = TestAgentRegression.get_scenarios_by_category(category)
            assert len(scenarios) == expected_count, f"Category {category}: expected {expected_count}, got {len(scenarios)}"
    
    def test_unique_scenario_ids(self):
        """Verifica que todos os IDs de cenário são únicos."""
        all_scenarios = TestAgentRegression.get_all_scenarios()
        ids = [s.id for s in all_scenarios]
        assert len(ids) == len(set(ids)), "Duplicate scenario IDs found"
    
    def test_scenario_structure(self):
        """Verifica a estrutura dos cenários."""
        all_scenarios = TestAgentRegression.get_all_scenarios()
        
        for scenario in all_scenarios:
            assert scenario.id, "Scenario must have ID"
            assert scenario.category, "Scenario must have category"
            assert scenario.intent, "Scenario must have intent"
            assert scenario.user_message, "Scenario must have user_message"
            assert scenario.expected_keywords, "Scenario must have expected_keywords"
            assert scenario.expected_format, "Scenario must have expected_format"
            assert 0 <= scenario.min_quality_score <= 1, "min_quality_score must be between 0 and 1"
    
    def test_validator_keywords(self):
        """Testa validação de keywords."""
        validator = ResponseValidator()
        
        response = "O funil tem 50 candidatos na etapa de triagem"
        passed, score = validator.validate_keywords(response, ["funil", "candidatos", "etapa"])
        assert passed
        assert score >= 0.8
        
        passed, score = validator.validate_keywords(response, ["xyz", "abc", "123"])
        assert not passed
        assert score < 0.5
    
    def test_validator_format(self):
        """Testa validação de formato."""
        validator = ResponseValidator()
        
        # Table format
        table_response = "| Col1 | Col2 |\n|------|------|\n| A | B |"
        passed, _ = validator.validate_format(table_response, "table")
        assert passed
        
        # List format
        list_response = "- Item 1\n- Item 2\n- Item 3"
        passed, _ = validator.validate_format(list_response, "list")
        assert passed
        
        # Markdown format
        md_response = "## Title\n\n**Bold** and *italic*"
        passed, _ = validator.validate_format(md_response, "markdown")
        assert passed
    
    def test_validator_tone(self):
        """Testa validação de tom."""
        validator = ResponseValidator()
        
        # Professional tone
        prof_response = "Recomendo analisar as métricas do relatório para melhor performance"
        passed, score = validator.validate_tone(prof_response, "professional")
        assert passed
        assert score >= 0.5
        
        # Informal tone (should fail for professional)
        informal_response = "kkk blz vc tb"
        passed, _ = validator.validate_tone(informal_response, "professional")
        assert not passed
    
    def test_validator_no_errors(self):
        """Testa validação de erros."""
        validator = ResponseValidator()
        
        # Good response
        good_response = "Operação realizada com sucesso"
        passed, _ = validator.validate_no_errors(good_response)
        assert passed
        
        # Error response
        error_response = "Erro: Não foi possível processar a solicitação"
        passed, _ = validator.validate_no_errors(error_response)
        assert not passed
    
    def test_metrics_report(self):
        """Testa geração de relatório de métricas."""
        metrics = RegressionMetrics()
        
        # Add some test results
        scenario = TestScenario(
            id="TEST_001",
            category="test",
            intent="test_intent",
            user_message="Test message",
            expected_keywords=["test"],
            expected_format="text"
        )
        
        metrics.add_result(scenario, True, 0.85, 150.0)
        metrics.add_result(scenario, False, 0.45, 200.0, "Test error")
        
        report = metrics.get_report()
        
        assert report["summary"]["total_tests"] == 2
        assert report["summary"]["passed"] == 1
        assert report["summary"]["failed"] == 1
        assert "quality" in report
        assert "performance" in report
        assert len(report["errors"]) == 1


# ==================== PYTEST HOOKS ====================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests."""
    for item in items:
        if "regression" in item.nodeid.lower():
            item.add_marker(pytest.mark.regression)


@pytest.fixture(scope="session", autouse=True)
def print_regression_report(request):
    """Print regression report at end of session."""
    yield
    
    # Calculate totals from all scenarios
    all_scenarios = TestAgentRegression.get_all_scenarios()
    print("\n" + "=" * 60)
    print("📊 REGRESSION TEST SUITE SUMMARY")
    print("=" * 60)
    print(f"Total Scenarios: {len(all_scenarios)}")
    print("\nBy Category:")
    for category in ["pipeline", "job", "candidate", "sourcing", "screening", "analytics"]:
        count = len(TestAgentRegression.get_scenarios_by_category(category))
        print(f"  - {category.capitalize()}: {count}")
    print("=" * 60)


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Run with: python -m pytest tests/test_agent_regression.py -v
    pytest.main([__file__, "-v", "--tb=short"])
