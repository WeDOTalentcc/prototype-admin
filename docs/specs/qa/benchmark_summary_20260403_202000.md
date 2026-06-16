# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T20:21:51.369408  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **13** de 18 (72.2%) |
| ❌ Falhou | **5** |
| 🎯 Score médio | **74.2/100** |
| ⏱️ Latência média | **6139ms** |
| ⏱️ Latência máxima | **21482ms** |
| ⏱️ Latência mínima | **113ms** |
| ⚠️ Riscos de alucinação | **3** |
| 🌐 Respostas não em PT-BR | **2** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 99.0/100 | 9856ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 80.0/100 | 3712ms |
| 🔴 `wizard` | 4 | 0 | 4 | 0% | 5.0/100 | 116ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 100.0/100 | 2737ms |
| 🟢 `wsi` | 2 | 2 | 0 | 100% | 100.0/100 | 18850ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `12736ms`
- **Score:** `95/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `80%`
- **Keywords ausentes:** `etapa`
- **⚠️ Palavras proibidas:** `null`

> **Resposta (preview):** ```json {     "thought": "O retorno da ferramenta indica 0 candidatos no pipeline. Isso pode significar que o pipeline está realmente vazio, ou que o company_id 'current' não é o correto. Vou informar o recrutador sobre o resultado e perguntar se há algo mais específico que ele queira verificar.",  

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `11641ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🔍 Análise de Pipeline - Vagas com Gargalos  Vou verificar as vagas com candidatos parados há mais de **5 dias sem movimentação**!  ---  ## ⚠️ Vagas com Pipeline Travado  | Vaga | Etapa Parada | Dias sem mov. | Candidatos presos | Responsável | |------|-------------|---------------|----------------

### ✅ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `9343ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Relatório de Processos Seletivos  Olá! Vou te ajudar a gerar esse relatório. Para garantir que ele seja completo e relevante para você, preciso de algumas informações:  ---  ## 🔍 Quais dados você precisa?  **1. Escopo do relatório:** - Todos os processos seletivos da empresa? - Apenas uma área/d

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `7471ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🔍 Buscando Candidatos - Vaga de Backend  Vou verificar os candidatos que aplicaram para essa vaga! Porém, precisei de algumas informações para trazer os dados corretos.  ---  ## 📋 Qual vaga de Backend você quer consultar?  Pode me informar um dos dados abaixo:  | Opção | Exemplo | |-------|-------

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `8090ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🥈 Buscando Silver Medalists — Product Manager  Olá! Vou verificar os **silver medalists** disponíveis para a vaga de Product Manager.  ---  ⚠️ **Preciso de mais informações para realizar essa busca!**  Não identifiquei detalhes suficientes no contexto atual para localizar os candidatos. Poderia me

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `7554ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `83%`
- **Keywords ausentes:** `mover`

> **Resposta (preview):** # Movendo João Silva no Kanban 📋  Para realizar essa ação, preciso de algumas informações adicionais:  ---  ## Qual vaga está vinculada a esse candidato?  Por favor, me informe:  1. 🏢 **Nome da vaga** ou código da posição 2. ✅ **Etapa atual** em que João Silva se encontra *(opcional — já vou buscar)

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
- **Latência:** `177ms`
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
- **Latência:** `6955ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** ```json {     "thought": "O recrutador quer criar uma vaga para Engenheiro de Dados Sênior. Já consigo extrair: título = 'Engenheiro de Dados', senioridade = 'Sênior'. Falta ainda: departamento (obrigatório), localização, modelo de trabalho e tipo de contrato. Vou confirmar o que já coletei e pergun

### ❌ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `120ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `113ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `118ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ❌ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `113ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`

### ✅ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `3074ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** Olá! Que bom te ver por aqui! 😊 Eu sou a LIA, sua assistente inteligente de recrutamento na WeDoTalent.  Neste chat, minha função principal é te ajudar com tudo relacionado à **criação e otimização de vagas de emprego**. Basicamente, eu te guio para:  1.  **Criar vagas do zero** com análises intelig

### ✅ [conv_002] Quero criar nova vaga

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `2383ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `60%`
- **Keywords ausentes:** `wizard, informação`

> **Resposta (preview):** Olá! Que ótimo! Posso te ajudar com isso, com certeza.  Vamos começar a criar essa nova vaga. Para dar o pontapé inicial, me diga: **qual é o cargo que você busca preencher?**  Assim que você me disser o cargo, começaremos o processo completo de criação da vaga, com análise inteligente para te ajuda

### ✅ [conv_003] Ajuda processo seletivo

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `2754ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** Olá! Que ótimo que você veio até aqui para otimizar seu processo seletivo! Eu sou a LIA, e posso te ajudar a dar o pontapé inicial, que é a criação das suas vagas.  Neste chat, sou especialista em: *   **Criar vagas de emprego** do zero, com uma análise inteligente. *   **Reutilizar vagas anteriores

### ✅ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `21482ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `experiência, desenvolveu`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em Django? Cite um desafio arquitetural complexo que você enfrentou e resolveu em um projeto Django de alta demanda ou escala. Qual foi sua abordagem e os resultados? | Sua equipe está com problemas de escalabilidade e latência em um serviço Python que utiliza uma

### ✅ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `16219ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `86%`
- **Keywords ausentes:** `métrica`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em técnicas de priorização de backlog (e.g., RICE, MoSCoW, ICE)? Conte sobre uma situação real em que você utilizou uma dessas técnicas para guiar as decisões de produto, e quais foram os resultados obtidos. | Você lançou uma nova funcionalidade e os dados iniciai

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_001] Risco de alucinação detectado
- [chat_001] Keywords ausentes: ['etapa']
- [chat_002] Risco de alucinação detectado
- [chat_004] Risco de alucinação detectado
- [orch_001] Keywords ausentes: ['mover']
- [orch_002] Resposta não está em português
- [orch_002] Keywords ausentes: ['amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['feedback', 'candidato', 'reprovado']
- [conv_002] Keywords ausentes: ['wizard', 'informação']
- [wsi_001] Keywords ausentes: ['experiência', 'desenvolveu']
- [wsi_002] Keywords ausentes: ['métrica']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T20:21:51.369408*
