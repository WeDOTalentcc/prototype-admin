"""
H1 — Testes: persistência de reasoning completo sem truncamento na auditoria.

Garante que prompt_full e reasoning_full são armazenados sem truncamento
nos entries de AuditCallback, e que to_full_dict() os inclui no payload
que vai para o storage.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_callback(domain: str = "test"):
    from lia_audit.audit_callback import AuditCallback
    return AuditCallback(
        user_id="user-001",
        company_id="company-001",
        session_id="sess-001",
        domain=domain,
        agent_type="react",
    )


LONG_TEXT = "X" * 2000  # texto maior que o limite de preview (500 chars)


# ---------------------------------------------------------------------------
# Testes: on_llm_call sem truncamento
# ---------------------------------------------------------------------------

class TestOnLlmCallNoTruncation:
    def test_prompt_preview_is_truncated_to_500(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview=LONG_TEXT,
            response_preview=LONG_TEXT,
            latency_ms=10.0,
        )
        entry = cb.entries[-1]
        assert len(entry["prompt_preview"]) == 500

    def test_response_preview_is_truncated_to_500(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview=LONG_TEXT,
            response_preview=LONG_TEXT,
            latency_ms=10.0,
        )
        entry = cb.entries[-1]
        assert len(entry["response_preview"]) == 500

    def test_prompt_full_stored_without_truncation(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview=LONG_TEXT[:500],
            response_preview="resp",
            latency_ms=10.0,
            prompt_full=LONG_TEXT,
        )
        entry = cb.entries[-1]
        assert "prompt_full" in entry
        assert len(entry["prompt_full"]) == 2000

    def test_reasoning_full_stored_without_truncation(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="prompt",
            response_preview=LONG_TEXT[:500],
            latency_ms=10.0,
            reasoning_full=LONG_TEXT,
        )
        entry = cb.entries[-1]
        assert "reasoning_full" in entry
        assert len(entry["reasoning_full"]) == 2000

    def test_both_full_fields_stored_together(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="preview",
            response_preview="preview",
            latency_ms=5.0,
            prompt_full=LONG_TEXT,
            reasoning_full=LONG_TEXT,
        )
        entry = cb.entries[-1]
        assert entry["prompt_full"] == LONG_TEXT
        assert entry["reasoning_full"] == LONG_TEXT

    def test_full_fields_absent_when_not_provided(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="p",
            response_preview="r",
            latency_ms=1.0,
        )
        entry = cb.entries[-1]
        assert "prompt_full" not in entry
        assert "reasoning_full" not in entry

    def test_entry_type_is_llm_call(self):
        cb = _make_callback()
        cb.on_llm_call("p", "r", latency_ms=1.0, reasoning_full="full reasoning")
        assert cb.entries[-1]["type"] == "llm_call"

    def test_model_stored_in_entry(self):
        cb = _make_callback()
        cb.on_llm_call("p", "r", latency_ms=1.0, model="claude-sonnet-4-6")
        assert cb.entries[-1]["model"] == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Testes: ExecutionAuditRecord.to_full_dict inclui entries
# ---------------------------------------------------------------------------

class TestAuditRecordFullDict:
    def test_to_full_dict_includes_entries(self):
        from lia_audit.audit_models import ExecutionAuditRecord
        record = ExecutionAuditRecord(
            execution_id="exec-001",
            company_id="company-001",
            domain="test",
        )
        record.entries = [
            {"type": "llm_call", "prompt_full": LONG_TEXT, "reasoning_full": LONG_TEXT}
        ]
        full = record.to_full_dict()
        assert "entries" in full
        assert full["entries"][0]["prompt_full"] == LONG_TEXT
        assert full["entries"][0]["reasoning_full"] == LONG_TEXT

    def test_to_metadata_dict_excludes_entries(self):
        from lia_audit.audit_models import ExecutionAuditRecord
        record = ExecutionAuditRecord(
            execution_id="exec-002",
            company_id="company-001",
            domain="test",
        )
        record.entries = [{"type": "llm_call", "reasoning_full": LONG_TEXT}]
        meta = record.to_metadata_dict()
        assert "entries" not in meta

    def test_full_dict_is_json_serializable(self):
        from lia_audit.audit_models import ExecutionAuditRecord
        record = ExecutionAuditRecord(
            execution_id="exec-003",
            company_id="company-001",
            domain="test",
        )
        record.entries = [{"type": "llm_call", "reasoning_full": LONG_TEXT}]
        serialized = json.dumps(record.to_full_dict())
        parsed = json.loads(serialized)
        assert parsed["entries"][0]["reasoning_full"] == LONG_TEXT


# ---------------------------------------------------------------------------
# Testes: _build_record inclui entries com full fields
# ---------------------------------------------------------------------------

class TestBuildRecord:
    def test_build_record_entries_contain_reasoning_full(self):
        cb = _make_callback()
        cb.on_chain_start_manual()
        cb.on_llm_call("p", "r", 10.0, reasoning_full="full reasoning text")
        record = cb._build_record(success=True)
        assert len(record.entries) == 1
        assert record.entries[0]["reasoning_full"] == "full reasoning text"

    def test_build_record_entries_contain_prompt_full(self):
        cb = _make_callback()
        cb.on_chain_start_manual()
        cb.on_llm_call("p", "r", 10.0, prompt_full="full prompt text")
        record = cb._build_record(success=True)
        assert record.entries[0]["prompt_full"] == "full prompt text"

    def test_multiple_iterations_all_entries_preserved(self):
        cb = _make_callback()
        cb.on_chain_start_manual()
        for i in range(5):
            cb.on_llm_call("p", "r", 10.0, reasoning_full=f"reasoning iteration {i}")
        record = cb._build_record(success=True)
        assert len(record.entries) == 5
        for i, entry in enumerate(record.entries):
            assert entry["reasoning_full"] == f"reasoning iteration {i}"


# ---------------------------------------------------------------------------
# Testes: LocalFileStorage salva payload completo
# ---------------------------------------------------------------------------

class TestLocalFileStorageSavesFullPayload:
    @pytest.mark.asyncio
    async def test_save_and_load_preserves_reasoning_full(self, tmp_path):
        from lia_audit.audit_storage import LocalFileStorage
        storage = LocalFileStorage(base_dir=str(tmp_path))
        payload = {
            "execution_id": "exec-001",
            "entries": [{"type": "llm_call", "reasoning_full": LONG_TEXT}],
        }
        path = "test/2026/03/01/company/exec-001.json"
        saved = await storage.save(path, payload)
        loaded = await storage.load(saved)
        assert loaded is not None
        assert loaded["entries"][0]["reasoning_full"] == LONG_TEXT

    @pytest.mark.asyncio
    async def test_save_returns_path(self, tmp_path):
        from lia_audit.audit_storage import LocalFileStorage
        storage = LocalFileStorage(base_dir=str(tmp_path))
        path = "test/exec.json"
        result = await storage.save(path, {"key": "value"})
        assert result.endswith("exec.json")


# ---------------------------------------------------------------------------
# Testes: integração AuditCallback → _persist → storage
# ---------------------------------------------------------------------------

class TestAuditCallbackPersistIntegration:
    @pytest.mark.asyncio
    async def test_persist_passes_entries_to_storage(self, tmp_path):
        """Verifica que _persist salva entries (incluindo reasoning_full) no storage."""
        from lia_audit.audit_storage import LocalFileStorage
        from lia_audit.audit_writer import AuditWriter

        storage = LocalFileStorage(base_dir=str(tmp_path))
        writer = AuditWriter()

        cb = _make_callback("vagas")
        cb.on_chain_start_manual()
        cb.on_llm_call("prompt", "response", 50.0, reasoning_full="full_reasoning_text")

        record = cb._build_record(success=True)

        # Salva com storage local
        with patch("lia_audit.audit_writer.get_audit_storage", return_value=storage), \
             patch("lia_audit.audit_writer.AuditWriter._save_metadata", new_callable=AsyncMock):
            await writer.persist(record)

        # Verifica que o arquivo foi criado
        files = list(tmp_path.rglob("*.json"))
        assert len(files) == 1

        with open(files[0]) as f:
            saved = json.load(f)

        assert "entries" in saved
        assert saved["entries"][0]["reasoning_full"] == "full_reasoning_text"
