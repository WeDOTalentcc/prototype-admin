"""T-1157 — Property tests para os endpoints públicos de self-scheduling.

Cobertura:

* Token não encontrado → 404.
* Token expirado (``status="expired"`` ou ``expires_at`` no passado) → 410.
* Token já utilizado (``status="used"``) → 410 (defesa contra replay).
* Confirm em token utilizado → 410 (defesa contra replay no caminho de
  mutation).
* GET retorna APENAS campos da whitelist pública — sem ``candidate_email``,
  ``candidate_phone``, ``company_id``, ``candidate_id``, ``interviewer_emails``
  ou outros internals (defesa contra information disclosure / PII leakage).
* POST ``/link`` (recrutador) sobrescreve ``body.company_id`` com o claim
  do JWT (defesa contra tenant-spoofing via body).
* Middleware: ``PUBLIC_REGEX_PATHS`` libera apenas o token endpoint +
  confirm; NÃO libera sub-rotas como ``/api/v1/scheduling/link/admin/X``
  ou o POST de criação ``/api/v1/scheduling/link``.

Os testes são **hermeticos**: chamam as funções dos endpoints
diretamente como corrotinas com o ``zero_touch_scheduling_service``
monkeypatched. Não dependem de DB, FastAPI TestClient ou rede.

Origem: Task #1157 (gap apontado em code review do bundle inicial).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v1 import self_scheduling_public as ssp
from app.middleware.auth_enforcement import (
    PUBLIC_PREFIXES,
    _path_matches_public_regex,
)


VALID_TOKEN = "abcdef0123456789abcdef0123456789"  # 32-char, dentro do regex
SHORT_TOKEN = "tooshort"  # 8-char, fora do regex (< 16)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _valid_link_payload() -> dict[str, Any]:
    return {
        "status": "pending",
        "candidate_name": "Maria Silva",
        "candidate_email": "maria@example.com",       # PII — não deve vazar
        "candidate_phone": "+5511999999999",          # PII — não deve vazar
        "candidate_id": "cand-uuid-XXX",              # interno — não deve vazar
        "company_id": "comp-uuid-YYY",                # interno — não deve vazar
        "interviewer_emails": ["rec@empresa.com"],    # PII — não deve vazar
        "job_title": "Engenheira de Software",
        "interview_type": "tech",
        "interview_mode": "video",
        "duration_minutes": 60,
        "available_slots": [{"start": "2099-12-31T10:00:00", "end": "2099-12-31T11:00:00"}],
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "is_valid": True,
    }


# ── Property 1: token não encontrado ──────────────────────────────────────────


def test_get_link_returns_404_when_token_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "get_link_by_token",
        AsyncMock(return_value=None),
    )
    with pytest.raises(HTTPException) as exc:
        _run(ssp.get_scheduling_link(token=VALID_TOKEN, db=None))
    assert exc.value.status_code == 404


# ── Property 2: token expirado (status) → 410 ─────────────────────────────────


def test_get_link_returns_410_when_status_used(monkeypatch) -> None:
    payload = _valid_link_payload()
    payload["status"] = "used"
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "get_link_by_token",
        AsyncMock(return_value=payload),
    )
    with pytest.raises(HTTPException) as exc:
        _run(ssp.get_scheduling_link(token=VALID_TOKEN, db=None))
    assert exc.value.status_code == 410


# ── Property 3: token expirado (expires_at < now) → 410 ───────────────────────


def test_get_link_returns_410_when_expires_at_in_past(monkeypatch) -> None:
    payload = _valid_link_payload()
    payload["expires_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "get_link_by_token",
        AsyncMock(return_value=payload),
    )
    with pytest.raises(HTTPException) as exc:
        _run(ssp.get_scheduling_link(token=VALID_TOKEN, db=None))
    assert exc.value.status_code == 410


# ── Property 4: GET response não vaza PII / internals ─────────────────────────


_PII_AND_INTERNAL_KEYS = {
    "candidate_email",
    "candidate_phone",
    "candidate_id",
    "company_id",
    "interviewer_emails",
    "created_by",
    "use_count",
    "max_uses",
    "id",
}


def test_get_link_response_does_not_leak_pii_or_internals(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "get_link_by_token",
        AsyncMock(return_value=_valid_link_payload()),
    )
    result = _run(ssp.get_scheduling_link(token=VALID_TOKEN, db=None))
    leaked = _PII_AND_INTERNAL_KEYS & set(result.keys())
    assert not leaked, (
        f"T-1157 — GET /scheduling/link/{{token}} vazou chaves "
        f"sensíveis: {sorted(leaked)}. Whitelist é {sorted(result.keys())}."
    )
    # candidate_name é OK (já está no link compartilhado por email/WhatsApp)
    assert "candidate_name" in result
    assert "available_slots" in result


# ── Property 5: confirm replay → 410 ──────────────────────────────────────────


def test_confirm_slot_returns_410_on_replay(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "confirm_slot",
        AsyncMock(return_value={"success": False, "error": "Link já utilizado"}),
    )
    body = ssp.ConfirmSlotRequest(start="2099-12-31T10:00:00", end="2099-12-31T11:00:00")
    with pytest.raises(HTTPException) as exc:
        _run(ssp.confirm_scheduling_slot(token=VALID_TOKEN, body=body, db=None))
    assert exc.value.status_code == 410


def test_confirm_slot_returns_410_on_expired(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "confirm_slot",
        AsyncMock(return_value={"success": False, "error": "Link expirado"}),
    )
    body = ssp.ConfirmSlotRequest(start="2099-12-31T10:00:00", end="2099-12-31T11:00:00")
    with pytest.raises(HTTPException) as exc:
        _run(ssp.confirm_scheduling_slot(token=VALID_TOKEN, body=body, db=None))
    assert exc.value.status_code == 410


def test_confirm_slot_returns_404_when_token_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "confirm_slot",
        AsyncMock(return_value={"success": False, "error": "Link não encontrado"}),
    )
    body = ssp.ConfirmSlotRequest(start="2099-12-31T10:00:00", end="2099-12-31T11:00:00")
    with pytest.raises(HTTPException) as exc:
        _run(ssp.confirm_scheduling_slot(token=VALID_TOKEN, body=body, db=None))
    assert exc.value.status_code == 404


def test_confirm_slot_success_returns_200_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "confirm_slot",
        AsyncMock(return_value={
            "success": True,
            "candidate_name": "Maria Silva",
            "job_title": "Engenheira de Software",
            "selected_slot": {"start": "2099-12-31T10:00:00", "end": "2099-12-31T11:00:00"},
        }),
    )
    body = ssp.ConfirmSlotRequest(start="2099-12-31T10:00:00", end="2099-12-31T11:00:00")
    result = _run(ssp.confirm_scheduling_slot(token=VALID_TOKEN, body=body, db=None))
    assert result["success"] is True
    assert result["candidate_name"] == "Maria Silva"
    # garante que NÃO vazou campos internos do service
    assert "company_id" not in result
    assert "candidate_id" not in result


# ── Property 6: POST /link (recrutador) sobrescreve company_id ────────────────


def test_create_scheduling_link_overrides_spoofed_company_id(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return {"success": True, "token": "x" * 32, "url": "https://app/x"}

    monkeypatch.setattr(
        ssp.zero_touch_scheduling_service,
        "send_scheduling_link",
        _capture,
    )

    body = ssp.CreateSchedulingLinkRequest(
        company_id="ATTACKER-TENANT",         # spoof
        candidate_id="cand-1",
        candidate_name="X",
        candidate_email="x@example.com",
        job_vacancy_id="job-1",
        job_title="X",
        available_slots=[ssp.SlotSchema(start="2099-12-31T10:00:00", end="2099-12-31T11:00:00")],
        interviewer_emails=["r@e.com"],
    )

    class _FakeUser:
        id = "user-1"

    _run(ssp.create_scheduling_link(
        body=body,
        current_user=_FakeUser(),
        db=None,
        company_id="LEGIT-TENANT",  # claim do JWT
    ))

    assert captured["company_id"] == "LEGIT-TENANT", (
        "T-1157 — body.company_id devia ter sido sobrescrito pelo claim "
        f"do JWT. captured.company_id={captured['company_id']!r}"
    )
    # body in-memory também foi corrigido (defesa em profundidade)
    assert body.company_id == "LEGIT-TENANT"


# ── Property 7: middleware regex matcher ──────────────────────────────────────


def test_middleware_public_regex_matches_only_intended_paths() -> None:
    # Públicos legítimos
    assert _path_matches_public_regex(f"/api/v1/scheduling/link/{VALID_TOKEN}")
    assert _path_matches_public_regex(f"/api/v1/scheduling/link/{VALID_TOKEN}/confirm")

    # NÃO públicos (devem retornar False → middleware exige JWT)
    assert not _path_matches_public_regex("/api/v1/scheduling/link")  # criação recrutador
    assert not _path_matches_public_regex("/api/v1/scheduling/link/")  # bare trailing slash
    assert not _path_matches_public_regex(f"/api/v1/scheduling/link/{VALID_TOKEN}/admin")
    assert not _path_matches_public_regex(f"/api/v1/scheduling/link/{VALID_TOKEN}/cancel")
    assert not _path_matches_public_regex("/api/v1/scheduling/link/admin/anything")
    assert not _path_matches_public_regex(f"/api/v1/scheduling/link/{SHORT_TOKEN}")  # token curto


def test_middleware_no_longer_uses_broad_scheduling_prefix() -> None:
    """Sentinela contra regressão: o prefixo amplo
    `/api/v1/scheduling/link/` não pode reaparecer em
    ``PUBLIC_PREFIXES`` (sub-rotas ficariam acidentalmente públicas).
    Use ``PUBLIC_REGEX_PATHS`` em vez disso.
    """
    assert "/api/v1/scheduling/link/" not in PUBLIC_PREFIXES, (
        "T-1157 — prefixo amplo `/api/v1/scheduling/link/` voltou para "
        "PUBLIC_PREFIXES. Use PUBLIC_REGEX_PATHS para limitar a apenas "
        "GET /link/{token} e POST /link/{token}/confirm."
    )
