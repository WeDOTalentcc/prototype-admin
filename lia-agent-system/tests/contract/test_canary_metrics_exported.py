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
    # Wave 3 (2026-05-22): counter now has 2 labels (company_id_hash + service).
    from app.shared.observability.canary_metrics import ai_credit_exhausted_total

    label_hash = "test_hash_12char"
    svc = "test_service"
    initial = ai_credit_exhausted_total.labels(
        company_id_hash=label_hash, service=svc
    )._value.get()
    ai_credit_exhausted_total.labels(company_id_hash=label_hash, service=svc).inc()
    final = ai_credit_exhausted_total.labels(
        company_id_hash=label_hash, service=svc
    )._value.get()
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


# ---------------------------------------------------------------------- #
# 4. Hardening C.2 -- PolicyEngine runtime invocations.
# ---------------------------------------------------------------------- #


def test_policy_engine_invocations_counter_exists():
    from app.shared.observability.canary_metrics import (
        policy_engine_runtime_invocations_total,
    )

    assert policy_engine_runtime_invocations_total is not None, (
        "policy_engine_runtime_invocations_total eh None -- "
        "sinal canary Hardening C.2 perdido."
    )


def test_policy_engine_has_method_label():
    from app.shared.observability.canary_metrics import (
        policy_engine_runtime_invocations_total,
    )

    assert "method" in policy_engine_runtime_invocations_total._labelnames, (
        "policy_engine_runtime_invocations_total perdeu label method "
        "-- contract break."
    )


def test_policy_engine_inc_helper_increments():
    from prometheus_client import REGISTRY
    from app.shared.observability.canary_metrics import (
        inc_policy_engine_invocation,
        policy_engine_runtime_invocations_total,
    )

    initial = (
        policy_engine_runtime_invocations_total.labels(method="evaluate")
        ._value.get()
    )
    inc_policy_engine_invocation("evaluate")
    final = REGISTRY.get_sample_value(
        "policy_engine_runtime_invocations_total", {"method": "evaluate"}
    )
    assert final == pytest.approx(initial + 1), (
        f"Counter nao incrementou: initial={initial} final={final}"
    )


def test_policy_engine_inc_helper_rejects_unknown_method():
    """Cardinality guard: metodos fora da whitelist NAO incrementam."""
    from app.shared.observability.canary_metrics import (
        inc_policy_engine_invocation,
        policy_engine_runtime_invocations_total,
    )

    # Acessar labels com valor desconhecido nao cria sample (skipped silently)
    # Verificamos chamando e confirmando que .labels(method="unknown")
    # nao foi criado como sample (._value.get() retorna 0 se nunca chamado).
    inc_policy_engine_invocation("not_a_real_method")
    # Se o guard funcionou, nenhum sample com method="not_a_real_method"
    # foi criado. Tentar acessar via labels() criaria o sample com 0,
    # entao usamos REGISTRY.get_sample_value pra check non-destructive.
    from prometheus_client import REGISTRY
    sample = REGISTRY.get_sample_value(
        "policy_engine_runtime_invocations_total",
        {"method": "not_a_real_method"},
    )
    assert sample is None, (
        "Cardinality guard falhou: method='not_a_real_method' criou sample. "
        "inc_policy_engine_invocation deveria rejeitar valores fora da "
        "whitelist _POLICY_ENGINE_METHODS."
    )


# ---------------------------------------------------------------------- #
# 5. Hardening C.3 -- LGPD granular consent revoke per purpose.
# ---------------------------------------------------------------------- #


def test_granular_consent_revoke_counter_exists():
    from app.shared.observability.canary_metrics import (
        granular_consent_revoke_per_purpose_total,
    )

    assert granular_consent_revoke_per_purpose_total is not None, (
        "granular_consent_revoke_per_purpose_total eh None -- "
        "sinal canary Hardening C.3 perdido."
    )


def test_granular_consent_revoke_has_purpose_label():
    from app.shared.observability.canary_metrics import (
        granular_consent_revoke_per_purpose_total,
    )

    assert (
        "purpose" in granular_consent_revoke_per_purpose_total._labelnames
    ), (
        "granular_consent_revoke_per_purpose_total perdeu label purpose "
        "-- contract break."
    )


def test_granular_consent_revoke_inc_helper_increments():
    from prometheus_client import REGISTRY
    from app.shared.observability.canary_metrics import (
        inc_granular_consent_revoke,
        granular_consent_revoke_per_purpose_total,
    )

    initial = (
        granular_consent_revoke_per_purpose_total.labels(
            purpose="ai_screening"
        )._value.get()
    )
    inc_granular_consent_revoke("ai_screening")
    final = REGISTRY.get_sample_value(
        "granular_consent_revoke_per_purpose_total",
        {"purpose": "ai_screening"},
    )
    assert final == pytest.approx(initial + 1), (
        f"Counter nao incrementou: initial={initial} final={final}"
    )


def test_granular_consent_revoke_inc_rejects_unknown_purpose():
    """Cardinality guard + LGPD: typos NAO podem criar timeseries arbitrarias."""
    from prometheus_client import REGISTRY
    from app.shared.observability.canary_metrics import (
        inc_granular_consent_revoke,
    )

    inc_granular_consent_revoke("typo_purpose_not_canonical")
    sample = REGISTRY.get_sample_value(
        "granular_consent_revoke_per_purpose_total",
        {"purpose": "typo_purpose_not_canonical"},
    )
    assert sample is None, (
        "Cardinality guard falhou: purpose typo criou sample. "
        "inc_granular_consent_revoke deveria rejeitar valores fora da "
        "whitelist _GRANULAR_CONSENT_PURPOSES."
    )
