# Correções Aplicadas — Plataforma LIA
**Executado em:** 03/04/2026

## Resumo de Scores

| Benchmark | Antes | Depois |
|-----------|-------|--------|
| Prompts   | 67.2/100 (12/18) | 83.9/100 (16/18) |
| Agentes   | 65.0/100 (6/13)  | 79.6/100 (8/13)  |

## Correções

### C1 P1 - WSI Event Loop
- Arquivo: wsi.py
- Fix: run_in_executor + wait_for(30s) em todas as chamadas Anthropic

### C2 P2 - thought field leak
- Arquivo: chat/route.ts (proxy) + chat-format.ts (cliente)
- Fix: strip thought key no proxy; regex cliente como segunda camada

### C3 P2 - Intent classifier fallback
- Arquivo: enhanced_intent_classifier.py
- Fix: logger.error + confidence 0.5 + reasoning descritivo

### C4 P3 - WSI score fields
- Arquivo: wsi.py
- Fix: score_max=5.0, score_normalized, star_completeness adicionados

### C5 P3 - CV Match structured output
- Arquivo: orchestrator.py
- Fix: _STRUCTURED_INTENT_ADDENDA injeta JSON schema no system prompt

### C6 P3 - Salary BRL values
- Arquivo: lia_assistant.py
- Fix: modo salary_benchmark com LLM prompt especializado em R$ X.XXX

### Bonus B-08 - Wizard proxy
- Arquivo criado: /api/backend-proxy/lia/[...path]/route.ts
- Fix: proxy catch-all para /api/v1/lia/*
- Impacto: wizard 0% -> 100%

### Bonus - WSI questions crash
- Arquivo: wsi_questions.py
- Fix: guard isinstance(comp, list) em competency_validated

### Bonus - Wizard lia_response null
- Arquivo: lia_assistant.py
- Fix: PROVIDE_DATA/QUESTION/CORRECTION agora retornam lia_response contextual

## Pendências

- WSI score range fora do esperado (wsi_001, wsi_003)
- CV Match matched_skills lista vazia
- Orchestrator respostas em ingles (orch_002, orch_003)
