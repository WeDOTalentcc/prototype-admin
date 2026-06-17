# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T18:19:25.740297  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **13** de 18 (72.2%) |
| ❌ Falhou | **5** |
| 🎯 Score médio | **73.6/100** |
| ⏱️ Latência média | **6082ms** |
| ⏱️ Latência máxima | **21365ms** |
| ⏱️ Latência mínima | **101ms** |
| ⚠️ Riscos de alucinação | **1** |
| 🌐 Respostas não em PT-BR | **2** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 99.0/100 | 10284ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 80.0/100 | 4495ms |
| 🔴 `wizard` | 4 | 0 | 4 | 0% | 5.0/100 | 358ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 96.7/100 | 513ms |
| 🟢 `wsi` | 2 | 2 | 0 | 100% | 100.0/100 | 18551ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `12654ms`
- **Score:** `95/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`
- **⚠️ Palavras proibidas:** `null`

> **Resposta (preview):** ```json {     "thought": "The pipeline health data returned 0 candidates across all stages. This could mean the pipeline is empty or there's no data for the default company. I should inform the recruiter clearly and offer next steps.",     "action": "respond",     "tool_name": null,     "tool_args":

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `13532ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🔍 Análise de Pipeline Travado  Vou verificar as vagas com candidatos parados há mais de 5 dias no pipeline!  ---  ## ⚠️ Vagas com Pipeline Estagnado  > *Simulando consulta ao sistema WeDOTalent...*  | # | Vaga | Etapa Travada | Dias Parado | Candidatos Afetados | Responsável | |---|------|--------

### ✅ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `8753ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Relatório de Processos Seletivos  Olá! Vou te ajudar a gerar esse relatório. Para que eu possa compilar as informações mais relevantes para você, preciso de alguns detalhes:  ---  ## 🔍 Quais dados você precisa?  **1. Escopo do relatório:** - Todas as vagas abertas no período? - Apenas vagas ence

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `7687ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `75%`
- **Keywords ausentes:** `aplicar`

> **Resposta (preview):** # 🔍 Buscando Candidatos - Vaga Backend  Vou buscar os candidatos dessa vaga para você! Só preciso de uma informação para localizar corretamente:  ---  ## 📋 Qual vaga específica você deseja consultar?  Você tem o **ID ou nome exato da vaga**? Por exemplo: - "Backend Developer Sênior" - "Engenheiro Ba

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `8795ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🔍 Buscando Silver Medalists — Product Manager  Deixa eu verificar os candidatos que ficaram em segundo lugar em processos anteriores para essa vaga!  ---  ⚠️ **Não encontrei dados carregados no momento**  Parece que não tenho acesso direto ao histórico de processos seletivos de Product Manager ago

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `9918ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `83%`
- **Keywords ausentes:** `pipeline`

> **Resposta (preview):** # Movendo João Silva para a Próxima Etapa 🔄  Para realizar essa ação no Kanban, preciso de algumas informações adicionais:  ---  ## 📋 Informações Necessárias  **1. Qual vaga está vinculado o João Silva?** > Ex: Analista de Marketing, Desenvolvedor Backend...  **2. Em qual etapa ele está atualmente?*

### ✅ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `215ms`
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
- **Latência:** `239ms`
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
- **Latência:** `7608ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** ```json {     "thought": "O usuário quer criar uma vaga para Engenheiro de Dados Sênior. Já consigo extrair: título = 'Engenheiro de Dados', senioridade = 'Sênior'. Falta coletar: departamento (obrigatório), localização, modelo de trabalho e tipo de contrato. Vou confirmar o que extraí e perguntar p

### ❌ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `1120ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `102ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `111ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `101ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ✅ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `1288ms`
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
- **Latência:** `127ms`
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
- **Latência:** `125ms`
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
- **Latência:** `21365ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `experiência, desenvolveu`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em Django? Compartilhe um desafio complexo de arquitetura ou otimização de performance que você enfrentou em um projeto Django e como o abordou. | Um serviço crítico em Python na AWS que você gerencia está apresentando latência elevada e intermitente. Descreva as 

### ✅ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `15737ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `71%`
- **Keywords ausentes:** `roadmap, manager`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em análise de dados para tomada de decisão de produto (e.g., Google Analytics, SQL, dashboards de métricas)? Compartilhe um exemplo específico onde uma análise sua impactou diretamente a decisão de construir ou iterar uma funcionalidade. | Você possui duas funcion

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_002] Risco de alucinação detectado
- [chat_004] Keywords ausentes: ['aplicar']
- [orch_001] Keywords ausentes: ['pipeline']
- [orch_002] Resposta não está em português
- [orch_002] Keywords ausentes: ['amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['feedback', 'candidato', 'reprovado']
- [conv_001] Keywords ausentes: ['candidato', 'funciona']
- [conv_002] Keywords ausentes: ['wizard', 'informação']
- [conv_003] Keywords ausentes: ['processo', 'seletivo', 'candidato', 'etapa']
- [wsi_001] Keywords ausentes: ['experiência', 'desenvolveu']
- [wsi_002] Keywords ausentes: ['roadmap', 'manager']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T18:19:25.740297*
