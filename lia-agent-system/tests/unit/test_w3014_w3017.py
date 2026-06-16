"""
Anti-regressão · W3-014 (c3b em agentic_loop) + W3-017 (DSR rate limit).
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestW3014C3bInAgenticLoop:
    """c3b_layer pre + post wirados em agentic_loop.run()."""

    def test_agentic_loop_imports_c3b(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "app/orchestrator/agentic_loop.py"
        )
        src = path.read_text()
        assert "c3b_layer" in src or "pre_compliance" in src, (
            "agentic_loop DEVE importar c3b_layer (W3-014)"
        )
        assert "_c3b_pre" in src, (
            "agentic_loop DEVE usar c3b pre_compliance alias _c3b_pre"
        )
        assert "_c3b_post" in src, (
            "agentic_loop DEVE usar c3b post_compliance alias _c3b_post"
        )

    def test_pre_compliance_called_before_llm(self) -> None:
        """pre_compliance call DEVE aparecer antes do LLM loop start."""
        path = (
            Path(__file__).resolve().parents[2]
            / "app/orchestrator/agentic_loop.py"
        )
        src = path.read_text()
        idx_pre = src.find("_c3b_pre(")
        idx_llm = src.find("self._llm_service.generate_with_tools(")
        assert idx_pre > 0 and idx_pre < idx_llm, (
            f"pre_compliance DEVE preceder generate_with_tools. "
            f"pre={idx_pre}, llm={idx_llm}"
        )

    def test_post_compliance_called_before_return(self) -> None:
        """post_compliance call DEVE preceder o return da response."""
        path = (
            Path(__file__).resolve().parents[2]
            / "app/orchestrator/agentic_loop.py"
        )
        src = path.read_text()
        assert "_c3b_post(_final_response, _c3b_ctx)" in src, (
            "post_compliance DEVE ser invocado antes de retornar response"
        )


class TestW3017DSRRateLimit:
    """DSR public POST endpoint protegido por IP-based rate limit."""

    def test_dsr_module_imports_rate_helper(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "app/api/v1/data_subject_requests.py"
        )
        src = path.read_text()
        assert "_dsr_rate_limit_check" in src, (
            "DSR module DEVE ter helper _dsr_rate_limit_check (W3-017)"
        )

    def test_dsr_post_calls_rate_limit(self) -> None:
        """POST handler DEVE chamar _dsr_rate_limit_check no início."""
        path = (
            Path(__file__).resolve().parents[2]
            / "app/api/v1/data_subject_requests.py"
        )
        src = path.read_text()
        post_section = src.split("async def create_data_subject_request")[1]
        # Pegar o body até o próximo def
        end_marker = post_section.find("\nasync def ")
        if end_marker > 0:
            post_section = post_section[:end_marker]
        assert "_dsr_rate_limit_check(request)" in post_section, (
            "POST handler DEVE invocar await _dsr_rate_limit_check(request)"
        )

    def test_dsr_rate_limit_threshold_documented(self) -> None:
        """Threshold canonical declarado."""
        path = (
            Path(__file__).resolve().parents[2]
            / "app/api/v1/data_subject_requests.py"
        )
        src = path.read_text()
        assert "_DSR_RATE_LIMIT_PER_IP_PER_MIN" in src
