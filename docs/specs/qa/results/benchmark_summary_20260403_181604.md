# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T18:16:04.892433  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **17** de 18 (94.4%) |
| ❌ Falhou | **1** |
| 🎯 Score médio | **59.2/100** |
| ⏱️ Latência média | **10ms** |
| ⏱️ Latência máxima | **47ms** |
| ⏱️ Latência mínima | **7ms** |
| ⚠️ Riscos de alucinação | **0** |
| 🌐 Respostas não em PT-BR | **18** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 47.0/100 | 16ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 50.0/100 | 8ms |
| 🟢 `wizard` | 4 | 4 | 0 | 100% | 70.0/100 | 9ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 70.0/100 | 7ms |
| 🟢 `wsi` | 2 | 2 | 0 | 100% | 70.0/100 | 7ms |

---

## 📋 Resultados Detalhados

### ✅ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `308`
- **Latência:** `47ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `candidato, triagem, semana, etapa, pipeline`

> **Resposta (preview):** /api/backend-proxy/chat/

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `308`
- **Latência:** `8ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `vaga, pipeline, dias, candidato`

> **Resposta (preview):** /api/backend-proxy/chat/

### ❌ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `308`
- **Latência:** `9ms`
- **Score:** `35/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `relatório, processo, seletivo, mês`

> **Resposta (preview):** /api/backend-proxy/chat/

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `308`
- **Latência:** `8ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `25%`
- **Keywords ausentes:** `candidato, vaga, aplicar`

> **Resposta (preview):** /api/backend-proxy/chat/

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat`
- **Status HTTP:** `308`
- **Latência:** `11ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `silver, medalist, candidato, vaga, product manager`

> **Resposta (preview):** /api/backend-proxy/chat/

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `308`
- **Latência:** `8ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `candidato, etapa, mover, pipeline, joão, silva`

> **Resposta (preview):** /api/backend-proxy/orchestrator/process/

### ✅ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `308`
- **Latência:** `10ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `entrevista, agenda, amanhã, 14, horário`

> **Resposta (preview):** /api/backend-proxy/orchestrator/process/

### ✅ [orch_003] Email feedback reprovados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `308`
- **Latência:** `8ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `email, feedback, candidato, reprovado, enviar`

> **Resposta (preview):** /api/backend-proxy/orchestrator/process/

### ✅ [orch_004] Criar vaga engenheiro dados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `vaga, engenheiro, dados, sênior, criar`

> **Resposta (preview):** /api/backend-proxy/orchestrator/process/

### ✅ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `308`
- **Latência:** `8ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `python, sênior, remoto, fintech, engenheiro`

> **Resposta (preview):** /api/backend-proxy/lia/job-wizard/interpret/

### ✅ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `308`
- **Latência:** `9ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `python, spark, aws, experiência, requisito`

> **Resposta (preview):** /api/backend-proxy/lia/job-wizard/interpret/

### ✅ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `308`
- **Latência:** `15ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `raciocínio, equipe, competência, avaliar, habilidade`

> **Resposta (preview):** /api/backend-proxy/lia/job-wizard/interpret/

### ✅ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `publicar, vaga, confirm, ok, publicada, pronto`

> **Resposta (preview):** /api/backend-proxy/lia/job-wizard/interpret/

### ✅ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `plataforma, recrutamento, ajudar, vaga, candidato, funciona`

> **Resposta (preview):** /api/backend-proxy/lia/conversational/

### ✅ [conv_002] Quero criar nova vaga

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `vaga, criar, wizard, informação, ajudar`

> **Resposta (preview):** /api/backend-proxy/lia/conversational/

### ✅ [conv_003] Ajuda processo seletivo

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `processo, seletivo, ajudar, candidato, etapa`

> **Resposta (preview):** /api/backend-proxy/lia/conversational/

### ✅ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `python, django, aws, experiência, desenvolveu, arquitetura`

> **Resposta (preview):** /api/lia/api/wsi/generate-job-screening-questions/

### ✅ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions`
- **Status HTTP:** `308`
- **Latência:** `7ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `produto, roadmap, stakeholder, prioridade, métrica, produto, manager`

> **Resposta (preview):** /api/lia/api/wsi/generate-job-screening-questions/

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_001] Resposta não está em português
- [chat_001] Resposta não menciona contexto de recrutamento
- [chat_001] Keywords ausentes: ['candidato', 'triagem', 'semana', 'etapa', 'pipeline']
- [chat_002] Resposta não está em português
- [chat_002] Resposta não menciona contexto de recrutamento
- [chat_002] Keywords ausentes: ['vaga', 'pipeline', 'dias', 'candidato']
- [chat_003] Resposta não está em português
- [chat_003] Resposta não menciona contexto de recrutamento
- [chat_003] Keywords ausentes: ['relatório', 'processo', 'seletivo', 'mês']
- [chat_004] Resposta não está em português
- [chat_004] Resposta não menciona contexto de recrutamento
- [chat_004] Keywords ausentes: ['candidato', 'vaga', 'aplicar']
- [chat_005] Resposta não está em português
- [chat_005] Resposta não menciona contexto de recrutamento
- [chat_005] Keywords ausentes: ['silver', 'medalist', 'candidato', 'vaga', 'product manager']
- [orch_001] Resposta não está em português
- [orch_001] Resposta não menciona contexto de recrutamento
- [orch_001] Keywords ausentes: ['candidato', 'etapa', 'mover', 'pipeline', 'joão', 'silva']
- [orch_002] Resposta não está em português
- [orch_002] Resposta não menciona contexto de recrutamento
- [orch_002] Keywords ausentes: ['entrevista', 'agenda', 'amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['email', 'feedback', 'candidato', 'reprovado', 'enviar']
- [orch_004] Resposta não está em português
- [orch_004] Resposta não menciona contexto de recrutamento
- [orch_004] Keywords ausentes: ['vaga', 'engenheiro', 'dados', 'sênior', 'criar']
- [wizard_001] Resposta não está em português
- [wizard_001] Keywords ausentes: ['python', 'sênior', 'remoto', 'fintech', 'engenheiro']
- [wizard_002] Resposta não está em português
- [wizard_002] Keywords ausentes: ['python', 'spark', 'aws', 'experiência', 'requisito']
- [wizard_003] Resposta não está em português
- [wizard_003] Keywords ausentes: ['raciocínio', 'equipe', 'competência', 'avaliar', 'habilidade']
- [wizard_004] Resposta não está em português
- [wizard_004] Keywords ausentes: ['publicar', 'vaga', 'confirm', 'ok', 'publicada', 'pronto']
- [conv_001] Resposta não está em português
- [conv_001] Keywords ausentes: ['plataforma', 'recrutamento', 'ajudar', 'vaga', 'candidato', 'funciona']
- [conv_002] Resposta não está em português
- [conv_002] Keywords ausentes: ['vaga', 'criar', 'wizard', 'informação', 'ajudar']
- [conv_003] Resposta não está em português
- [conv_003] Keywords ausentes: ['processo', 'seletivo', 'ajudar', 'candidato', 'etapa']
- [wsi_001] Resposta não está em português
- [wsi_001] Keywords ausentes: ['python', 'django', 'aws', 'experiência', 'desenvolveu', 'arquitetura']
- [wsi_002] Resposta não está em português
- [wsi_002] Keywords ausentes: ['produto', 'roadmap', 'stakeholder', 'prioridade', 'métrica', 'produto', 'manager']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T18:16:04.892433*
