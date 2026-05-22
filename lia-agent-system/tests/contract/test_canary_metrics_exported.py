"""WT-2022 contract test: canary metrics estao exportadas e funcionando.

Garante que os 4 counters Prometheus canary em
app.shared.observability.canary_metrics sao importaveis, sao instancias
reais de Counter (nao None de fail-open), e suportam .inc() sem raise.

Por que contract test (e nao unit test):
Counters Prometheus sao SINAIS de observability que outros servicos /
dashboards Grafana / alarmes oncall confiam. Se um counter desaparece
silenciosamente (refactor que delete o modulo, typo em label), o sinal
sera 0 forever e ninguem percebe ate o proximo incidente.

Este contract test eh o sensor canonical: roda em CI, falha se contract
quebrar (counter removido, renomeado, ou labels alteradas).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------- #
# 1. Imports nao raise + counters nao sao None.
# ---------------------------------------------------------------------- #


def test_ai_credit_exhausted_counter_exists():
    from app.shared.observability.canary_metrics import ai_credit_exhausted_total

    assert ai_credit_exhausted_total is not None, (
        "ai_credit_exhausted_total eh None -- prometheus_client nao instalado "
        "ou registro falhou. Sinal canary perdido."
    )


def test_fairness_guard_skip_counter_exists():
    from app.shared.observability.canary_metrics import fairness_guard_skip_total

    assert fairness_guard_skip_total is not None, (
        "fairness_guard_skip_total eh None -- sinal canary REGRA 4 perdido."
    )


def test_dsr_overdue_created_counter_exists():
    from app.shared.observability.canary_metrics import dsr_overdue_created_total

    assert dsr_overdue_created_total is not None, (
        "dsr_overdue_created_total eh None -- sinal SLA LGPD perdido."
    )


def test_tasks_cross_tenant_blocked_counter_exists():
    from app.shared.observability.canary_metrics import (
        tasks_cross_tenant_blocked_total,
    )

    assert tasks_cross_tenant_blocked_total is not None, (
        "tasks_cross_tenant_blocked_total eh None -- sinal de bug em "
        "RuntimeContext propagation perdido."
    )


# ---------------------------------------------------------------------- #
# 2. Counters suportam .inc() sem raise.
# ---------------------------------------------------------------------- #


def test_ai_credit_counter_increments():
    from app.shared.observability.canary_metrics import ai_credit_exhausted_total

    label_hash = "test_hash_12char"
    initial = ai_credit_exhausted_total.labels(
        company_id_hash=label_hash
    )._value.get()
    ai_credit_exhausted_total.labels(company_id_hash=label_hash).inc()
    final = ai_credit_exhausted_total.labels(company_id_hash=label_hash)._value.get()
    assert final == pytest.approx(initial + 1), (
        f"Counter nao incrementou: initial={initial} final={final}"
    )


def test_fairness_counter_increments():
    from app.shared.observability.canary_metrics import fairness_guard_skip_total

    initial = fairness_guard_skip_total.labels(
        caller_module="test_module"
    )._value.get()
    fairness_guard_skip_total.labels(caller_module="test_module").inc()
    final = fairness_guard_skip_total.labels(caller_module="test_module")._value.get()
    assert final == pytest.approx(initial + 1)


def test_dsr_counter_increments():
    from app.shared.observability.canary_metrics import dsr_overdue_created_total

    initial = dsr_overdue_created_total._value.get()
    dsr_overdue_created_total.inc()
    final = dsr_overdue_created_total._value.get()
    assert final == pytest.approx(initial + 1)


def test_tasks_counter_increments():
    from app.shared.observability.canary_metrics import (
        tasks_cross_tenant_blocked_total,
    )

    initial = tasks_cross_tenant_blocked_total.labels(
        method="test_method"
    )._value.get()
    tasks_cross_tenant_blocked_total.labels(method="test_method").inc()
    final = tasks_cross_tenant_blocked_total.labels(
        method="test_method"
    )._value.get()
    assert final == pytest.approx(initial + 1)


# ---------------------------------------------------------------------- #
# 3. Contract labels: counters tem labels esperadas (anti-rename).
# ---------------------------------------------------------------------- #


def test_ai_credit_has_company_id_hash_label():
    from app.shared.observability.canary_metrics import ai_credit_exhausted_total

    # _labelnames eh tuple privada do Counter -- usar pra contract check
    assert "company_id_hash" in ai_credit_exhausted_total._labelnames, (
        "ai_credit_exhausted_total perdeu label company_id_hash -- contract break."
    )


def test_fairness_has_caller_module_label():
    from app.shared.observability.canary_metrics import fairness_guard_skip_total

    assert "caller_module" in fairness_guard_skip_total._labelnames, (
        "fairness_guard_skip_total perdeu label caller_module -- contract break."
    )


def test_tasks_has_method_label():
    from app.shared.observability.canary_metrics import (
        tasks_cross_tenant_blocked_total,
    )

    assert "method" in tasks_cross_tenant_blocked_total._labelnames, (
        "tasks_cross_tenant_blocked_total perdeu label method -- contract break."
    )


def test_dsr_has_no_labels():
    """dsr_overdue_created_total eh counter SEM label (global)."""
    from app.shared.observability.canary_metrics import dsr_overdue_created_total

    assert dsr_overdue_created_total._labelnames == (), (
        "dsr_overdue_created_total tem labels inesperados -- "
        f"esperado tuple vazia, got {dsr_overdue_created_total._labelnames}"
    )
