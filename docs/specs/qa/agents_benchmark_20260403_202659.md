# Benchmark de Agentes de Processo — Plataforma LIA

**Gerado em:** 20260403_202659  
**Base URL:** `http://localhost:5000`  
**Agente filtrado:** `todos`  

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de casos | 13 |
| Aprovados | 8 |
| Reprovados | 5 |
| Score médio | 79.6/100 |
| Latência média | 15236ms |

## Resultados por Caso

### Agente: `WSI`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| wsi_001 | WSI — Resposta STAR completa (deve score >= 7) | ❌ HTTP 200 | 60/100 | 11919.9ms | Score 3.8 fora do intervalo esperado [7.0, 10.0] |
| wsi_002 | WSI — Resposta vaga (deve score <= 4) | ✅ HTTP 200 | 85/100 | 8308.4ms | — |
| wsi_003 | WSI — Resposta parcial STAR (deve score 4-7) | ❌ HTTP 200 | 45/100 | 8491.9ms | Score 1.5 fora do intervalo esperado [4.0, 7.0] |
| wsi_004 | WSI — Resposta irrelevante/off-topic (deve score <= 3) | ✅ HTTP 200 | 85/100 | 7959.0ms | — |

### Agente: `CV_MATCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| cv_001 | CV Match — Match forte (deve match_score > 80) | ❌ HTTP 200 | 70/100 | 14614.6ms | Lista 'matched_skills' ausente ou vazia |
| cv_002 | CV Match — Match fraco (deve match_score < 30) | ❌ HTTP 200 | 70/100 | 22364.2ms | Lista 'missing_skills' ausente ou vazia |
| cv_003 | CV Match — Match parcial (deve match_score 40-70) | ❌ HTTP 200 | 30/100 | 26453.5ms | match_score 28.0 fora do intervalo esperado [40.0, 70.0] |

### Agente: `SALARY`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| salary_001 | Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k) | ✅ HTTP 200 | 90/100 | 27366.4ms | — |
| salary_002 | Salary — Analista de Dados Júnior BH (R$ 3k-6k) | ✅ HTTP 200 | 100/100 | 37351.4ms | — |

### Agente: `PIPELINE`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| pipeline_001 | Pipeline — Saúde geral do funil | ✅ HTTP 200 | 100/100 | 11601.8ms | — |
| pipeline_002 | Pipeline — Tempo médio de contratação tech | ✅ HTTP 200 | 100/100 | 113.4ms | — |

### Agente: `CANDIDATE_SEARCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| search_001 | Candidate Search — Engenheiro Python Sênior | ✅ HTTP 200 | 100/100 | 10295.6ms | — |
| search_002 | Candidate Search — Product Manager | ✅ HTTP 200 | 100/100 | 11222.2ms | — |

## Detalhes dos Casos Reprovados

### wsi_001 — WSI — Resposta STAR completa (deve score >= 7)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 200
- **Score:** 60/100
- **Issues:**
  - Score 3.8 fora do intervalo esperado [7.0, 10.0]
- **Resposta (trecho):**
  ```
  {"question_id": "q-benchmark-001", "bloom_score": 4, "bloom_level_name": "Analyze", "dreyfus_level": 3, "dreyfus_level_name": "Competent", "big_five_indicators": {"openness": 60, "conscientiousness": 
  ```

### wsi_003 — WSI — Resposta parcial STAR (deve score 4-7)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 200
- **Score:** 45/100
- **Issues:**
  - Score 1.5 fora do intervalo esperado [4.0, 7.0]
- **Resposta (trecho):**
  ```
  {"question_id": "q-benchmark-001", "bloom_score": 3, "bloom_level_name": "Apply", "dreyfus_level": 2, "dreyfus_level_name": "Advanced Beginner", "big_five_indicators": {"openness": 40, "conscientiousn
  ```

### cv_001 — CV Match — Match forte (deve match_score > 80)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 200
- **Score:** 70/100
- **Issues:**
  - Lista 'matched_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  # 🎯 Análise de Match — Engenheiro de Dados Sênior

---

## 📊 Score Geral de Compatibilidade

```
████████████████████░░  92% Match
```
### ✅ **Resultado: Candidato Altamente Recomendado**

---

## 🔍 A
  ```

### cv_002 — CV Match — Match fraco (deve match_score < 30)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 200
- **Score:** 70/100
- **Issues:**
  - Lista 'missing_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  # Análise de Match: Engenheiro de Dados Sênior × UX Designer

---

## 📊 Resultado Geral

> **Match Score: 8-12%** — Incompatibilidade crítica de perfil

---

## 🔍 Análise Detalhada por Dimensão

| Dim
  ```

### cv_003 — CV Match — Match parcial (deve match_score 40-70)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 200
- **Score:** 30/100
- **Issues:**
  - match_score 28.0 fora do intervalo esperado [40.0, 70.0]
- **Resposta (trecho):**
  ```
  # Análise de Match: Engenheiro de Dados Sênior 🔍

## Resultado Geral: ⚠️ **Match Baixo — 28%**

---

## Comparativo Detalhado

| Requisito da Vaga | Perfil do Candidato | Status |
|---|---|---|
| Pyth
  ```

---

_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  
_Para testar componentes de chat/UI, use `benchmark_prompts.py`._