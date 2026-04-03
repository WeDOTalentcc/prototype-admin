# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T18:15:31.245215  
**Ambiente:** http://localhost:3000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **0** de 18 (0.0%) |
| ❌ Falhou | **18** |
| 🎯 Score médio | **5.0/100** |
| ⏱️ Latência média | **8ms** |
| ⏱️ Latência máxima | **47ms** |
| ⏱️ Latência mínima | **5ms** |
| ⚠️ Riscos de alucinação | **0** |
| 🌐 Respostas não em PT-BR | **0** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🔴 `chat` | 5 | 0 | 5 | 0% | 5.0/100 | 14ms |
| 🔴 `orchestrator` | 4 | 0 | 4 | 0% | 5.0/100 | 6ms |
| 🔴 `wizard` | 4 | 0 | 4 | 0% | 5.0/100 | 6ms |
| 🔴 `conversational` | 3 | 0 | 3 | 0% | 5.0/100 | 6ms |
| 🔴 `wsi` | 2 | 0 | 2 | 0% | 5.0/100 | 8ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `None`
- **Latência:** `47ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [orch_003] Email feedback reprovados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [orch_004] Criar vaga engenheiro dados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `None`
- **Latência:** `6ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `None`
- **Latência:** `5ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [conv_002] Quero criar nova vaga

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [conv_003] Ajuda processo seletivo

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `None`
- **Latência:** `7ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions`
- **Status HTTP:** `None`
- **Latência:** `8ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

### ❌ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions`
- **Status HTTP:** `None`
- **Latência:** `8ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro de conexão: servidor inacessível em http://localhost:3000`

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T18:15:31.245215*
