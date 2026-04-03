# Benchmark de Agentes de Processo — Plataforma LIA

**Gerado em:** 20260403_202000  
**Base URL:** `http://localhost:5000`  
**Agente filtrado:** `todos`  

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de casos | 13 |
| Aprovados | 8 |
| Reprovados | 5 |
| Score médio | 74.2/100 |
| Latência média | 13373ms |

## Resultados por Caso

### Agente: `WSI`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| wsi_001 | WSI — Resposta STAR completa (deve score >= 7) | ❌ HTTP 200 | 60/100 | 13292.8ms | Score 3.8 fora do intervalo esperado [7.0, 10.0] |
| wsi_002 | WSI — Resposta vaga (deve score <= 4) | ✅ HTTP 200 | 85/100 | 8420.4ms | — |
| wsi_003 | WSI — Resposta parcial STAR (deve score 4-7) | ❌ HTTP 200 | 45/100 | 9565.1ms | Score 1.5 fora do intervalo esperado [4.0, 7.0] |
| wsi_004 | WSI — Resposta irrelevante/off-topic (deve score <= 3) | ✅ HTTP 200 | 85/100 | 8497.0ms | — |

### Agente: `CV_MATCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| cv_001 | CV Match — Match forte (deve match_score > 80) | ❌ HTTP 200 | 0/100 | 14780.9ms | Campo 'match_score' ausente ou não numérico; Lista 'matched_skills' ausente ou vazia |
| cv_002 | CV Match — Match fraco (deve match_score < 30) | ❌ HTTP 200 | 70/100 | 15505.5ms | Lista 'missing_skills' ausente ou vazia |
| cv_003 | CV Match — Match parcial (deve match_score 40-70) | ❌ HTTP 200 | 30/100 | 24237.3ms | match_score 28.0 fora do intervalo esperado [40.0, 70.0] |

### Agente: `SALARY`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| salary_001 | Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k) | ✅ HTTP 200 | 90/100 | 26175.3ms | — |
| salary_002 | Salary — Analista de Dados Júnior BH (R$ 3k-6k) | ✅ HTTP 200 | 100/100 | 11276.4ms | — |

### Agente: `PIPELINE`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| pipeline_001 | Pipeline — Saúde geral do funil | ✅ HTTP 200 | 100/100 | 9105.5ms | — |
| pipeline_002 | Pipeline — Tempo médio de contratação tech | ✅ HTTP 200 | 100/100 | 11979.8ms | — |

### Agente: `CANDIDATE_SEARCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| search_001 | Candidate Search — Engenheiro Python Sênior | ✅ HTTP 200 | 100/100 | 11606.5ms | — |
| search_002 | Candidate Search — Product Manager | ✅ HTTP 200 | 100/100 | 9401.1ms | — |

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
- **Score:** 0/100
- **Issues:**
  - Campo 'match_score' ausente ou não numérico
  - Lista 'matched_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  # 📊 Análise de Match — Engenheiro de Dados Sênior

---

## ✅ Resultado Geral

# 🎯 Match Score: **94/100** — Candidato Altamente Recomendado

---

## 🔍 Análise Detalhada por Critério

| Critério | Requ
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

## 📊 Resultado do Match

**Compatibilidade Geral: 8%** ❌ Match Crítico

---

## 🔍 Análise Detalhada por Dimensão

| Dimensão | Peso | Scor
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
  # Análise de Match: Engenheiro de Dados Sênior 📊

## Resultado Geral

> ## ❌ Match Baixo — **28%**
> Candidato **não recomendado** para esta vaga no momento.

---

## Análise Detalhada por Critério

|
  ```

---

_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  
_Para testar componentes de chat/UI, use `benchmark_prompts.py`._