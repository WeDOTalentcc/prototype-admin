# 📊 Benchmark de Qualidade — Plataforma LIA

**Data:** 2026-04-03T20:29:22.879405  
**Ambiente:** http://localhost:5000  
**Total de testes:** 18  

---

## 📈 Resumo Geral

| Métrica | Valor |
|---------|-------|
| ✅ Passou | **16** de 18 (88.9%) |
| ❌ Falhou | **2** |
| 🎯 Score médio | **83.9/100** |
| ⏱️ Latência média | **7991ms** |
| ⏱️ Latência máxima | **30022ms** |
| ⏱️ Latência mínima | **106ms** |
| ⚠️ Riscos de alucinação | **2** |
| 🌐 Respostas não em PT-BR | **4** |

---

## 🔍 Resultados por Componente

| Componente | Total | ✅ Pass | ❌ Fail | Taxa | Score Médio | Latência Média |
|-----------|-------|--------|--------|------|-------------|----------------|
| 🟢 `chat` | 5 | 4 | 1 | 80% | 99.0/100 | 10452ms |
| 🟢 `orchestrator` | 4 | 4 | 0 | 100% | 80.0/100 | 9772ms |
| 🟢 `wizard` | 4 | 4 | 0 | 100% | 72.5/100 | 115ms |
| 🟢 `conversational` | 3 | 3 | 0 | 100% | 100.0/100 | 2761ms |
| 🟡 `wsi` | 2 | 1 | 1 | 50% | 52.5/100 | 21874ms |

---

## 📋 Resultados Detalhados

### ❌ [chat_001] Consulta candidatos triagem

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `14239ms`
- **Score:** `95/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`
- **⚠️ Palavras proibidas:** `null`

> **Resposta (preview):** ```json {     "thought": "O retorno indica 0 candidatos no pipeline. Isso pode significar que o company_id 'current' não é válido, ou realmente não há candidatos. Vou informar o recrutador de forma amigável sobre o resultado e sugerir verificações.",     "action": "respond",     "tool_name": null,  

### ✅ [chat_002] Pipeline travado

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `12568ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ⚠️ SIM
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Análise de Pipeline Travado  Vou verificar as vagas com candidatos parados há mais de 5 dias no pipeline!  ---  ## ⚠️ Vagas com Pipeline Travado  > 🔄 *Para trazer os dados em tempo real, preciso acessar seu painel Kanban. Aqui está o que posso fazer:*  ---  ### 🔍 O que analiso para identificar t

### ✅ [chat_003] Relatório processos seletivos

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `7900ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 📊 Relatório de Processos Seletivos  Olá! Vou te ajudar a gerar esse relatório. Para compilar os dados do mês passado com precisão, preciso de algumas informações:  ---  ## 🔍 Qual o escopo do relatório?  **1. Abrangência:** - [ ] Todos os processos seletivos da empresa - [ ] Uma área/departamento e

### ✅ [chat_004] Candidatos vaga backend

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `8348ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `75%`
- **Keywords ausentes:** `aplicar`

> **Resposta (preview):** # 🔍 Buscando Candidatos - Vaga de Backend  Vou buscar os candidatos para você! Porém, precisei de algumas informações para localizar a vaga correta. 😊  ---  ## ℹ️ Preciso de mais detalhes  Para trazer os candidatos certos, me informe:  **1. Identificação da vaga:** - Você tem o **ID ou código** da v

### ✅ [chat_005] Silver medalist Product Manager

- **Componente:** `chat`
- **Endpoint:** `/api/backend-proxy/chat/`
- **Status HTTP:** `200`
- **Latência:** `9208ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** # 🥈 Buscando Silver Medalists — Product Manager  Olá! Vou verificar os candidatos **silver medalists** para a vaga de Product Manager no nosso banco de talentos.  ---  ⚠️ **Atenção:** Não tenho acesso direto ao sistema neste momento para consultar os dados em tempo real da sua conta.  ---  ## O que 

### ✅ [orch_001] Mover candidato próxima etapa

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `21395ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `83%`
- **Keywords ausentes:** `pipeline`

> **Resposta (preview):** # Movendo João Silva para a Próxima Etapa 🔄  Para realizar essa ação no Kanban, preciso de algumas informações adicionais:  ---  ## 📋 Dados Necessários  **1. Qual vaga está vinculado o João Silva?** > Ex: Analista de Marketing, Desenvolvedor Backend...  **2. Em qual etapa ele está atualmente?**  | E

### ✅ [orch_002] Agendar entrevista

- **Componente:** `orchestrator`
- **Endpoint:** `/api/backend-proxy/orchestrator/process/`
- **Status HTTP:** `200`
- **Latência:** `12219ms`
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
- **Latência:** `208ms`
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
- **Latência:** `5268ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `100%`

> **Resposta (preview):** ```json {     "thought": "O recrutador quer criar uma vaga para Engenheiro de Dados Sênior. Já consigo extrair: título = 'Engenheiro de Dados', senioridade = 'Sênior'. Falta coletar: departamento (obrigatório), localização, modelo de trabalho e tipo de contrato. Vou confirmar o que já extraí e pergu

### ✅ [wizard_001] Wizard info básica Python fintech

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `106ms`
- **Score:** `60/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `60%`
- **Keywords ausentes:** `fintech, engenheiro`

> **Resposta (preview):** ✅ Registrado! Senioridade: **sênior**, modelo: **remoto**, skills: **python**. Deseja adicionar mais detalhes ou podemos avançar?

### ✅ [wizard_002] Wizard requisitos Python Spark AWS

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `127ms`
- **Score:** `50/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `40%`
- **Keywords ausentes:** `spark, experiência, requisito`

> **Resposta (preview):** ✅ Registrado! Skills: **python, aws**. Deseja adicionar mais detalhes ou podemos avançar?

### ✅ [wizard_003] Wizard competências raciocínio equipe

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `112ms`
- **Score:** `90/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `raciocínio, equipe, competência, avaliar, habilidade`

> **Resposta (preview):** ✅ Informações registradas. Deseja adicionar mais detalhes ou podemos avançar para a próxima etapa?

### ✅ [wizard_004] Wizard revisão publicar vaga

- **Componente:** `wizard`
- **Endpoint:** `/api/backend-proxy/lia/job-wizard/interpret/`
- **Status HTTP:** `200`
- **Latência:** `118ms`
- **Score:** `90/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **Keywords ausentes:** `publicar, vaga, confirm, ok, publicada, pronto`

> **Resposta (preview):** ✅ Informações registradas. Deseja adicionar mais detalhes ou podemos avançar para a próxima etapa?

### ✅ [conv_001] Olá como funciona plataforma

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `2659ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `83%`
- **Keywords ausentes:** `recrutamento`

> **Resposta (preview):** Olá! Que ótimo ter você por aqui. Eu sou a LIA, sua assistente inteligente da WeDoTalent.  Neste chat, minha especialidade é te ajudar com tudo relacionado à **criação e otimização de vagas de emprego**. Podemos:  *   Criar vagas do zero com minha análise inteligente. *   Reaproveitar vagas que você

### ✅ [conv_002] Quero criar nova vaga

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `1291ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `60%`
- **Keywords ausentes:** `wizard, informação`

> **Resposta (preview):** Olá! Que ótimo! Posso te ajudar a criar essa nova vaga.  Para começarmos, qual é o **título da vaga** que você gostaria de anunciar? Assim, já posso iniciar o processo de forma mais assertiva. 😊

### ✅ [conv_003] Ajuda processo seletivo

- **Componente:** `conversational`
- **Endpoint:** `/api/backend-proxy/lia/conversational/`
- **Status HTTP:** `200`
- **Latência:** `4333ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `60%`
- **Keywords ausentes:** `candidato, etapa`

> **Resposta (preview):** Olá! Sou a LIA, a assistente de recrutamento da WeDoTalent. Fico feliz em ajudar com o seu processo seletivo!  Neste chat, meu foco principal é te auxiliar na **criação e otimização de vagas de emprego**. É o primeiro e super importante passo para um processo seletivo de sucesso!  Podemos começar po

### ✅ [wsi_001] Perguntas triagem Python Sênior

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `200`
- **Latência:** `13726ms`
- **Score:** `100/100`
- **Em português:** ✅
- **Relevante para RH:** ✅
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `67%`
- **Keywords ausentes:** `experiência, desenvolveu`

> **Resposta (preview):** De 1 a 5, qual seu nível de domínio em Python, Django e AWS? Para cada um, descreva brevemente o projeto mais complexo que você arquitetou ou otimizou, destacando os desafios técnicos e sua contribuição. | Sua aplicação Django, hospedada na AWS com RDS PostgreSQL e uso de cache Redis, está apresenta

### ❌ [wsi_002] Perguntas triagem Product Manager

- **Componente:** `wsi`
- **Endpoint:** `/api/lia/api/wsi/generate-job-screening-questions/`
- **Status HTTP:** `None`
- **Latência:** `30022ms`
- **Score:** `5/100`
- **Em português:** ❌
- **Relevante para RH:** ❌
- **Risco de alucinação:** ✅ Não
- **Cobertura de keywords:** `0%`
- **❌ Erro:** `Timeout após 30s`

---

## ⚠️ Problemas de Qualidade Encontrados

- [chat_001] Risco de alucinação detectado
- [chat_002] Risco de alucinação detectado
- [chat_004] Keywords ausentes: ['aplicar']
- [orch_001] Keywords ausentes: ['pipeline']
- [orch_002] Resposta não está em português
- [orch_002] Keywords ausentes: ['amanhã', '14', 'horário']
- [orch_003] Resposta não está em português
- [orch_003] Resposta não menciona contexto de recrutamento
- [orch_003] Keywords ausentes: ['feedback', 'candidato', 'reprovado']
- [wizard_001] Resposta não está em português
- [wizard_001] Resposta não menciona contexto de recrutamento
- [wizard_001] Keywords ausentes: ['fintech', 'engenheiro']
- [wizard_002] Resposta não está em português
- [wizard_002] Resposta não menciona contexto de recrutamento
- [wizard_002] Keywords ausentes: ['spark', 'experiência', 'requisito']
- [wizard_003] Keywords ausentes: ['raciocínio', 'equipe', 'competência', 'avaliar', 'habilidade']
- [wizard_004] Keywords ausentes: ['publicar', 'vaga', 'confirm', 'ok', 'publicada', 'pronto']
- [conv_001] Keywords ausentes: ['recrutamento']
- [conv_002] Keywords ausentes: ['wizard', 'informação']
- [conv_003] Keywords ausentes: ['candidato', 'etapa']
- [wsi_001] Keywords ausentes: ['experiência', 'desenvolveu']

---

*Relatório gerado automaticamente por `benchmark_prompts.py`*  
*Plataforma LIA — plataforma-lia — 2026-04-03T20:29:22.879405*
