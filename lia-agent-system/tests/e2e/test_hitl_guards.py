"""
D2 — HITL Guards (automatizados).

D2-06: receive_approval com pending_id desconhecido → retorna skeleton sem exceção;
       is_approved para ID inválido → None (fail-closed, sem execução de ação sensível)
D2-07: LIA_HITL_GATE=off → módulos importam sem erro; hitl_preflight retorna None (dormante);
       hitl_preflight retorna bloqueio quando gate ON; pelo menos 7 call sites de gate HITL
"""
from __future__ import annotations

import ast
import importlib
import pathlib
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# D2-06: receive_approval com pending_id inválido (desconhecido)
# ---------------------------------------------------------------------------

class TestHITLReceiveApprovalInvalidId:
    """D2-06: Aprovar pending_id que não existe não deve executar ação sensível."""

    @pytest.mark.asyncio
    async def test_receive_approval_unknown_id_returns_skeleton_not_exception(self):
        """D2-06a: receive_approval de ID desconhecido devolve dict skeleton (sem crash).

        O serviço HITL nunca deve lançar exceção não-tratada para um pending_id
        que não existe em Redis/memória. Comportamento: cria skeleton local e
        tenta DB resolve em best-effort (logging warning). Exceção seria risco de
        DoS no SSE handler.
        """
        from app.domains.cv_screening.services.hitl_service import HITLService

        svc = HITLService()
        unknown_id = "00000000-dead-beef-0000-000000000000"
        thread_id = "test-hitl-d206-thread"

        # DB resolve é best-effort; mock para não precisar de DB em teste unitário
        with patch(
            "app.domains.cv_screening.services.hitl_service._db_resolve",
            side_effect=Exception("no db in unit test"),
        ):
            result = await svc.receive_approval(
                thread_id=thread_id,
                pending_id=unknown_id,
                approved=True,
            )

        assert isinstance(result, dict), (
            f"D2-06a: receive_approval deve retornar dict, retornou {type(result)}"
        )
        # Skeleton deve conter o pending_id passado (rastreabilidade de auditoria)
        assert result.get("pending_id") == unknown_id, (
            f"D2-06a: skeleton deve conter pending_id={unknown_id}, got: {result}"
        )
        # Aprovação registrada no skeleton (estado coerente para auditoria)
        assert result.get("approved") is True, (
            f"D2-06a: skeleton deve registrar approved=True, got: {result.get('approved')}"
        )

    @pytest.mark.asyncio
    async def test_is_approved_unknown_id_returns_none_fail_closed(self):
        """D2-06b: is_approved de ID não solicitado → None (fail-closed).

        None = 'ainda pendente / não encontrado' — o agente interpreta como
        'não aprovado' e NÃO executa a ação sensível. Garante que IDs fabricados
        não bypassam o gate.
        """
        from app.domains.cv_screening.services.hitl_service import HITLService

        # Instância limpa sem Redis → usa _memory vazio
        svc = HITLService()
        result = await svc.is_approved("totally-unknown-id-xyz-d206b")

        assert result is None, (
            f"D2-06b: is_approved para ID desconhecido deve retornar None (fail-closed), "
            f"retornou: {result!r}"
        )

    @pytest.mark.asyncio
    async def test_receive_approval_rejected_unknown_id_also_safe(self):
        """D2-06c: Rejeitar pending_id desconhecido também é seguro (sem crash)."""
        from app.domains.cv_screening.services.hitl_service import HITLService

        svc = HITLService()
        with patch(
            "app.domains.cv_screening.services.hitl_service._db_resolve",
            side_effect=Exception("no db in unit test"),
        ):
            result = await svc.receive_approval(
                thread_id="test-hitl-d206c-thread",
                pending_id="00000000-dead-beef-ffff-111111111111",
                approved=False,
                comment="teste de rejeição com ID inválido",
            )

        assert isinstance(result, dict), "D2-06c: rejeição de ID desconhecido deve retornar dict"
        assert result.get("approved") is False, "D2-06c: approved deve ser False no skeleton"


# ---------------------------------------------------------------------------
# D2-07: LIA_HITL_GATE=off → comportamento dormante sem regressão
# ---------------------------------------------------------------------------

class TestHITLGateOff:
    """D2-07: Com LIA_HITL_GATE desligado, módulos carregam e gates ficam dormantes."""

    def test_hitl_modules_import_without_gate(self, monkeypatch):
        """D2-07a: Módulos HITL importam sem erro independente do valor da flag."""
        monkeypatch.setenv("LIA_HITL_GATE", "false")
        import app.shared.hitl.hitl_approval_context as hitl_ctx
        importlib.reload(hitl_ctx)
        assert hitl_ctx.hitl_preflight is not None
        assert callable(hitl_ctx.hitl_preflight)

    def test_hitl_gate_enabled_false_when_unset(self, monkeypatch):
        """D2-07b: hitl_gate_enabled() retorna False quando variável não está definida."""
        monkeypatch.delenv("LIA_HITL_GATE", raising=False)
        from app.shared.hitl.hitl_approval_context import hitl_gate_enabled
        assert hitl_gate_enabled() is False, (
            "D2-07b: gate deve ser False (dormante) quando LIA_HITL_GATE não está definida"
        )

    def test_hitl_gate_enabled_false_with_falsy_values(self, monkeypatch):
        """D2-07c: hitl_gate_enabled() retorna False para todos os valores falsy."""
        from app.shared.hitl.hitl_approval_context import hitl_gate_enabled
        for falsy in ("0", "false", "off", "no", "FALSE", "OFF"):
            monkeypatch.setenv("LIA_HITL_GATE", falsy)
            assert hitl_gate_enabled() is False, (
                f"D2-07c: gate deve ser False com LIA_HITL_GATE={falsy!r}"
            )

    def test_hitl_gate_enabled_true_when_on(self, monkeypatch):
        """D2-07d: hitl_gate_enabled() retorna True para valores truthy."""
        from app.shared.hitl.hitl_approval_context import hitl_gate_enabled
        for truthy in ("1", "true", "on", "yes", "TRUE", "ON"):
            monkeypatch.setenv("LIA_HITL_GATE", truthy)
            assert hitl_gate_enabled() is True, (
                f"D2-07d: gate deve ser True com LIA_HITL_GATE={truthy!r}"
            )

    def test_hitl_preflight_returns_none_when_gate_off(self, monkeypatch):
        """D2-07e: hitl_preflight retorna None (dormante) quando gate está desligado.

        Garante zero regressão: tools que chamam hitl_preflight continuam
        executando normalmente com LIA_HITL_GATE=off.
        """
        monkeypatch.setenv("LIA_HITL_GATE", "false")
        from app.shared.hitl.hitl_approval_context import hitl_preflight
        result = hitl_preflight(tool="close_job", domain="job_management")
        assert result is None, (
            f"D2-07e: hitl_preflight deve retornar None com gate OFF, retornou: {result}"
        )

    def test_hitl_preflight_returns_block_when_gate_on_not_approved(self, monkeypatch):
        """D2-07f: hitl_preflight retorna dict de bloqueio quando gate ON e não aprovado.

        Verifica o caso positivo: quando LIA_HITL_GATE=on e o ContextVar não
        está marcado como aprovado, a tool deve ser bloqueada.
        """
        monkeypatch.setenv("LIA_HITL_GATE", "true")
        from app.shared.hitl.hitl_approval_context import (
            hitl_preflight,
            set_hitl_approved,
            reset_hitl_approved,
        )
        # Garantir que ContextVar não está aprovado
        token = set_hitl_approved(False)
        try:
            result = hitl_preflight(
                tool="send_email",
                domain="communication",
                message="Confirmação necessária.",
            )
        finally:
            reset_hitl_approved(token)

        assert result is not None, (
            "D2-07f: hitl_preflight deve retornar dict de bloqueio com gate ON"
        )
        assert isinstance(result, dict), f"D2-07f: esperado dict, got {type(result)}"
        assert result.get("needs_confirmation") is True, (
            f"D2-07f: resultado deve ter needs_confirmation=True, got: {result}"
        )
        assert result.get("success") is False, (
            f"D2-07f: resultado deve ter success=False, got: {result}"
        )
        assert "hitl" in result, f"D2-07f: resultado deve ter chave 'hitl', got: {result}"
        assert result["hitl"].get("tool") == "send_email", (
            f"D2-07f: hitl.tool deve ser 'send_email', got: {result['hitl']}"
        )

    def test_hitl_preflight_returns_none_when_approved(self, monkeypatch):
        """D2-07g: hitl_preflight retorna None quando turno já aprovado pelo usuário.

        Mesmo com gate ON, se o ContextVar de aprovação está True (usuário
        confirmou), a tool não deve ser bloqueada novamente.
        """
        monkeypatch.setenv("LIA_HITL_GATE", "true")
        from app.shared.hitl.hitl_approval_context import (
            hitl_preflight,
            set_hitl_approved,
            reset_hitl_approved,
        )
        token = set_hitl_approved(True)
        try:
            result = hitl_preflight(tool="close_job", domain="job_management")
        finally:
            reset_hitl_approved(token)

        assert result is None, (
            f"D2-07g: hitl_preflight deve retornar None quando turno já aprovado, "
            f"retornou: {result}"
        )


# ---------------------------------------------------------------------------
# D2-07h: Ratchet — contagem de call sites de hitl_preflight (≥7 tools gated)
# ---------------------------------------------------------------------------

class TestHITLGatedToolsCount:
    """D2-07h: Ratchet — mínimo de 7 tools com gate HITL via hitl_preflight."""

    def test_at_least_7_tools_gated_via_hitl_preflight(self):
        """D2-07h: Ao menos 7 call sites de hitl_preflight em tools de domínio.

        Ratchet: se alguém remover um gate sem perceber, o teste falha antes do
        deploy. Usa AST para contar chamadas reais de hitl_preflight() em
        arquivos de tools/agents, excluindo o arquivo de definição e testes.
        """
        workspace = pathlib.Path("/home/runner/workspace/lia-agent-system/app")
        if not workspace.exists():
            pytest.skip("Workspace Replit não disponível neste ambiente")

        call_sites: list[str] = []
        exclude_names = frozenset({"hitl_approval_context.py", "hitl_service.py"})

        for py_file in workspace.rglob("*.py"):
            if py_file.name in exclude_names:
                continue
            if "test_" in py_file.name or "__pycache__" in str(py_file):
                continue

            try:
                source = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            if "hitl_preflight" not in source:
                continue

            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else func.attr
                    if isinstance(func, ast.Attribute)
                    else None
                )
                if name == "hitl_preflight":
                    rel = py_file.relative_to(workspace)
                    call_sites.append(f"{rel}:{node.lineno}")

        assert len(call_sites) >= 7, (
            f"D2-07h: Apenas {len(call_sites)} call sites de hitl_preflight encontrados "
            f"(ratchet ≥7, commit 8dea17558). "
            f"Sites: {call_sites}"
        )
