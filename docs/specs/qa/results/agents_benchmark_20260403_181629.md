# Benchmark de Agentes de Processo — Plataforma LIA

**Gerado em:** 20260403_181629  
**Base URL:** `http://localhost:5000`  
**Agente filtrado:** `todos`  

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de casos | 13 |
| Aprovados | 0 |
| Reprovados | 13 |
| Score médio | 9.2/100 |
| Latência média | 16ms |

## Resultados por Caso

### Agente: `WSI`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| wsi_001 | WSI — Resposta STAR completa (deve score >= 7) | ❌ HTTP 308 | 0/100 | 61.0ms | Campo 'score' ausente ou não numérico na resposta; Campo 'star_completeness' ausente; Feedback não parece estar em português |
| wsi_002 | WSI — Resposta vaga (deve score <= 4) | ❌ HTTP 308 | 0/100 | 11.4ms | Campo 'score' ausente ou não numérico na resposta; Feedback não parece estar em português |
| wsi_003 | WSI — Resposta parcial STAR (deve score 4-7) | ❌ HTTP 308 | 0/100 | 12.5ms | Campo 'score' ausente ou não numérico na resposta; Feedback não parece estar em português |
| wsi_004 | WSI — Resposta irrelevante/off-topic (deve score <= 3) | ❌ HTTP 308 | 0/100 | 12.3ms | Campo 'score' ausente ou não numérico na resposta; Feedback não parece estar em português |

### Agente: `CV_MATCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| cv_001 | CV Match — Match forte (deve match_score > 80) | ❌ HTTP 308 | 0/100 | 15.0ms | Campo 'match_score' ausente ou não numérico; Lista 'matched_skills' ausente ou vazia |
| cv_002 | CV Match — Match fraco (deve match_score < 30) | ❌ HTTP 308 | 0/100 | 10.7ms | Campo 'match_score' ausente ou não numérico; Lista 'missing_skills' ausente ou vazia |
| cv_003 | CV Match — Match parcial (deve match_score 40-70) | ❌ HTTP 308 | 0/100 | 10.7ms | Campo 'match_score' ausente ou não numérico |

### Agente: `SALARY`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| salary_001 | Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k) | ❌ HTTP 308 | 0/100 | 11.5ms | Esperado >= 1 valor(es) BRL na resposta, encontrado 0; Resposta não parece estar em português |
| salary_002 | Salary — Analista de Dados Júnior BH (R$ 3k-6k) | ❌ HTTP 308 | 0/100 | 8.5ms | Esperado >= 1 valor(es) BRL na resposta, encontrado 0; Resposta não parece estar em português |

### Agente: `PIPELINE`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| pipeline_001 | Pipeline — Saúde geral do funil | ❌ HTTP 308 | 20/100 | 10.0ms | Resposta não menciona etapas do pipeline (triagem, entrevista, oferta, etc.); Resposta não parece estar em português |
| pipeline_002 | Pipeline — Tempo médio de contratação tech | ❌ HTTP 308 | 20/100 | 12.0ms | Resposta não menciona etapas do pipeline (triagem, entrevista, oferta, etc.); Resposta não parece estar em português |

### Agente: `CANDIDATE_SEARCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| search_001 | Candidate Search — Engenheiro Python Sênior | ❌ HTTP 308 | 40/100 | 11.3ms | Resposta não parece estar em português; Resposta não menciona candidatos ou perfis relevantes |
| search_002 | Candidate Search — Product Manager | ❌ HTTP 308 | 40/100 | 26.1ms | Resposta não parece estar em português; Resposta não menciona candidatos ou perfis relevantes |

## Detalhes dos Casos Reprovados

### wsi_001 — WSI — Resposta STAR completa (deve score >= 7)
- **Agente:** wsi
- **Endpoint:** `/api/lia/api/wsi/analyze-response`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'score' ausente ou não numérico na resposta
  - Campo 'star_completeness' ausente
  - Feedback não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/lia/api/wsi/analyze-response/"}
  ```

### wsi_002 — WSI — Resposta vaga (deve score <= 4)
- **Agente:** wsi
- **Endpoint:** `/api/lia/api/wsi/analyze-response`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'score' ausente ou não numérico na resposta
  - Feedback não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/lia/api/wsi/analyze-response/"}
  ```

### wsi_003 — WSI — Resposta parcial STAR (deve score 4-7)
- **Agente:** wsi
- **Endpoint:** `/api/lia/api/wsi/analyze-response`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'score' ausente ou não numérico na resposta
  - Feedback não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/lia/api/wsi/analyze-response/"}
  ```

### wsi_004 — WSI — Resposta irrelevante/off-topic (deve score <= 3)
- **Agente:** wsi
- **Endpoint:** `/api/lia/api/wsi/analyze-response`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'score' ausente ou não numérico na resposta
  - Feedback não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/lia/api/wsi/analyze-response/"}
  ```

### cv_001 — CV Match — Match forte (deve match_score > 80)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'match_score' ausente ou não numérico
  - Lista 'matched_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### cv_002 — CV Match — Match fraco (deve match_score < 30)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'match_score' ausente ou não numérico
  - Lista 'missing_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### cv_003 — CV Match — Match parcial (deve match_score 40-70)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Campo 'match_score' ausente ou não numérico
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### salary_001 — Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Esperado >= 1 valor(es) BRL na resposta, encontrado 0
  - Resposta não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/lia/conversational/"}
  ```

### salary_002 — Salary — Analista de Dados Júnior BH (R$ 3k-6k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **HTTP Status:** 308
- **Score:** 0/100
- **Issues:**
  - Esperado >= 1 valor(es) BRL na resposta, encontrado 0
  - Resposta não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/lia/conversational/"}
  ```

### pipeline_001 — Pipeline — Saúde geral do funil
- **Agente:** pipeline
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 20/100
- **Issues:**
  - Resposta não menciona etapas do pipeline (triagem, entrevista, oferta, etc.)
  - Resposta não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### pipeline_002 — Pipeline — Tempo médio de contratação tech
- **Agente:** pipeline
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 20/100
- **Issues:**
  - Resposta não menciona etapas do pipeline (triagem, entrevista, oferta, etc.)
  - Resposta não parece estar em português
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### search_001 — Candidate Search — Engenheiro Python Sênior
- **Agente:** candidate_search
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 40/100
- **Issues:**
  - Resposta não parece estar em português
  - Resposta não menciona candidatos ou perfis relevantes
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

### search_002 — Candidate Search — Product Manager
- **Agente:** candidate_search
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **HTTP Status:** 308
- **Score:** 40/100
- **Issues:**
  - Resposta não parece estar em português
  - Resposta não menciona candidatos ou perfis relevantes
- **Resposta (trecho):**
  ```
  {"_raw": "/api/backend-proxy/orchestrator/process/"}
  ```

---

_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  
_Para testar componentes de chat/UI, use `benchmark_prompts.py`._