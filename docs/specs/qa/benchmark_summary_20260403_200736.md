# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T20:09:46.895807  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **12** de 18 (66.7%) |
| ❌ Falhou | **6** |
| 🎯 Score médio | **67.2/100** |
| ⏱️ Latência média | **7243ms** |
| ⏱️ Latência máxima | **28847ms** |
| ⏱️ Latência mínima | **99ms** |
| ⚠️ Riscos de alucinação | **4** |
| 🌐 Respostas não em PT-BR | **2** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 99.0/100 | 11447ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 80.0/100 | 3669ms |
| 🔴 `wizard` | 4 | 0 | 4 | 0% | 5.0/100 | 685ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 96.7/100 | 386ms |
| 🟡 `wsi` | 2 | 1 | 1 | 50% | 42.5/100 | 27282ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `17387ms`
- **Score:** `95/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`
- **⚠️ Palavras proibidas:** `null`

> **Resposta (preview):** ```json {     "thought": "O retorno da ferramenta indica 0 candidatos no pipeline. Isso pode ser porque o company_id 'current' não é o correto, ou realmente não há candidatos. Vou informar o recrutador de forma amigável sobre o resultado e perguntar se os dados estão corretos ou se preciso de mais i

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `12609ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Análise de Pipeline Travado  Vou verificar as vagas com candidatos parados há mais de 5 dias no pipeline!  ---  ## ⚠️ Vagas com Pipeline Travado  > 🔄 *Consultando dados em tempo real do seu Kanban...*  Parece que não tenho acesso direto aos dados do seu pipeline neste momento. Mas posso te ajuda

### ✅ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `9551ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Relatório de Processos Seletivos  Olá! Vou te ajudar a gerar esse relatório. Para que eu possa compilar as informações mais relevantes para você, preciso de alguns detalhes:  ---  ## 🔍 Quais informações você precisa?  **1. Escopo do relatório:** - [ ] Todos os processos seletivos da empresa - [ 

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `7161ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `75%`
- **Keywords ausentes:** `aplicar`

> **Resposta (preview):** # 🔍 Buscando Candidatos - Vaga Backend  Vou ajudá-lo a visualizar os candidatos dessa vaga! Para trazer as informações corretas, preciso de alguns detalhes:  ---  ## ❓ Qual vaga exatamente?  Encontrei **mais de uma vaga** que pode corresponder. Você poderia confirmar?  | # | Vaga | Status | Candidat

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `10527ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🔍 Buscando Silver Medalists — Product Manager  Deixa eu verificar os candidatos que ficaram em segundo lugar em processos anteriores para vagas de Product Manager!  ---  ⚠️ **Não consegui acessar os dados em tempo real neste momento.**  Para localizar os **silver medalists** dessa vaga, posso te a

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `7590ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `candidato, pipeline`

> **Resposta (preview):** # Movendo João Silva para a Próxima Etapa 🔄  Para realizar essa ação no Kanban, preciso de algumas informações adicionais:  ---  ## 📋 Informações Necessárias  **1. Qual vaga está vinculado o João Silva?** > Ex: Analista de Marketing, Desenvolvedor Backend...  **2. Em qual etapa ele está atualmente?*

### ✅ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `163ms`
- **Score:** `70/100`
- **Em português:** ❌
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `40%`
- **Keywords ausentes:** `amanhã, 14, horário`

> **Resposta (preview):** Confirma a execução de: Agendar Entrevista?

### ✅ [orch_003] Email feedback reprovados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `162ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `40%`
- **Keywords ausentes:** `feedback, candidato, reprovado`

> **Resposta (preview):** Confirma a execução de: Enviar Email?

### ✅ [orch_004] Criar vaga engenheiro dados

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `6763ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** ```json {     "thought": "O recrutador quer criar uma vaga para Engenheiro de Dados Sênior. Já consigo extrair: título = 'Engenheiro de Dados', senioridade = 'Sênior'. Falta coletar: departamento (obrigatório), localização, modelo de trabalho e tipo de contrato. Vou confirmar o que já extraí e pergu

### ❌ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `2353ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `159ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `131ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `99ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ✅ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `879ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `candidato, funciona`

> **Resposta (preview):** Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:  • **Criar uma nova vaga** do zero com toda inteligência da plataforma • **Reutilizar uma vaga anterior** para publicar rapidamente  Como gostaria de começar?

### ✅ [conv_002] Quero criar nova vaga

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `117ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `60%`
- **Keywords ausentes:** `wizard, informação`

> **Resposta (preview):** Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:  • **Criar uma nova vaga** do zero com toda inteligência da plataforma • **Reutilizar uma vaga anterior** para publicar rapidamente  Como gostaria de começar?

### ✅ [conv_003] Ajuda processo seletivo

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `164ms`
- **Score:** `90/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `20%`
- **Keywords ausentes:** `processo, seletivo, candidato, etapa`

> **Resposta (preview):** Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:  • **Criar uma nova vaga** do zero com toda inteligência da plataforma • **Reutilizar uma vaga anterior** para publicar rapidamente  Como gostaria de começar?

### ❌ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `500`
- **Latência:** `25718ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro do servidor (500): {"error":{"error":true,"status_code":500,"message":"Failed to generate screening questions: 'list' object has no attribute 'lower'","request_id":"8c43c055-5367-4574-920e-4f02cbf9deb8"}}`

### ✅ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `28847ms`
- **Score:** `80/100`
- **Em português:** ✅
- **Relevante para RH:** ❌
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `57%`
- **Keywords ausentes:** `roadmap, prioridade, manager`

> **Resposta (preview):** De 1 a 5, qual seu domínio em técnicas de priorização de backlog (ex: MoSCoW, RICE, WSJF)? Conte sobre um projeto em que você aplicou uma dessas técnicas para priorizar funcionalidades e como isso impactou o resultado final. | De 1 a 5, qual seu nível de proficiência em definir, acompanhar e analisa

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_001] Risco de alucinação detectado
- [chat_002] Risco de alucinação detectado
- [chat_004] Risco de alucinação detectado
- [chat_004] Keywords ausentes: ['aplicar']
- [orch_001] Keywords ausentes: ['candidato', 'pipeline']
- [orch_002] Resposta não está em português
- [orch_002] Keywords ausentes: ['amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['feedback', 'candidato', 'reprovado']
- [conv_001] Keywords ausentes: ['candidato', 'funciona']
- [conv_002] Keywords ausentes: ['wizard', 'informação']
- [conv_003] Keywords ausentes: ['processo', 'seletivo', 'candidato', 'etapa']
- [wsi_002] Risco de alucinação detectado
- [wsi_002] Resposta não menciona contexto de recrutamento
- [wsi_002] Keywords ausentes: ['roadmap', 'prioridade', 'manager']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T20:09:46.895807*
