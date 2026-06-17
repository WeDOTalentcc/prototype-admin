# Benchmark de Agentes de Processo — Plataforma LIA

**Gerado em:** 20260403_200736  
**Base URL:** `http://localhost:5000`  
**Agente filtrado:** `todos`  

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de casos | 13 |
| Aprovados | 6 |
| Reprovados | 7 |
| Score médio | 65.0/100 |
| Latência média | 13578ms |

## Resultados por Caso

### Agente: `WSI`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| wsi_001 | WSI — Resposta STAR completa (deve score >= 7) | ❌ HTTP 200 | 60/100 | 12973.8ms | Score 3.8 fora do intervalo esperado [7.0, 10.0] |
| wsi_002 | WSI — Resposta vaga (deve score <= 4) | ✅ HTTP 200 | 85/100 | 8763.8ms | — |
| wsi_003 | WSI — Resposta parcial STAR (deve score 4-7) | ❌ HTTP 200 | 45/100 | 8503.0ms | Score 1.5 fora do intervalo esperado [4.0, 7.0] |
| wsi_004 | WSI — Resposta irrelevante/off-topic (deve score <= 3) | ✅ HTTP 200 | 85/100 | 8351.5ms | — |

### Agente: `CV_MATCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| cv_001 | CV Match — Match forte (deve match_score > 80) | ❌ HTTP 200 | 70/100 | 19969.4ms | Lista 'matched_skills' ausente ou vazia |
| cv_002 | CV Match — Match fraco (deve match_score < 30) | ❌ HTTP 200 | 30/100 | 17218.7ms | match_score 40.0 fora do intervalo esperado [0.0, 30.0]; Lista 'missing_skills' ausente ou vazia |
| cv_003 | CV Match — Match parcial (deve match_score 40-70) | ❌ HTTP 200 | 30/100 | 25788.5ms | match_score 25.0 fora do intervalo esperado [40.0, 70.0] |

### Agente: `SALARY`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| salary_001 | Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k) | ❌ HTTP 200 | 20/100 | 834.3ms | Esperado >= 1 valor(es) BRL na resposta, encontrado 0 |
| salary_002 | Salary — Analista de Dados Júnior BH (R$ 3k-6k) | ❌ HTTP 200 | 20/100 | 28012.0ms | Esperado >= 1 valor(es) BRL na resposta, encontrado 0 |

### Agente: `PIPELINE`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| pipeline_001 | Pipeline — Saúde geral do funil | ✅ HTTP 200 | 100/100 | 9840.4ms | — |
| pipeline_002 | Pipeline — Tempo médio de contratação tech | ✅ HTTP 200 | 100/100 | 13808.8ms | — |

### Agente: `CANDIDATE_SEARCH`

| ID | Nome | Status | Score | Latência | Issues |
|----|------|--------|-------|----------|--------|
| search_001 | Candidate Search — Engenheiro Python Sênior | ✅ HTTP 200 | 100/100 | 13049.9ms | — |
| search_002 | Candidate Search — Product Manager | ✅ HTTP 200 | 100/100 | 9405.2ms | — |

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
**Classificação: ✅ CANDIDATO ALTAMENTE RECOMENDADO**

---

## 🔍 A
  ```

### cv_002 — CV Match — Match fraco (deve match_score < 30)
- **Agente:** cv_match
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **HTTP Status:** 200
- **Score:** 30/100
- **Issues:**
  - match_score 40.0 fora do intervalo esperado [0.0, 30.0]
  - Lista 'missing_skills' ausente ou vazia
- **Resposta (trecho):**
  ```
  # Análise de Match: Engenheiro de Dados Sênior vs. UX Designer

---

## 📊 Resultado Geral

# ❌ Match Incompatível — Score: **8/100**

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
  - match_score 25.0 fora do intervalo esperado [40.0, 70.0]
- **Resposta (trecho):**
  ```
  # Análise de Match: Engenheiro de Dados Sênior 📊

## Resultado Geral

# ❌ Match Baixo — ~25%

---

## Análise Detalhada por Critério

| Critério | Requisito da Vaga | CV do Candidato | Status |
|---|-
  ```

### salary_001 — Salary — Engenheiro de Dados Sênior SP (R$ 12k-25k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **HTTP Status:** 200
- **Score:** 20/100
- **Issues:**
  - Esperado >= 1 valor(es) BRL na resposta, encontrado 0
- **Resposta (trecho):**
  ```
  Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:

• **Criar uma nova vaga** do zero com toda inteligência da plataforma
• **Reutilizar uma vaga anterior** para publicar rapidamente


  ```

### salary_002 — Salary — Analista de Dados Júnior BH (R$ 3k-6k)
- **Agente:** salary
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **HTTP Status:** 200
- **Score:** 20/100
- **Issues:**
  - Esperado >= 1 valor(es) BRL na resposta, encontrado 0
- **Resposta (trecho):**
  ```
  Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:

• **Criar uma nova vaga** do zero com toda inteligência da plataforma
• **Reutilizar uma vaga anterior** para publicar rapidamente


  ```

---

_benchmark_agents.py — Testa AGENTES DE PROCESSO, não chat/UI._  
_Para testar componentes de chat/UI, use `benchmark_prompts.py`._