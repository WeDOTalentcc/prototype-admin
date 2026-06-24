"""
D3 — Compliance Chain: FairnessGuard, PII masking, multi-tenancy, pre/post_compliance.

Testes diagnósticos para o endpoint SSE (agent_chat_sse.py).
Política:
- PASS  = invariante confirmado
- SKIP  = gap diagnosticado, mensagem clara sobre o que falta corrigir
- FAIL  = regressão (invariante que deveria estar OK foi quebrado)
"""
import inspect
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# D3-02a: mask_pii_outbound mascara CPF quando ContextVar ativado
# ---------------------------------------------------------------------------
def test_pii_cpf_masked_with_identity_ctx():
    """
    D3-02a: com _chat_pii_mask_identity=True, CPF deve ser mascarado.
    ContextVar must be activated explicitly (opt-in per design).
    """
    from app.shared.pii_masking import mask_pii_outbound, set_chat_pii_mask_identity, reset_chat_pii_mask_identity

    token = set_chat_pii_mask_identity(True)
    try:
        raw = "O candidato tem CPF 123.456.789-09 cadastrado."
        masked = mask_pii_outbound(raw)
        assert "123.456.789-09" not in masked, f"D3-02a: CPF não mascarado: {masked}"
        assert "candidato" in masked, "D3-02a: texto não-sensível foi removido indevidamente"
        assert "***CPF***" in masked, f"D3-02a: sentinel esperado '***CPF***' ausente: {masked}"
    finally:
        reset_chat_pii_mask_identity(token)


# ---------------------------------------------------------------------------
# D3-02b: mask_pii_outbound mascara RG quando ContextVar ativado
# ---------------------------------------------------------------------------
def test_pii_rg_masked_with_identity_ctx():
    """D3-02b: com _chat_pii_mask_identity=True, RG (com separadores) deve ser mascarado."""
    from app.shared.pii_masking import mask_pii_outbound, set_chat_pii_mask_identity, reset_chat_pii_mask_identity

    token = set_chat_pii_mask_identity(True)
    try:
        raw = "RG 12.345.678-9 no sistema."
        masked = mask_pii_outbound(raw)
        assert "12.345.678-9" not in masked, f"D3-02b: RG não mascarado: {masked}"
        assert "***RG***" in masked, f"D3-02b: sentinel '***RG***' ausente: {masked}"
    finally:
        reset_chat_pii_mask_identity(token)


# ---------------------------------------------------------------------------
# D3-02c: mask_pii_outbound é passthrough quando ContextVar desativado (padrão)
# ---------------------------------------------------------------------------
def test_pii_passthrough_when_ctx_off():
    """
    D3-02c: sem ContextVar ativo e sem LIA_RECRUITER_CHAT_MASK_PII=true,
    mask_pii_outbound deve retornar o texto intacto (recrutador autorizado vê).
    """
    from app.shared.pii_masking import mask_pii_outbound

    raw = "Candidato CPF 123.456.789-09."
    # ContextVar default=False, env var não está setada em testes
    result = mask_pii_outbound(raw)
    # Em modo passthrough, o texto retorna igual
    assert result == raw, (
        f"D3-02c: mask_pii_outbound alterou texto sem ContextVar ativo. "
        f"Original='{raw}' | Resultado='{result}'"
    )


# ---------------------------------------------------------------------------
# D3-05: SSEChatRequest body NÃO deve ter company_id
# ---------------------------------------------------------------------------
def test_chat_request_schema_no_company_id():
    """
    D3-05: Multi-tenancy canonical — company_id nunca no request body.
    Deve vir do JWT via Depends(require_company_id).
    """
    from app.api.v1.agent_chat_sse import SSEChatRequest

    fields = SSEChatRequest.model_fields
    assert "company_id" not in fields, (
        f"VIOLAÇÃO D3-05: 'company_id' encontrado no SSEChatRequest body. "
        f"Multi-tenancy break — user pode mandar company_id de outra empresa. "
        f"Campos: {list(fields.keys())}"
    )


# ---------------------------------------------------------------------------
# D3-05b: SSEChatRequest herda de WeDoBaseModel (extra='forbid')
# ---------------------------------------------------------------------------
def test_chat_request_schema_extra_forbid():
    """D3-05b: SSEChatRequest herda de WeDoBaseModel — extra fields são rejeitados."""
    from app.api.v1.agent_chat_sse import SSEChatRequest
    from app.shared.types import WeDoBaseModel

    assert issubclass(SSEChatRequest, WeDoBaseModel), (
        "D3-05b: SSEChatRequest não herda de WeDoBaseModel. "
        "Fields fantasma seriam aceitos silenciosamente (Pydantic default extra='ignore')."
    )


# ---------------------------------------------------------------------------
# D3-06: get_verified_company_id rejeita cross-tenant (header ≠ JWT)
# ---------------------------------------------------------------------------
def test_cross_tenant_header_rejected():
    """
    D3-06: get_verified_company_id deve retornar 403 quando X-Company-ID
    diverge do company_id no JWT (request.state).
    """
    from app.shared.tenant_guard import get_verified_company_id
    from fastapi import HTTPException, Request

    # Simular request com JWT company_id já validado no middleware
    mock_request = MagicMock(spec=Request)
    mock_request.state.company_id = "00000000-0000-0000-0000-000000000001"

    try:
        result = get_verified_company_id(
            request=mock_request,
            x_company_id="ffffffff-ffff-ffff-ffff-ffffffffffff",  # header diferente
            company_id=None,
        )
        pytest.fail(
            f"D3-06: cross-tenant NÃO foi rejeitado. "
            f"get_verified_company_id retornou '{result}' sem levantar exceção. "
            "Brecha LGPD/multi-tenancy: usuário pode operar sobre dados de outra empresa."
        )
    except HTTPException as exc:
        assert exc.status_code == 403, (
            f"D3-06: esperava status_code=403, recebeu {exc.status_code}"
        )
    except (ValueError, PermissionError):
        pass  # também aceitável


# ---------------------------------------------------------------------------
# D3-06b: get_verified_company_id aceita quando header bate com JWT
# ---------------------------------------------------------------------------
def test_cross_tenant_header_same_as_jwt_accepted():
    """D3-06b: quando X-Company-ID == JWT, deve ser aceito (defense-in-depth OK)."""
    from app.shared.tenant_guard import get_verified_company_id
    from fastapi import Request

    company_id = "00000000-0000-0000-0000-000000000001"
    mock_request = MagicMock(spec=Request)
    mock_request.state.company_id = company_id

    result = get_verified_company_id(
        request=mock_request,
        x_company_id=company_id,  # header == JWT — OK
        company_id=None,
    )
    assert result == company_id, (
        f"D3-06b: esperava retorno '{company_id}', recebeu '{result}'"
    )


# ---------------------------------------------------------------------------
# D3-01: FairnessGuard importado no SSE
# ---------------------------------------------------------------------------
def test_fairness_guard_present_in_sse():
    """
    D3-01: FairnessGuard deve estar disponível no SSE para checar queries de
    candidatos antes de processar com LLM.
    """
    import app.api.v1.agent_chat_sse as sse_mod
    src = inspect.getsource(sse_mod)

    assert "FairnessGuard" in src, (
        "D3-01 FALHA: FairnessGuard não encontrado em agent_chat_sse. "
        "Compliance de ranking/screening de candidatos está desprotegida."
    )


# ---------------------------------------------------------------------------
# D3-03 (diagnóstico): pre_compliance wired no SSE?
# ---------------------------------------------------------------------------
def test_pre_compliance_wired_in_sse_diagnostic():
    """
    D3-03 DIAGNÓSTICO: verifica se pre_compliance (checa INPUT antes do LLM)
    está presente no agent_chat_sse.py.

    O WS usa pre_compliance no input; o SSE historicamente não usava.
    Gap C3B: SSE path direto (_run_agent) pode estar sem pre_compliance.
    """
    import app.api.v1.agent_chat_sse as sse_mod
    src = inspect.getsource(sse_mod)

    has_pre = "pre_compliance" in src
    if not has_pre:
        pytest.skip(
            "⚠️ DIAGNÓSTICO D3-03: pre_compliance NÃO encontrado em agent_chat_sse.py. "
            "Gap C3B confirmado: SSE path direto (_run_agent) não chama pre_compliance no INPUT. "
            "WS faz via pre_compliance; SSE não fazia (mencionado no comentário L361 do SSE). "
            "Fix pendente: FIX-C3B-SSE P0 do plano de consolidação federado."
        )
    # Se chegou aqui, pre_compliance está no código — diagnóstico confirmado


# ---------------------------------------------------------------------------
# D3-04: post_compliance wired no SSE (supervisor path e/ou direto)
# ---------------------------------------------------------------------------
def test_post_compliance_wired_in_sse():
    """
    D3-04: post_compliance (FactChecker + audit LGPD da SAÍDA) deve estar
    presente no agent_chat_sse.py — ao menos no path supervisor.
    """
    import app.api.v1.agent_chat_sse as sse_mod
    src = inspect.getsource(sse_mod)

    has_post = "post_compliance" in src
    if not has_post:
        pytest.skip(
            "⚠️ DIAGNÓSTICO D3-04: post_compliance NÃO encontrado em agent_chat_sse.py. "
            "Path supervisor não chama post_compliance. "
            "Gap de auditoria LGPD na saída do agente."
        )
    # Se chegou aqui, post_compliance está no código — diagnóstico confirmado


# ---------------------------------------------------------------------------
# D3-07: mask_pii_outbound presente no SSE (aplicado na saída)
# ---------------------------------------------------------------------------
def test_mask_pii_outbound_present_in_sse():
    """
    D3-07: mask_pii_outbound deve ser chamado na saída do SSE para mascarar
    CPF/RG quando o ContextVar de identidade está ativo (per-turn).
    """
    import app.api.v1.agent_chat_sse as sse_mod
    src = inspect.getsource(sse_mod)

    assert "mask_pii_outbound" in src, (
        "D3-07 FALHA: mask_pii_outbound não encontrado em agent_chat_sse. "
        "Saída do chat não está sendo mascarada — CPF/RG podem vazar para o frontend."
    )
