# Plataforma LIA - Especificação de Desenvolvimento MVP

**Data:** Janeiro 2026  
**Versão:** 2.0  
**Status:** Documento de Referência para Desenvolvimento  
**Última Atualização:** 26 Janeiro 2026

---

## JIRA - Cards MVP Importados

> **Projeto Jira:** wedotalent tasks 2026 (WT)

| Categoria | Cards | Range Jira | Status |
|-----------|-------|------------|--------|
| **MVP Principal** | 144 | WT-893 a WT-1036 | ✅ Importados com conteúdo completo |
| **Configurações Admin** | 58 | WT-1037 a WT-1094 | ✅ Importados (MENU CONFIG) |
| **TOTAL** | **202** | WT-893 a WT-1094 | ✅ Todos com detalhes |

### Labels Aplicadas
- `lia-mvp` / `config-admin` - Identificação do projeto
- `sprint-0` a `sprint-8` - Sprint correspondente
- `tipo-feature` / `tipo-backend` / `tipo-frontend` - Tipo do card
- `epic-*` - Epic relacionado
- `priority-*` - Prioridade
- `implemented` - Cards já implementados
- `hub-*` - Hub de configuração (cards config)

---

## DOCUMENTOS RELACIONADOS

> **Referência rápida para o time de desenvolvimento consultar durante a implementação**

| Documento | Descrição | Atualização |
|-----------|-----------|-------------|
| [lia-mvp-cards-jira.md](./lia-mvp-cards-jira.md) | **144 Cards MVP detalhados** (importados no Jira WT-893 a WT-1036) | 26 Jan ✅ |
| [configuracoes-admin-cards-jira.md](./configuracoes-admin-cards-jira.md) | **58 Cards Config Admin** (importados no Jira WT-1037 a WT-1094) | 26 Jan ✅ |
| [LIA_UNIFIED_METHODOLOGY.md](./LIA_UNIFIED_METHODOLOGY.md) | Metodologia unificada 4 camadas (Pré-req + BARS + WSI + Calibração) | 22 Jan ✅ |
| [WSI_METHODOLOGY_REFERENCE.md](./WSI_METHODOLOGY_REFERENCE.md) | Referência completa WSI (Bloom, Dreyfus, Big Five, CBI) | 22 Jan ✅ |
| [JOB_CREATION_WIZARD_FLOW.md](./JOB_CREATION_WIZARD_FLOW.md) | Fluxo wizard conversacional 9 steps com Saturação e Governança | 22 Jan ✅ |
| [funil-talentos-ia-architecture.md](./funil-talentos-ia-architecture.md) | Arquitetura IA do funil (agentes, saturação, governança, calibração) | 22 Jan ✅ |
| [funil-talentos-cards-jira.md](./funil-talentos-cards-jira.md) | Cards Jira do Funil de Talentos (complementar a este documento) | 22 Jan ✅ |
| [AI_STAGE_AUTOMATION_ARCHITECTURE.md](./AI_STAGE_AUTOMATION_ARCHITECTURE.md) | Arquitetura de automação de estágios com IA | 19 Jan ⚠️ |
| [CANDIDATE_STATUS_REFERENCE.md](./CANDIDATE_STATUS_REFERENCE.md) | Referência completa de status e sub-status de candidatos dentro da vaga | 19 Jan ⚠️ |
| [gestao-vagas-fluxos.md](./gestao-vagas-fluxos.md) | Fluxos de usuário da gestão de vagas (UX/UI patterns) | 12 Dez ❌ |
| [DATABASE_FIELDS_REFERENCE.md](./DATABASE_FIELDS_REFERENCE.md) | Mapeamento completo de campos do banco de dados (65 tabelas) | 22 Jan ✅ |
| [COMPANY_DEFAULTS_SYNC_ARCHITECTURE.md](./COMPANY_DEFAULTS_SYNC_ARCHITECTURE.md) | Arquitetura de pré-preenchimento inteligente com defaults da empresa | 22 Jan ✅ |
| [SETTINGS_MENU_MAPPING_FOR_WIZARD.md](./SETTINGS_MENU_MAPPING_FOR_WIZARD.md) | Mapeamento completo do menu Configurações para consumo no Wizard | 22 Jan ✅ |
| [design-system-para-designer.md](./design-system-para-designer.md) | Design System completo para modais (dimensões, tipografia, cores, hierarquia) | 23 Jan ✅ |
| [WEDOTALENT_INTEGRACOES_COMPLETO.md](./WEDOTALENT_INTEGRACOES_COMPLETO.md) | Ecossistema completo de 35+ integrações (mapas visuais, fluxo de dados, custos) | 23 Jan ✅ |
| [LIA_AGENT_ARCHITECTURE_COMPLETE.md](./LIA_AGENT_ARCHITECTURE_COMPLETE.md) | Arquitetura completa dos 9 agentes LIA (LangGraph, compliance, auditoria, replicação) | 23 Jan ✅ |
| [proposals/job-wizard-enhancement-plan.md](./proposals/job-wizard-enhancement-plan.md) | Documento consolidado v4.0 do Wizard de Criação de Vagas (27 seções) | 24 Jan ✅ |

**Legenda:** ✅ Atualizado | ⚠️ Revisar | ❌ Desatualizado

---

## 1. Visão Geral do MVP

### 1.1 Objetivo
Entregar um sistema funcional onde o recrutador consiga:
- Pesquisar e adicionar candidatos em vagas (busca manual pelo recrutador OU solicitação para LIA buscar)
- Ter a LIA gerando perguntas de triagem automaticamente
- **Aprovar candidatos mapeados** antes da LIA iniciar contato
- Ter a LIA fazendo contato via WhatsApp e triagem WSI (somente após aprovação)
- **Aprovar/reprovar candidatos triados** com base no score WSI
- Ter a LIA agendando entrevistas (aprovados) ou dando feedback (reprovados)

### 1.2 Escopo MVP
O MVP termina no **agendamento da entrevista pela LIA**. Etapas posteriores (entrevista, proposta, contratação) serão gerenciadas no ATS integrado.

### 1.3 Portões de Aprovação (Gates)
O fluxo MVP possui **2 portões de aprovação obrigatórios** onde o recrutador deve agir:

| Gate | Momento | Ação do Recrutador | Se APROVADO | Se REPROVADO |
|------|---------|-------------------|-------------|--------------|
| **Gate 1** | Após mapeamento | Aprovar candidatos para triagem | LIA inicia contato WhatsApp | LIA envia feedback → Coluna "Reprovados" |
| **Gate 2** | Após triagem WSI | Aprovar/Reprovar com base no score | LIA agenda entrevista | LIA envia feedback → Coluna "Reprovados" |

**Importante:** Em ambos os gates, candidatos reprovados recebem feedback automático da LIA e são movidos para a coluna "Reprovados" com sub-status `feedback_enviado`.

### 1.4 Fontes de Candidatos
Os candidatos podem vir de 4 fontes:

| Fonte | Descrição | Quem Adiciona |
|-------|-----------|---------------|
| **Base Interna** | Candidatos já cadastrados na plataforma | Recrutador busca e adiciona |
| **Busca Global** | LinkedIn, Pearch, outras fontes externas | Recrutador solicita, LIA busca e sugere |
| **Importação ATS** | Candidatos vindos do ATS integrado | Sistema importa automaticamente |
| **Inscrição via Link** | Candidatos que se inscrevem via link publicado em mídias sociais | Candidato se auto-cadastra via WhatsApp |

#### Fluxo de Inscrição via Link Publicado

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO: INSCRIÇÃO VIA LINK PUBLICADO                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. GERAR LINK                    2. PUBLICAR                              │
│   ───────────────                  ──────────────                           │
│   • Recrutador acessa              • LinkedIn, Instagram,                   │
│     tabela de vagas                  Facebook, WhatsApp,                    │
│   • Clica em "Gerar Link"            Job Boards                             │
│   • Sistema cria URL única         • Link compartilhável                    │
│     com tracking                     com preview                            │
│                                                                             │
│   3. CANDIDATO CLICA               4. WHATSAPP ABRE                         │
│   ────────────────────             ─────────────────                        │
│   • Link redireciona para          • Mensagem pré-formatada                 │
│     WhatsApp da LIA                  com código da vaga                     │
│   • Deep link: wa.me/...           • LIA identifica a vaga                  │
│                                      automaticamente                        │
│                                                                             │
│   5. COLETA DE DADOS               6. TRIAGEM AUTOMÁTICA                    │
│   ──────────────────               ────────────────────                     │
│   • LIA solicita CV                • Candidato entra na                     │
│     (PDF/DOC ou link)                coluna TRIAGEM                         │
│   • LIA faz perguntas de           • LIA aplica perguntas WSI               │
│     cadastro (nome, email,         • Score calculado                        │
│     telefone, cidade)              • Candidato pronto para                  │
│   • Cria perfil do candidato         Gate 2 (aprovação)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Componentes do Link:**
- **URL Base**: `https://lia.wedotalent.com/apply/{vacancy_code}`
- **Redirect**: Abre WhatsApp com mensagem pré-formatada
- **Tracking**: UTM params para medir conversão por canal
- **Preview**: Open Graph tags para preview em redes sociais

**Perguntas de Cadastro (via WhatsApp):**
1. Nome completo
2. Email
3. Telefone (já capturado do WhatsApp)
4. Cidade/Estado
5. Envio de CV (arquivo ou link LinkedIn)
6. Pretensão salarial (opcional)
7. Disponibilidade para início

**Diferença para outros candidatos:**
- Candidatos via link **pulam a etapa Funil** e vão direto para **Triagem**
- Não precisam de aprovação no Gate 1 (já demonstraram interesse ativo)
- Recebem perguntas WSI imediatamente após cadastro

### 1.5 Dependência de ATS
A integração com ATS é **desejável mas não bloqueante** para o MVP:
- **Sem ATS**: Recrutador cadastra vagas e candidatos manualmente na plataforma
- **Com ATS**: Vagas e candidatos são importados automaticamente

O fluxo core (triagem, score, agendamento) funciona independentemente do ATS.

### 1.6 Status das Funcionalidades (Fevereiro 2026)
| Módulo | Funcionalidade | Status | Observação |
|--------|----------------|--------|------------|
| Autenticação | Login/Logout | ⚠️ Parcial | Estrutura básica, falta integração WorkOS |
| Funil de Talentos | Busca de candidatos | ⚠️ Parcial | UI básica, falta busca semântica |
| Funil de Talentos | Filtros de busca | ⚠️ Parcial | Falta filtros avançados |
| Funil de Talentos | Visualização de candidatos | ⚠️ Parcial | Falta preview completo |
| Funil de Talentos | Adicionar candidatos à vaga | ⚠️ Parcial | Falta integração com sourcing |
| Vagas | Criar/Editar vaga (Wizard) | 📋 A fazer | 6 estágios planejados, wizard conversacional |
| Vagas | Listar vagas | 📋 A fazer | Falta integração com backend |
| Kanban | Estrutura básica (colunas) | ⚠️ Parcial | Falta badges, ícones, ações, aprovação |
| Kanban | Drag and drop entre colunas | ⚠️ Parcial | Falta integração com gates |
| Kanban | Navegação horizontal (setas) | ⚠️ Parcial | - |
| Tabela | Estrutura básica | ⚠️ Parcial | Falta filtros, colunas config, highlight, preview |
| Pipeline | Cards de etapas (carrossel) | ⚠️ Parcial | Falta badges e contadores |

**Nota:** Status atualizado em Fevereiro 2026. A maioria das funcionalidades tem estrutura básica de UI mas falta integração com backend e agentes IA.

---

## 2. Fluxo MVP Detalhado

### 2.1 Diagrama do Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO MVP - PLATAFORMA LIA                            │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                              ┌──────────────┐
    │  RECRUTADOR  │                              │     LIA      │
    └──────┬───────┘                              └──────┬───────┘
           │                                             │
           │  1. CRIAR VAGA                              │
           │  ─────────────────────────────────────────► │
           │  • Usa Wizard Conversacional                │
           │  • Define requisitos, benefícios            │
           │  • Configura pipeline customizado           │
           │                                             │
           │                    2. GERAR PERGUNTAS       │
           │  ◄───────────────────────────────────────── │
           │  • LIA analisa requisitos da vaga           │
           │  • Gera perguntas WSI (7 blocos)            │
           │  • Perguntas comportamentais + técnicas     │
           │                                             │
           │  3. BUSCAR CANDIDATOS                       │
           │  ─────────────────────────────────────────► │
           │  • Solicita busca na base interna           │
           │  • Solicita busca global (Pearch/LinkedIn)  │
           │                                             │
           │                    4. MAPEAR CANDIDATOS     │
           │  ◄───────────────────────────────────────── │
           │  • LIA busca e ranqueia candidatos          │
           │  • Adiciona candidatos na vaga              │
           │  • Etapa: FUNIL                             │
           │                                             │
           │  5. APROVAR MAPEADOS                        │
           │  ─────────────────────────────────────────► │
           │  • Revisa candidatos mapeados               │
           │  • Aprova para triagem                      │
           │  • Move para etapa: TRIAGEM                 │
           │                                             │
           │                    6. CONTATAR VIA WHATSAPP │
           │  ◄───────────────────────────────────────── │
           │  • LIA envia mensagem de abordagem          │
           │  • Usa template configurado                 │
           │  • Aguarda resposta do candidato            │
           │                                             │
           │                    7. FAZER TRIAGEM WSI     │
           │  ◄───────────────────────────────────────── │
           │  • LIA conduz conversa via WhatsApp         │
           │  • Aplica perguntas de triagem              │
           │  • Avalia respostas (Bloom, Dreyfus, CBI)   │
           │  • Calcula Score WSI                        │
           │                                             │
           │                    8. DEVOLVER TRIADOS      │
           │  ◄───────────────────────────────────────── │
           │  • Candidatos voltam com Score WSI          │
           │  • Parecer LIA gerado                       │
           │  • Notificação para recrutador              │
           │                                             │
           │  9. APROVAR/REPROVAR TRIADOS                │
           │  ─────────────────────────────────────────► │
           │  • Revisa score e parecer                   │
           │  • Aprova → Move para SHORT LIST            │
           │  • Reprova → Marca como REPROVADO           │
           │                                             │
           │                    10A. AGENDAR ENTREVISTA  │
           │  ◄───────────────────────────────────────── │
           │  (Se APROVADO)                              │
           │  • LIA envia convite de agendamento         │
           │  • Candidato escolhe horário                │
           │  • LIA confirma no calendário               │
           │  • Envia confirmação para ambos             │
           │                                             │
           │                    10B. DAR FEEDBACK        │
           │  ◄───────────────────────────────────────── │
           │  (Se REPROVADO)                             │
           │  • LIA envia mensagem de feedback           │
           │  • Usa template configurado                 │
           │  • Agradece participação                    │
           │                                             │
           ▼                                             ▼
    ┌──────────────────────────────────────────────────────────┐
    │              FIM DO ESCOPO MVP                           │
    │  Candidatos aprovados: Entrevista agendada               │
    │  Candidatos reprovados: Feedback enviado                 │
    │  Próximas etapas: Gerenciadas no ATS                     │
    └──────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Estados do Candidato no MVP

```
                                    ┌─────────────┐
                                    │   INÍCIO    │
                                    └──────┬──────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: FUNIL                                                              │
│ Candidatos mapeados pela LIA (busca interna + global)                       │
│ Sub-status: mapeado, aguardando_aprovacao                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │ Recrutador aprova?                │
                         │                                   │
                    ┌────┴────┐                         ┌────┴────┐
                    │   SIM   │                         │   NÃO   │
                    └────┬────┘                         └────┬────┘
                         │                                   │
                         ▼                                   ▼
┌─────────────────────────────────────┐     ┌─────────────────────────────────┐
│ ETAPA 2: TRIAGEM                    │     │ ETAPA: REPROVADO (Gate 1)       │
│ LIA contata via WhatsApp            │     │ LIA envia feedback automático   │
│ LIA aplica perguntas WSI            │     │ Sub-status: feedback_enviado    │
│ Sub-status: aguardando_contato,     │     │ Candidato movido para coluna    │
│ em_triagem, triagem_concluida       │     │ "Reprovados"                    │
└─────────────────────────────────────┘     └─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: TRIAGEM CONCLUÍDA                                                  │
│ Score WSI calculado                                                         │
│ Parecer LIA gerado                                                          │
│ Notificação enviada ao recrutador                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                         ┌─────────────────┴─────────────────┐
                         │ Recrutador aprova score?          │
                         │                                   │
                    ┌────┴────┐                         ┌────┴────┐
                    │   SIM   │                         │   NÃO   │
                    └────┬────┘                         └────┬────┘
                         │                                   │
                         ▼                                   ▼
┌─────────────────────────────────────┐     ┌─────────────────────────────────┐
│ ETAPA 4: SHORT LIST                 │     │ ETAPA: REPROVADO (Gate 2)       │
│ LIA agenda entrevista               │     │ LIA envia feedback automático   │
│ Sub-status: aguardando_agendamento, │     │ Sub-status: feedback_enviado    │
│ entrevista_agendada                 │     │ Candidato movido para coluna    │
│                                     │     │ "Reprovados"                    │
└─────────────────────────────────────┘     └─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: ENTREVISTA AGENDADA                                                │
│ ══════════════════════════════════════════════════════════════════════════  │
│                         FIM DO ESCOPO MVP                                   │
│ ══════════════════════════════════════════════════════════════════════════  │
│ A partir daqui o recrutador gerencia no ATS                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Funcionalidades a Desenvolver

### 3.1 Wizard Conversacional de Criação de Vaga

**Descrição:**  
Interface conversacional onde a LIA guia o recrutador na criação da vaga, fazendo perguntas e sugerindo valores.

**Requisitos Funcionais:**
- [ ] Chat conversacional para criar vaga
- [ ] LIA faz perguntas sobre o cargo (título, senioridade, área)
- [ ] LIA pergunta sobre requisitos (skills, experiência, formação)
- [ ] LIA pergunta sobre benefícios e remuneração
- [ ] LIA permite configurar pipeline customizado (quais etapas usar)
- [ ] Ao final, LIA apresenta resumo para confirmação
- [ ] Salvar vaga no banco de dados

**Requisitos Técnicos:**
- API: `POST /api/v1/vacancies` (criar vaga)
- API: `POST /api/v1/lia/wizard/conversation` (conversa wizard)
- Integração com Claude/Anthropic para processamento de linguagem natural
- Armazenar configuração de pipeline por vaga

**Critérios de Aceite:**
- [ ] Recrutador consegue criar vaga conversando com LIA
- [ ] Vaga é salva com todos os campos preenchidos
- [ ] Pipeline customizado é salvo corretamente
- [ ] Tempo de resposta da LIA < 3 segundos

---

### 3.2 Geração de Perguntas de Triagem

**Descrição:**  
LIA analisa os requisitos da vaga e gera automaticamente perguntas de triagem baseadas na metodologia WSI.

**Requisitos Funcionais:**
- [ ] Analisar requisitos técnicos da vaga
- [ ] Analisar requisitos comportamentais
- [ ] Gerar perguntas usando metodologia WSI (7 blocos)
- [ ] Incluir metadados: Big Five, Bloom Taxonomy, Dreyfus Model
- [ ] Permitir recrutador revisar/editar perguntas geradas
- [ ] Salvar perguntas vinculadas à vaga

**Estrutura WSI - 7 Blocos de Perguntas:**
1. **Elegibilidade** - Requisitos eliminatórios (localização, disponibilidade)
2. **Experiência Técnica** - Conhecimentos específicos da função
3. **Competências Comportamentais** - Soft skills e atitudes
4. **Fit Cultural** - Alinhamento com valores da empresa
5. **Motivação** - Interesse e expectativas
6. **Situacionais** - Cenários hipotéticos (STAR)
7. **Expectativas** - Pretensão salarial, disponibilidade

**Requisitos Técnicos:**
- API: `POST /api/v1/vacancies/{id}/generate-questions`
- API: `GET /api/v1/vacancies/{id}/questions`
- API: `PUT /api/v1/vacancies/{id}/questions`
- Integração com Claude para geração de perguntas
- Prompt engineering para qualidade das perguntas

**Critérios de Aceite:**
- [ ] Mínimo 10 perguntas geradas por vaga (verificável por contagem)
- [ ] Cada pergunta tem metadados: categoria (técnica/comportamental/cultural), peso, e mapeamento WSI
- [ ] Recrutador pode editar texto, remover ou adicionar perguntas
- [ ] Perguntas são salvas vinculadas à vaga no banco de dados

---

### 3.3 Screening via WhatsApp (Triagem Conversacional)

**Descrição:**  
LIA conduz triagem automatizada via WhatsApp, fazendo perguntas e avaliando respostas em tempo real.

**Requisitos Funcionais:**
- [ ] Enviar mensagem de abordagem inicial com consentimento (candidato deve aceitar participar)
- [ ] Respeitar opt-out: se candidato responder "Não" ou "Parar", encerrar conversa
- [ ] Conduzir conversa aplicando perguntas de triagem sequencialmente
- [ ] Encerrar triagem ao completar todas as perguntas
- [ ] Calcular Score WSI final
- [ ] Gerar Parecer LIA
- [ ] Registrar histórico completo da conversa

**Requisitos de Consentimento (LGPD):**
- [ ] Primeira mensagem deve explicar propósito e pedir consentimento
- [ ] Candidato deve responder "Sim" para prosseguir
- [ ] Opção de opt-out ("Parar", "Não quero participar") deve ser respeitada
- [ ] Registrar aceite/recusa no sistema

**Nota:** Flow adaptativo (perguntas que mudam baseado em respostas) é **Pós-MVP**. No MVP, as perguntas são aplicadas sequencialmente.

**Flow da Conversa:**
```
1. ABORDAGEM
   LIA: "Olá [Nome]! Sou a LIA, assistente de recrutamento da [Empresa]. 
         Você foi selecionado para a vaga de [Cargo]. Posso fazer algumas 
         perguntas rápidas? (Sim/Não)"

2. ELEGIBILIDADE (se Sim)
   LIA: "Ótimo! Para começar: você está disponível para trabalhar em [Local]?"
   LIA: "Qual sua disponibilidade para início?"

3. EXPERIÊNCIA TÉCNICA
   LIA: "Me conta sobre sua experiência com [Skill Principal]"
   LIA: "Você já trabalhou com [Tecnologia X]?"

4. COMPORTAMENTAL
   LIA: "Me dá um exemplo de uma situação difícil que você enfrentou 
         no trabalho e como resolveu" (STAR)

5. MOTIVAÇÃO
   LIA: "O que te atraiu nessa oportunidade?"
   LIA: "Qual sua pretensão salarial?"

6. ENCERRAMENTO
   LIA: "Obrigada pelas respostas, [Nome]! Analisarei seu perfil e 
         em breve você terá um retorno. Até logo!"
```

**Requisitos Técnicos:**
- Integração Twilio (WhatsApp Business API)
- API: `POST /api/v1/whatsapp/send` (enviar mensagem)
- API: `POST /api/v1/whatsapp/webhook` (receber mensagens)
- API: `POST /api/v1/screening/evaluate-response` (avaliar resposta)
- Armazenar histórico de conversa
- State machine para controle do flow

**Critérios de Aceite:**
- [ ] Mensagens enviadas via WhatsApp com sucesso (verificar logs Twilio)
- [ ] Todas as perguntas são aplicadas sequencialmente até encerramento
- [ ] Histórico de conversa é salvo no banco com timestamps
- [ ] Opt-out é respeitado e registrado
- [ ] Score WSI calculado ao final da conversa

**Nota sobre SLA de resposta:** Tempo de resposta da LIA depende de infraestrutura (Claude API, Twilio). Meta inicial: < 10 segundos. Otimização de latência é **Pós-MVP**.

---

### 3.4 Score WSI (WeDoTalent Skill Index)

**Descrição:**  
Sistema de pontuação que avalia candidatos com base nas respostas da triagem, gerando um score numérico e qualitativo.

**Requisitos Funcionais:**
- [ ] Avaliar cada resposta individualmente (0-10)
- [ ] Aplicar pesos por categoria (técnico, comportamental, cultural)
- [ ] Calcular score final (0-100)
- [ ] Classificar candidato (A, B, C, D)
- [ ] Gerar parecer textual da LIA
- [ ] Exibir score na interface (badge, card)

**Estrutura do Score:**
```
SCORE WSI = (
  Elegibilidade × 15% +
  Experiência Técnica × 30% +
  Competências Comportamentais × 25% +
  Fit Cultural × 15% +
  Motivação × 10% +
  Expectativas × 5%
)

CLASSIFICAÇÃO:
- A (80-100): Altamente recomendado
- B (60-79): Recomendado
- C (40-59): Recomendado com ressalvas
- D (0-39): Não recomendado
```

**Requisitos Técnicos:**
- API: `POST /api/v1/screening/{id}/calculate-score`
- API: `GET /api/v1/candidates/{id}/wsi-score`
- Modelo de avaliação com Claude
- Armazenar score e parecer no banco

**Critérios de Aceite:**
- [ ] Score calculado corretamente (0-100)
- [ ] Classificação A/B/C/D correta
- [ ] Parecer LIA gerado em linguagem natural
- [ ] Score visível na tabela de candidatos
- [ ] Score visível no card do candidato

---

### 3.5 Templates de Mensagens

**Descrição:**  
Templates configuráveis para mensagens automáticas enviadas pela LIA.

**Templates MVP (4 tipos):**

| Template | Momento | Variáveis |
|----------|---------|-----------|
| **Abordagem** | Primeiro contato com candidato | {{nome}}, {{cargo}}, {{empresa}} |
| **Agendamento** | Convite para entrevista | {{nome}}, {{cargo}}, {{link_agendamento}}, {{data_limite}} |
| **Confirmação** | Após candidato confirmar horário | {{nome}}, {{data}}, {{horario}}, {{local_ou_link}}, {{entrevistador}} |
| **Pós-Entrevista** | Feedback do recrutador | {{nome}}, {{cargo}}, {{resultado}}, {{feedback}} |

**Requisitos Funcionais:**
- [ ] CRUD de templates por empresa
- [ ] Editor de template com variáveis
- [ ] Preview de template com dados de exemplo
- [ ] Template padrão para cada tipo (default)
- [ ] Histórico de versões do template

**Requisitos Técnicos:**
- API: `GET /api/v1/templates`
- API: `POST /api/v1/templates`
- API: `PUT /api/v1/templates/{id}`
- API: `DELETE /api/v1/templates/{id}`
- API: `POST /api/v1/templates/{id}/render` (renderizar com variáveis)

**Critérios de Aceite:**
- [ ] 4 templates padrão criados
- [ ] Variáveis substituídas corretamente
- [ ] Recrutador pode personalizar templates
- [ ] Templates salvos por empresa

---

### 3.6 Agendamento Automático de Entrevista

**Descrição:**  
LIA agenda entrevistas automaticamente para candidatos aprovados, sincronizando com calendário do recrutador.

**Requisitos Funcionais:**
- [ ] Consultar disponibilidade do recrutador (calendário)
- [ ] Enviar opções de horário para candidato (via WhatsApp)
- [ ] Candidato escolhe horário preferido
- [ ] Criar evento no calendário
- [ ] Enviar confirmação para recrutador e candidato
- [ ] Atualizar status do candidato na vaga

**Flow de Agendamento:**
```
1. Candidato APROVADO após triagem
2. LIA consulta slots disponíveis no calendário do recrutador
3. LIA envia mensagem WhatsApp:
   "Parabéns, [Nome]! Você foi aprovado para a próxima etapa.
    Escolha um horário para sua entrevista:
    1️⃣ Segunda, 10h
    2️⃣ Terça, 14h
    3️⃣ Quarta, 16h"
4. Candidato responde com número da opção
5. LIA cria evento no calendário (Microsoft Graph)
6. LIA envia confirmação com detalhes
7. Status do candidato → "entrevista_agendada"
```

**Requisitos Técnicos:**
- Integração Microsoft Graph API (calendário)
- API: `GET /api/v1/calendar/availability`
- API: `POST /api/v1/calendar/events`
- API: `POST /api/v1/interviews/schedule`
- Webhook para respostas do candidato

**Critérios de Aceite:**
- [ ] Slots disponíveis são detectados corretamente
- [ ] Evento criado no calendário do recrutador
- [ ] Candidato recebe confirmação com detalhes
- [ ] Status atualizado para "entrevista_agendada"

---

### 3.7 Feedback Automático para Reprovados

**Descrição:**  
LIA envia mensagem de feedback para candidatos reprovados, agradecendo a participação.

**Requisitos Funcionais:**
- [ ] Detectar quando candidato é reprovado
- [ ] Selecionar template de feedback apropriado
- [ ] Enviar mensagem via WhatsApp
- [ ] Registrar feedback enviado no histórico
- [ ] Atualizar sub-status para "feedback_enviado"

**Requisitos Técnicos:**
- Trigger automático na mudança de status
- API: `POST /api/v1/candidates/{id}/send-feedback`
- Usar template de feedback configurado
- Log de mensagens enviadas

**Critérios de Aceite:**
- [ ] Feedback enviado automaticamente ao reprovar
- [ ] Mensagem usa template correto
- [ ] Histórico registrado
- [ ] Sub-status atualizado

---

### 3.8 Integração com ATS

**Descrição:**  
Sincronização bidirecional com sistemas ATS (Gupy, Pandapé, Merge.dev).

**Requisitos Funcionais:**
- [ ] Importar vagas do ATS
- [ ] Importar candidatos do ATS
- [ ] Exportar candidatos para o ATS
- [ ] Sincronizar status/etapa
- [ ] Sincronizar notas e pareceres
- [ ] Webhook para atualizações em tempo real

**Fluxo de Sincronização:**
```
┌─────────────────┐         ┌─────────────────┐
│   PLATAFORMA    │ ◄─────► │      ATS        │
│      LIA        │         │ (Gupy/Pandapé)  │
└─────────────────┘         └─────────────────┘
        │                           │
        │  1. Importar vagas        │
        │  ◄──────────────────────  │
        │                           │
        │  2. Importar candidatos   │
        │  ◄──────────────────────  │
        │                           │
        │  3. Triagem na LIA        │
        │  (interno)                │
        │                           │
        │  4. Exportar resultados   │
        │  ──────────────────────►  │
        │  • Score WSI              │
        │  • Parecer LIA            │
        │  • Status atualizado      │
        │                           │
```

**Requisitos Técnicos:**
- Conectores: Gupy API, Pandapé API, Merge.dev (API unificada para 180+ ATS/HRIS)
- API: `POST /api/v1/ats/sync`
- API: `GET /api/v1/ats/jobs`
- API: `POST /api/v1/ats/candidates/export`
- Mapeamento de campos entre sistemas
- Fila de sincronização (async)

**Critérios de Aceite:**
- [ ] Vagas importadas do ATS
- [ ] Candidatos importados do ATS
- [ ] Score e parecer exportados para ATS
- [ ] Status sincronizado em tempo real

---

### 3.9 Template de Pipeline Customizável

**Descrição:**  
Permitir que cada empresa configure quais etapas do pipeline deseja utilizar.

**Etapas Disponíveis:**
1. Funil
2. Triagem
3. Long List
4. Short List
5. Entrevista RH
6. Teste Técnico
7. Teste de Inglês
8. Entrevista Técnica
9. Entrevista Gestor
10. Entrevista Gestor 2
11. Entrevista Final
12. Referências
13. Proposta
14. Contratado
15. Reprovado
16. Proposta Recusada

**Requisitos Funcionais:**
- [ ] Interface para selecionar etapas ativas
- [ ] Ordenar etapas (drag-and-drop)
- [ ] Salvar template por empresa
- [ ] Aplicar template ao criar vaga
- [ ] Permitir template diferente por vaga

**Requisitos Técnicos:**
- API: `GET /api/v1/pipeline-templates`
- API: `POST /api/v1/pipeline-templates`
- API: `PUT /api/v1/pipeline-templates/{id}`
- Armazenar configuração no banco

**Critérios de Aceite:**
- [ ] Empresa pode ativar/desativar etapas
- [ ] Ordem das etapas é respeitada
- [ ] Vaga usa template da empresa ou customizado

---

### 3.10 Perguntas de Triagem Customizadas

**Descrição:**  
Permitir que empresas criem banco de perguntas próprias além das geradas pela LIA.

**Requisitos Funcionais:**
- [ ] CRUD de perguntas por empresa
- [ ] Categorizar perguntas (técnica, comportamental, cultural)
- [ ] Vincular perguntas a vagas específicas ou globais
- [ ] Importar perguntas de banco padrão
- [ ] Exportar perguntas

**Requisitos Técnicos:**
- API: `GET /api/v1/questions-bank`
- API: `POST /api/v1/questions-bank`
- API: `PUT /api/v1/questions-bank/{id}`
- API: `DELETE /api/v1/questions-bank/{id}`

**Critérios de Aceite:**
- [ ] Empresa pode criar perguntas próprias
- [ ] Perguntas podem ser usadas em qualquer vaga
- [ ] Perguntas são categorizadas

---

### 3.11 Benefícios da Empresa

**Descrição:**  
Cadastro de benefícios oferecidos pela empresa para usar nas vagas.

**Requisitos Funcionais:**
- [ ] CRUD de benefícios
- [ ] Categorizar (saúde, alimentação, transporte, etc.)
- [ ] Selecionar benefícios ao criar vaga
- [ ] Exibir benefícios na página pública da vaga

**Requisitos Técnicos:**
- API: `GET /api/v1/benefits`
- API: `POST /api/v1/benefits`
- API: `PUT /api/v1/benefits/{id}`
- API: `DELETE /api/v1/benefits/{id}`

**Critérios de Aceite:**
- [ ] Benefícios cadastrados por empresa
- [ ] Benefícios vinculados às vagas
- [ ] Exibidos na descrição da vaga

---

### 3.12 Gestão de Equipes/Usuários

**Descrição:**  
Gerenciar usuários e permissões dentro da empresa.

**Requisitos Funcionais:**
- [ ] Convidar novos usuários
- [ ] Definir papéis (Admin, Recrutador, Gestor, Visualizador)
- [ ] Atribuir recrutador responsável por vaga
- [ ] Listar membros da equipe
- [ ] Remover/desativar usuário

**Requisitos Técnicos:**
- API: `GET /api/v1/team/members`
- API: `POST /api/v1/team/invite`
- API: `PUT /api/v1/team/members/{id}/role`
- API: `DELETE /api/v1/team/members/{id}`
- Sistema de permissões (RBAC)

**Critérios de Aceite:**
- [ ] Convite enviado por email
- [ ] Usuário consegue aceitar convite
- [ ] Permissões aplicadas corretamente
- [ ] Admin pode gerenciar equipe

---

### 3.13 Notificações Básicas

**Descrição:**  
Sistema de notificações para alertar recrutador sobre eventos importantes.

**Eventos que geram notificação:**
- Candidato completou triagem
- Candidato agendou entrevista
- Novo candidato mapeado pela LIA
- Triagem com score alto (A)
- Candidato respondeu mensagem

**Requisitos Funcionais:**
- [ ] Notificações in-app (sino)
- [ ] Badge com contador de não lidas
- [ ] Marcar como lida
- [ ] Listar histórico de notificações
- [ ] Link direto para ação

**Requisitos Técnicos:**
- API: `GET /api/v1/notifications`
- API: `PUT /api/v1/notifications/{id}/read`
- API: `PUT /api/v1/notifications/read-all`
- WebSocket para real-time (opcional MVP)

**Critérios de Aceite:**
- [ ] Notificações aparecem ao ocorrer evento
- [ ] Badge mostra quantidade correta
- [ ] Click leva para contexto correto

---

## 4. Integrações Necessárias

### 4.1 WhatsApp (Twilio ou Meta/Facebook)

> **Alternativas disponíveis:** Twilio WhatsApp Business API ou WhatsApp Business Platform (Meta/Facebook)

#### Opção A: Twilio (Recomendada para MVP)

**Credenciais necessárias:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

**Endpoints Twilio:**
- Enviar mensagem: `POST /2010-04-01/Accounts/{AccountSid}/Messages.json`
- Webhook recebimento: Configurar URL no Twilio Console

**Fluxo:**
```
LIA → Twilio API → WhatsApp → Candidato
Candidato → WhatsApp → Twilio Webhook → LIA
```

#### Opção B: WhatsApp Business Platform (Meta/Facebook)

**Credenciais necessárias:**
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_BUSINESS_ACCOUNT_ID`
- `WHATSAPP_ACCESS_TOKEN`

**Endpoints Meta:**
- Enviar mensagem: `POST /{phone-number-id}/messages`
- Webhook recebimento: Configurar webhook no Facebook App Dashboard
- Templates: `POST /{whatsapp-business-account-id}/message_templates`

**Fluxo:**
```
LIA → Meta Graph API → WhatsApp → Candidato
Candidato → WhatsApp → Meta Webhook → LIA
```

**Vantagens Meta:**
- Custo potencialmente menor para alto volume
- Acesso direto à API oficial
- Melhor suporte a recursos nativos do WhatsApp

**Vantagens Twilio:**
- Setup mais rápido (sandbox disponível)
- Suporte multi-canal (SMS, Voice, Email)
- Dashboard unificado de comunicações

---

### 4.2 Calendário via Microsoft Graph

**Credenciais necessárias:**
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`

**Endpoints Graph:**
- Listar eventos: `GET /me/calendar/events`
- Criar evento: `POST /me/calendar/events`
- Buscar disponibilidade: `POST /me/calendar/getSchedule`

---

### 4.3 ATS e HRIS (Gupy/Pandapé/Merge)

**Para cada ATS:**
- API Key ou OAuth credentials
- Documentação de endpoints
- Mapeamento de campos

**Merge.dev (Unified API):**
- Conecta 180+ integrações ATS e HRIS via uma única API
- Suporta: Greenhouse, Lever, Workday, SAP SuccessFactors, BambooHR, etc
- Vantagens: Uma única integração para múltiplos sistemas
- API REST com OpenAPI spec
- Credenciais: `MERGE_API_KEY`, `MERGE_ACCOUNT_TOKEN`
- Endpoints principais:
  - `GET /ats/v1/jobs` (listar vagas)
  - `GET /ats/v1/candidates` (listar candidatos)
  - `POST /ats/v1/candidates` (criar candidato)
  - `GET /hris/v1/employees` (listar funcionários)

---

### 4.4 IA (Claude/Anthropic)

**Credenciais:**
- `ANTHROPIC_API_KEY` (já configurado)

**Uso:**
- Geração de perguntas
- Avaliação de respostas
- Parecer LIA
- Wizard conversacional

---

## 5. Modelo de Dados (Entidades Principais)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Company     │────►│     Vacancy     │────►│    Candidate    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PipelineTemplate    │   VacancyCandidate    │   ScreeningSession  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Benefit     │     │   Notification  │     │   WSIScore      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 6. Priorização de Desenvolvimento

**Nota:** A priorização abaixo foca no fluxo core primeiro (triagem → score → agendamento). A integração ATS é importante mas pode ser desenvolvida em paralelo sem bloquear o fluxo principal.

### Sprint 1-2: Fundação + LIA Core (Início)
1. 🔧 Autenticação (a fazer - WorkOS)
2. 🔧 CRUD Vagas (a fazer)
3. 🔧 Funil de Talentos (a fazer)
4. 🔧 Gestão de equipes/usuários
5. 🔧 Wizard conversacional de criação de vaga

### Sprint 3-4: LIA Core (Triagem)
6. 🔧 Geração de perguntas de triagem
7. 🔧 Integração WhatsApp (Twilio)
8. 🔧 Flow de triagem conversacional (com consentimento)
9. 🔧 Score WSI

### Sprint 5-6: Automação + Comunicação
10. 🔧 Parecer LIA
11. 🔧 Templates de mensagens (4 tipos)
12. 🔧 Notificações básicas
13. 🔧 Feedback automático para reprovados

### Sprint 7-8: Agendamento
14. 🔧 Integração calendário (Microsoft Graph)
15. 🔧 Agendamento automático
16. 🔧 Confirmação de agendamento

### Sprint 9-10: Configurações + ATS
17. 🔧 Perguntas customizadas
18. 🔧 Benefícios da empresa
19. 🔧 Template de pipeline customizável
20. 🔧 Integração ATS (pode rodar em paralelo desde Sprint 3)

### Desenvolvimento Paralelo (Opcional)
A integração ATS pode ser desenvolvida em paralelo por outra pessoa/equipe:
- **Sprint 3-4**: Importação de vagas do ATS
- **Sprint 5-6**: Importação de candidatos do ATS
- **Sprint 7-8**: Exportação de resultados (score, parecer) para ATS
- **Sprint 9-10**: Sincronização bidirecional completa

### Caminho Crítico (Mínimo para Valor)
```
Wizard → Perguntas → WhatsApp → Triagem → Score → Aprovação → Agendamento
```
Este é o caminho que deve ser priorizado. ATS, configurações avançadas e notificações são importantes mas não bloqueiam a demonstração de valor do MVP.

---

## 6.5 Mapa de Integrações

### Integrações MVP (Obrigatórias)

| Integração | Propósito | Status Atual | Prioridade |
|------------|-----------|--------------|------------|
| **Twilio** | WhatsApp Business API - triagem e comunicação | ✅ Secrets configurados | Alta |
| **Microsoft Graph** | Calendário (agendamento), Teams (link entrevista) | ✅ Secrets configurados | Alta |
| **Anthropic Claude** | LLM principal para LIA (triagem, parecer, wizard) | ✅ Integração instalada | Alta |
| **Google Gemini** | LLM fallback, voz-para-texto | ✅ Integração instalada | Média |
| **WorkOS** | SSO, MFA, gestão de equipes/usuários | 🔧 A configurar | Alta |

### Integrações Pré-Configuradas (Antes do MVP)

| Integração | Propósito | Status |
|------------|-----------|--------|
| **HubSpot** | CRM, gestão comercial, dashboard de métricas | 🔧 Pré-integração |
| **Mailgun** | Email transacional (convites, feedback, notificações) | 🔧 Pré-integração |

### Integrações Pós-MVP / Paralelo

| Integração | Propósito | Quando |
|------------|-----------|--------|
| **Gupy ATS** | Sincronização vagas/candidatos (Brasil) | Paralelo ao MVP |
| **Pandapé ATS** | Sincronização vagas/candidatos (Brasil) | Paralelo ao MVP |
| **Merge.dev** | API unificada para 180+ ATS e HRIS | Paralelo ao MVP |
| **Pearch AI** | Busca global de candidatos (800M+ perfis) | Sprint 2-3 |
| **Apify** | Web scraping LinkedIn para sourcing | MVP |
| **Deepgram** | Speech-to-text (transcrição entrevistas) | Pós-MVP |
| **OpenMic.ai** | Voice screening platform | Pós-MVP |

### Mapa Visual de Integrações

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                 │
│                                    🏢  WEDO TALENT - ECOSSISTEMA COMPLETO                                       │
│                                         35+ Integrações | 2 Capítulos                                           │
│                                                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                 │
│    ┌─────────────────────────────────────────────────┐    ┌─────────────────────────────────────────────────┐   │
│    │                                                 │    │                                                 │   │
│    │            WEDO TALENT ADMIN                    │    │          WEDO TALENT PLATAFORMA                 │   │
│    │          (Capítulo 1 - 8 SaaS)                  │    │        (Capítulo 2 - 25+ APIs)                  │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │         BILLING & MÉTRICAS          │     │    │    │           LLMs & IA                 │     │   │
│    │    │  ┌─────────┐      ┌──────────┐      │     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │  │ Stripe  │      │ProfitWell│      │     │    │    │  │ Claude  │      │ Gemini  │      │     │   │
│    │    │  │ Billing │      │ Metrics  │      │     │    │    │  │Anthropic│      │ Google  │      │     │   │
│    │    │  │  💳     │      │  📊     │      │     │    │    │  │  🧠     │      │  🔮     │      │     │   │
│    │    │  └─────────┘      └──────────┘      │     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │         CRM & ONBOARDING            │     │    │    │        ORQUESTRAÇÃO AGENTES         │     │   │
│    │    │  ┌─────────┐      ┌──────────┐      │     │    │    │  ┌─────────┐ ┌─────────┐ ┌────────┐│     │   │
│    │    │  │ HubSpot │      │  Arrows  │      │     │    │    │  │LangGraph│ │LangChain│ │LangSmith││     │   │
│    │    │  │   CRM   │      │Onboarding│      │     │    │    │  │  Graph  │ │ Chains  │ │ Traces ││     │   │
│    │    │  │  📇     │      │  🎯     │      │     │    │    │  │  🔄     │ │  ⛓️    │ │  🔍   ││     │   │
│    │    │  └─────────┘      └──────────┘      │     │    │    │  └─────────┘ └─────────┘ └────────┘│     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │      AUTENTICAÇÃO ENTERPRISE        │     │    │    │          SOURCING & BUSCA           │     │   │
│    │    │             ┌──────────┐             │     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │             │  WorkOS  │             │     │    │    │  │ Pearch  │      │  Apify  │      │     │   │
│    │    │             │SSO/SCIM  │             │     │    │    │  │ 800M+   │      │LinkedIn │      │     │   │
│    │    │             │  🔐     │             │     │    │    │  │  🔎     │      │  🕷️    │      │     │   │
│    │    │             └──────────┘             │     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │    ┌─────────────────────────────────────┐     │    │    ┌─────────────────────────────────────┐     │   │
│    │    │      COMPLIANCE & GOVERNANÇA        │     │    │    │           VOZ & SPEECH              │     │   │
│    │    │  ┌─────────┐ ┌─────────┐ ┌────────┐│     │    │    │  ┌─────────┐      ┌─────────┐      │     │   │
│    │    │  │ Vanta/  │ │Privacy  │ │ Warden ││     │    │    │  │Deepgram │      │ OpenMic │      │     │   │
│    │    │  │ Drata   │ │ Tools   │ │   AI   ││     │    │    │  │   STT   │      │  Voice  │      │     │   │
│    │    │  │  ✅    │ │  🇧🇷   │ │  🤖   ││     │    │    │  │  🎤     │      │  📞    │      │     │   │
│    │    │  └─────────┘ └─────────┘ └────────┘│     │    │    │  └─────────┘      └─────────┘      │     │   │
│    │    └─────────────────────────────────────┘     │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │                                                 │    │    ┌─────────────────────────────────────┐     │   │
│    │                                                 │    │    │          COMUNICAÇÃO                │     │   │
│    │                                                 │    │    │  ┌────────┐ ┌────────┐ ┌─────────┐ │     │   │
│    │                                                 │    │    │  │MS Graph│ │WhatsApp│ │ Mailgun │ │     │   │
│    │                                                 │    │    │  │Calendar│ │Twilio/ │ │  Email  │ │     │   │
│    │                                                 │    │    │  │  📅    │ │ Meta   │ │  ✉️    │ │     │   │
│    │                                                 │    │    │  └────────┘ └────────┘ └─────────┘ │     │   │
│    │                                                 │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    │                                                 │    │    ┌─────────────────────────────────────┐     │   │
│    │                                                 │    │    │         INTEGRAÇÕES ATS/HRIS        │     │   │
│    │                                                 │    │    │  ┌─────────┐ ┌────────┐ ┌─────────┐ │     │   │
│    │                                                 │    │    │  │ Merge   │ │ Gupy   │ │ Pandapé │ │     │   │
│    │                                                 │    │    │  │ Unified │ │  ATS   │ │  ATS    │ │     │   │
│    │                                                 │    │    │  │  🔗    │ │  🇧🇷   │ │  🇧🇷   │ │     │   │
│    │                                                 │    │    │  └─────────┘ └────────┘ └─────────┘ │     │   │
│    │                                                 │    │    └─────────────────────────────────────┘     │   │
│    │                                                 │    │                                                 │   │
│    └─────────────────────────────────────────────────┘    └─────────────────────────────────────────────────┘   │
│                                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Mapa de Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FLUXO DE INTEGRAÇÕES                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                      │
│   ADMIN (Gestão)                        PLATAFORMA (Core)                        INFRAESTRUTURA     │
│   ──────────────                        ────────────────                         ───────────────     │
│                                                                                                      │
│   ┌──────────┐                                                                                      │
│   │  Stripe  │ ─────────────────────────────────────────────────────────────────┐                   │
│   │ Billing  │                                                                   │                   │
│   └──────────┘                                                                   │                   │
│        │                                                                         │                   │
│        ▼                                                                         ▼                   │
│   ┌──────────┐        ┌───────────────────────────────────────────────┐    ┌──────────┐             │
│   │ProfitWell│        │                                               │    │PostgreSQL│             │
│   │ Metrics  │        │         📋 FUNIL DE VAGAS                     │    │ Database │             │
│   └──────────┘        │                                               │    └──────────┘             │
│        │              │  Wizard ──► Claude ──► JD ──► Publicar        │         │                   │
│        ▼              │    │         │         │          │           │         │                   │
│   ┌──────────┐        │    └────► LangGraph ◄──┘          │           │         ▼                   │
│   │ HubSpot  │        │              │                     │           │    ┌──────────┐             │
│   │   CRM    │ ◄──────┼──────────────┘                     │           │    │  Redis   │             │
│   └──────────┘        │                                    │           │    │  Cache   │             │
│        │              └────────────────────────────────────│───────────┘    └──────────┘             │
│        ▼                                                   │                     │                   │
│   ┌──────────┐        ┌───────────────────────────────────▼───────────┐         │                   │
│   │  Arrows  │        │                                               │         │                   │
│   │Onboarding│        │         👥 FUNIL DE TALENTOS                  │         ▼                   │
│   └──────────┘        │                                               │    ┌──────────┐             │
│        │              │  Pearch ──► Triagem ──► Entrevista ──► Hire   │    │ RabbitMQ │             │
│        │              │    │          │            │           │      │    │  Queue   │             │
│        │              │    │      ┌───┴───┐    ┌───┴───┐       │      │    └──────────┘             │
│        │              │    │      │Claude │    │OpenMic│       │      │         │                   │
│        │              │    │      │Scoring│    │Deepgrm│       │      │         │                   │
│        │              │    │      └───────┘    └───────┘       │      │         ▼                   │
│        │              │    │                                   │      │    ┌──────────┐             │
│        │              │    ▼                                   ▼      │    │  Replit  │             │
│        │              │  ┌─────────────────────────────────────────┐  │    │ Hosting  │             │
│        │              │  │         COMUNICAÇÃO                     │  │    └──────────┘             │
│        │              │  │  MS Graph │ WhatsApp │ Mailgun          │  │                              │
│        │              │  │ (Calendar)│(Twilio/  │ (Email)          │  │                              │
│        │              │  │           │  Meta)   │                  │  │                              │
│        │              │  └─────────────────────────────────────────┘  │                              │
│        │              │                    │                          │                              │
│        │              │                    ▼                          │                              │
│        │              │  ┌─────────────────────────────────────────┐  │                              │
│        │              │  │         INTEGRAÇÕES ATS/HRIS            │  │                              │
│        │              │  │  Merge.dev │ Gupy │ Pandapé             │  │                              │
│        │              │  │  (180+ ATS)│      │                     │  │                              │
│        │              │  └─────────────────────────────────────────┘  │                              │
│        │              │                                               │                              │
│        │              └───────────────────────────────────────────────┘                              │
│        │                                     │                                                       │
│        ▼                                     ▼                                                       │
│   ┌──────────┐        ┌───────────────────────────────────────────────┐                             │
│   │  WorkOS  │ ◄──────┤         ⚙️ MENU CONFIGURAÇÕES                 │                             │
│   │ SSO/SCIM │        │                                               │                             │
│   └──────────┘        │  SSO Setup │ Templates │ Conexões ATS         │                             │
│        │              └───────────────────────────────────────────────┘                             │
│        ▼                                                                                             │
│   ┌──────────────────────────────────────────────────────────────────┐                              │
│   │                    COMPLIANCE & GOVERNANÇA                        │                              │
│   │  Vanta/Drata (SOC 2) │ Privacy Tools (LGPD) │ Warden AI (Bias)   │                              │
│   └──────────────────────────────────────────────────────────────────┘                              │
│                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Secrets e Credenciais Disponíveis

**Comunicação:**
```
✅ TWILIO_ACCOUNT_SID
✅ TWILIO_AUTH_TOKEN
✅ TWILIO_PHONE_NUMBER
```

**Microsoft (Calendário/Teams):**
```
✅ AZURE_CLIENT_ID
✅ AZURE_CLIENT_SECRET
✅ AZURE_TENANT_ID
```

**LLMs (Gerenciados por Replit Integrations):**
```
✅ ANTHROPIC_API_KEY (via python_anthropic_ai_integrations)
✅ GEMINI_API_KEY (via python_gemini_ai_integrations)
```

**Autenticação:**
```
❌ WORKOS_API_KEY (não configurado)
❌ WORKOS_CLIENT_ID (não configurado)
```

**Email (Pré-integração):**
```
❌ MAILGUN_API_KEY (não configurado)
❌ MAILGUN_DOMAIN (não configurado)
```

**CRM (Pré-integração):**
```
❌ HUBSPOT_API_KEY (não configurado)
```

**WhatsApp Meta (Alternativa):**
```
❌ WHATSAPP_PHONE_NUMBER_ID (não configurado)
❌ WHATSAPP_BUSINESS_ACCOUNT_ID (não configurado)
❌ WHATSAPP_ACCESS_TOKEN (não configurado)
```

**ATS (Pós-MVP):**
```
❌ GUPY_CLIENT_ID (não configurado)
❌ GUPY_CLIENT_SECRET (não configurado)
❌ MERGE_API_KEY (não configurado)
❌ MERGE_ACCOUNT_TOKEN (não configurado)
```

**Sourcing (Pós-MVP):**
```
❌ APIFY_API_TOKEN (não configurado)
```

---

## 7. Épicos e Cards para Desenvolvimento

### Legenda de Status
- ✅ **Pronto** - Funcionalidade implementada (frontend/protótipo)
- 🔧 **A Desenvolver** - Precisa ser implementado
- 🔗 **Integração** - Depende de serviço externo
- 📋 **Backend** - Apenas backend
- 🎨 **Frontend** - Apenas frontend

---

### ÉPICO 1: Autenticação e Gestão de Usuários
**Prioridade:** Sprint 1-2 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 1.1 | Login/Logout | ⚠️ Parcial | 🎨 | 📋 WorkOS pendente |
| 1.2 | Gestão de equipes/usuários | 🔧 A desenvolver | 🎨 | 📋 |
| 1.3 | Permissões e papéis (Admin, Recruiter) | 🔧 A desenvolver | 🎨 | 📋 |
| 1.4 | Convite de novos usuários | 🔧 A desenvolver | 🎨 | 📋 |

---

### ÉPICO 2: Wizard Conversacional de Criação de Vaga
**Prioridade:** Sprint 1-2 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 2.1 | Chat conversacional LIA para criar vaga | 🔧 A desenvolver | 🎨 | 📋 |
| 2.2 | LIA pergunta título, senioridade, área | 🔧 A desenvolver | - | 📋 |
| 2.3 | LIA pergunta requisitos (skills, experiência) | 🔧 A desenvolver | - | 📋 |
| 2.4 | LIA pergunta benefícios e remuneração | 🔧 A desenvolver | - | 📋 |
| 2.5 | Configurar pipeline customizado | 🔧 A desenvolver | 🎨 | 📋 |
| 2.6 | Resumo para confirmação e salvar | 🔧 A desenvolver | 🎨 | 📋 |
| 2.7 | Preview da vaga (visualização antes de publicar) | 🔧 A desenvolver | 🎨 | - |
| 2.8 | Editar vaga completa (todos campos + etapas + perguntas) | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `POST /api/v1/vacancies` (criar vaga)
- `GET /api/v1/vacancies/{id}` (preview/detalhes da vaga)
- `PUT /api/v1/vacancies/{id}` (editar vaga completa)
- `PUT /api/v1/vacancies/{id}/stages` (editar etapas)
- `PUT /api/v1/vacancies/{id}/questions` (editar perguntas)
- `POST /api/v1/lia/wizard/conversation` (conversa wizard)

---

### ÉPICO 3: Busca e Mapeamento de Candidatos
**Prioridade:** Sprint 1-2 | **Status:** Parcialmente Pronto
**Dependências:** Épico 2 (Vaga criada)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 3.1 | Buscar candidatos na base interna | ✅ Pronto | ✅ | ✅ |
| 3.2 | Buscar candidatos global (Pearch/LinkedIn) | 🔧 A desenvolver | 🎨 | 📋 |
| 3.3 | LIA ranqueia candidatos por fit | 🔧 A desenvolver | - | 📋 |
| 3.4 | Adicionar candidatos à vaga | ✅ Pronto | ✅ | ✅ |
| 3.5 | Exibir candidatos mapeados no Kanban | ✅ Pronto | ✅ | - |
| 3.6 | Candidato entra como "aguardando_aprovacao" | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `GET /api/v1/candidates/search` (busca interna)
- `POST /api/v1/sourcing/search` (busca global)
- `POST /api/v1/vacancies/{id}/candidates` (adicionar candidato)
- `GET /api/v1/vacancies/{id}/candidates` (listar candidatos da vaga)

---

### ÉPICO 4: Geração de Perguntas de Triagem
**Prioridade:** Sprint 3-4 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 4.1 | Analisar requisitos da vaga | 🔧 A desenvolver | - | 📋 |
| 4.2 | Gerar perguntas WSI (7 blocos) | 🔧 A desenvolver | - | 📋 |
| 4.3 | Incluir metadados (Big Five, Bloom, Dreyfus) | 🔧 A desenvolver | - | 📋 |
| 4.4 | Recrutador revisa/edita perguntas | 🔧 A desenvolver | 🎨 | 📋 |
| 4.5 | Salvar perguntas vinculadas à vaga | 🔧 A desenvolver | - | 📋 |

**APIs:**
- `POST /api/v1/vacancies/{id}/generate-questions`
- `GET /api/v1/vacancies/{id}/questions`
- `PUT /api/v1/vacancies/{id}/questions`

---

### ÉPICO 5: Triagem via WhatsApp
**Prioridade:** Sprint 3-4 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 5.1 | Integração Twilio (WhatsApp Business API) | 🔗 Integração | - | 📋 |
| 5.2 | Enviar mensagem de abordagem + consentimento | 🔧 A desenvolver | - | 📋 |
| 5.3 | Respeitar opt-out (candidato recusa) | 🔧 A desenvolver | - | 📋 |
| 5.4 | State machine para controle do flow | 🔧 A desenvolver | - | 📋 |
| 5.5 | Aplicar perguntas sequencialmente | 🔧 A desenvolver | - | 📋 |
| 5.6 | Avaliar respostas em tempo real | 🔧 A desenvolver | - | 📋 |
| 5.7 | Encerrar triagem e notificar | 🔧 A desenvolver | - | 📋 |
| 5.8 | Salvar histórico de conversa | 🔧 A desenvolver | - | 📋 |
| 5.9 | Visualizar histórico de conversa | 🔧 A desenvolver | 🎨 | 📋 |
| 5.10 | Botão "Iniciar Triagens" em massa (vaga toda) | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `POST /api/v1/whatsapp/send`
- `POST /api/v1/whatsapp/webhook`
- `POST /api/v1/screening/evaluate-response`
- `GET /api/v1/candidates/{id}/screening-history`
- `POST /api/v1/vacancies/{id}/start-screening` (iniciar triagens em massa)

---

### ÉPICO 6: Score WSI e Parecer LIA
**Prioridade:** Sprint 3-4 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 6.1 | Avaliar cada resposta (0-10) | 🔧 A desenvolver | - | 📋 |
| 6.2 | Aplicar pesos por categoria | 🔧 A desenvolver | - | 📋 |
| 6.3 | Calcular score final (0-100) | 🔧 A desenvolver | - | 📋 |
| 6.4 | Classificar A/B/C/D | 🔧 A desenvolver | - | 📋 |
| 6.5 | Gerar parecer textual da LIA | 🔧 A desenvolver | - | 📋 |
| 6.6 | Exibir score na tabela de candidatos | 🔧 A desenvolver | 🎨 | - |
| 6.7 | Exibir score no card do candidato | 🔧 A desenvolver | 🎨 | - |
| 6.8 | Badge de classificação no Kanban | 🔧 A desenvolver | 🎨 | - |

**APIs:**
- `POST /api/v1/screening/{id}/calculate-score`
- `GET /api/v1/candidates/{id}/wsi-score`

---

### ÉPICO 7: Gates de Aprovação
**Prioridade:** Sprint 5-6 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 7.1 | Gate 1: Aprovar candidatos mapeados | 🔧 A desenvolver | 🎨 | 📋 |
| 7.2 | Gate 1: Reprovar → LIA envia feedback | 🔧 A desenvolver | - | 📋 |
| 7.3 | Gate 2: Aprovar candidatos triados | 🔧 A desenvolver | 🎨 | 📋 |
| 7.4 | Gate 2: Reprovar → LIA envia feedback | 🔧 A desenvolver | - | 📋 |
| 7.5 | Mover para coluna "Reprovados" | 🔧 A desenvolver | 🎨 | 📋 |
| 7.6 | Substatus "feedback_enviado" | 🔧 A desenvolver | 🎨 | 📋 |
| 7.7 | Botão bulk de aprovar/reprovar | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `POST /api/v1/candidates/{id}/approve`
- `POST /api/v1/candidates/{id}/reject`
- `POST /api/v1/candidates/bulk-approve`
- `POST /api/v1/candidates/bulk-reject`

---

### ÉPICO 8: Templates de Mensagens
**Prioridade:** Sprint 5-6 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 8.1 | CRUD de templates por empresa | 🔧 A desenvolver | 🎨 | 📋 |
| 8.2 | Template: Abordagem | 🔧 A desenvolver | 🎨 | 📋 |
| 8.3 | Template: Agendamento | 🔧 A desenvolver | 🎨 | 📋 |
| 8.4 | Template: Confirmação | 🔧 A desenvolver | 🎨 | 📋 |
| 8.5 | Template: Pós-Entrevista (Feedback) | 🔧 A desenvolver | 🎨 | 📋 |
| 8.6 | Variáveis dinâmicas ({{nome}}, {{cargo}}) | 🔧 A desenvolver | 🎨 | 📋 |
| 8.7 | Preview de template | 🔧 A desenvolver | 🎨 | - |

**APIs:**
- `GET /api/v1/templates`
- `POST /api/v1/templates`
- `PUT /api/v1/templates/{id}`
- `DELETE /api/v1/templates/{id}`
- `POST /api/v1/templates/{id}/render` (renderizar com variáveis)

---

### ÉPICO 9: Agendamento Automático
**Prioridade:** Sprint 7-8 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 9.1 | Integração Microsoft Graph (calendário) | 🔗 Integração | - | 📋 |
| 9.2 | Buscar disponibilidade do recrutador | 🔧 A desenvolver | - | 📋 |
| 9.3 | LIA envia convite com slots disponíveis | 🔧 A desenvolver | - | 📋 |
| 9.4 | Candidato escolhe horário (via WhatsApp) | 🔧 A desenvolver | - | 📋 |
| 9.5 | LIA cria evento no calendário | 🔧 A desenvolver | - | 📋 |
| 9.6 | LIA envia confirmação para ambos | 🔧 A desenvolver | - | 📋 |
| 9.7 | Exibir entrevistas agendadas no sistema | 🔧 A desenvolver | 🎨 | 📋 |
| 9.8 | Lembrete automático (24h antes) | 🔧 A desenvolver | - | 📋 |

**APIs:**
- `GET /api/v1/calendar/availability` (buscar disponibilidade)
- `POST /api/v1/calendar/events` (criar evento no calendário)
- `GET /api/v1/interviews` (listar entrevistas)
- `POST /api/v1/interviews/schedule` (agendar entrevista)

---

### ÉPICO 10: Notificações
**Prioridade:** Sprint 5-6 | **Status:** A Desenvolver

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 10.1 | Central de notificações (sino) | 🔧 A desenvolver | 🎨 | 📋 |
| 10.2 | Notificação: Triagem concluída | 🔧 A desenvolver | 🎨 | 📋 |
| 10.3 | Notificação: Candidato aprovado Gate | 🔧 A desenvolver | 🎨 | 📋 |
| 10.4 | Notificação: Entrevista agendada | 🔧 A desenvolver | 🎨 | 📋 |
| 10.5 | Badge de contagem não lidas | 🔧 A desenvolver | 🎨 | - |
| 10.6 | Marcar como lida | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `GET /api/v1/notifications`
- `PUT /api/v1/notifications/{id}/read`
- `PUT /api/v1/notifications/read-all`

---

### ÉPICO 12: Integração ATS (Pós-MVP / Paralelo)
**Prioridade:** Paralelo ao MVP | **Status:** Pós-MVP
**Nota:** Pode ser desenvolvido em paralelo sem bloquear o fluxo core.

#### 12.A - Gupy ATS

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 12.1 | Configurar OAuth2 com Gupy | 🔗 Integração | - | 📋 |
| 12.2 | Importar vagas do Gupy | 🔧 A desenvolver | - | 📋 |
| 12.3 | Importar candidatos do Gupy | 🔧 A desenvolver | - | 📋 |
| 12.4 | Exportar score WSI para Gupy (custom field) | 🔧 A desenvolver | - | 📋 |
| 12.5 | Exportar parecer LIA para Gupy (nota) | 🔧 A desenvolver | - | 📋 |
| 12.6 | Sincronizar status de candidato bidirecional | 🔧 A desenvolver | - | 📋 |

**Detalhes Técnicos:**
- **API:** https://api.gupy.io/v2
- **Auth:** OAuth2 com client_credentials
- **Webhooks:** Suporta webhooks para atualizações em tempo real
- **Rate limit:** 100 requests/minuto

#### 12.B - Pandapé ATS

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 12.7 | Configurar API Pandapé | 🔗 Integração | - | 📋 |
| 12.8 | Importar vagas do Pandapé | 🔧 A desenvolver | - | 📋 |
| 12.9 | Importar candidatos do Pandapé | 🔧 A desenvolver | - | 📋 |
| 12.10 | Exportar resultados LIA para Pandapé | 🔧 A desenvolver | - | 📋 |

#### 12.C - Merge.dev (API Unificada ATS + HRIS)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 12.11 | Configurar Merge.dev como hub de integração | 🔗 Integração | - | 📋 |
| 12.12 | Usar Merge para múltiplos ATS e HRIS | 🔧 A desenvolver | - | 📋 |
| 12.13 | Mapeamento unificado de campos | 🔧 A desenvolver | 🎨 | 📋 |

**Detalhes Técnicos:**
- **Vantagem:** Uma única integração para 180+ sistemas ATS e HRIS
- **ATS suportados:** Greenhouse, Lever, Workday, SAP SuccessFactors, etc
- **HRIS suportados:** BambooHR, Rippling, Gusto, etc
- **API:** REST com OpenAPI spec
- **Docs:** https://docs.merge.dev/

**Secrets Necessários:**
- `MERGE_API_KEY`
- `MERGE_ACCOUNT_TOKEN`

#### 12.D - Configuração e UI

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 12.14 | Tela de seleção de ATS para conectar | 🔧 A desenvolver | 🎨 | - |
| 12.15 | Wizard de mapeamento de campos | 🔧 A desenvolver | 🎨 | 📋 |
| 12.16 | Dashboard de sync status | 🔧 A desenvolver | 🎨 | 📋 |
| 12.17 | Logs de sincronização | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `GET /api/v1/ats/providers` (listar ATS disponíveis)
- `POST /api/v1/ats/connect` (conectar ATS)
- `DELETE /api/v1/ats/disconnect` (desconectar)
- `POST /api/v1/ats/sync-vacancies` (sincronizar vagas)
- `POST /api/v1/ats/sync-candidates` (sincronizar candidatos)
- `POST /api/v1/ats/export-results` (exportar resultados)
- `GET /api/v1/ats/field-mapping` (mapeamento de campos)
- `PUT /api/v1/ats/field-mapping` (salvar mapeamento)
- `GET /api/v1/ats/sync-logs` (logs de sincronização)

**Critérios de Aceite:**
- [ ] Conexão OAuth com Gupy funciona
- [ ] Vagas importadas aparecem no sistema
- [ ] Candidatos importados com dados corretos
- [ ] Score WSI exportado como custom field
- [ ] Parecer LIA exportado como nota/comentário
- [ ] Mudança de status sincronizada nos dois sistemas

---

### ÉPICO 13: Configurações da Empresa (Pós-MVP)
**Prioridade:** Pós-MVP | **Status:** Pós-MVP
**Nota:** Configurações avançadas não são bloqueantes para demonstrar valor do MVP.

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 13.1 | CRUD de benefícios da empresa | 🔧 A desenvolver | 🎨 | 📋 |
| 13.2 | Perguntas de triagem customizadas | 🔧 A desenvolver | 🎨 | 📋 |
| 13.3 | Template de pipeline customizável | 🔧 A desenvolver | 🎨 | 📋 |
| 13.4 | Configurações gerais (logo, nome, etc.) | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `GET /api/v1/company/benefits`
- `POST /api/v1/company/benefits`
- `GET /api/v1/company/default-questions`
- `POST /api/v1/company/default-questions`
- `GET /api/v1/company/pipeline-template`
- `PUT /api/v1/company/pipeline-template`

---

### ÉPICO 14: Integrações MVP
**Prioridade:** Sprint 1-2 | **Status:** A Desenvolver
**Nota:** Integrações essenciais para o funcionamento do fluxo core.

#### 14.A - Twilio (WhatsApp Business API)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 14.1 | Configurar Twilio WhatsApp Sandbox/Business | 🔧 A desenvolver | - | 📋 |
| 14.2 | Implementar envio de mensagens via API | 🔧 A desenvolver | - | 📋 |
| 14.3 | Configurar webhook para receber respostas | 🔧 A desenvolver | - | 📋 |
| 14.4 | Tratamento de status de entrega (sent, delivered, read) | 🔧 A desenvolver | - | 📋 |
| 14.5 | Tratamento de opt-out (STOP, PARAR) | 🔧 A desenvolver | - | 📋 |
| 14.6 | Rate limiting e retry logic | 🔧 A desenvolver | - | 📋 |
| 14.7 | Logs de mensagens enviadas/recebidas | 🔧 A desenvolver | 🎨 | 📋 |

**Detalhes Técnicos:**
- **Secrets:** TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER (📋 a configurar)
- **Webhook URL:** `POST /api/v1/whatsapp/webhook`
- **Formato:** Twilio Message API com Content-Type application/x-www-form-urlencoded
- **Templates:** Aprovação prévia no WhatsApp Business necessária para mensagens de template

**APIs:**
- `POST /api/v1/whatsapp/send` (enviar mensagem)
- `POST /api/v1/whatsapp/webhook` (receber callback Twilio)
- `GET /api/v1/whatsapp/status/{messageId}` (status da mensagem)
- `GET /api/v1/whatsapp/logs` (histórico de mensagens)

**Critérios de Aceite:**
- [ ] Mensagem de abordagem enviada com sucesso
- [ ] Respostas do candidato recebidas e processadas
- [ ] Opt-out respeitado automaticamente
- [ ] Logs disponíveis para auditoria

---

#### 14.B - Microsoft Graph (Calendário e Teams)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 14.8 | Configurar OAuth2 com Azure AD | 🔗 Integração | - | 📋 |
| 14.9 | Implementar busca de disponibilidade do recrutador | 🔧 A desenvolver | - | 📋 |
| 14.10 | Criar eventos no calendário do recrutador | 🔧 A desenvolver | - | 📋 |
| 14.11 | Gerar link do Teams para entrevista | 🔧 A desenvolver | - | 📋 |
| 14.12 | Enviar convite para candidato e recrutador | 🔧 A desenvolver | - | 📋 |
| 14.13 | Atualizar/cancelar eventos existentes | 🔧 A desenvolver | - | 📋 |
| 14.14 | Sincronizar status do evento (aceito, recusado) | 🔧 A desenvolver | - | 📋 |

**Detalhes Técnicos:**
- **Secrets:** AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID (📋 a configurar)
- **Scopes necessários:** Calendars.ReadWrite, OnlineMeetings.ReadWrite, User.Read
- **Endpoint base:** https://graph.microsoft.com/v1.0
- **Auth flow:** OAuth 2.0 Authorization Code Flow com refresh token

**APIs:**
- `GET /api/v1/calendar/availability` (slots disponíveis)
- `POST /api/v1/calendar/events` (criar evento com Teams)
- `PUT /api/v1/calendar/events/{id}` (atualizar evento)
- `DELETE /api/v1/calendar/events/{id}` (cancelar evento)
- `GET /api/v1/calendar/events` (listar eventos)

**Critérios de Aceite:**
- [ ] Disponibilidade do recrutador consultada corretamente
- [ ] Evento criado com link do Teams
- [ ] Candidato e recrutador recebem convite
- [ ] Reagendamento/cancelamento funciona

---

#### 14.C - LLMs (Claude e Gemini)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 14.15 | Configurar cliente Anthropic Claude | ✅ Pronto | - | ✅ |
| 14.16 | Configurar cliente Google Gemini | ✅ Pronto | - | ✅ |
| 14.17 | Implementar fallback Claude → Gemini | 🔧 A desenvolver | - | 📋 |
| 14.18 | Prompt engineering para wizard de vaga | 🔧 A desenvolver | - | 📋 |
| 14.19 | Prompt engineering para geração de perguntas WSI | 🔧 A desenvolver | - | 📋 |
| 14.20 | Prompt engineering para avaliação de respostas | 🔧 A desenvolver | - | 📋 |
| 14.21 | Prompt engineering para parecer LIA | 🔧 A desenvolver | - | 📋 |
| 14.22 | Rate limiting e caching de respostas | 🔧 A desenvolver | - | 📋 |
| 14.23 | Logging de tokens consumidos | 🔧 A desenvolver | - | 📋 |

**Detalhes Técnicos:**
- **Claude:** Modelo claude-3-sonnet, max_tokens 4096
- **Gemini:** Modelo gemini-1.5-flash para fallback
- **Temperatura:** 0.3 para avaliação, 0.7 para wizard
- **Retry:** 3 tentativas com backoff exponencial

**APIs:**
- `POST /api/v1/lia/wizard/conversation` (wizard de vaga)
- `POST /api/v1/lia/generate-questions` (gerar perguntas)
- `POST /api/v1/lia/evaluate-response` (avaliar resposta)
- `POST /api/v1/lia/generate-opinion` (gerar parecer)
- `GET /api/v1/lia/usage` (consumo de tokens)

**Critérios de Aceite:**
- [ ] Wizard conversa naturalmente e extrai dados da vaga
- [ ] Perguntas geradas seguem metodologia WSI (7 blocos)
- [ ] Avaliação de respostas gera score 0-10
- [ ] Parecer textual coerente e útil
- [ ] Fallback para Gemini funciona em caso de erro Claude

---

#### 14.D - WorkOS (Autenticação e Gestão de Equipes)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 14.24 | Configurar WorkOS no projeto | 🔗 Integração | - | 📋 |
| 14.25 | Implementar SSO com provedores (Google, Microsoft) | 🔧 A desenvolver | 🎨 | 📋 |
| 14.26 | Implementar MFA (Multi-Factor Authentication) | 🔧 A desenvolver | 🎨 | 📋 |
| 14.27 | Implementar gestão de organizações (multi-tenant) | 🔧 A desenvolver | 🎨 | 📋 |
| 14.28 | Implementar convite de usuários | 🔧 A desenvolver | 🎨 | 📋 |
| 14.29 | Implementar papéis e permissões (Admin, Recruiter) | 🔧 A desenvolver | 🎨 | 📋 |
| 14.30 | SCIM Directory Sync (sincronizar com AD/Okta) | 🔧 A desenvolver | - | 📋 |

**Detalhes Técnicos:**
- **SDK:** @workos-inc/node
- **Features:** SSO, MFA, Directory Sync, Admin Portal
- **Pricing:** Enterprise feature (verificar plano)
- **Alternativa MVP:** JWT simples com bcrypt (já implementado)

**APIs:**
- `POST /api/v1/auth/sso/authorize` (iniciar SSO)
- `GET /api/v1/auth/sso/callback` (callback SSO)
- `POST /api/v1/auth/mfa/enroll` (ativar MFA)
- `POST /api/v1/auth/mfa/verify` (verificar código MFA)
- `GET /api/v1/organizations` (listar organizações)
- `POST /api/v1/organizations/{id}/users` (convidar usuário)

**Critérios de Aceite:**
- [ ] Login via Google/Microsoft funciona
- [ ] MFA opcional para administradores
- [ ] Convite de novos usuários funciona
- [ ] Permissões respeitadas (Admin vs Recruiter)

---

### ÉPICO 15: Integrações Pós-MVP
**Prioridade:** Pós-MVP | **Status:** Planejado
**Nota:** Integrações que agregam valor mas não bloqueiam o MVP.

#### 15.A - Pearch AI (Busca Global de Candidatos)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 15.1 | Configurar API Pearch AI | 🔗 Integração | - | 📋 |
| 15.2 | Implementar busca por skills e localização | 🔧 A desenvolver | 🎨 | 📋 |
| 15.3 | Importar candidatos encontrados para base LIA | 🔧 A desenvolver | - | 📋 |
| 15.4 | Enriquecimento de perfil com dados Pearch | 🔧 A desenvolver | - | 📋 |
| 15.5 | Deduplicação de candidatos existentes | 🔧 A desenvolver | - | 📋 |

**APIs:**
- `POST /api/v1/sourcing/search` (buscar candidatos)
- `POST /api/v1/sourcing/import` (importar candidato)
- `GET /api/v1/sourcing/providers` (provedores disponíveis)

**Critérios de Aceite:**
- [ ] Busca retorna candidatos relevantes por skills
- [ ] Candidatos importados sem duplicatas
- [ ] Perfil enriquecido com dados externos

---

#### 15.B - Deepgram (Transcrição de Entrevistas)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 15.6 | Configurar Deepgram API | 🔗 Integração | - | 📋 |
| 15.7 | Transcrever áudio de entrevista em tempo real | 🔧 A desenvolver | - | 📋 |
| 15.8 | Salvar transcrição vinculada ao candidato | 🔧 A desenvolver | - | 📋 |
| 15.9 | Análise de sentimento na transcrição | 🔧 A desenvolver | - | 📋 |
| 15.10 | Exibir transcrição na interface | 🔧 A desenvolver | 🎨 | - |

**APIs:**
- `POST /api/v1/transcription/start` (iniciar transcrição)
- `GET /api/v1/candidates/{id}/transcriptions` (listar transcrições)

**Critérios de Aceite:**
- [ ] Áudio de entrevista transcrito em tempo real
- [ ] Transcrição salva e vinculada ao candidato
- [ ] Análise de sentimento disponível

---

#### 15.C - OpenMic.ai (Voice Screening)

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 15.11 | Configurar OpenMic.ai | 🔗 Integração | - | 📋 |
| 15.12 | Criar sessão de voice screening | 🔧 A desenvolver | - | 📋 |
| 15.13 | Receber resultados via webhook | 🔧 A desenvolver | - | 📋 |
| 15.14 | Sincronizar score com WSI | 🔧 A desenvolver | - | 📋 |

**APIs:**
- `POST /api/v1/voice-screening/create` (criar sessão)
- `POST /api/v1/voice-screening/webhook` (receber resultado)

**Critérios de Aceite:**
- [ ] Sessão de voice screening criada com sucesso
- [ ] Resultados recebidos via webhook
- [ ] Score integrado ao WSI do candidato

---

#### 15.D - HubSpot (CRM) - PRÉ-INTEGRAÇÃO

> **⚡ Pré-Integração:** Configurar antes do MVP para gestão comercial

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 15.15 | Configurar HubSpot API | 🔗 Pré-integração | - | 📋 |
| 15.16 | Sincronizar empresas clientes | 🔧 A desenvolver | - | 📋 |
| 15.17 | Sincronizar vagas como deals | 🔧 A desenvolver | - | 📋 |
| 15.18 | Dashboard comercial com métricas HubSpot | 🔧 A desenvolver | 🎨 | 📋 |

**APIs:**
- `POST /api/v1/hubspot/sync` (sincronizar dados)
- `GET /api/v1/hubspot/dashboard` (métricas)

**Secrets Necessários:**
- `HUBSPOT_API_KEY`

**Critérios de Aceite:**
- [ ] Empresas sincronizadas entre LIA e HubSpot
- [ ] Vagas refletidas como deals no CRM
- [ ] Dashboard com métricas comerciais

---

#### 15.E - Mailgun (Email Transacional) - PRÉ-INTEGRAÇÃO

> **⚡ Pré-Integração:** Configurar antes do MVP para comunicação com candidatos

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 15.19 | Configurar Mailgun API | 🔗 Pré-integração | - | 📋 |
| 15.20 | Templates de email (convite, feedback, confirmação) | 🔧 A desenvolver | 🎨 | 📋 |
| 15.21 | Envio de emails transacionais | 🔧 A desenvolver | - | 📋 |
| 15.22 | Tracking de abertura e cliques | 🔧 A desenvolver | - | 📋 |

**APIs:**
- `POST /api/v1/email/send` (enviar email)
- `GET /api/v1/email/templates` (listar templates)

**Secrets Necessários:**
- `MAILGUN_API_KEY`
- `MAILGUN_DOMAIN`

**Vantagens Mailgun:**
- Melhor deliverability para Brasil
- Preço competitivo para alto volume
- API simples e bem documentada
- Suporte a templates HTML

**Critérios de Aceite:**
- [ ] Email enviado com sucesso via Mailgun
- [ ] Templates configuráveis por empresa
- [ ] Tracking de abertura/cliques disponível

---

### ÉPICO 11: Kanban e Tabela de Candidatos (MVP)
**Prioridade:** Sprint 1-2 | **Status:** Parcialmente Pronto

#### 11.A - Kanban

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 11.1 | 4 colunas principais (Pipeline, Triagem, Entrevista, Reprovados) | 🔧 A desenvolver | 🎨 | - |
| 11.2 | Badges de sub-status nos cards | 🔧 A desenvolver | 🎨 | - |
| 11.3 | Drag and drop entre colunas | ✅ Pronto | ✅ | - |
| 11.4 | Navegação horizontal com setas | ✅ Pronto | ✅ | - |
| 11.5 | Toggle visão simplificada/completa | 🔧 A desenvolver | 🎨 | - |
| 11.6 | Ícones no card: Nota Geral, Nota Triagem, Nota CV (com modais) | 🔧 A desenvolver | 🎨 | - |
| 11.7 | Botões Aprovar/Reprovar nos cards (Funil + Triagem) | 🔧 A desenvolver | 🎨 | 📋 |
| 11.8 | Link do Teams no card (etapa Entrevista) | 🔧 A desenvolver | 🎨 | - |
| 11.9 | Ações no card: Enviar Triagem, Favoritos | 🔧 A desenvolver | 🎨 | 📋 |
| 11.10 | Ícone LinkedIn e dados externos | 🔧 A desenvolver | 🎨 | - |
| 11.11 | Ícone cérebro (gerar análise LIA) | 🔧 A desenvolver | 🎨 | 📋 |

#### 11.B - Tabela de Candidatos

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 11.12 | Tabela completa com colunas configuráveis | 🔧 A desenvolver | 🎨 | - |
| 11.13 | Mesmos ícones do Kanban (notas, LinkedIn, cérebro) | 🔧 A desenvolver | 🎨 | - |
| 11.14 | Botões Aprovar/Reprovar na coluna inicial | 🔧 A desenvolver | 🎨 | - |
| 11.15 | Highlight visual: candidatos que precisam ação | 🔧 A desenvolver | 🎨 | - |
| 11.16 | Edição de etapa inline (dropdown na coluna Etapa) | 🔧 A desenvolver | 🎨 | 📋 |
| 11.17 | Preview do candidato (modal lateral) | 🔧 A desenvolver | 🎨 | - |
| 11.18 | Filtros avançados | 🔧 A desenvolver | 🎨 | 📋 |
| 11.19 | Colunas como recurso (mostrar/ocultar) | 🔧 A desenvolver | 🎨 | - |

#### 11.C - Perfil do Candidato

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 11.20 | Tab: Perfil Completo | 🔧 A desenvolver | 🎨 | - |
| 11.21 | Tab: Atividades | 🔧 A desenvolver | 🎨 | 📋 |
| 11.22 | Tab: Arquivos | 🔧 A desenvolver | 🎨 | 📋 |
| 11.23 | Tab: Parecer e Análises LIA | 🔧 A desenvolver | 🎨 | 📋 |

#### 11.D - Ações da Vaga

| Card | Descrição | Status | Frontend | Backend |
|------|-----------|--------|----------|---------|
| 11.24 | Pausar vaga (com desdobramentos) | 🔧 A desenvolver | 🎨 | 📋 |
| 11.25 | Menu ações candidato: Triagem WSI, Mover Etapa, Reprovar | 🔧 A desenvolver | 🎨 | 📋 |
| 11.26 | Mover etapa restrito: Funil ↔ Triagem ↔ Reprovados | 🔧 A desenvolver | 🎨 | 📋 |

---

### Componentes e UI MVP

Esta seção detalha os ícones, botões e comportamentos esperados na interface.

#### Ícones do Card de Candidato

| Ícone | Função | Comportamento ao Clicar |
|-------|--------|------------------------|
| 📊 Nota Geral | Score consolidado do candidato | Abre modal com breakdown de notas |
| 📝 Nota Triagem | Score da triagem WSI | Abre modal com detalhes da triagem |
| 📄 Nota CV | Score de análise do currículo | Abre modal com análise do CV |
| 🔗 LinkedIn | Link externo para perfil | Abre LinkedIn em nova aba |
| 🧠 Cérebro | Gerar análise LIA | Dispara análise AI e exibe parecer |
| ⭐ Favoritos | Marcar como favorito | Toggle favorito (salva/remove) |
| 📅 Teams | Link da entrevista | Abre link do Teams (etapa Entrevista) |

#### Botões de Ação Rápida

| Local | Botão | Ação |
|-------|-------|------|
| Card Kanban (Funil) | ✅ Aprovar | Move para Triagem → LIA inicia triagem |
| Card Kanban (Funil) | ❌ Reprovar | Abre modal feedback → Move para Reprovados |
| Card Kanban (Triagem) | ✅ Aprovar | Move para Entrevista → LIA agenda |
| Card Kanban (Triagem) | ❌ Reprovar | Abre modal feedback → Move para Reprovados |
| Tabela (coluna inicial) | ✅/❌ | Mesmos comportamentos do Kanban |
| Menu Ações | Triagem WSI | Inicia triagem individual |
| Menu Ações | Mover Etapa | Dropdown: Funil, Triagem, Reprovados |
| Menu Ações | Reprovar | Abre modal de feedback |

#### Modal de Feedback (Reprovação)

- **Trigger:** Ao clicar em Reprovar
- **Conteúdo:** Textarea com mensagem pré-preenchida pela LIA
- **Opções:** 
  - Editar mensagem manualmente
  - Enviar automático (LIA envia o template padrão)
- **Canais:** WhatsApp (MVP), Email (Pós-MVP)

#### Preview do Candidato (Modal Lateral)

- **Trigger:** Clicar no nome/card do candidato na tabela
- **Tipo:** Slide-in lateral (não tela cheia)
- **Tabs:** Perfil, Atividades, Arquivos, Parecer LIA
- **Ações disponíveis:** Aprovar, Reprovar, Enviar Triagem, Favoritos

#### Tabela de Candidatos - Recursos

- **Filtros:** Etapa, Score, Data, Status
- **Colunas configuráveis:** Mostrar/ocultar via dropdown
- **Highlight:** Candidatos que precisam ação (aguardando_aprovacao) em destaque visual
- **Edição inline:** Dropdown na coluna Etapa para mover rapidamente

#### Ações da Vaga

| Ação | Comportamento |
|------|---------------|
| Pausar Vaga | Pausa triagens ativas, notifica recrutador |
| Iniciar Triagens | Dispara triagem para todos candidatos elegíveis |

---

### Funcionalidades Pendentes de Decisão (Talvez MVP)

| Funcionalidade | Decisão Necessária |
|----------------|-------------------|
| Mudar recrutador da vaga | Avaliar se é crítico para MVP |

---

### Funcionalidades Pós-MVP (UI)

| Funcionalidade | Motivo |
|----------------|--------|
| Visão tela cheia do perfil do candidato | Preview lateral é suficiente para MVP |
| Cancelar vaga (alterar status) | Apenas pausar por agora |
| Prompt LIA expandido/super expandido | Dentro da vaga, simplificar para MVP |

---

### Resumo de Cards por Épico

**MVP Core (Sprints 1-8):**

| Épico | Total Cards | Prontos | A Desenvolver | Integrações |
|-------|-------------|---------|---------------|-------------|
| 1. Autenticação | 4 | 1 | 3 | 0 |
| 2. Wizard Conversacional | 8 | 0 | 8 | 0 |
| 3. Busca e Mapeamento | 6 | 3 | 3 | 0 |
| 4. Geração Perguntas | 5 | 0 | 5 | 0 |
| 5. Triagem WhatsApp | 10 | 0 | 9 | 1 |
| 6. Score WSI | 8 | 0 | 8 | 0 |
| 7. Gates Aprovação | 7 | 0 | 7 | 0 |
| 8. Templates | 7 | 0 | 7 | 0 |
| 9. Agendamento | 8 | 0 | 7 | 1 |
| 10. Notificações | 6 | 0 | 6 | 0 |
| 11. Kanban e Tabela de Candidatos | 26 | 2 | 24 | 0 |
| 14. Integrações MVP | 30 | 2 | 25 | 3 |
| **Subtotal MVP** | **125** | **8** | **112** | **5** |

**Pós-MVP / Paralelo:**

| Épico | Total Cards | Prontos | A Desenvolver | Integrações |
|-------|-------------|---------|---------------|-------------|
| 12. Integração ATS | 17 | 0 | 14 | 3 |
| 13. Configurações | 4 | 0 | 4 | 0 |
| 15. Integrações Pós-MVP | 22 | 0 | 17 | 5 |
| **Subtotal Pós-MVP** | **43** | **0** | **35** | **8** |

**TOTAL GERAL:** 168 cards (8 prontos, 147 a desenvolver, 13 integrações)

---

### Distribuição por Tipo de Trabalho

| Categoria | Cards | % do Total |
|-----------|-------|------------|
| Backend puro | 92 | 55% |
| Frontend + Backend | 50 | 30% |
| Frontend puro | 13 | 8% |
| Integrações | 13 | 8% |

---

### Ordem de Épicos para Jira

**MVP (importar primeiro):** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14

**Pós-MVP (importar depois):** 12, 13, 15

---

## 8. Wireframes e Componentes de Tela

Esta seção documenta visualmente as telas do MVP com wireframes ASCII e especificação detalhada de cada componente, indicando o que está incluído e o que fica fora do escopo MVP.

---

### 8.1 Tabela de Vagas

**Nota:** A tela de "Visão Geral" com cards de métricas NÃO será construída no MVP. Apenas a tabela com tabs de status.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VAGAS                                                      [+ Nova Vaga]   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┬──────────┬───────────┬───────────┬───────────┐                │
│  │  Todas   │  Ativas  │  Pausadas │ Rascunhos │ Arquivadas│  ← Tabs       │
│  │   (24)   │   (12)   │    (3)    │    (5)    │    (4)    │                │
│  └──────────┴──────────┴───────────┴───────────┴───────────┘                │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 Buscar vagas...                      [Filtros ▼]  [Colunas ▼]           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ☐ │ Título           │ Empresa    │ Status  │ Candidatos │ Criada  │ ⋮    │
│ ───┼──────────────────┼────────────┼─────────┼────────────┼─────────┼───── │
│  ☐ │ Dev Senior React │ TechCorp   │ 🟢 Ativa │ 45 / 120   │ 15/01   │ ⋮    │
│  ☑ │ UX Designer Sr   │ DesignCo   │ 🟡 Pausa │ 23 / 80    │ 10/01   │ ⋮ ←──┼── Selecionada
│  ☐ │ Product Manager  │ StartupX   │ 🟢 Ativa │ 67 / 150   │ 08/01   │ ⋮    │
│  ☐ │ Backend Python   │ DataLabs   │ ⚪ Rasc. │ 0 / 0      │ 20/01   │ ⋮    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Mostrando 1-10 de 24                              [◀ 1 2 3 ▶]              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (ao clicar ⋮ ou botão direito)
                         ┌─────────────────────────┐
                         │  👁  Ver detalhes       │
                         │  ✏️  Editar vaga        │
                         │  📋  Duplicar           │
                         ├─────────────────────────┤
                         │  ▶️  Ativar             │  ← Condicional
                         │  ⏸️  Pausar             │  ← Condicional
                         ├─────────────────────────┤
                         │  📦  Arquivar           │
                         │  🗑️  Excluir            │  ← Confirmação
                         └─────────────────────────┘
```

#### Componentes da Tela - Tabela de Vagas

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição | Comportamento |
|------------|-----------|---------------|
| **Tabs de Status** | Todas, Ativas, Pausadas, Rascunhos, Arquivadas | Contador atualiza em tempo real, filtra tabela |
| **Botão Nova Vaga** | CTA principal cyan | Abre wizard conversacional |
| **Campo de Busca** | Busca por título, empresa | Debounce 300ms, busca client-side |
| **Tabela com Colunas** | Título, Empresa, Status, Candidatos, Criada | Colunas ordenáveis por clique no header |
| **Checkbox de Seleção** | Seleção individual e múltipla | Habilita barra de ações em massa |
| **Badge de Status** | 🟢 Ativa, 🟡 Pausada, ⚪ Rascunho, 📦 Arquivada | Cores consistentes |
| **Contador Candidatos** | "45 / 120" (triados / total) | Clicável, abre Kanban da vaga |
| **Menu de Ações (⋮)** | Dropdown com ações contextuais | Ações variam por status |
| **Paginação** | Navegação entre páginas | 10 itens por página padrão |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Dashboard de métricas (visão geral) | Complexidade, priorizar fluxo core |
| Filtros avançados (dropdown) | Simplificar para busca textual |
| Configurador de colunas | Colunas fixas no MVP |
| Drag-and-drop de linhas | Não necessário |
| Export CSV/Excel | Pós-MVP |
| Tags/Labels customizadas | Pós-MVP |

**Estados da Linha:**
- `default`: Fundo branco
- `hover`: Fundo gray-50
- `selected`: Fundo cyan-50, checkbox marcado
- `disabled`: Opacity 50% (vagas arquivadas)

---

### 8.2 Kanban de Candidatos (Dentro da Vaga)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Voltar    Dev Senior React @ TechCorp                    [⚙️] [⋮ Ações] │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┬─────────┬─────────┬───────────┐                                │
│  │ Kanban  │ Tabela  │ Config  │ Analytics │  ← Tabs (Analytics = Pós-MVP) │
│  └─────────┴─────────┴─────────┴───────────┘                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 Buscar candidato...                    [Filtros ▼]                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ FUNIL (45) ──────┐  ┌─ TRIAGEM (12) ────┐  ┌─ ENTREVISTA (8) ─┐        │
│  │                   │  │                   │  │                  │        │
│  │ ┌───────────────┐ │  │ ┌───────────────┐ │  │ ┌──────────────┐ │        │
│  │ │ 👤 João Silva │ │  │ │ 👤 Maria Lima │ │  │ │ 👤 Pedro Ro. │ │        │
│  │ │ ⭐ 85 │ 📝│🔗│🧠│ │  │ │ ⭐ 92 │📝│🔗│🧠│ │  │ │ ⭐ 88 │ 📅  │ │        │
│  │ │ Backend • 5a   │ │  │ │ Full • 7a     │ │  │ │ Ter 14:00   │ │        │
│  │ └───────────────┘ │  │ │ ✅ WSI: 78    │ │  │ └──────────────┘ │        │
│  │ ┌───────────────┐ │  │ └───────────────┘ │  │                  │        │
│  │ │ 👤 Ana Costa  │ │  │ ┌───────────────┐ │  └──────────────────┘        │
│  │ │ ⭐ 78 │ 📝│🔗│  │ │  │ │ 👤 Carlos M. │ │                              │
│  │ │ Frontend • 3a  │ │  │ │ ⭐ 71 │📝│🔗│🧠│ │  ┌─ REPROVADOS (15)─┐        │
│  │ └───────────────┘ │  │ │ DevOps • 4a   │ │  │                  │        │
│  │        ...        │  │ │ ⏳ WSI: pend. │ │  │ ┌──────────────┐ │        │
│  └───────────────────┘  │ └───────────────┘ │  │ │ 👤 Lucia F.  │ │        │
│                         │        ...        │  │ │ ❌ Reprov.   │ │        │
│                         └───────────────────┘  │ │ Motivo: XYZ  │ │        │
│                                                │ └──────────────┘ │        │
│  ◀ ════════════════════════════════════ ▶     └──────────────────┘        │
│              Scroll horizontal entre colunas                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Card do Candidato (Expandido)

```
┌─────────────────────────────────┐
│  👤 João Silva da Costa         │  ← Nome (truncado se longo)
│  ─────────────────────────────  │
│  ⭐ 85  │ 📝 │ 🔗 │ 🧠 │ ❤️     │  ← Score + Ícones de ação
│  ─────────────────────────────  │
│  Backend Developer              │  ← Cargo atual
│  TechCorp • 5 anos exp.         │  ← Empresa + Experiência
│  ─────────────────────────────  │
│  📍 São Paulo, SP               │  ← Localização
│  💰 R$ 15-18k                   │  ← Pretensão (se disponível)
│  ─────────────────────────────  │
│  ✅ WSI: 78/100                 │  ← Score WSI (se triado)
│  📅 Última ativ: 2h atrás       │  ← Última interação
└─────────────────────────────────┘
         │
         ▼ (ao clicar no card)
┌─────────────────────────────────┐
│      AÇÕES DO CANDIDATO         │
├─────────────────────────────────┤
│  👁  Ver perfil completo        │
│  📋  Ver parecer LIA            │
├─────────────────────────────────┤
│  ➡️  Mover para etapa...        │  ← Abre submenu
│  📱  Enviar triagem WSI         │  ← Só se não triado
│  📅  Agendar entrevista         │  ← Só se triado
├─────────────────────────────────┤
│  ✅  Aprovar                    │  ← Verde
│  ❌  Reprovar                   │  ← Vermelho, abre modal
├─────────────────────────────────┤
│  📝  Adicionar nota             │
│  ⭐  Favoritar                  │
└─────────────────────────────────┘
```

#### Ícones do Card (Legenda)

| Ícone | Nome | Comportamento | Tooltip |
|-------|------|---------------|---------|
| 📝 | Notas | Clique abre modal de notas | "3 notas" |
| 🔗 | LinkedIn | Abre perfil em nova aba | "Ver LinkedIn" |
| 🧠 | Parecer LIA | Abre parecer no preview | "Ver análise LIA" |
| ❤️ | Favorito | Toggle on/off | "Favoritar" |
| 📅 | Entrevista | Mostra data/hora agendada | "Ter 15/01 14:00" |
| ⏳ | WSI Pendente | Aguardando resposta | "Triagem em andamento" |
| ✅ | WSI Completo | Score disponível | "WSI: 78/100" |

#### Componentes do Kanban

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **4 Colunas Fixas** | Funil, Triagem, Entrevista, Reprovados |
| **Cards de Candidato** | Nome, score, ícones, cargo, experiência |
| **Drag-and-drop** | Entre colunas permitidas (ver regras) |
| **Scroll Horizontal** | Navegação entre colunas |
| **Contador por Coluna** | "(45)" ao lado do título |
| **Menu de Ações** | Click no card abre menu contextual |
| **Busca de Candidato** | Por nome, cargo |
| **Ícones de Ação Rápida** | Notas, LinkedIn, LIA, Favorito |
| **Badge WSI** | Score ou status pendente |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Sub-colunas (sub-status) | Complexidade, usar apenas 4 colunas |
| Filtros avançados | Simplificar para busca |
| Ordenação dentro da coluna | Ordenação fixa por score |
| Cores customizadas | Cores fixas por etapa |
| Tab Analytics | Pós-MVP |
| Bulk selection no Kanban | Apenas na tabela |

**Regras de Movimentação:**

| De | Para | Permitido | Observação |
|----|------|-----------|------------|
| Funil | Triagem | ✅ | Requer Gate 1 (aprovar mapeados) |
| Triagem | Entrevista | ✅ | Requer Gate 2 (aprovar triados) |
| Triagem | Reprovados | ✅ | Abre modal de feedback |
| Funil | Reprovados | ✅ | Abre modal de feedback |
| Entrevista | Reprovados | ✅ | Abre modal de feedback |
| Reprovados | Qualquer | ❌ | Candidato reprovado é final |
| Entrevista | Funil | ❌ | Não pode voltar |

---

### 8.3 Preview Lateral do Candidato

```
                                              ┌─────────────────────────────────┐
                                              │  ✕                              │
                                              ├─────────────────────────────────┤
                                              │      👤                         │
                                              │   João Silva                    │
                                              │   Backend Developer             │
                                              │   ⭐ 85 │ 🔗 │ ❤️               │
                                              ├─────────────────────────────────┤
                                              │ ┌───────┬───────┬───────┬─────┐ │
                                              │ │Perfil │Ativid.│Arquiv.│ LIA │ │
                                              │ └───────┴───────┴───────┴─────┘ │
                                              ├─────────────────────────────────┤
    Kanban (background blur/dim)              │                                 │
    ┌─────────────────────────────┐           │  📧 joao@email.com              │
    │                             │           │  📱 (11) 99999-9999             │
    │    Cards do Kanban          │◀─────────▶│  📍 São Paulo, SP               │
    │    visíveis mas             │           │  💼 5 anos de experiência       │
    │    não interativos          │           │  💰 R$ 15-18k                   │
    │                             │           │                                 │
    └─────────────────────────────┘           ├─────────────────────────────────┤
                                              │  SKILLS                         │
                                              │  ┌─────┐ ┌────┐ ┌──────┐       │
                                              │  │React│ │Node│ │Python│       │
                                              │  └─────┘ └────┘ └──────┘       │
                                              ├─────────────────────────────────┤
                                              │  SCORE WSI                      │
                                              │  ████████████░░░░ 78/100       │
                                              │                                 │
                                              │  Técnico: 82   Comportam.: 75  │
                                              │  Cultural: 78  Comunicação: 80 │
                                              ├─────────────────────────────────┤
                                              │  [✅ Aprovar]  [❌ Reprovar]   │
                                              └─────────────────────────────────┘
```

#### Tabs do Preview

**Tab Perfil:**
- Dados de contato (email, telefone)
- Localização
- Experiência resumida
- Skills/Tags
- Score WSI (se disponível)
- Links (LinkedIn, Portfolio)

**Tab Atividades:**
- Timeline de interações
- Mensagens enviadas/recebidas
- Mudanças de etapa
- Notas adicionadas

**Tab Arquivos:**
- CV anexado
- Documentos enviados
- Transcrições (Pós-MVP)

**Tab LIA (Parecer):**
- Parecer gerado pela LIA
- Pontos fortes
- Pontos de atenção
- Recomendação
- Perguntas sugeridas para entrevista

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **Header com foto/avatar** | Nome, cargo, score |
| **4 Tabs** | Perfil, Atividades, Arquivos, LIA |
| **Dados de contato** | Email, telefone, localização |
| **Skills como tags** | Badges clicáveis |
| **Score WSI visual** | Barra de progresso + breakdown |
| **Botões de ação** | Aprovar/Reprovar fixos no footer |
| **Fechar (✕)** | Volta ao Kanban |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Edição inline de dados | Apenas visualização |
| Upload de documentos | Apenas visualizar existentes |
| Comparação lado-a-lado | Pós-MVP |
| Histórico completo de empresa | Simplificar |

---

### 8.4 Modal de Feedback (Reprovação)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                            ✕    │
│                     Reprovar Candidato                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   👤 João Silva - Backend Developer                             │
│   Vaga: Dev Senior React @ TechCorp                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Motivo da Reprovação *                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ▼ Selecione o motivo                                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Opções:                                                       │
│   • Não atende requisitos técnicos                              │
│   • Pretensão salarial incompatível                             │
│   • Disponibilidade inadequada                                  │
│   • Perfil não alinha com cultura                               │
│   • Candidato declinou                                          │
│   • Outro (especificar)                                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Mensagem de Feedback                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ○ Usar mensagem automática da LIA                       │   │
│   │ ● Personalizar mensagem                                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Olá João,                                               │   │
│   │                                                         │   │
│   │ Agradecemos seu interesse na vaga de Dev Senior React   │   │
│   │ na TechCorp. Após análise cuidadosa do seu perfil,      │   │
│   │ decidimos seguir com outros candidatos cujas            │   │
│   │ experiências estão mais alinhadas com o momento atual   │   │
│   │ da posição.                                             │   │
│   │                                                         │   │
│   │ Desejamos sucesso em sua jornada profissional!          │   │
│   │                                                         │   │
│   │ Atenciosamente,                                         │   │
│   │ Equipe TechCorp                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Canal de Envio                                                │
│   ┌───────────┐  ┌───────────┐                                  │
│   │ 📱 WhatsApp│  │ 📧 Email │  ← Seleção única                │
│   │     ✓     │  │          │                                  │
│   └───────────┘  └───────────┘                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ☐ Enviar feedback automaticamente                             │
│   ☑ Manter candidato no banco para futuras vagas                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│           [Cancelar]              [Confirmar Reprovação]        │
│                                           ↑ vermelho            │
└─────────────────────────────────────────────────────────────────┘
```

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **Header com candidato/vaga** | Contexto claro |
| **Dropdown de motivo** | Lista predefinida + "Outro" |
| **Toggle mensagem** | Automática LIA vs Personalizada |
| **Textarea editável** | Pré-preenchido pela LIA |
| **Seletor de canal** | WhatsApp ou Email |
| **Checkbox banco futuro** | Manter para outras vagas |
| **Botões Cancelar/Confirmar** | Confirmar em vermelho |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Preview do template renderizado | Complexidade |
| Múltiplos candidatos (bulk) | Apenas individual no modal |
| Agendamento de envio | Envio imediato |
| Histórico de feedbacks anteriores | Pós-MVP |

---

### 8.5 Modal de Ações em Massa (Bulk Actions)

```
┌─────────────────────────────────────────────────────────────────┐
│  TABELA DE CANDIDATOS                                           │
├─────────────────────────────────────────────────────────────────┤
│  ☑ │ Nome          │ Score │ Etapa    │ Status    │            │
│  ☑ │ João Silva    │ 85    │ Funil    │ Mapeado   │            │
│  ☑ │ Maria Lima    │ 92    │ Funil    │ Mapeado   │            │
│  ☐ │ Pedro Santos  │ 78    │ Triagem  │ Triado    │            │
│  ☑ │ Ana Costa     │ 81    │ Funil    │ Mapeado   │            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 3 candidatos selecionados                               │    │
│  │                                                         │    │
│  │ [Mover Etapa ▼] [Enviar Triagem] [Reprovar] [Cancelar] │    │
│  └─────────────────────────────────────────────────────────┘    │
│              ↑ Barra de ações em massa (sticky bottom)          │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼ (ao clicar "Reprovar")
┌─────────────────────────────────────────────────────────────────┐
│                    Reprovar 3 Candidatos                   ✕    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Candidatos selecionados:                                      │
│   • João Silva - Backend Developer                              │
│   • Maria Lima - Full Stack                                     │
│   • Ana Costa - Frontend Developer                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│   Motivo (aplicado a todos) *                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ▼ Selecione o motivo                                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Mensagem de Feedback                                          │
│   ○ Usar mensagem automática da LIA (personalizada por cand.)   │
│   ● Usar mensagem padrão para todos                             │
│                                                                 │
│   Canal: 📱 WhatsApp                                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│           [Cancelar]              [Reprovar 3 Candidatos]       │
└─────────────────────────────────────────────────────────────────┘
```

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **Checkbox de seleção múltipla** | Na tabela de candidatos |
| **Barra sticky de ações** | Aparece ao selecionar 1+ |
| **Contador de selecionados** | "3 candidatos selecionados" |
| **Botões de ação em massa** | Mover, Enviar Triagem, Reprovar |
| **Modal de confirmação bulk** | Lista candidatos afetados |
| **Motivo único para todos** | Simplificação |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Mensagem individual por candidato | Complexidade |
| Progress bar de envio | Simplificar |
| Undo/desfazer ação | Pós-MVP |

---

### 8.6 Wizard Conversacional (Criar Vaga)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Voltar                    Nova Vaga                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  🤖 LIA                                                            │   │
│  │  ─────────────────────────────────────────────────────────────     │   │
│  │  Olá! Vou ajudar você a criar uma nova vaga. Para começar,         │   │
│  │  me conte: qual é o título da posição que você está buscando?      │   │
│  │                                                                     │   │
│  │  💡 Dica: Seja específico, ex: "Desenvolvedor Backend Senior       │   │
│  │      com foco em Python e AWS"                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  👤 Você                                                           │   │
│  │  ─────────────────────────────────────────────────────────────     │   │
│  │  Preciso de um Desenvolvedor Full Stack com experiência em         │   │
│  │  React e Node.js, preferencialmente senior.                        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  🤖 LIA                                                            │   │
│  │  ─────────────────────────────────────────────────────────────     │   │
│  │  Ótimo! Desenvolvedor Full Stack Senior com React e Node.js.       │   │
│  │                                                                     │   │
│  │  📊 Baseado em vagas similares no mercado:                         │   │
│  │  • Salário médio: R$ 15.000 - R$ 22.000                           │   │
│  │  • Tempo médio de preenchimento: 32 dias                          │   │
│  │  • Skills mais pedidas: TypeScript, AWS, Docker                    │   │
│  │                                                                     │   │
│  │  Qual é a faixa salarial para esta posição?                        │   │
│  │                                                                     │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │   │
│  │  │ R$ 15-18k   │ │ R$ 18-22k   │ │ Outro valor │  ← Sugestões   │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘               │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Digite sua mensagem...                                         📎 ▶ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ RESUMO DA VAGA ──────────────────────────────────────────────────┐     │
│  │ Título: Dev Full Stack Senior          Status: 🔄 Em construção   │     │
│  │ Salário: -                             Local: -                   │     │
│  │ Skills: React, Node.js                 Modelo: -                  │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  [Pular para formulário]                              [Salvar rascunho]    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **Chat conversacional** | Mensagens LIA ↔ Recrutador |
| **Sugestões clicáveis** | Botões de resposta rápida |
| **Insights de mercado** | Salário médio, tempo, skills |
| **Resumo lateral/inferior** | Preview da vaga em construção |
| **Campo de input** | Texto livre + anexo |
| **Botão salvar rascunho** | Salva progresso parcial |
| **Skip para formulário** | Preencher manualmente |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Upload de JD para parsing | Complexidade |
| Voz/áudio | Texto apenas |
| Templates de vaga anteriores | Pós-MVP |
| Comparação com vagas da empresa | Pós-MVP |

---

### 8.7 Tela de Triagem WhatsApp (Monitoramento)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Voltar    Triagens em Andamento - Dev Senior React                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ AGUARDANDO RESPOSTA (5) ─────────────────────────────────────────┐     │
│  │                                                                   │     │
│  │  👤 João Silva    📱 Enviado há 2h    ⏳ Aguardando               │     │
│  │  👤 Maria Lima    📱 Enviado há 4h    ⏳ Aguardando               │     │
│  │  👤 Pedro Santos  📱 Enviado há 1d    ⚠️ Sem resposta             │     │
│  │                                                                   │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌─ EM ANDAMENTO (3) ────────────────────────────────────────────────┐     │
│  │                                                                   │     │
│  │  👤 Ana Costa     💬 Respondendo     Pergunta 4/7   ████████░░   │     │
│  │  👤 Carlos M.     💬 Respondendo     Pergunta 2/7   ███░░░░░░░   │     │
│  │  👤 Lucia F.      💬 Respondendo     Pergunta 6/7   █████████░   │     │
│  │                                                                   │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌─ CONCLUÍDAS (12) ─────────────────────────────────────────────────┐     │
│  │                                                                   │     │
│  │  👤 Roberto N.    ✅ Concluído    Score: 85    [Ver Conversa]    │     │
│  │  👤 Fernanda S.   ✅ Concluído    Score: 72    [Ver Conversa]    │     │
│  │  👤 Diego R.      ✅ Concluído    Score: 91    [Ver Conversa]    │     │
│  │                                                                   │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌─ DESISTÊNCIAS (2) ────────────────────────────────────────────────┐     │
│  │                                                                   │     │
│  │  👤 Marcos T.     ❌ Desistiu     Motivo: "Aceitei outra oferta" │     │
│  │  👤 Julia C.      ❌ Timeout      Sem resposta após 3 tentativas │     │
│  │                                                                   │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**✅ INCLUÍDO NO MVP:**

| Componente | Descrição |
|------------|-----------|
| **Agrupamento por status** | Aguardando, Em andamento, Concluídas, Desistências |
| **Progress bar por candidato** | Pergunta X de Y |
| **Tempo desde envio** | "Enviado há 2h" |
| **Alerta sem resposta** | Destaque visual após 24h |
| **Link ver conversa** | Abre histórico do chat |
| **Score final** | Exibido após conclusão |

**❌ FORA DO MVP:**

| Componente | Motivo |
|------------|--------|
| Reenviar mensagem manual | LIA gerencia automaticamente |
| Editar perguntas mid-flow | Perguntas fixas após início |
| Análise em tempo real | Apenas após conclusão |

---

### Resumo de Componentes UI

| Tela | Componentes MVP | Componentes Pós-MVP |
|------|-----------------|---------------------|
| Tabela de Vagas | 9 | 6 |
| Kanban Candidatos | 10 | 6 |
| Card do Candidato | 7 ícones + menu | - |
| Preview Lateral | 4 tabs + ações | 4 |
| Modal Feedback | 7 | 4 |
| Bulk Actions | 6 | 3 |
| Wizard Conversacional | 7 | 4 |
| Monitoramento Triagem | 6 | 3 |

---

## 9. Checklist de Entrega MVP

### Recrutador consegue:
- [ ] Fazer login
- [ ] Criar vaga via wizard conversacional
- [ ] Buscar candidatos (base + global)
- [ ] Adicionar candidatos à vaga
- [ ] Aprovar candidatos mapeados
- [ ] Ver score WSI após triagem
- [ ] Aprovar/reprovar candidatos triados
- [ ] Ver entrevista agendada no calendário
- [ ] Receber notificações

### LIA consegue:
- [ ] Gerar perguntas de triagem
- [ ] Contatar candidato via WhatsApp
- [ ] Conduzir triagem conversacional
- [ ] Calcular score WSI
- [ ] Gerar parecer textual
- [ ] Agendar entrevista automaticamente
- [ ] Enviar feedback para reprovados

### Sistema consegue:
- [ ] Sincronizar com ATS
- [ ] Enviar notificações
- [ ] Salvar histórico de conversas
- [ ] Registrar logs de ações

---

**Documento gerado para discussão com time de desenvolvimento.**  
**Plataforma LIA - WeDoTalent**
