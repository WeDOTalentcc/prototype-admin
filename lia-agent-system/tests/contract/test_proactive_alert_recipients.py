"""Sensor E5 (escopo): alertas proativos vao para TODOS os recrutadores.

Causa raiz (2026-06-09): run_proactive_alerts usava func.min(User.id) group by
company_id + role==admin -> SO 1 admin por empresa recebia os 15 alertas. Os
demais recrutadores nunca eram notificados. Decisao Paulo: cada recrutador
(admin/manager/recruiter) recebe conforme sua preferencia (cooldown por-user
evita spam entre runs).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def test_recipient_roles_include_recruiter_and_manager_not_only_admin():
    """Sensor anti-regressao: nao voltar a notificar so admin."""
    from app.auth.models import UserRole
    from app.domains.automation.services.automation_scheduler import (
        AutomationScheduler,
    )

    roles = AutomationScheduler.PROACTIVE_ALERT_RECIPIENT_ROLES
    # StrEnum compara igual a str, entao funciona com constante de strings.
    assert UserRole.recruiter in roles, "recrutadores devem receber alertas"
    assert UserRole.manager in roles, "managers devem receber alertas"
    assert UserRole.admin in roles, "admins devem receber alertas"


@pytest.mark.asyncio
async def test_select_recipients_does_not_collapse_to_one_per_company():
    """O seletor retorna todos os recrutadores ativos, sem agrupar por empresa."""
    from app.domains.automation.services.automation_scheduler import (
        AutomationScheduler,
    )

    captured = {}

    async def fake_execute(query):
        captured["sql"] = str(query)
        r = MagicMock()
        # 2 users da MESMA empresa c1 + 1 de c2: devem voltar os 3.
        r.all = MagicMock(return_value=[("c1", "u1"), ("c1", "u2"), ("c2", "u3")])
        return r

    db = MagicMock()
    db.execute = AsyncMock(side_effect=fake_execute)

    pairs = await AutomationScheduler._select_proactive_alert_recipients(db)

    assert pairs == [("c1", "u1"), ("c1", "u2"), ("c2", "u3")], (
        "todos os recrutadores devem ser retornados (2 da mesma empresa inclusive)"
    )
    sql = captured["sql"].upper()
    assert "GROUP BY" not in sql, "nao deve agrupar/limitar a 1 destinatario por empresa"
    assert "MIN(" not in sql, "nao deve usar func.min (limitava a 1 admin/empresa)"
