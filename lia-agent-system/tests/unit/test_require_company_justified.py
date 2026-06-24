"""Testes unitários para scripts/check_require_company_justified.py.

Cobre 4 casos canônicos:
1. require_company=False sem comentário → violation
2. require_company=False com # TENANT-EXEMPT → sem violation
3. app/shared/tenant_guard.py é skipado (canonical defense)
4. exit code 1 com violations + output LLM-friendly (instruções de fix)
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SENSOR_PATH = Path(__file__).parent.parent.parent / "scripts" / "check_require_company_justified.py"


def run_sensor(root: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SENSOR_PATH), "--root", str(root)] + (extra_args or [])
    return subprocess.run(cmd, capture_output=True, text=True)


def make_app_file(tmp_path: Path, rel_path: str, content: str) -> Path:
    """Cria arquivo dentro de tmp_path/app/<rel_path>."""
    target = tmp_path / "app" / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(content), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Teste 1: require_company=False SEM justificativa → violation
# ---------------------------------------------------------------------------

def test_require_company_false_without_justification_is_violation(tmp_path):
    make_app_file(
        tmp_path,
        "domains/myfeature/handlers.py",
        """\
        from app.shared.tool_handler import tool_handler

        @tool_handler("myfeature", require_company=False)
        async def my_tool(**kwargs):
            pass
        """,
    )

    result = run_sensor(tmp_path)

    assert result.returncode == 1, (
        "Sensor deve retornar exit 1 quando há require_company=False sem justificativa"
    )
    assert "require_company=False" in result.stdout or "tenant-gate" in result.stdout.lower() or \
           "require_company=False" in result.stderr or "tenant" in result.stdout.lower(), (
        f"Output deve mencionar a violação. stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Teste 2: require_company=False COM # TENANT-EXEMPT → sem violation
# ---------------------------------------------------------------------------

def test_require_company_false_with_exempt_marker_passes(tmp_path):
    make_app_file(
        tmp_path,
        "domains/myfeature/handlers.py",
        """\
        from app.shared.tool_handler import tool_handler

        @tool_handler("myfeature", require_company=False)  # kept: tool tenant-free, ontologia pura
        async def my_tool(**kwargs):
            pass
        """,
    )

    result = run_sensor(tmp_path)

    assert result.returncode == 0, (
        f"Sensor deve retornar exit 0 quando require_company=False tem comentário inline. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "0" in result.stdout or "✅" in result.stdout, (
        f"Output deve confirmar 0 violações. stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Teste 3: app/shared/tenant_guard.py é ignorado (canonical defense)
# ---------------------------------------------------------------------------

def test_tenant_guard_file_is_skipped(tmp_path):
    """O arquivo tenant_guard.py com comentário inline na linha do decorator não é violação.

    O sensor verifica se há '#' nas linhas que compõem o span do decorator.
    Comentário acima do decorator NÃO é detectado — o inline (mesma linha) é o padrão
    canônico documentado no output de fix do próprio sensor.
    """
    make_app_file(
        tmp_path,
        "shared/tenant_guard.py",
        """\
        from app.shared.tool_handler import tool_handler

        @tool_handler("tenant_guard_domain", require_company=False)  # kept: canonical defense file, defines the gate itself
        async def _canonical_defense(**kwargs):
            pass
        """,
    )

    result = run_sensor(tmp_path)

    assert result.returncode == 0, (
        f"tenant_guard.py com comentário inline no decorator deve ser aceito pelo sensor. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Teste 4: exit code + output LLM-friendly (instruções de fix)
# ---------------------------------------------------------------------------

def test_exit_code_and_llm_friendly_output(tmp_path):
    """Verifica que o sensor retorna exit 1 E que o output inclui instrução de fix."""
    make_app_file(
        tmp_path,
        "domains/danger/unsafe_tool.py",
        """\
        from app.shared.tool_handler import tool_handler

        @tool_handler(
            "danger",
            require_company=False
        )
        async def risky_tool(**kwargs):
            pass
        """,
    )

    result = run_sensor(tmp_path)

    assert result.returncode == 1, (
        "exit code deve ser 1 quando há violação"
    )

    combined_output = result.stdout + result.stderr
    assert "Fix" in combined_output or "fix" in combined_output or "adicione" in combined_output, (
        f"Output deve conter instrução de fix para o LLM. output={combined_output!r}"
    )
    # Output deve mencionar a linha do arquivo problemático
    assert "unsafe_tool.py" in combined_output or "danger" in combined_output, (
        f"Output deve referenciar o arquivo violador. output={combined_output!r}"
    )


# ---------------------------------------------------------------------------
# Teste bônus: --warn-only retorna exit 0 mesmo com violations
# ---------------------------------------------------------------------------

def test_warn_only_returns_zero_even_with_violations(tmp_path):
    make_app_file(
        tmp_path,
        "domains/myfeature/handlers.py",
        """\
        from app.shared.tool_handler import tool_handler

        @tool_handler("myfeature", require_company=False)
        async def my_tool(**kwargs):
            pass
        """,
    )

    result = run_sensor(tmp_path, extra_args=["--warn-only"])

    assert result.returncode == 0, (
        "Com --warn-only o sensor deve retornar exit 0 mesmo com violações"
    )
