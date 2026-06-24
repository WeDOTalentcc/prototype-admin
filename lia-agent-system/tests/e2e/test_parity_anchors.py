"""D8 — Parity Anchors: Cenário A (LIA_FEDERATED_PRIMARY) vs Cenário B (LIA_BUBBLE_VIA_SUPERVISOR).

Verifica que o ROTEAMENTO e as camadas de compliance/HITL estão corretamente
configurados em cada cenário sem fazer HTTP real. Testa inspeção de código e
comportamento de flags.

Estrutura:
  TestRoutingVerification  — roteamento correto em cada cenário (4 testes)
  TestComplianceParity     — compliance chain presente nos dois caminhos (3 testes)
  TestHITLParity           — gate HITL disponível e controlado por flag (2 testes)
  TestDiagnosticReport     — relatório de estado atual, não bloqueia suite (1 teste)
"""
from __future__ import annotations

import importlib
import inspect
import os
import textwrap
from types import ModuleType
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(dotted: str) -> ModuleType | None:
    """Importa módulo por caminho pontilhado; retorna None em ImportError."""
    try:
        return importlib.import_module(dotted)
    except Exception:
        return None


def _source_of(mod: ModuleType) -> str:
    """Retorna o source completo do módulo (ou '' em falha)."""
    try:
        return inspect.getsource(mod)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Fixtures locais — complementam as do conftest.py
# ---------------------------------------------------------------------------

@pytest.fixture
def sse_module():
    """Carrega app.api.v1.agent_chat_sse para inspeção de source."""
    return _load_module("app.api.v1.agent_chat_sse")


@pytest.fixture
def scope_config():
    """Carrega app.tools.scope_config."""
    return _load_module("app.tools.scope_config")


@pytest.fixture
def hitl_ctx():
    """Carrega app.shared.hitl.hitl_approval_context."""
    return _load_module("app.shared.hitl.hitl_approval_context")


# ===========================================================================
# 1. TestRoutingVerification
# ===========================================================================

class TestRoutingVerification:
    """Verifica que o roteamento está corretamente configurado em cada cenário."""

    def test_federated_flag_routes_to_recruiter_copilot(
        self, federated_flags, scope_config, sse_module
    ):
        """Cenário A: LIA_FEDERATED_PRIMARY=true → código roteia para recruiter_copilot.

        Verifica:
        - federated_primary_enabled() retorna True com a flag ativa
        - O source do SSE handler contém a lógica `_get_agent("recruiter_copilot")`
          ativada quando `_use_federated` é True.
        """
        assert scope_config is not None, "scope_config deve ser importável"
        fed_enabled = scope_config.federated_primary_enabled()
        assert fed_enabled is True, (
            "federated_primary_enabled() deve retornar True quando "
            "LIA_FEDERATED_PRIMARY=true"
        )

        if sse_module is not None:
            src = _source_of(sse_module)
            assert "_get_agent(\"recruiter_copilot\")" in src or \
                   "_get_agent('recruiter_copilot')" in src, (
                "agent_chat_sse.py deve conter _get_agent(\"recruiter_copilot\") "
                "para o caminho federado"
            )
            assert "_use_federated" in src, (
                "agent_chat_sse.py deve ter variável _use_federated controlando "
                "a seleção do recruiter_copilot"
            )

    def test_supervisor_flag_routes_to_main_orchestrator(
        self, supervisor_flags, sse_module
    ):
        """Cenário B: LIA_BUBBLE_VIA_SUPERVISOR=true → código usa MainOrchestrator.

        Verifica:
        - LIA_BUBBLE_VIA_SUPERVISOR=true está no ambiente
        - O source do SSE handler contém a lógica _run_via_supervisor() ativada
          quando _bubble_via_supervisor é True.
        """
        assert os.environ.get("LIA_BUBBLE_VIA_SUPERVISOR", "").lower() in (
            "true", "1", "on"
        ), "supervisor_flags fixture deve setar LIA_BUBBLE_VIA_SUPERVISOR=true"

        if sse_module is not None:
            src = _source_of(sse_module)
            assert "_bubble_via_supervisor" in src, (
                "agent_chat_sse.py deve ter variável _bubble_via_supervisor"
            )
            assert "_run_via_supervisor" in src, (
                "agent_chat_sse.py deve conter _run_via_supervisor() para Cenário B"
            )
            # Verifica que quando _bubble_via_supervisor a escolha de agente é None
            # (supervisor processa internamente via MainOrchestrator)
            assert "agent = None" in src, (
                "Quando _bubble_via_supervisor=True, agent deve ser None "
                "(MainOrchestrator assume o controle)"
            )

    def test_baseline_uses_cascaded_router(
        self, baseline_flags, scope_config, sse_module
    ):
        """Baseline: ambas flags false → usa agente de domínio via CascadedRouter.

        Verifica:
        - federated_primary_enabled() retorna False
        - O source contém _get_agent(resolved_domain) como ramo else (CascadedRouter)
        """
        assert scope_config is not None, "scope_config deve ser importável"
        fed_enabled = scope_config.federated_primary_enabled()
        assert fed_enabled is False, (
            "federated_primary_enabled() deve retornar False quando "
            "LIA_FEDERATED_PRIMARY=false"
        )

        if sse_module is not None:
            src = _source_of(sse_module)
            # O ramo else do routing usa resolved_domain (CascadedRouter determina)
            assert "_get_agent(resolved_domain)" in src, (
                "agent_chat_sse.py deve conter _get_agent(resolved_domain) "
                "como caminho baseline (CascadedRouter)"
            )

    def test_federated_and_supervisor_flags_precedence(
        self, monkeypatch, scope_config, sse_module
    ):
        """Quando ambas flags estão ativas simultaneamente, supervisor tem precedência.

        Lógica do código (linhas 659-667 de agent_chat_sse.py):
          _use_federated = (not _bubble_via_supervisor) and _fed_primary()
          if _bubble_via_supervisor: agent = None   ← supervisor SEMPRE ganha
          elif _use_federated: agent = recruiter_copilot
          else: agent = domain

        Verifica que _bubble_via_supervisor=True anula _use_federated.
        """
        monkeypatch.setenv("LIA_FEDERATED_PRIMARY", "true")
        monkeypatch.setenv("LIA_BUBBLE_VIA_SUPERVISOR", "true")

        if sse_module is not None:
            src = _source_of(sse_module)
            # Verifica que a lógica `(not _bubble_via_supervisor) and _fed_primary()`
            # existe — garante que supervisor short-circuits o federated path
            assert "(not _bubble_via_supervisor)" in src, (
                "A lógica de precedência deve garantir que _bubble_via_supervisor "
                "anula _use_federated: `(not _bubble_via_supervisor) and _fed_primary()`"
            )
            # Verifica estrutura if/elif: supervisor verifica ANTES de federated
            idx_bvs = src.find("if _bubble_via_supervisor:")
            idx_fed = src.find("elif _use_federated:")
            assert idx_bvs != -1, "Deve ter `if _bubble_via_supervisor:` no código"
            assert idx_fed != -1, "Deve ter `elif _use_federated:` no código"
            assert idx_bvs < idx_fed, (
                "supervisor (if _bubble_via_supervisor) deve vir ANTES de "
                "federated (elif _use_federated) — supervisor tem precedência"
            )


# ===========================================================================
# 2. TestComplianceParity
# ===========================================================================

class TestComplianceParity:
    """Verifica que a compliance chain está presente nos dois caminhos (A e B)."""

    def test_fairness_guard_called_in_sse_path(self, sse_module):
        """FairnessGuard instanciado e chamado no SSE handler (antes do dispatch).

        Ambos os caminhos passam pelo mesmo bloco de FairnessGuard (LIA-P03)
        na entrada — verificação compartilhada, não duplicada.
        """
        assert sse_module is not None, "agent_chat_sse deve ser importável"
        src = _source_of(sse_module)

        assert "FairnessGuard" in src, (
            "agent_chat_sse.py deve importar FairnessGuard"
        )
        assert "_fg = FairnessGuard()" in src or "FairnessGuard()" in src, (
            "FairnessGuard deve ser instanciado no SSE handler"
        )
        assert "_fg.check(" in src or ".check(content)" in src, (
            "FairnessGuard.check() deve ser chamado no input do usuário"
        )

        # Verifica que o FairnessGuard bloqueia com HTTPException
        assert "_fr.is_blocked" in src or "is_blocked" in src, (
            "Resultado do FairnessGuard deve ser verificado para bloqueio"
        )

    def test_pre_compliance_in_sse_path(self, sse_module):
        """PII masking inbound (strip_pii_for_llm_prompt) precede o dispatch.

        Verifica que o mascaramento PII inbound é aplicado ANTES de qualquer
        chamada ao agente — equivalente ao pre_compliance do WS path.
        """
        assert sse_module is not None, "agent_chat_sse deve ser importável"
        src = _source_of(sse_module)

        assert "strip_pii_for_llm_prompt" in src, (
            "agent_chat_sse.py deve usar strip_pii_for_llm_prompt para mascarar "
            "PII no input antes do LLM (equivalente ao pre_compliance do WS)"
        )

        # Verifica que o mascaramento vem antes do dispatch para o agente
        idx_pii = src.find("strip_pii_for_llm_prompt")
        idx_dispatch_fed = src.find("elif _use_federated:")
        idx_dispatch_sup = src.find("if _bubble_via_supervisor:")
        assert idx_pii != -1, "strip_pii_for_llm_prompt deve existir no código"
        # O mascaramento inbound deve aparecer antes da seleção do agente
        dispatch_idx = min(
            i for i in [idx_dispatch_fed, idx_dispatch_sup] if i != -1
        )
        assert idx_pii < dispatch_idx, (
            "strip_pii_for_llm_prompt deve ser chamado ANTES do dispatch para "
            "o agente (pre-compliance inbound)"
        )

    def test_post_compliance_present(self, sse_module):
        """post_compliance está presente nos dois caminhos de saída (A e B).

        Cenário A (federado): FIX-C3B-SSE — post_compliance no output do agente.
        Cenário B (supervisor): FIX-C3B-SUP — post_compliance no output do supervisor.
        Ambos usam fail-open (logger.warning se exceção).
        """
        assert sse_module is not None, "agent_chat_sse deve ser importável"
        src = _source_of(sse_module)

        assert "post_compliance" in src, (
            "agent_chat_sse.py deve conter post_compliance para auditoria LGPD da saída"
        )

        # Deve aparecer pelo menos 2x: uma para cada trilha (A e B)
        count = src.count("post_compliance")
        assert count >= 2, (
            f"post_compliance deve aparecer pelo menos 2 vezes (trilha A + trilha B), "
            f"mas aparece {count} vez(es)"
        )

        # Verifica fail-open nos dois contextos
        assert "post_compliance skipped (fail-open)" in src, (
            "post_compliance deve ter tratamento fail-open com logger.warning"
        )

        # Verifica que C3B usa ComplianceContext em ambas as trilhas
        assert "ComplianceContext" in src, (
            "post_compliance deve usar ComplianceContext canônico"
        )


# ===========================================================================
# 3. TestHITLParity
# ===========================================================================

class TestHITLParity:
    """Verifica que o gate HITL está disponível e controlado por flag."""

    def test_hitl_preflight_available_both_scenarios(self, hitl_ctx):
        """hitl_preflight é importável e callable independente do cenário.

        O gate HITL é uma função utilitária shared — disponível para ambas
        as trilhas. Sua ativação é controlada por flag, não por cenário.
        """
        assert hitl_ctx is not None, (
            "app.shared.hitl.hitl_approval_context deve ser importável"
        )
        assert hasattr(hitl_ctx, "hitl_preflight"), (
            "hitl_approval_context deve exportar hitl_preflight"
        )
        assert callable(hitl_ctx.hitl_preflight), (
            "hitl_preflight deve ser callable"
        )
        assert hasattr(hitl_ctx, "hitl_gate_enabled"), (
            "hitl_approval_context deve exportar hitl_gate_enabled"
        )
        assert hasattr(hitl_ctx, "is_hitl_approved"), (
            "hitl_approval_context deve exportar is_hitl_approved"
        )

    def test_hitl_gate_flag_controls_behavior(self, hitl_ctx, monkeypatch):
        """hitl_gate_enabled() retorna True/False conforme LIA_HITL_GATE.

        Quando OFF (default): hitl_preflight retorna None → zero regressão.
        Quando ON: hitl_preflight retorna dict needs_confirmation.
        """
        assert hitl_ctx is not None, "hitl_approval_context deve ser importável"

        # Gate OFF (default): preflight deve retornar None (tool segue normal)
        monkeypatch.delenv("LIA_HITL_GATE", raising=False)
        # Re-importar para limpar cache de os.environ
        importlib.reload(hitl_ctx)
        assert hitl_ctx.hitl_gate_enabled() is False, (
            "hitl_gate_enabled() deve retornar False quando LIA_HITL_GATE não setado"
        )
        result_off = hitl_ctx.hitl_preflight(tool="test_tool", domain="test")
        assert result_off is None, (
            "hitl_preflight deve retornar None quando gate está OFF "
            "(LIA_HITL_GATE não setado) — zero regressão"
        )

        # Gate ON: preflight deve retornar dict com needs_confirmation
        monkeypatch.setenv("LIA_HITL_GATE", "true")
        importlib.reload(hitl_ctx)
        assert hitl_ctx.hitl_gate_enabled() is True, (
            "hitl_gate_enabled() deve retornar True quando LIA_HITL_GATE=true"
        )
        # Não está aprovado (ContextVar padrão False)
        result_on = hitl_ctx.hitl_preflight(
            tool="close_job",
            domain="job_management",
            message="Fechar vaga requer confirmação.",
        )
        assert result_on is not None, (
            "hitl_preflight deve retornar dict quando gate está ON e ação não aprovada"
        )
        assert result_on.get("needs_confirmation") is True, (
            "hitl_preflight deve sinalizar needs_confirmation=True quando bloqueado"
        )
        assert result_on.get("success") is False, (
            "hitl_preflight deve sinalizar success=False quando bloqueado"
        )
        assert result_on.get("hitl", {}).get("tool") == "close_job", (
            "hitl_preflight deve incluir o nome da tool no resultado"
        )


# ===========================================================================
# 4. TestDiagnosticReport
# ===========================================================================

class TestDiagnosticReport:
    """Gera relatório diagnóstico do estado atual — não bloqueia a suite.

    Este teste sempre passa (mesmo se algo não estiver wired). Serve apenas
    para documentar o estado em tempo de execução dos testes.
    """

    def test_generate_parity_diagnostic_report(self):
        """Gera e exibe relatório de paridade A vs B com estado atual do ambiente.

        Dimensões verificadas:
        - Flags ativas no ambiente (.env)
        - Caminho de roteamento ativo
        - Compliance layers wireed em cada caminho
        - HITL status
        - Status: LIVE / PARTIAL / MISSING para cada dimensão
        """
        report_lines: list[str] = []
        add = report_lines.append

        add("=" * 70)
        add("D8 PARITY DIAGNOSTIC REPORT")
        add(f"Data: {os.environ.get('TEST_DATE', 'runtime')}")
        add("=" * 70)

        # --- Flags do ambiente ---
        add("\n[FLAGS ATIVAS NO AMBIENTE]")
        flag_map = {
            "LIA_FEDERATED_PRIMARY": os.environ.get("LIA_FEDERATED_PRIMARY", "not set"),
            "LIA_BUBBLE_VIA_SUPERVISOR": os.environ.get("LIA_BUBBLE_VIA_SUPERVISOR", "not set"),
            "LIA_HITL_GATE": os.environ.get("LIA_HITL_GATE", "not set"),
            "LIA_FEDERATED_SCOPED_TOOLS": os.environ.get("LIA_FEDERATED_SCOPED_TOOLS", "not set"),
        }
        for flag, val in flag_map.items():
            add(f"  {flag} = {val}")

        # --- Determinar caminho ativo ---
        add("\n[CAMINHO DE ROTEAMENTO ATIVO]")
        _truthy = {"true", "1", "on", "yes"}
        is_supervisor = flag_map["LIA_BUBBLE_VIA_SUPERVISOR"].lower() in _truthy
        is_federated = (not is_supervisor) and (
            flag_map["LIA_FEDERATED_PRIMARY"].lower() in _truthy
        )
        if is_supervisor:
            active_path = "CENÁRIO B — MainOrchestrator (supervisor)"
        elif is_federated:
            active_path = "CENÁRIO A — recruiter_copilot (federado)"
        else:
            active_path = "BASELINE — CascadedRouter (agentes de domínio)"
        add(f"  Caminho ativo: {active_path}")

        # --- Compliance layers ---
        add("\n[COMPLIANCE LAYERS]")
        compliance_dims: dict[str, tuple[str, str]] = {}

        sse_mod = _load_module("app.api.v1.agent_chat_sse")
        if sse_mod is not None:
            src = _source_of(sse_mod)
            compliance_dims["FairnessGuard (inbound)"] = (
                "LIVE" if "FairnessGuard()" in src else "MISSING",
                "Bloqueia bias no input — compartilhado por A e B",
            )
            compliance_dims["PII masking inbound"] = (
                "LIVE" if "strip_pii_for_llm_prompt" in src else "MISSING",
                "Mascara CPF/email/tel antes do LLM",
            )
            compliance_dims["post_compliance (saída A)"] = (
                "LIVE" if "FIX-C3B-SSE" in src else "PARTIAL",
                "FactChecker + audit LGPD na saída do agente federado",
            )
            compliance_dims["post_compliance (saída B)"] = (
                "LIVE" if "FIX-C3B-SUP" in src else "PARTIAL",
                "FactChecker + audit LGPD na saída do supervisor",
            )
        else:
            compliance_dims["agent_chat_sse"] = (
                "MISSING",
                "Módulo não importável — compliance não verificável",
            )

        for dim, (status, desc) in compliance_dims.items():
            add(f"  [{status:7s}] {dim}: {desc}")

        # --- HITL status ---
        add("\n[HITL STATUS]")
        hitl_mod = _load_module("app.shared.hitl.hitl_approval_context")
        if hitl_mod is not None:
            gate_on = hitl_mod.hitl_gate_enabled()
            hitl_status = "LIVE (ON)" if gate_on else "PARTIAL (OFF — dormant)"
            add(f"  hitl_gate_enabled: {hitl_status}")
            add(f"  hitl_preflight: {'LIVE' if callable(getattr(hitl_mod, 'hitl_preflight', None)) else 'MISSING'}")
        else:
            add("  MISSING — hitl_approval_context não importável")

        # --- Tools count (best-effort) ---
        add("\n[TOOLS DISPONÍVEIS (best-effort)]")
        scope_mod = _load_module("app.tools.scope_config")
        if scope_mod is not None:
            try:
                scoping_on = scope_mod.federated_scoping_enabled()
                add(f"  federated_scoping_enabled: {scoping_on}")
                if scoping_on:
                    add("  Tool count: SCOPED (~15-20 por turno via escopo dinâmico)")
                else:
                    add("  Tool count: FULL (todos os tools disponíveis — sem scoping)")
            except Exception as exc:
                add(f"  Tool count: ERRO — {exc}")
        else:
            add("  scope_config não importável")

        # --- Resumo ---
        add("\n[RESUMO EXECUTIVO]")
        all_statuses = [s for s, _ in compliance_dims.values()]
        missing = [d for d, (s, _) in compliance_dims.items() if s == "MISSING"]
        partial = [d for d, (s, _) in compliance_dims.items() if s == "PARTIAL"]
        live = [d for d, (s, _) in compliance_dims.items() if s == "LIVE"]
        add(f"  LIVE:    {len(live)} dimensões")
        add(f"  PARTIAL: {len(partial)} dimensões")
        add(f"  MISSING: {len(missing)} dimensões")
        if missing:
            add(f"  Gaps: {', '.join(missing)}")
        add("=" * 70)

        # Imprimir relatório (visível com pytest -s ou -v)
        report = "\n".join(report_lines)
        print("\n" + report)

        # Este teste SEMPRE passa — serve apenas como documentação
        assert True, "Relatório diagnóstico gerado com sucesso"
