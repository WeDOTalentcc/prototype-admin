"""
Configuração de load test para a plataforma LIA (Sprint K3).

Define perfis de carga, endpoints alvo e thresholds de SLA.
Usar com: locust -f locustfile.py --config=locust.conf
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# SLA Thresholds
# ---------------------------------------------------------------------------

@dataclass
class SLAConfig:
    """Thresholds de SLA por endpoint (P95 em ms)."""
    p95_ms: int
    p99_ms: int
    error_rate_pct: float


SLA: Dict[str, SLAConfig] = {
    "candidate_search":     SLAConfig(p95_ms=2000,  p99_ms=5000,  error_rate_pct=1.0),
    "toon_card":            SLAConfig(p95_ms=3000,  p99_ms=6000,  error_rate_pct=1.0),
    "wsi_screening_batch":  SLAConfig(p95_ms=5000,  p99_ms=10000, error_rate_pct=2.0),
    "wizard_interaction":   SLAConfig(p95_ms=4000,  p99_ms=8000,  error_rate_pct=2.0),
    "chat_screening":       SLAConfig(p95_ms=5000,  p99_ms=10000, error_rate_pct=2.0),
    "sourcing_search":      SLAConfig(p95_ms=3000,  p99_ms=6000,  error_rate_pct=1.0),
}


# ---------------------------------------------------------------------------
# Load Profiles
# ---------------------------------------------------------------------------

@dataclass
class LoadProfile:
    """Perfil de carga para um cenário de teste."""
    name: str
    users: int
    spawn_rate: float
    duration_seconds: int
    description: str


PROFILES: Dict[str, LoadProfile] = {
    "smoke": LoadProfile(
        name="smoke",
        users=5,
        spawn_rate=1.0,
        duration_seconds=60,
        description="Smoke test — verifica que o sistema responde corretamente",
    ),
    "load": LoadProfile(
        name="load",
        users=50,
        spawn_rate=5.0,
        duration_seconds=300,
        description="Load test — carga esperada em produção (50 recrutadores simultâneos)",
    ),
    "stress": LoadProfile(
        name="stress",
        users=200,
        spawn_rate=10.0,
        duration_seconds=600,
        description="Stress test — 4× a carga esperada para encontrar ponto de ruptura",
    ),
    "soak": LoadProfile(
        name="soak",
        users=30,
        spawn_rate=2.0,
        duration_seconds=3600,
        description="Soak test — carga moderada por 1h para detectar vazamentos de memória",
    ),
}


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

SAMPLE_COMPANY_IDS = [
    "c-load-001",
    "c-load-002",
    "c-load-003",
]

SAMPLE_QUERIES = [
    "desenvolvedor python sênior",
    "analista de dados",
    "gerente de projetos",
    "engenheiro de software backend",
    "ux designer",
    "cientista de dados",
    "devops engineer",
    "product manager",
]

SAMPLE_JOB_IDS = [
    "job-load-001",
    "job-load-002",
    "job-load-003",
    "job-load-004",
]

SAMPLE_CANDIDATE_IDS = [
    "cand-load-001",
    "cand-load-002",
    "cand-load-003",
    "cand-load-004",
    "cand-load-005",
]

SAMPLE_SCREENING_QUERIES = [
    "avaliar candidato para vaga de desenvolvedor python",
    "triagem de currículo para cargo de analista de dados",
    "análise de perfil para gerente de projetos",
    "screening inicial para engenheiro de software",
    "avaliar fit cultural e técnico para product manager",
]
