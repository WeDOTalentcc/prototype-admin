# Benchmark de Agentes de Processo — Plataforma LIA

**Gerado em:** 20260403_203408  
**Base URL:** `http://localhost:5000`  
**Agente filtrado:** `todos`  

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de casos | 13 |
| Aprovados | 0 |
| Reprovados | 13 |
| Score médio | 0.0/100 |
| Latência média | 0ms |

## Resultados por Caso

### Agente: `WSI`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| wsi_001 | WSI — Resposta STAR completa (deve score >= 7) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| wsi_002 | WSI — Resposta vaga (deve score <= 4) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| wsi_003 | WSI — Resposta parcial STAR (deve score 4-7) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| wsi_004 | WSI — Resposta irrelevante/off-topic (deve score <= 3) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |

### Agente: `CV_MATCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| cv_001 | CV Match — Match forte (deve match_score > 80) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| cv_002 | CV Match — Match fraco (deve match_score < 30) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| cv_003 | CV Match — Match parcial (deve match_score 40-70) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |

### Agente: `SALARY`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| salary_001 | Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| salary_002 | Salary — Analista de Dados Júnior BH (R$ 3k-6k) | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |

### Agente: `PIPELINE`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| pipeline_001 | Pipeline — Saúde geral do funil | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| pipeline_002 | Pipeline — Tempo médio de contratação tech | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |

### Agente: `CANDIDATE_SEARCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| search_001 | Candidate Search — Engenheiro Python Sênior | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |
| search_002 | Candidate Search — Product Manager | ❌ HTTP 0 | 0/100 | 0ms | Falha de conexão: All connection attempts failed |

## Detalhes dos Casos Reprovados

### wsi_001 — WSI — Resposta STAR completa (deve score >= 7)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### wsi_002 — WSI — Resposta vaga (deve score <= 4)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### wsi_003 — WSI — Resposta parcial STAR (deve score 4-7)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### wsi_004 — WSI — Resposta irrelevante/off-topic (deve score <= 3)
- **Agente:** wsi
- **Endpoint:** `http://localhost:8000/api/v1/wsi/analyze-response`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### cv_001 — CV Match — Match forte (deve match_score > 80)
- **Agente:** cv_match
- **Endpoint:** `/api/lia/api/cv-match`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### cv_002 — CV Match — Match fraco (deve match_score < 30)
- **Agente:** cv_match
- **Endpoint:** `/api/lia/api/cv-match`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### cv_003 — CV Match — Match parcial (deve match_score 40-70)
- **Agente:** cv_match
- **Endpoint:** `/api/lia/api/cv-match`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### salary_001 — Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### salary_002 — Salary — Analista de Dados Júnior BH (R$ 3k-6k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### pipeline_001 — Pipeline — Saúde geral do funil
- **Agente:** pipeline
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### pipeline_002 — Pipeline — Tempo médio de contratação tech
- **Agente:** pipeline
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### search_001 — Candidate Search — Engenheiro Python Sênior
- **Agente:** candidate_search
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

### search_002 — Candidate Search — Product Manager
- **Agente:** candidate_search
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 0
- **Score:** 0/100
- **Issues:**
  - Falha de conexão: All connection attempts failed
- **Resposta (trecho):**
  ```
  {"error": "All connection attempts failed"}
  ```

---

_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  
_Para testar componentes de chat/UI, use `benchmark_prompts.py`._