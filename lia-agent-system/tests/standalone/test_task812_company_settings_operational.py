"""Task #812 — testes estruturais standalone.

Validam, sem subir o backend, que:
  1. O registry do agente `company_settings` expõe as tools operacionais
     primárias (`create_job_vacancy`, `list_jobs`, `view_job_details`,
     `search_candidates`) reaproveitando as ToolDefinitions canônicas dos
     registries de jobs_mgmt e talent (mesma `function`).
  2. A constante `OPERATIONAL_TOOL_NAMES` está sincronizada com as tools
     de fato expostas.
  3. O wrapper `_wrap_create_job_vacancy` falha alto quando `title` é vazio
     (sem fallback silencioso).
  4. A telemetria do orchestrator NÃO loga warning quando o agente chamou
     uma tool operacional (anti regressão do falso-positivo do P2#7).
  5. O system_prompt do YAML inclui o bloco "Atendimento de intenções
     operacionais (Task #812)" e o `scope_in` agora menciona as tools
     operacionais.
  6. O `SystemPromptBuilder.build(agent_type='company_settings')` — caminho
     REAL de produção usado pelo `MainOrchestrator` — injeta a guidance
     operacional (mapping de tools + regra de não-bloqueio).

Executar:
    python3 lia-agent-system/tests/standalone/test_task812_company_settings_operational.py

Saída: linha por teste; sai com código != 0 se algum falhar.
"""
from __future__ import annotations

import asyncio
import os
import pathlib
import sys
import traceback
from typing import Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def _ok(label: str) -> None:
    print(f"  PASS  {label}")


def _fail(label: str, err: BaseException) -> None:
    print(f"  FAIL  {label}: {err!r}")


_FAILS: list[str] = []


def _run(label: str, fn: Callable[[], None]) -> None:
    try:
        fn()
        _ok(label)
    except BaseException as exc:  # noqa: BLE001 — captura ampla é o objetivo
        _FAILS.append(label)
        _fail(label, exc)
        traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────
# 1) Registry expõe as tools operacionais
# ──────────────────────────────────────────────────────────────────────
def test_registry_exposes_operational_tools() -> None:
    from app.domains.company_settings.agents.company_tool_registry import (
        OPERATIONAL_TOOL_NAMES,
        get_company_settings_tools,
    )

    tools = get_company_settings_tools()
    names = {t.name for t in tools}

    expected_operational = {
        "create_job_vacancy",
        "list_jobs",
        "view_job_details",
        "search_candidates",
    }
    missing = expected_operational - names
    assert not missing, f"Tools operacionais ausentes do registry: {missing}"
    assert expected_operational == set(OPERATIONAL_TOOL_NAMES), (
        "OPERATIONAL_TOOL_NAMES desincronizada do conjunto exposto: "
        f"{set(OPERATIONAL_TOOL_NAMES)} vs {expected_operational}"
    )

    # Tools de onboarding continuam presentes (regressão #811 não pode quebrar)
    onboarding_must_remain = {
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "analyze_company_website",
        "get_company_completion",
    }
    missing_onb = onboarding_must_remain - names
    assert not missing_onb, f"Tools de onboarding sumiram do registry: {missing_onb}"


# ──────────────────────────────────────────────────────────────────────
# 2) Tools operacionais reaproveitam handlers canônicos (mesma `function`)
# ──────────────────────────────────────────────────────────────────────
def test_operational_tools_reuse_canonical_handlers() -> None:
    from app.domains.company_settings.agents.company_tool_registry import (
        get_company_settings_tools,
    )
    from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
        TOOL_DEFINITIONS as JOBS_MGMT_TOOLS,
    )
    from app.domains.recruiter_assistant.agents.talent_tool_registry import (
        TOOL_DEFINITIONS as TALENT_TOOLS,
    )

    by_name = {t.name: t for t in get_company_settings_tools()}
    canonical_jobs = {t.name: t for t in JOBS_MGMT_TOOLS}
    canonical_talent = {t.name: t for t in TALENT_TOOLS}

    # Mesma função (reuso, não duplicação de handler)
    assert by_name["list_jobs"].function is canonical_jobs["list_jobs"].function
    assert (
        by_name["view_job_details"].function
        is canonical_jobs["view_job_details"].function
    )
    assert (
        by_name["search_candidates"].function
        is canonical_talent["search_candidates"].function
    )


# ──────────────────────────────────────────────────────────────────────
# 3) Wrapper create_job_vacancy: title vazio => erro estruturado
# ──────────────────────────────────────────────────────────────────────
def test_create_job_vacancy_requires_title() -> None:
    from app.domains.company_settings.agents.company_tool_registry import (
        _wrap_create_job_vacancy,
    )

    async def _call() -> dict:
        return await _wrap_create_job_vacancy(
            company_id="00000000-0000-0000-0000-000000000001",
            title="",
        )

    result = asyncio.get_event_loop().run_until_complete(_call())
    assert result["success"] is False, f"Esperava success=False, veio: {result}"
    assert result.get("error") == "validation_error", result
    assert "title" in result.get("message", "").lower(), result


# ──────────────────────────────────────────────────────────────────────
# 4) Telemetria do orchestrator não dispara para tool operacional
# ──────────────────────────────────────────────────────────────────────
def test_telemetry_accepts_operational_tools() -> None:
    """Reproduz a lógica do bloco P2#7 atualizado para garantir que NÃO
    loga falso-positivo quando o LLM chamou uma tool operacional."""
    from app.domains.company_settings.agents.company_tool_registry import (
        OPERATIONAL_TOOL_NAMES,
    )

    onboarding = {
        "check_company_completeness",
        "analyze_company_website",
        "suggest_recruiting_policy",
        "import_benefits_from_data",
        "save_company_field",
        "save_company_section",
        "get_company_profile",
        "get_company_completion",
        "process_uploaded_document",
        "import_workforce_plan",
    }
    acceptable = onboarding | set(OPERATIONAL_TOOL_NAMES)

    # Cenário: agente chamou apenas create_job_vacancy => NÃO deve disparar warning
    tools_called = {"create_job_vacancy"}
    assert tools_called & acceptable, "Bug: tool operacional considerada inaceitável"

    # Cenário: agente chamou apenas get_company_profile (onboarding) => também aceito
    tools_called_onb = {"get_company_profile"}
    assert tools_called_onb & acceptable

    # Cenário regressão: agente NÃO chamou tool nenhuma => warning legítimo
    tools_called_none: set[str] = set()
    assert not (tools_called_none & acceptable)


# ──────────────────────────────────────────────────────────────────────
# 5) YAML do prompt foi atualizado
# ──────────────────────────────────────────────────────────────────────
def test_prompt_yaml_updated() -> None:
    yaml_path = (
        REPO_ROOT / "app" / "prompts" / "domains" / "company_settings.yaml"
    )
    raw = yaml_path.read_text(encoding="utf-8")

    # system_prompt enriquecido
    assert "Atendimento de intenções operacionais (Task #812)" in raw, (
        "system_prompt não inclui o bloco operacional"
    )
    assert "create_job_vacancy" in raw
    assert "list_jobs" in raw
    assert "search_candidates" in raw

    # scope_out NÃO deve mais bloquear "criar vagas" / "buscar candidatos"
    assert "Criar vagas (→ job_management)" not in raw, (
        "scope_out ainda bloqueia criação de vagas"
    )
    assert "Buscar candidatos (→ sourcing)" not in raw

    # Nova regra 8 menciona o comportamento de não-bloqueio
    assert "intenção operacional clara" in raw


# ──────────────────────────────────────────────────────────────────────
# 6) SystemPromptBuilder (caminho de produção do orchestrator)
# ──────────────────────────────────────────────────────────────────────
def test_system_prompt_builder_injects_operational_guidance() -> None:
    """Garante que o caminho REAL usado pelo `MainOrchestrator`
    (`SystemPromptBuilder.build(agent_type='company_settings')`) injeta a
    guidance operacional. Cobre o defeito de wiring identificado no code
    review: editar `app/prompts/domains/company_settings.yaml` não chega ao
    LLM em produção; o builder lê `app/prompts/shared/agent_prompts.yaml`.
    """
    # Limpa cache do lru_cache para garantir leitura fresca após edição
    from app.shared.prompts import system_prompt_builder as spb
    spb._load_domain_additions.cache_clear()

    prompt = spb.SystemPromptBuilder.build(agent_type="company_settings")

    # Bloco operacional injetado
    assert "Atendimento de intenções operacionais (Task #812)" in prompt, (
        "SystemPromptBuilder NÃO injetou o bloco operacional — "
        "agent_prompts.yaml provavelmente não tem a chave company_settings."
    )

    # Mapping explícito das 4 tools operacionais
    for tool_name in (
        "create_job_vacancy",
        "list_jobs",
        "view_job_details",
        "search_candidates",
    ):
        assert tool_name in prompt, (
            f"Mapping da tool {tool_name!r} ausente do prompt de produção."
        )

    # Regra de não-bloqueio explícita
    assert "NÃO bloqueie" in prompt or "não bloqueie" in prompt.lower(), (
        "Regra de não bloquear intenção operacional ausente do prompt."
    )

    # A especialização do agente foi anexada (heurística pelo header)
    assert "Especialização do Agente (company_settings)" in prompt


def main() -> int:
    os.environ.setdefault("LIA_TEST_MODE", "1")

    _section("Task #812 — company_settings: tools operacionais")
    _run("registry expõe tools operacionais", test_registry_exposes_operational_tools)
    _run("reaproveita handlers canônicos", test_operational_tools_reuse_canonical_handlers)
    _run("create_job_vacancy exige title", test_create_job_vacancy_requires_title)
    _run("telemetria aceita tools operacionais", test_telemetry_accepts_operational_tools)
    _run("YAML do prompt atualizado", test_prompt_yaml_updated)
    _run(
        "SystemPromptBuilder injeta guidance operacional",
        test_system_prompt_builder_injects_operational_guidance,
    )

    print()
    if _FAILS:
        print(f"FALHARAM ({len(_FAILS)}): {_FAILS}")
        return 1
    print("Todos os testes passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
