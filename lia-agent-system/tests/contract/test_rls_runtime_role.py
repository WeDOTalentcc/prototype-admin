"""Sensor (audit C8/#7 2026-06-05): torna VISIVEL que o RLS do projeto esta
inerte em runtime porque o app conecta como superuser.

Descoberta: o app conecta como 'postgres' (superuser). Postgres IGNORA Row-Level
Security para superusers — logo TODO o RLS (068 deny-by-default, job_vacancies,
etc.) NAO protege contra as queries do proprio app. A protecao multi-tenant REAL
e a camada de aplicacao (ownership gates + _require_company_id). Este sensor
expoe a verdade pra ninguem confiar em RLS como protecao enquanto for superuser.

Testa a funcao pura format_verdict (sem DB). O main() do script faz o diagnostico
contra DATABASE_URL.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../lia-agent-system
_SPEC = importlib.util.spec_from_file_location(
    "check_rls_runtime_role", ROOT / "scripts" / "check_rls_runtime_role.py"
)
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
format_verdict = _MOD.format_verdict


def test_superuser_warns_rls_inert():
    code, msg = format_verdict("postgres", True, ["job_vacancies", "screening_question_sets"])
    assert code == 0, "modo diagnostico (sem --block) nao deve falhar"
    assert "INERTE" in msg
    assert "camada de aplicacao" in msg
    assert "job_vacancies" in msg


def test_superuser_block_mode_exits_nonzero():
    code, _msg = format_verdict("postgres", True, [], block=True)
    assert code == 1, "--block deve sinalizar falha quando role e superuser"


def test_non_superuser_reports_enforced():
    code, msg = format_verdict("lia_app", False, [])
    assert code == 0
    assert "enforced" in msg.lower()
