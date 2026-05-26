"""Sensor PR-9 (F-3.1 sub-sprint A): ws_stage_payload helper canonical.

Cobre:
1. build_ws_stage_payload retorna shape canonical para todos os stage names.
2. Validacao defensiva (stage canonical, message obrigatorio, types corretos).
3. Byte-identical: payload construido via helper == dict literal manual.
4. ui_action opcional preservado.
"""

from __future__ import annotations

import pytest

from app.domains.job_creation.helpers.ws_payload_builder import (
    WIZARD_STAGE_NAMES,
    build_ws_stage_payload,
)


# ─── Shape canonical ──────────────────────────────────────────────────


class TestShapeCanonical:
    """payload tem keys canonical sempre presentes."""

    def test_minimal_payload_has_all_required_keys(self):
        payload = build_ws_stage_payload(
            stage="intake",
            completeness=0.1,
            requires_approval=False,
            data={"message": "ok"},
        )
        assert set(payload.keys()) == {
            "type", "stage", "data", "completeness", "requires_approval",
        }
        assert payload["type"] == "wizard_stage"

    def test_payload_without_completeness_omits_key(self):
        """Block paths sites originais omitem completeness — preservar byte-equiv."""
        payload = build_ws_stage_payload(
            stage="jd_enrichment",
            requires_approval=False,
            data={"message": "fairness blocked"},
            # completeness omitido (default None)
        )
        assert "completeness" not in payload
        assert set(payload.keys()) == {"type", "stage", "data", "requires_approval"}

    def test_payload_with_ui_action_adds_key(self):
        payload = build_ws_stage_payload(
            stage="pipeline_template",
            completeness=0.3,
            requires_approval=True,
            ui_action="suggest_pipeline_template",
            data={"message": "ok", "templates": []},
        )
        assert payload["ui_action"] == "suggest_pipeline_template"
        assert set(payload.keys()) == {
            "type", "stage", "data", "completeness", "requires_approval", "ui_action",
        }

    def test_ui_action_none_omits_key(self):
        payload = build_ws_stage_payload(
            stage="intake",
            completeness=0,
            requires_approval=False,
            data={"message": "ok"},
            ui_action=None,
        )
        assert "ui_action" not in payload

    @pytest.mark.parametrize("stage", WIZARD_STAGE_NAMES)
    def test_all_canonical_stages_accepted(self, stage):
        payload = build_ws_stage_payload(
            stage=stage,
            completeness=0.5,
            requires_approval=False,
            data={"message": f"stage {stage}"},
        )
        assert payload["stage"] == stage
        assert payload["type"] == "wizard_stage"


# ─── Validacao defensiva ──────────────────────────────────────────────


class TestValidation:
    """Helper falha alto contra inputs invalidos (REGRA 4 anti-silent-fallback)."""

    def test_invalid_stage_raises_valueerror(self):
        with pytest.raises(ValueError, match="nao e canonical"):
            build_ws_stage_payload(
                stage="invalid_stage",
                completeness=0,
                requires_approval=False,
                data={"message": "x"},
            )

    def test_missing_message_raises_valueerror(self):
        """Task #1099 invariant: data.message obrigatorio."""
        with pytest.raises(ValueError, match="message.*obrigatorio"):
            build_ws_stage_payload(
                stage="intake",
                completeness=0,
                requires_approval=False,
                data={"foo": "bar"},  # sem message
            )

    def test_empty_message_raises_valueerror(self):
        with pytest.raises(ValueError, match="message.*obrigatorio"):
            build_ws_stage_payload(
                stage="intake",
                completeness=0,
                requires_approval=False,
                data={"message": ""},
            )

    def test_data_not_dict_raises_typeerror(self):
        with pytest.raises(TypeError, match="data deve ser dict"):
            build_ws_stage_payload(
                stage="intake",
                completeness=0,
                requires_approval=False,
                data="not a dict",  # type: ignore[arg-type]
            )

    def test_requires_approval_not_bool_raises_typeerror(self):
        with pytest.raises(TypeError, match="requires_approval deve ser bool"):
            build_ws_stage_payload(
                stage="intake",
                completeness=0,
                requires_approval=1,  # type: ignore[arg-type]
                data={"message": "x"},
            )

    def test_completeness_out_of_range_raises(self):
        with pytest.raises(ValueError, match="completeness.*fora de"):
            build_ws_stage_payload(
                stage="intake",
                completeness=1.5,
                requires_approval=False,
                data={"message": "x"},
            )

    def test_completeness_negative_raises(self):
        with pytest.raises(ValueError, match="completeness.*fora de"):
            build_ws_stage_payload(
                stage="intake",
                completeness=-0.1,
                requires_approval=False,
                data={"message": "x"},
            )


# ─── Byte-identical: helper == literal canonical pre-refactor ─────────


class TestByteIdenticalWithLiteralForm:
    """payload construido via helper == dict literal usado nos 20 sites originais.

    Caso 1: intake_node:746 minimal shape (sem ui_action).
    Caso 2: pipeline_template_node:1621 com ui_action.
    Caso 3: bigfive policy block (completeness=0).
    Caso 4: handoff_node:3160 (completeness=1.0).
    """

    def test_intake_node_shape(self):
        data = {
            "message": "Captei: Engenheiro de Software.",
            "raw_input": "vamos abrir vaga de eng",
            "parsed_title": "Engenheiro de Software",
        }
        helper = build_ws_stage_payload(
            stage="intake",
            completeness=0.083,
            requires_approval=False,
            data=data,
        )
        literal = {
            "type": "wizard_stage",
            "stage": "intake",
            "data": data,
            "completeness": 0.083,
            "requires_approval": False,
        }
        assert helper == literal

    def test_pipeline_template_node_shape_with_ui_action(self):
        data = {
            "message": "Vamos usar este pipeline?",
            "templates": [],
            "suggested_template_id": "tpl-1",
            "allow_skip": True,
        }
        helper = build_ws_stage_payload(
            stage="pipeline_template",
            completeness=0.166,
            requires_approval=True,
            ui_action="suggest_pipeline_template",
            data=data,
        )
        literal = {
            "type": "wizard_stage",
            "stage": "pipeline_template",
            "ui_action": "suggest_pipeline_template",
            "data": data,
            "completeness": 0.166,
            "requires_approval": True,
        }
        assert helper == literal

    def test_bigfive_policy_block_shape(self):
        """Sites de bloqueio: completeness=0 int, requires_approval=False."""
        data = {
            "message": "Nao consigo gerar Big Five — bloqueado.",
            "policy_blocked": True,
            "policy_decision": {"policy_decision": "DENY", "rationale": "tenant_policy"},
        }
        helper = build_ws_stage_payload(
            stage="bigfive",
            completeness=0,
            requires_approval=False,
            data=data,
        )
        literal = {
            "type": "wizard_stage",
            "stage": "bigfive",
            "data": data,
            "completeness": 0,
            "requires_approval": False,
        }
        assert helper == literal

    def test_jd_enrichment_fairness_block_shape_no_completeness(self):
        """jd_enrichment_node:852 L1 block — original SEM completeness."""
        data = {
            "error": "fairness_blocked",
            "category": "gender",
            "message": "Removido termo enviesado.",
        }
        helper = build_ws_stage_payload(
            stage="jd_enrichment",
            requires_approval=False,
            data=data,
        )
        literal = {
            "type": "wizard_stage",
            "stage": "jd_enrichment",
            "data": data,
            "requires_approval": False,
        }
        assert helper == literal

    def test_handoff_node_shape_completeness_1(self):
        data = {
            "message": "Vaga pronta!",
            "job_id": "j-123",
            "handoff_url": "/jobs/j-123",
            "share_link": "https://example.com",
        }
        helper = build_ws_stage_payload(
            stage="handoff",
            completeness=1.0,
            requires_approval=False,
            data=data,
        )
        literal = {
            "type": "wizard_stage",
            "stage": "handoff",
            "data": data,
            "completeness": 1.0,
            "requires_approval": False,
        }
        assert helper == literal


# ─── Mutabilidade preservada (alguns sites mutam payload depois) ──────


class TestMutabilityPreserved:
    """jd_enrichment_node:797 muta ws_stage_payload['data']['templates'] depois.

    Helper retorna dict mutavel para preservar esse pattern existente.
    """

    def test_data_dict_is_mutable_after_build(self):
        payload = build_ws_stage_payload(
            stage="intake",
            completeness=0.083,
            requires_approval=False,
            data={"message": "ok"},
        )
        payload["data"]["new_key"] = "added_after"
        payload["ui_action"] = "added_after"
        assert payload["data"]["new_key"] == "added_after"
        assert payload["ui_action"] == "added_after"
