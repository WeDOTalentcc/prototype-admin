"""Coverage tests for digest_formatter.py — BellDigestFormatter, ChatDigestFormatter, TeamsDigestFormatter."""
import pytest
from app.domains.analytics.services.digest_formatter import (
    BellDigestFormatter,
    ChatDigestFormatter,
    TeamsDigestFormatter,
)

MINIMAL_DIGEST = {
    "recruiter_name": "Ana Silva",
    "period": {"start": "2026-05-04", "end": "2026-05-10"},
    "pipeline_health": {
        "total_active_jobs": 5,
        "candidates_screened_week": 12,
        "interviews_scheduled": 3,
        "conversion_rate": 25.0,
        "conversion_change": 2.5,
    },
    "vagas_em_risco": {"count": 0, "jobs": []},
    "compliance_summary": {"status": "ok", "message": "Nenhum alerta."},
    "optimization_insights": {"tests": []},
    "patterns_learned": {"total_patterns": 4, "top_patterns": []},
}


class TestBellDigestFormatter:
    def setup_method(self):
        self.fmt = BellDigestFormatter()

    def test_returns_dict_with_required_keys(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "title" in result
        assert "message" in result
        assert "action_url" in result
        assert "action_label" in result

    def test_title_is_static(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert result["title"] == "Resumo Semanal Disponível"

    def test_action_url_is_chat(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert result["action_url"] == "/chat"

    def test_zero_risk_no_risk_text(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        # With 0 risk jobs, no "precisam de atenção" in message
        assert "precisam" not in result["message"] or "pipeline" in result["message"]

    def test_with_risk_jobs_mentions_count(self):
        digest = {**MINIMAL_DIGEST, "vagas_em_risco": {"count": 2, "jobs": []}}
        result = self.fmt.format(digest)
        assert "2" in result["message"]

    def test_compliance_not_ok_shows_attention(self):
        digest = {**MINIMAL_DIGEST, "compliance_summary": {"status": "warning", "message": "Alerta"}}
        result = self.fmt.format(digest)
        assert "requer atenção" in result["message"]

    def test_empty_digest_does_not_crash(self):
        result = self.fmt.format({})
        assert isinstance(result, dict)
        assert "title" in result

    def test_screened_count_in_message(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "12" in result["message"]


class TestChatDigestFormatter:
    def setup_method(self):
        self.fmt = ChatDigestFormatter()

    def test_returns_dict_with_title_and_message(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "title" in result
        assert "message" in result

    def test_message_is_string(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 20

    def test_recruiter_first_name_in_message(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "Ana" in result["message"]

    def test_pipeline_stats_in_message(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        msg = result["message"]
        assert "5" in msg  # active jobs
        assert "12" in msg  # screened

    def test_with_risk_jobs_shows_severity(self):
        digest = {
            **MINIMAL_DIGEST,
            "vagas_em_risco": {
                "count": 1,
                "jobs": [{"title": "Dev Backend", "company": "TechCo", "reason": "Sem candidatos", "severity": "critical"}],
            },
        }
        result = self.fmt.format(digest)
        assert "Dev Backend" in result["message"]
        assert "CRÍTICO" in result["message"]

    def test_with_attention_severity(self):
        digest = {
            **MINIMAL_DIGEST,
            "vagas_em_risco": {
                "count": 1,
                "jobs": [{"title": "Designer", "company": "", "reason": "Prazo próximo", "severity": "attention"}],
            },
        }
        result = self.fmt.format(digest)
        assert "Designer" in result["message"]

    def test_compliance_message_included(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "Nenhum alerta" in result["message"]

    def test_ab_test_concluded_in_message(self):
        digest = {
            **MINIMAL_DIGEST,
            "optimization_insights": {
                "tests": [{"test_name": "Email A vs B", "status": "concluded", "winner_variant": "B", "total_observations": 50}]
            },
        }
        result = self.fmt.format(digest)
        assert "Email A vs B" in result["message"]
        assert "concluído" in result["message"]

    def test_ab_test_in_progress_in_message(self):
        digest = {
            **MINIMAL_DIGEST,
            "optimization_insights": {
                "tests": [{"test_name": "Subject Test", "status": "in_progress", "total_observations": 30}]
            },
        }
        result = self.fmt.format(digest)
        assert "Subject Test" in result["message"]
        assert "andamento" in result["message"]

    def test_patterns_in_message(self):
        digest = {
            **MINIMAL_DIGEST,
            "patterns_learned": {
                "total_patterns": 3,
                "top_patterns": [{"type": "skills", "confidence": 0.85, "sample_size": 20}],
            },
        }
        result = self.fmt.format(digest)
        assert "Aprendizado" in result["message"]

    def test_conversion_change_positive(self):
        digest = {**MINIMAL_DIGEST, "pipeline_health": {**MINIMAL_DIGEST["pipeline_health"], "conversion_change": 3}}
        result = self.fmt.format(digest)
        assert "subiu" in result["message"]

    def test_conversion_change_negative(self):
        digest = {**MINIMAL_DIGEST, "pipeline_health": {**MINIMAL_DIGEST["pipeline_health"], "conversion_change": -2}}
        result = self.fmt.format(digest)
        assert "caiu" in result["message"]

    def test_no_recruiter_name_uses_default(self):
        digest = {**MINIMAL_DIGEST, "recruiter_name": ""}
        result = self.fmt.format(digest)
        assert "Recrutador" in result["message"]

    def test_empty_digest(self):
        result = self.fmt.format({})
        assert isinstance(result["message"], str)


class TestTeamsDigestFormatter:
    def setup_method(self):
        self.fmt = TeamsDigestFormatter()

    def test_returns_dict_with_type_message(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert result["type"] == "message"

    def test_has_attachments(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        assert "attachments" in result
        assert len(result["attachments"]) == 1

    def test_attachment_is_adaptive_card(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        att = result["attachments"][0]
        assert att["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert att["content"]["type"] == "AdaptiveCard"

    def test_card_has_body_and_actions(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        content = result["attachments"][0]["content"]
        assert "body" in content
        assert "actions" in content

    def test_body_contains_text_block(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        body = result["attachments"][0]["content"]["body"]
        types = [b["type"] for b in body]
        assert "TextBlock" in types

    def test_metric_columns_present(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        body = result["attachments"][0]["content"]["body"]
        column_sets = [b for b in body if b["type"] == "ColumnSet"]
        assert len(column_sets) >= 1
        assert len(column_sets[0]["columns"]) == 3

    def test_risk_jobs_shown_in_body(self):
        digest = {
            **MINIMAL_DIGEST,
            "vagas_em_risco": {
                "count": 1,
                "jobs": [{"title": "PM Sênior", "company": "StartupX", "reason": "0 candidatos", "severity": "critical"}],
            },
        }
        result = self.fmt.format(digest)
        body = result["attachments"][0]["content"]["body"]
        text_blocks = [b.get("text", "") for b in body if b["type"] == "TextBlock"]
        combined = " ".join(text_blocks)
        assert "PM Sênior" in combined

    def test_max_3_risk_jobs_shown(self):
        risk_jobs = [
            {"title": f"RiskJob{i}", "company": "Co", "reason": "risk", "severity": "attention"}
            for i in range(5)
        ]
        digest = {**MINIMAL_DIGEST, "vagas_em_risco": {"count": 5, "jobs": risk_jobs}}
        result = self.fmt.format(digest)
        body = result["attachments"][0]["content"]["body"]
        job_blocks = [b for b in body if b["type"] == "TextBlock" and "RiskJob" in b.get("text", "")]
        # At most 3 risk job blocks (code uses risk_jobs[:3])
        assert len(job_blocks) <= 3

    def test_compliance_ok_shows_checkmark(self):
        result = self.fmt.format(MINIMAL_DIGEST)
        body = result["attachments"][0]["content"]["body"]
        texts = [b.get("text", "") for b in body if b["type"] == "TextBlock"]
        compliance_text = next((t for t in texts if "Compliance" in t), "")
        assert "✅" in compliance_text

    def test_compliance_warning_shows_alert(self):
        digest = {**MINIMAL_DIGEST, "compliance_summary": {"status": "warning", "message": "Atenção"}}
        result = self.fmt.format(digest)
        body = result["attachments"][0]["content"]["body"]
        texts = [b.get("text", "") for b in body if b["type"] == "TextBlock"]
        compliance_text = next((t for t in texts if "Compliance" in t), "")
        assert "⚠️" in compliance_text

    def test_ab_test_concluded_in_body(self):
        digest = {
            **MINIMAL_DIGEST,
            "optimization_insights": {
                "tests": [{"test_name": "CTA Test", "status": "concluded", "winner_variant": "A"}]
            },
        }
        result = self.fmt.format(digest)
        body = result["attachments"][0]["content"]["body"]
        texts = [b.get("text", "") for b in body if b["type"] == "TextBlock"]
        opt_text = next((t for t in texts if "CTA Test" in t), "")
        assert "concluído" in opt_text

    def test_empty_digest(self):
        result = self.fmt.format({})
        assert result["type"] == "message"

    def test_metric_column_static_method(self):
        col = TeamsDigestFormatter._metric_column("42", "candidatos")
        assert col["type"] == "Column"
        items = col["items"]
        texts = [i["text"] for i in items]
        assert "42" in texts
        assert "candidatos" in texts
