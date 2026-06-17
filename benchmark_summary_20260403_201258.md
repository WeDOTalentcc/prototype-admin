# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T20:14:37.928159  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **12** de 18 (66.7%) |
| ❌ Falhou | **6** |
| 🎯 Score médio | **68.3/100** |
| ⏱️ Latência média | **5505ms** |
| ⏱️ Latência máxima | **27140ms** |
| ⏱️ Latência mínima | **99ms** |
| ⚠️ Riscos de alucinação | **0** |
| 🌐 Respostas não em PT-BR | **2** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 99.0/100 | 10880ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 80.0/100 | 3594ms |
| 🔴 `wizard` | 4 | 0 | 4 | 0% | 5.0/100 | 448ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 96.7/100 | 367ms |
| 🟡 `wsi` | 2 | 1 | 1 | 50% | 52.5/100 | 13707ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `12685ms`
- **Score:** `95/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`
- **⚠️ Palavras proibidas:** `null`

> **Resposta (preview):** ```json {     "thought": "The pipeline health returned 0 candidates across all stages. This could mean the pipeline is empty or there's no data for the current context. I should communicate this clearly and offer to help the recruiter investigate further or take action.",     "action": "respond",   

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `14198ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `75%`
- **Keywords ausentes:** `candidato`

> **Resposta (preview):** # 📊 Análise de Pipeline — Vagas com Gargalo  Ótima pergunta! Identificar pipelines travados é essencial para manter o processo seletivo fluindo. Vou verificar isso para você.  ---  ## ⚠️ Situação Atual  Parece que **não tenho acesso direto aos dados do seu Kanban** neste momento para puxar as inform

### ✅ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `9709ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Relatório de Processos Seletivos  Olá! Vou te ajudar a gerar esse relatório. Para preparar a análise mais completa e útil para você, preciso de algumas informações:  ---  ## 🔍 Quais dados você precisa?  ### 📁 Escopo do Relatório - **Todas as vagas** abertas no mês passado ou **vagas específicas*

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `9223ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `75%`
- **Keywords ausentes:** `aplicar`

> **Resposta (preview):** # 🔍 Buscando Candidatos - Vaga de Backend  Vou localizar os candidatos para você! Porém, preciso de mais algumas informações para trazer o resultado certinho. 😊  ---  ## ❓ Qual vaga de Backend você quer consultar?  Encontrei **mais de uma vaga** que pode corresponder à sua busca. Você poderia me inf

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `8587ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🥈 Buscando Silver Medalists — Product Manager  Olá! Vou verificar os **silver medalists** disponíveis para a vaga de Product Manager.  ---  ⚠️ **Preciso de mais informações para fazer essa busca!**  Parece que não tenho acesso direto aos dados do processo seletivo neste momento. Para te ajudar da 

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `7490ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `mover, pipeline`

> **Resposta (preview):** # Movendo João Silva para a próxima etapa 🔄  Para realizar essa ação no Kanban, preciso de algumas informações adicionais:  ---  ## 📋 Informações Necessárias  **1. Qual vaga está relacionada?** > Ex: Analista de Marketing, Desenvolvedor Backend, Gerente Comercial...  **2. Em qual etapa João Silva es

### ✅ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `177ms`
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
- **Latência:** `195ms`
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
- **Latência:** `6517ms`
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
- **Latência:** `1473ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `106ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `116ms`
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
- **Latência:** `872ms`
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
- **Latência:** `111ms`
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
- **Latência:** `119ms`
- **Score:** `90/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `20%`
- **Keywords ausentes:** `processo, seletivo, candidato, etapa`

> **Resposta (preview):** Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:  • **Criar uma nova vaga** do zero com toda inteligência da plataforma • **Reutilizar uma vaga anterior** para publicar rapidamente  Como gostaria de começar?

### ✅ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `27140ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `experiência, desenvolveu`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em Django? Descreva um desafio significativo de arquitetura ou otimização que você resolveu em uma aplicação Django em produção, explicando sua análise e as decisões tomadas. | Uma API Django na AWS enfrenta instabilidade sob carga variável. Quais serviços e estra

### ❌ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `500`
- **Latência:** `274ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Erro do servidor (500): {"error":"Failed to connect to LIA backend"}`

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_002] Keywords ausentes: ['candidato']
- [chat_004] Keywords ausentes: ['aplicar']
- [orch_001] Keywords ausentes: ['mover', 'pipeline']
- [orch_002] Resposta não está em português
- [orch_002] Keywords ausentes: ['amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['feedback', 'candidato', 'reprovado']
- [conv_001] Keywords ausentes: ['candidato', 'funciona']
- [conv_002] Keywords ausentes: ['wizard', 'informação']
- [conv_003] Keywords ausentes: ['processo', 'seletivo', 'candidato', 'etapa']
- [wsi_001] Keywords ausentes: ['experiência', 'desenvolveu']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T20:14:37.928159*
