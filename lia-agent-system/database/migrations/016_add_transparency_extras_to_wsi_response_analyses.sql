-- Audit task #528 (G23-02 / G23-03) — Transparência granular WSI (LGPD/EU AI Act).
--
-- Adiciona coluna JSONB `transparency_extras` na tabela `wsi_response_analyses`
-- para persistir, por análise:
--   - flags_structured: dict[str, bool] (is_inflation, is_paraphrase,
--     is_prompt_injection, is_llm_fallback, etc.)
--   - penalty_breakdown / bonus_breakdown: dict[str, float]
--   - degraded_quality: bool
--   - degraded_reasons: list[str]
--   - layer2_degraded_reason: str | None
--
-- Endpoints `/api/v1/wsi/f11-report/{session_id}` e
-- `/api/wsi/results/{result_id}/details` consomem essa coluna para expor
-- o selo de qualidade degradada e o breakdown granular para a UI.
--
-- Idempotente: pode ser reaplicada sem efeito caso a coluna já exista.
ALTER TABLE wsi_response_analyses
  ADD COLUMN IF NOT EXISTS transparency_extras JSONB;
