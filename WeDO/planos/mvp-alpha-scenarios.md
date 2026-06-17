# PLATAFORMA LIA — CENÁRIO MVP ALPHA 1

**Versão:** 2.9
**Data:** 19/fev/2026
**Referências:** `docs/lia-mvp-cards-jira.md`, `docs/configuracoes-admin-cards-jira.md`, `docs/pipeline-transition-cards-jira.md` (PIP-001~018), `docs/lia-ai-architecture-cards-jira.md` (AGT/SRV/AUT/INF/TRV/LRN), `docs/lia-mvp-cards-jira-v2.md` (CFG-001~012)

---

> ### 📋 CHANGELOG — O QUE FOI ADICIONADO NESTE DOCUMENTO
>
> **Conteúdo original:** Seções 1 a 2.7 vêm do documento base `mvp-alpha-scenarios.md`.
>
> **Enriquecimentos adicionados (v2.4–v2.8):**
> - Nas tabelas das etapas (2.2.1): anotações **🆕 IA:** nas colunas Obs vinculando cards de produto a cards IA — **MARCADAS COM 🆕**
> - Abaixo de cada tabela de etapa: blocos **🆕 Pré-requisitos IA:** listando dependências IA — **MARCADOS COM 🆕**
> - Avisos **🆕 ⚠️** redirecionando para gaps em 2.8.7 — **MARCADOS COM 🆕**
> - Seção 2.2.2 (Mapa de Agentes): atualizada com Ag.10 e roles — **MARCADA COM 🆕**
> - Seção 2.2.3 (Cards a Criar): centralizada em 2.8.7 — **MARCADA COM 🆕**
> - **Seção 2.8 inteira é 100% NOVA** — inventário completo + roadmap por sprint
>
> **v2.8 — Correções de consistência:**
> - AGT-005 (JobIntakeAgent/Ag.1) removido do Alpha 1 — wizard conversacional adiado para Alpha 2+
> - Etapas 2 e 3 atualizadas: removidas referências a Ag.1, mantidos Ag.8 (IntegradorATS) e Ag.4 (EntrevistadorWSI)
> - WIZ-012 atualizado: "UI do estágio no wizard" → "UI de configuração de perguntas WSI no modal de edição"
> - Seção 2.8.2 duplicada (cards de produto) removida — referência cruzada para seção 2.2.1
> - Totais recalculados: Alpha 1 = 62 cards IA (477 pts) + 10 PIP (62 pts) + ~20 produto (~121 pts) = ~92 cards / ~660 pts
> - Sprint 2 corrigido: 38 cards / 327 pts (sem AGT-005)
>
> **Regra visual:** Todo conteúdo novo antes da seção 2.8 está prefixado com **🆕** para fácil identificação.

---

## ÍNDICE

1. [Visão Geral do MVP](#1-visão-geral-do-mvp)
2. [Cenário Alpha 1 — Teste Interno com Consultores](#2-cenário-alpha-1--teste-interno-com-consultores)
   - 2.1 [Premissas do Cenário](#21-premissas-do-cenário)
   - 2.2 [Fluxo Alpha 1 — Passo a Passo (v2)](#22-fluxo-alpha-1--passo-a-passo-v2)
     - 2.2.1 [Detalhamento por Etapa — Bloqueantes, Alertas e Cards](#221-detalhamento-por-etapa--bloqueantes-alertas-e-cards)
     - 2.2.2 [Mapa de Agentes IA por Etapa do Alpha 1](#222-mapa-de-agentes-ia-por-etapa-do-alpha-1)
     - 2.2.3 [Cards a Criar → centralizado em 2.8.7](#223-cards-a-criar-sem-card-jira-existente)
     - 2.2.4 [Contagem de Cards por Etapa](#224-contagem-de-cards-por-etapa)
     - 2.2.5 [🆕 Pré-requisitos IA por Semana → movido para 2.8.2](#225-pré-requisitos-ia-por-semana)
     - 2.2.6 [Resumo de Alertas por Canal](#226-resumo-de-alertas-por-canal)
   - 2.4 [Restrições Conhecidas no Alpha 1](#24-restrições-conhecidas-no-alpha-1)
   - 2.5 [Estratégia de Contato — Diagrama de Decisão](#25-estratégia-de-contato--diagrama-de-decisão)
   - 2.6 [Fluxo Especial: Candidato Inscrito via Web](#26-fluxo-especial-candidato-inscrito-via-web)
   - 2.7 [Critérios de Sucesso do Alpha 1](#27-critérios-de-sucesso-do-alpha-1)
   - 2.8 [⚡ CARDS A IMPLEMENTAR — Inventário Completo para MVP Alpha 1 e Fases Seguintes](#28--cards-a-implementar--inventário-completo-para-mvp-alpha-1-e-fases-seguintes)
     - 2.8.1 [🔗 MAPA DE DEPENDÊNCIAS](#281--mapa-de-dependências--o-que-vem-antes-do-quê)
     - 2.8.2 [🗺️ ROADMAP POR SEMANA](#282--roadmap-por-semana--o-que-trabalhar-em-cada-semana)
     - 2.8.7 [Cards a Criar — Gaps Identificados](#287-cards-a-criar--gaps-identificados)
3. [Integrações MVP](#3-integrações-mvp)
4. [Itens Temporariamente Excluídos do MVP](#4-itens-temporariamente-excluídos-do-mvp)

---

## 1. VISÃO GERAL DO MVP

### Objetivo
Permitir que o recrutador conduza um processo seletivo completo assistido pela LIA, desde a edição da vaga (importada do ATS) até o agendamento da entrevista.

### O que o recrutador precisa conseguir fazer:
- Fazer login
- Editar vaga importada do ATS (definir requisitos, benefícios, faixa salarial, modelo de trabalho)
- Configurar roteiro de triagem WSI a partir do JD (customizado ou gerado) via modal (Preview Vaga → Roteiro de Triagem → Editar)
- Buscar candidatos na base (via Pearch/Apify) e adicionar à vaga (email obrigatório)
- Aprovar candidatos mapeados para triagem (Gate 1) — candidatos inscritos via web fazem bypass
- Acompanhar a LIA contatando candidatos via email (primário) e/ou WhatsApp (secundário)
- Acompanhar a LIA fazendo triagem WSI (via chat web ou WhatsApp)
- Aprovar/reprovar candidatos triados com base no score WSI (Gate 2)
- Ter a LIA agendando entrevistas (aprovados) e enviando feedback (reprovados)

### Escopo MVP
O MVP termina no **agendamento da entrevista pela LIA**. Etapas posteriores (entrevista, proposta, contratação) serão gerenciadas no ATS integrado.

> **Nota:** O Wizard Conversacional (Épico 2) foi adiado para pós-MVP. No Alpha 1, vagas são importadas do ATS (não criadas na WeDo) e editadas pelo consultor. O roteiro de triagem WSI é configurado a partir do JD via modal (Preview Vaga → Roteiro de Triagem → Editar).

### Fontes de Candidatos

| Fonte | Descrição | Quem Adiciona |
|-------|-----------|---------------|
| **Base Interna (ATS)** | Candidatos importados do ATS integrado via Merge — constituem a base interna da plataforma | Sistema importa automaticamente; recrutador busca e adiciona à vaga |
| **Busca Global** | LinkedIn, Pearch, outras fontes externas | LIA busca e sugere |
| **Inscrição via Link** | Candidatos via link publicado em redes sociais ou página de carreiras/website | Candidato se auto-cadastra pela página web |

### Portões de Aprovação (Gates)

| Gate | Momento | Ação do Recrutador | Se APROVADO | Se REPROVADO |
|------|---------|-------------------|-------------|--------------|
| **Gate 1** | Após mapeamento | Aprovar candidatos para triagem (inscritos via web fazem bypass) | LIA inicia contato via email e/ou WhatsApp | LIA envia feedback → Coluna "Reprovados" |
| **Gate 2** | Após triagem WSI | Aprovar/Reprovar com base no score | LIA agenda entrevista | LIA envia feedback → Coluna "Reprovados" |

---

## 2. CENÁRIO ALPHA 1 — TESTE INTERNO COM CONSULTORES

### 2.1 Premissas do Cenário

O Alpha 1 é o primeiro cenário de teste real com o time interno de consultores de recrutamento da WeDo Talent.

**Premissas assumidas como prontas:**
1. **ATS integrado** — WeDo Talent já conectada ao ATS via Merge (INT-005 funcional)
2. **Vagas importadas do ATS** — Vagas já sincronizadas do ATS para a plataforma LIA
3. **Login funcional** — Consultores já conseguem fazer login com email/senha
4. **Adicionar candidatos à vaga** — Consultores conseguem adicionar candidatos na vaga com email

**Quem testa:** Time interno de consultores de recrutamento da WeDo Talent
**Objetivo:** Validar o fluxo core de recrutamento antes de abrir para clientes

### 2.2 Fluxo Alpha 1 — Passo a Passo (v2)

> **Legenda:** Cada etapa inclui bloqueantes, alertas (Teams/Email/Bell) e cards Jira vinculados.
> Formato de cards: `CÓDIGO Título (Épico, Sprint)`

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          FLUXO ALPHA 1 — TESTE INTERNO WEDOTALENT (v2)                         │
│                                                                                                │
│  PREMISSAS: ATS integrado | Vagas importadas | Login email/senha                              │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                                              ┌──────────────────┐
    │    CONSULTOR      │                                              │       LIA         │
    └────────┬─────────┘                                              └────────┬─────────┘
             │                                                                  │
             │  1. LOGIN                                                         │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Login com email/senha                                         │
             │  • Acessa dashboard de vagas                                     │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  2. EDITAR VAGA (importada do ATS)                                │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Acessa página de vagas WeDo, seleciona vaga existente        │
             │  • NÃO cria vaga na WeDo — edita dados importados              │
             │  • Define requisitos, benefícios, faixa salarial, modelo        │
             │  • 🤖 Ag.8 IntegradorATS (sync dados do ATS)                     │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  3. CONFIGURAR ROTEIRO WSI                                        │
             │  ──────────────────────────────────────────────────────────────► │
             │  • A partir do JD da vaga (importado do ATS ou gerado no modal) │
             │  • Via modal: Preview Vaga → Revisar/Ajustar JD                 │
             │  • Modal: Roteiro de Triagem → Criar (completo/compacto)        │
             │  •   ou Editar roteiro existente                                │
             │  • Selecionar/ajustar perguntas de triagem com ajuda da LIA     │
             │  • 🤖 JD Generator Service (LLM) gera/ajusta JD                 │
             │  • 🤖 Ag.4 EntrevistadorWSI (gera perguntas WSI)                │
             │                                                                  │
             │                              3B. GERAR PERGUNTAS WSI             │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • LIA analisa JD/requisitos → gera perguntas WSI (Blocos 2-5)  │
             │  • Consultor edita/ajusta via modal                              │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  4. BUSCAR CANDIDATOS (Funil de Talentos)                          │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Busca no Funil de Talentos: banco interno + Pearch           │
             │  • Gera prompt no campo de busca do Funil de Talentos           │
             │  • Metodologias de busca:                                        │
             │    - Elasticsearch + PGVector + WRF (Weighted Rank Fusion)      │
             │    - ES Score Drop Analyzer + PGV Gap Analyzer (pré-WRF)        │
             │    - WRF Dynamic K (ajuste por nível de qualificação)           │
             │    - LLM Job Classification para otimização de K values         │
             │  • Modos de busca:                                              │
             │    - IA Natural (linguagem livre)                               │
             │    - Boolean (operadores AND/OR/NOT)                            │
             │    - Perfil Similar (a partir de candidato referência)          │
             │    - Job Description (busca por JD colada/importada)            │
             │    - Archetypes (perfis pré-configurados por área)              │
             │  • Filtros Avançados (MAP-003):                                 │
             │    - Cargo: títulos, senioridade, tempo no cargo                │
             │    - Empresa: nome, indústria, porte, funding, HQ              │
             │    - Skills: técnicas + nível de expertise                      │
             │    - Educação: universidade, grau, área, ano graduação          │
             │    - Idiomas: idioma + nível proficiência                       │
             │    - Geral: experiência mín/máx, ocultar perfis já vistos      │
             │    - Perfil: decision maker, top universities, startup          │
             │    - Pearch: fast/pro, exigir email/telefone, open to work     │
             │  • Tabela de candidatos: 10 por vez, botão "Carregar +10"       │
             │  • Preview do candidato inline na tabela (4 tabs):               │
             │    - Perfil Completo: dados, experiência, skills, educação     │
             │    - Atividades: timeline (triagens WSI, emails, entrevistas,  │
             │      candidaturas, testes, ofertas + eventos do ATS)           │
             │    - Arquivos: CVs e documentos anexados                       │
             │    - Pareceres e Análises: análises LIA salvas + opiniões      │
             │  • Like/Dislike feedback por candidato (otimiza busca)           │
             │  • Prompt expandido da LIA (lado esquerdo da tabela):           │
             │    - Análise de perfil, comparação, ranking, skills             │
             │    - 🤖 Ag.2 SourcingAgent (busca/perfis similares)             │
             │    - 🤖 Ag.3 TriagemCurricular (triagem/screening)              │
             │    - 🤖 AvaliadorWSI (análise/comparação/ranking)               │
             │  • Pearch + Apify (captura emails + enriquecimento)             │
             │  • Email OBRIGATÓRIO | Telefone opcional                         │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  5. APROVAR MAPEADOS (Gate 1)                                     │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Candidatos vão para coluna FUNIL no Kanban ou Tabela         │
             │  • Card do candidato no Kanban — ícones de score com modais:    │
             │    - 🧠 Triagem (BrainCircuit) → Modal detalhes triagem WSI     │
             │    - 🎯 CV (Target) → Modal análise de CV                       │
             │    - ⚙️ Geral (Gauge) → Modal nota média geral                  │
             │    - 👁️ Preview (Eye) → Abre preview do candidato (4 tabs)      │
             │  • Aprovação INDIVIDUAL (card a card) ou EM MASSA (max 100)     │
             │  • Drag-and-drop manual para qualquer coluna (incl. Reprovado) │
             │  • Etapas críticas → SmartTransitionModal pede confirmação      │
             │  • Aprovados → LIA inicia contato | Reprovados → Feedback       │
             │  ⚡ Inscritos via web BYPASS Gate 1 → triagem automática          │
             │  • 🤖 Ag.0 Orchestrator | 🤖 Ag.7 AnalistaFeedback              │
             │  • 🤖 Ag.8 IntegradorATS (sync status)                          │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              6. CONTATO VIA EMAIL                 │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Contato primário: SEMPRE email                                │
             │  • Email com 2 opções:                                           │
             │    A) Link para triagem via CHAT WEB (canal principal)           │
             │    B) Solicita nº celular → WhatsApp (canal secundário)         │
             │  • 🤖 Ag.0 Orchestrator dispara contato                         │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              6B. FOLLOW-UP AUTOMÁTICO (7 DIAS)   │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Se candidato NÃO abre/clica email                             │
             │  • Re-envio automático a cada 24h por 7 dias consecutivos       │
             │  • Após 7 dias sem resposta → status "sem_resposta"             │
             │  • Consultor notificado                                          │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7. TRIAGEM WSI                       │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Via chat web (link do email) OU WhatsApp (se forneceu nº)    │
             │  • LIA aplica perguntas WSI com agentes coordenados:            │
             │    🤖 Ag.0 Orchestrator (coordenação geral)                      │
             │    🤖 Ag.4 EntrevistadorWSI (conduz chat, aplica perguntas)      │
             │    🤖 Ag.5 AvaliadorWSI (analisa respostas, calcula score)       │
             │  • Score WSI calculado ao final | Parecer textual gerado        │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7A. TRIAGEM ABANDONADA              │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Candidato inicia mas para de responder                        │
             │  • Timeout: 48h sem atividade → 1º lembrete automático          │
             │  • +48h sem retorno → 2º lembrete                               │
             │  • Após 2º lembrete sem retorno → alerta ao consultor           │
             │  • Progresso parcial SALVO                                       │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              7B. FEEDBACK PÓS-TRIAGEM           │
             │  ◄────────────────────────────────────────────────────────────── │
             │  • Ag.4 EntrevistadorWSI agradece, dá feedback,                 │
             │    informa próximos passos                                       │
             │  • Canal: mesmo da triagem (chat web ou WhatsApp)               │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │  8. APROVAR/REPROVAR TRIADOS (Gate 2)                             │
             │  ──────────────────────────────────────────────────────────────► │
             │  • Consultor recebeu alerta Teams (7B)                           │
             │  • Revisa score WSI + parecer LIA na plataforma                 │
             │  • Aprova → SHORT LIST | Reprova → FEEDBACK                     │
             │  • 🤖 Ag.7 AnalistaFeedback | 🤖 Ag.8 IntegradorATS             │
             │                                                                  │
             ├──────────────────────────────────────────────────────────────────┤
             │                                                                  │
             │                              9A. AGENDAR ENTREVISTA              │
             │  ◄────────────────────────────────────────────────────────────── │
             │  (Se APROVADO) LIA agenda entrevista                             │
             │  • Email + WhatsApp ao candidato (data/hora + link reunião)      │
             │  • 🤖 Ag.6 SchedulingAgent                                       │
             │  • Se NÃO encontra horário → alerta ao consultor via Teams      │
             │                                                                  │
             │                              9B. ENVIAR FEEDBACK                 │
             │  ◄────────────────────────────────────────────────────────────── │
             │  (Se REPROVADO) LIA envia feedback via email e/ou WhatsApp      │
             │  • 🤖 Ag.7 AnalistaFeedback                                      │
             │                                                                  │
             ▼                                                                  ▼
    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │                               FIM DO ESCOPO ALPHA 1                                    │
    └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2.1 Detalhamento por Etapa — Bloqueantes, Alertas e Cards

#### Etapa 1 — Login

**Descrição:** Consultor faz login com email/senha e acessa o dashboard de vagas.

**Bloqueantes:**
- Auth email/senha funcional, tela de login, sessão JWT, dashboard de vagas

**Alertas:** —

**Cards (4):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| VAG-001 | Tabela de Vagas | É11 | S1 | 🟠 Alta | 8 | | Título, status, candidatos, data |
| VAG-002 | Tabs de Status | É11 | S1 | 🟢 Baixa | 3 | | Ativas, Pausadas, Fechadas |
| VAG-007 | Contador Candidatos | É11 | S1 | 🟢 Baixa | 2 | | Badge por etapa |
| VAG-008 | Navegação Vaga→Kanban | É11 | S1 | 🟢 Baixa | 2 | | Link para pipeline da vaga |
| | | | | **Total** | **15** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** Nenhum card IA específico. TRV-001 (LGPD Básico) deve estar pronto para consentimento no login.

---

#### Etapa 2 — Editar Vaga (importada do ATS)

**Descrição:** Consultor edita dados da vaga importada do ATS (título, área, requisitos, benefícios, salário, modelo, localidade, senioridade). NÃO cria vagas na WeDo.

**Bloqueantes:**
- Formulário de edição de vaga, campos obrigatórios (título, área, requisitos, benefícios, salário, modelo, localidade, senioridade), persistência DB

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 📬 Teams | Consultor | "Nova vaga importada: {título}. Acesse para editar e configurar." |
| 🔔 Bell | Consultor | Mesma mensagem |

**Agentes:** Ag.8 IntegradorATS (sync bidirecional com ATS do cliente)

**Cards (4):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| WIZ-008 | Form Edição Completa | É4 | S2 | 🟠 Alta | 8 | | Edição completa da vaga importada via modal. 🆕 IA: AGT-009 (IntegradorATS — sync dados ATS) |
| VAG-003 | Menu Ações Vaga | É11 | S1 | 🟡 Média | 5 | | Editar, pausar, duplicar, arquivar |
| VAG-004 | Pausar/Ativar Vaga | É11 | S1 | 🟢 Baixa | 3 | | Com confirmação |
| NOT-007 | Notif. Teams | É10 | Pós-MVP | 🟡 Média | 5 | | Depende INT-MSG-* (MS Graph). 🆕 IA: SRV-013 (Teams Notification Service) |
| | | | | **Total** | **21** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-009 (Ag.8 IntegradorATS, É15/S3) + SRV-014 (ATS Sync Service, É17/S2) para sync bidirecional com ATS. *(AGT-005/JobIntakeAgent removido — wizard conversacional adiado para Alpha 2+; vagas são importadas do ATS e editadas via modal.)*

---

#### Etapa 3 — Configurar Roteiro WSI + 3B Gerar Perguntas

**Descrição:** Configuração do roteiro de triagem a partir do JD da vaga (importado do ATS ou gerado pela LIA). Via modal: Preview Vaga → Roteiro de Triagem → Editar. LIA gera perguntas WSI automaticamente. Consultor pode editar/ajustar.

**Bloqueantes:**
- JD da vaga (importado ou gerado), modal Preview→Roteiro→Editar (TRI-*), endpoint geração JD, pipeline WSI (Blocos 2-5), tabela screening_question_sets, Ag.4 EntrevistadorWSI, endpoint geração perguntas, UI edição perguntas, calibração contextual de senioridade

**Alertas:** —

**Agentes:** JD Generator Service (LLM — geração/ajuste de JD a partir dos dados importados), Ag.4 EntrevistadorWSI (geração perguntas WSI via modal)

##### Resumo da Metodologia WSI (WeDoTalent Skill Index)

> **Referência técnica completa:** `docs/WSI_Technical_Documentation.md` (4.500+ linhas)
> **Referência metodológica:** `docs/WSI_METHODOLOGY_REFERENCE.md`

**Princípio Fundamental:**
> O LLM é usado APENAS para geração de texto (perguntas, parecer, feedback) e extração de informações. O CÁLCULO DE SCORES é 100% determinístico — fórmulas fixas, reproduzíveis, sem LLM.

**4 Frameworks Científicos Integrados:**

| Framework | Base Acadêmica | Aplicação no WSI |
|-----------|---------------|-----------------|
| CBI (Competency-Based Interviewing) | McClelland, 1973 — Harvard | Perguntas STAR (Situation, Task, Action, Result) |
| Taxonomia de Bloom (Revisada) | Anderson et al., 2001 | 5 níveis cognitivos (Lembrar → Criar) |
| Modelo Dreyfus | Dreyfus & Dreyfus, 1980 | Escala 1-5 de maturidade (Novice → Expert) |
| Big Five (OCEAN) | Goldberg, 1992 | Abertura, Conscienciosidade, Extroversão, Amabilidade, Estabilidade |

**Pipeline WSI — 6 Etapas Macro:**

| # | Etapa | Entrada | Saída | Usa LLM? |
|---|-------|---------|-------|:--------:|
| 1 | Análise JD + Sugestão Competências | JD (texto) | 5 técnicas + 2 comportamentais com pesos | Sim |
| 2 | Geração de Perguntas | Competências + Senioridade | 6-10 perguntas científicas | Sim (ou Templates) |
| 3 | Análise de Resposta | Pergunta + Resposta candidato | Score 1-5 determinístico | Não |
| 4 | Cálculo WSI Final | Scores + Pesos | WSI Técnico + Comportamental + Overall | Não |
| 5 | Geração de Parecer | WSI Result + Respostas | Parecer estruturado (p/ recrutador) | Sim |
| 6 | Geração de Feedback | WSI Result + Decisão | Feedback construtivo (p/ candidato) | Sim |

**Screening Pipeline Unificado — Blocos 2-5:**

| Block ID | Nome | Fonte | Descrição |
|:--------:|------|-------|-----------|
| 2 | Perguntas da Empresa | Database | Perguntas customizadas pela empresa |
| 3 | Elegibilidade WSI | Templates | Disponibilidade, salário, modelo de trabalho |
| 4 | Avaliação Técnica | Templates + Skills | Perguntas CBI/Bloom por skill técnica |
| 5 | Análise Situacional + Fit | Templates + Big Five | Comportamental + Cultural |

**Distribuição de Perguntas por Modelo:**

| Modelo | Elegib. | Técnico | Comport. | Total | Tempo | Precisão |
|--------|:-------:|:-------:|:--------:|:-----:|:-----:|:--------:|
| WSI Compact | 2 | 3 | 3 | 6-8 | 5-7 min | ~90% |
| WSI Compact+ | 3 | 5 | 4 | 8-10 | 6:30-9 min | ~95% |

**Scoring Determinístico (Fórmula):**
```
Score = (0.60 × Autodeclaração) + (0.40 × Contexto) - Penalidade + Bônus
WSI Final = 0.70 × WSI_Técnico + 0.30 × WSI_Comportamental
```

**Classificação WSI e Cutoffs de Decisão:**

| Faixa | Classificação | Decisão (Corte Inicial, <50 triagens) |
|:-----:|:-------------:|:-------------------------------------:|
| ≥ 4.2 | Excelente/Alto | Aprovado automático |
| 3.8-4.1 | Alto | Revisão manual |
| 3.0-3.7 | Médio | Aguardando comparação |
| < 3.0 | Regular/Baixo | Não aprovado |

> **Corte Dinâmico (>50 triagens):** Top 25% → Aprovado; 25-60% → Revisão manual; <60% → Reprovado. Recalibrado a cada nova triagem.

**Dois Sistemas de Geração de Perguntas:**

| Sistema | Arquivo | Quando Usado | Usa LLM? |
|---------|---------|-------------|:--------:|
| WSIQuestionGenerator | `wsi_service.py` | Sem question set versionado ativo | Sim (Claude) |
| WSIScreeningQuestionGenerator | `wsi_question_generator.py` | Templates hardcoded | Não |

**Funcionalidades-Chave Implementadas:**
- Versionamento de question sets (SHA-256 hash + auto-versioning)
- Deduplicação de perguntas (threshold 0.65 — SequenceMatcher)
- Calibração contextual de senioridade (13 perfis profissionais)
- Multi-Signal Seniority Resolution (5 sinais paralelos)
- Normalização de scores cross-version (difficulty coefficient)
- Ações afirmativas (pergunta adicional no Block 3)
- Governança humana (limites de autonomia configuráveis por vaga)

**Cards (7):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| WSI-001 | Motor Geração Perguntas | É4 | S2 | 🔴 Muito Alta | 13 | | Motor WSI por bloco — core do sistema. 🆕 IA: SRV-003 (WSI Question Generator) |
| WSI-002 | Blocos Metodologia WSI | É4 | S2 | 🟠 Alta | 8 | | Blocos 2-5: empresa, elegibilidade, técnico, comportamental. 🆕 IA: SRV-002 (WSI Screening Pipeline) |
| WSI-003 | Preview de Perguntas | É4 | S2 | 🟡 Média | 5 | | Prévia antes de aprovar |
| WSI-005 | Aprovação Perguntas | É4 | S2 | 🟢 Baixa | 3 | | Aprovar perguntas geradas |
| WSI-006 | Edição via Prompt Conversacional | É4 | S2 | 🟠 Alta | 8 | | Alterações em linguagem natural via Gemini. 🆕 IA: SRV-001 (LLM Service — Gemini) |
| WIZ-012 | Estágio Perguntas WSI | É4 | S2 | 🟡 Média | 5 | | UI de configuração de perguntas WSI no modal de edição da vaga |
| WIZ-013 | Quality Gates WSI | É4 | S2 | 🟡 Média | 5 | | Validação qualidade mínima. 🆕 IA: SRV-004 (WSI Scoring Engine) |
| | | | | **Total** | **47** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** SRV-002 (WSI Screening Pipeline, É17/S2), SRV-003 (WSI Question Generator, É17/S2), SRV-004 (WSI Scoring Engine, É17/S2), SRV-005 (JD Generator, É17/S2). AGT-007 (Ag.4 EntrevistadorWSI, É15/S2) para geração de perguntas via modal. TRV-003 (Calibração Senioridade, É20/S2) e TRV-004 (Multi-Signal Seniority, É20/S2) para calibração. *(AGT-005/JobIntakeAgent removido — coleta conversacional adiada para Alpha 2+.)*

##### Disclaimer — Estruturação da Metodologia WSI: Cards e Gaps Identificados

> **Fonte:** Cruzamento entre `docs/WSI_Technical_Documentation.md` e os cards Jira existentes.
> Os itens abaixo representam capacidades documentadas na especificação técnica WSI que **não possuem card Jira dedicado** ou que **precisam de observações adicionais** nos cards existentes.

**Cards existentes que precisam de observações/complementos:**

| Card | Título | O que adicionar/verificar |
|------|--------|--------------------------|
| WSI-001 | Motor Geração Perguntas | Garantir que suporta os **2 sistemas** de geração (LLM via Claude + Templates hardcoded). Incluir fallback CBI quando LLM falha. Ref: seções 5.1-5.8 do WSI Tech Doc |
| WSI-002 | Blocos Metodologia WSI | Atualizar de "7 blocos" para **Blocos 2-5** (Pipeline Unificado). Incluir lógica de rebalanceamento quando total < target. Ref: seção 6 do WSI Tech Doc |
| SCO-001 | Cálculo Score WSI | Garantir scoring 100% determinístico (sem LLM). Incluir extração de autodeclaração via regex, context score via indicadores, penalidades/bônus. Ref: seção 7 do WSI Tech Doc |
| SCO-002 | Modelo Big Five | Incluir as 15 perguntas hardcoded do Big Five (seção 20.2). Mapear 5 fatores OCEAN corretamente |
| SCO-003 | Avaliação Bloom/Dreyfus | Incluir classificação Bloom via keywords (5 níveis) + Dreyfus via anos+contexto (5 estágios). Ref: seções 5.5-5.6 |
| SCO-004 | Parecer Textual LIA | Incluir pré-processamento de respostas + critérios objetivos para decisão + 8 regras de qualidade. Ref: seção 14 |
| TRI-004 | Fluxo Conversacional LIA | Garantir que segue estrutura conversacional de 4 etapas (abertura → validação técnica → fit comportamental → fechamento). Ref: WSI_METHODOLOGY_REFERENCE seção 3 |

**Capacidades WSI sem card Jira dedicado (candidatos a novos cards):**

| ID Sugerido | Capacidade | Referência | Complexidade | Pts | Prioridade | Justificativa |
|-------------|-----------|-----------|:---:|:---:|:---:|------|
| WSI-007 | Versionamento de Question Sets | Tech Doc §11 | 🟠 Alta | 8 | P1 | SHA-256 hash, auto-versioning, deduplicação — sem card específico |
| WSI-008 | Normalização de Scores Cross-Version | Tech Doc §12 | 🟠 Alta | 8 | P2 | Difficulty coefficient para comparação justa entre versões |
| WSI-009 | Cutoffs e Decisões Automatizadas | Tech Doc §13 | 🟡 Média | 5 | P1 | Corte inicial (sem histórico) + corte dinâmico (percentis) — core do Gate |
| WSI-010 | Saturação Inteligente de Pipeline | Methodology §7.3 | 🟡 Média | 5 | P2 | Pausa automática quando aprovados atingem limite da vaga |
| WSI-011 | Governança Humana (GovernanceRules) | Methodology §8 | 🟠 Alta | 8 | P1 | Configuração de autonomia por vaga (auto_schedule, auto_feedback, etc.) |
| WSI-012 | Templates Hardcoded WSI | Tech Doc §20 | 🟡 Média | 5 | P1 | 15 Big Five + técnicas + elegibilidade + culturais + scoring criteria |
| WSI-013 | Ações Afirmativas WSI | Tech Doc §16 | 🟢 Baixa | 3 | P3 | Pergunta adicional no Block 3 para vagas afirmativas |
| WSI-014 | Calibração Contextual de Senioridade | Tech Doc §22 | 🟠 Alta | 8 | P1 | 13 perfis profissionais, ajustes geográficos, fator idade tecnologia |
| WSI-015 | Multi-Signal Seniority Resolution | Tech Doc §24 | 🔴 Muito Alta | 13 | P1 | 5 sinais paralelos, motor de combinação, detecção de conflitos |
| WSI-016 | Triagem por Voz (OpenMic) | Tech Doc §10 | 🔴 Muito Alta | 13 | P3 | Orquestrador de voz, extração Q/A de transcript — Pós-MVP? |
| | | | **Subtotal sugerido** | **76** | | |

> **Nota:** Os cards WSI-014 e WSI-015 já possuem código implementado (`seniority_context_calibrator.py`, `seniority_resolver.py`) mas não têm cards Jira para tracking. Os demais representam funcionalidades documentadas que precisam de cards para garantir rastreabilidade no sprint planning.
>
> **Recomendação:** Criar ao menos WSI-007, WSI-009, WSI-011, WSI-012 e WSI-014 (P1) para o Alpha 1, totalizando +34 pontos. Os demais (P2/P3) podem ser adiados para sprints posteriores.

---

#### Etapa 4 — Buscar Candidatos (Funil de Talentos)

**Descrição:** Busca no Banco de Talentos interno + Pearch/Apify para captura de emails e enriquecimento. Email obrigatório, telefone opcional. Ag.2 SourcingAgent auxilia busca.

**Bloqueantes:**
- Funil de Talentos (tela), Banco de Talentos interno, Pearch+Apify (enriquecimento), email obrigatório por candidato, busca/filtros funcionais, ação "Adicionar à vaga"

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 📬 Teams | Consultor | "{X} candidatos mapeados para {vaga}. Acesse o Funil para revisar e aprovar." |
| 🔔 Bell | Consultor | Mesma mensagem |

**Agentes:** Ag.2 SourcingAgent (busca/perfis similares), Ag.3 TriagemCurricular (triagem/screening CV), Ag.5 AvaliadorWSI (análise/comparação/ranking)

**Cards (17):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| MAP-001 | Lista Candidatos Base | É3 | S1 | 🟡 Média | 5 | | Cards da base de candidatos |
| MAP-002 | Busca Semântica ES+PGV+WRF | É3 | S1 | 🔴 Muito Alta | 13 | | Core do search — ES+PGV+WRF+Dynamic K. 🆕 IA: SRV-009 (Sourcing Pipeline ES+PGV+WRF), SRV-008 (Embedding+Search) |
| MAP-003 | Filtros Avançados | É3 | S1 | 🟠 Alta | 8 | | 8 categorias de filtros |
| MAP-004 | Adicionar Cand. à Vaga | É3 | S1 | 🟡 Média | 5 | | Individual + massa (até 100) |
| MAP-005 | Matching Score IA | É3 | S1 | 🔴 Muito Alta | 13 | | Score candidato×vaga via LLM. 🆕 IA: AGT-001 (Avaliador WSI — scoring), SRV-007 (CV Parser) |
| MAP-006 | Sugestões Proativas LIA | É3 | S1 | 🟠 Alta | 8 | | Score > 75 → sugestão automática. 🆕 IA: AGT-006 (SourcingAgent — sugestões) |
| MAP-007 | Endpoint Busca Paginada | É3 | S1 | 🟡 Média | 5 | | 10 por vez, cursor-based |
| MAP-008 | Paginação On-Demand | É3 | S1 | 🟢 Baixa | 3 | | Botão "Carregar mais 10" |
| MAP-009 | Exclusão IDs no ES | É3 | S1 | 🟢 Baixa | 3 | | Transparente no backend |
| MAP-010 | Exclusão IDs no PGV | É3 | S1 | 🟢 Baixa | 3 | | Transparente no backend |
| MAP-011 | API Feedback Like/Dislike | É3 | S1 | 🟡 Média | 5 | | CRUD + unicidade por busca |
| MAP-012 | Componente Like/Dislike | É3 | S1 | 🟢 Baixa | 3 | | Toggle thumbs up/down |
| MAP-013 | Remover Ord. por Ranking | É3 | S2 | 🟢 Baixa | 3 | | Dropdown de ordenação manual |
| AGT-002 | Ag. Triagem Curricular | É15 | S3 | 🟠 Alta | 8 | | Análise automatizada de CVs. 🆕 IA: AGT-002 (card IA direto) |
| INT-APY-001 | Config Apify | É14 | S3 | 🟢 Baixa | 3 | | Setup conta + API keys |
| INT-APY-002 | LinkedIn Scraper | É14 | S3 | 🟡 Média | 5 | | Captura emails + enriquecimento |
| INT-APY-003 | Integr. Sourcing Agent | É14 | S3 | 🟡 Média | 5 | | Integração Apify→Ag.2. 🆕 IA: AGT-006 (SourcingAgent — integração) |
| | | | | **Total** | **98** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** SRV-009 (Sourcing Pipeline, É17/S2) para busca ES+PGV+WRF. SRV-007 (CV Parser, É17/S2) e SRV-008 (Embedding Service, É17/S2) para análise de CVs. AGT-006 (Ag.2 SourcingAgent, É15/S2) para busca inteligente. AGT-002 (Ag.3 Triagem Curricular, É15/S2) para screening automatizado. AGT-001 (Ag.5 Avaliador WSI, É15/S2) para ranking e comparação.

---

#### Etapa 5 — Gate 1: Aprovação de Mapeados

**Descrição:** Candidatos mapeados ficam na coluna Funil do Kanban. Consultor aprova individual ou em massa (checkboxes + barra flutuante, limite 100). Inscritos via web fazem bypass do Gate 1.

**Bloqueantes:**
- Kanban com coluna "Funil" (KAN-001), card do candidato no Kanban, checkboxes + barra flutuante (ação em lote), lógica bypass Gate 1 (inscritos via web), Ag.7 AnalistaFeedback, Ag.8 IntegradorATS

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 📬 Teams | Consultor | "Novo candidato inscrito via web: {nome}. Bypass Gate 1 — triagem iniciada." *(apenas bypass)* |
| ✉️ Email | Candidato reprovado | Feedback construtivo automático |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.0 Orchestrator, Ag.7 AnalistaFeedback (feedback reprovados), Ag.8 IntegradorATS (sync status ATS)

**Cards (20 — +2 novos):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| GAT-001 | Gate 1: Aprovar Mapeados | É7 | S3 | 🟠 Alta | 8 | | Aprovar para triagem. 🆕 IA: AGT-008 (AnalistaFeedback), AGT-009 (IntegradorATS) |
| GAT-003 | Modal de Reprovação | É7 | S3 | 🟢 Baixa | 3 | | Com motivo obrigatório |
| GAT-004 | Geração Feedback LIA | É7 | S3 | 🟠 Alta | 8 | | Feedback construtivo via Ag.7. 🆕 IA: AGT-008 (AnalistaFeedback — geração feedback) |
| GAT-005 | Envio de Feedback | É7 | S3 | 🟡 Média | 5 | | Via email/WhatsApp. 🆕 IA: AGT-011 (CommunicationAgent), SRV-011 (Email) |
| GAT-006 | Aprovação em Massa | É7 | S3 | 🟡 Média | 5 | | Max 100 candidatos. 🆕 IA: AUT-006 (Cascata stage→rejection). Ver PIP-010 |
| GAT-007 | Histórico Decisões | É7 | S3 | 🟡 Média | 5 | | Audit trail. 🆕 IA: CMP-004 (Audit Trail) |
| KAN-001 | Estrutura Kanban 4 Col. | É11 | S1 | 🟠 Alta | 8 | | Funil, Triagem, Entrevista, Reprovados. Ver PIP-001 (3 Camadas) |
| KAN-002 | Card de Candidato | É11 | S1 | 🟡 Média | 5 | | 6 ícones de score com modais. Ver PIP-006 (Badges) |
| KAN-003 | Drag-and-Drop | É11 | S1 | 🟠 Alta | 8 | | Entre colunas + SmartTransitionModal. Ver PIP-005 (Movimentação Livre). 🆕 IA: SRV-016 (Stage Automation) |
| KAN-004 | Menu Ações Card | É11 | S1 | 🟡 Média | 5 | | Ver perfil, agendar, reprovar, mover |
| KAN-006 | Badge Score WSI | É11 | S1 | 🟢 Baixa | 2 | | Score no card. 🆕 IA: SRV-004 (WSI Scoring Engine) |
| KAN-007 | Filtro por Status | É11 | S1 | 🟢 Baixa | 3 | | Dentro do Kanban |
| KAN-008 | Busca por Nome | É11 | S1 | 🟢 Baixa | 3 | | Pesquisar candidato no Kanban |
| KAN-011 | Triagem em Lote | É11 | S1 | 🟡 Média | 5 | | Disparar para múltiplos. 🆕 IA: AUT-006 (bulk reject). Ver PIP-010 |
| TAB-001 | Tabela Candidatos | É11 | S1 | 🟡 Média | 5 | | View tabular alternativa |
| TAB-002 | Colunas Ordenáveis | É11 | S1 | 🟢 Baixa | 3 | | Nome, score, data, status |
| TAB-003 | Seleção Múltipla | É11 | S1 | 🟢 Baixa | 3 | | Checkboxes |
| TAB-004 | Paginação | É11 | S1 | 🟢 Baixa | 2 | | Paginação da tabela |
| TAB-005 | Ações em Massa/Barra | É11 | S1 | 🟡 Média | 5 | | Barra flutuante para selecionados. Ver PIP-010 (Bulk Actions detalhado) |
| | | | | **Total** | **91** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa: ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-008 (Ag.7 AnalistaFeedback, É15/S2) para feedback de reprovados. AGT-009 (Ag.8 IntegradorATS, É15/S3) + SRV-014 (ATS Sync, É17/S2) para sync status. AGT-011 (Ag.10 CommunicationAgent, É15/S2) para envio multi-canal. SRV-016 (Stage Automation, É17/S3) para transições AI. AUT-006 (Cascata stage→rejection, É19/S3) para bulk reject. INF-005 (EventDispatcher, É16/S2) para cascata de eventos. PIP-001~010 (Pipeline Produto, É24-25/S1-S2) para infraestrutura de movimentação.

---

#### Etapa 6 — Contato via Email

**Descrição:** Contato primário é SEMPRE via email. Email contém: (A) link para triagem via chat web, (B) solicita nº celular para WhatsApp. Candidato escolhe por onde quer ser triado.

**Bloqueantes:**
- Template email contato (pré-configurado)

> 📌 **PONTO DE ATENÇÃO:** Discutir se template fica pré-configurado no backend ou se cria hub de templates no menu configurações.

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| ✉️ Email | Candidato | Convite triagem (link chat web + opção WhatsApp) |
| 🔔 Bell | Consultor | "Email enviado para {nome} ({vaga})" |

**Agentes:** Ag.0 Orchestrator (disparo contato), CommunicationAgent (orquestração email/multi-canal)

> 🆕 **INFORMAÇÃO NOVA — CommunicationAgent** existe no código (`communication_agent.py`, AgentType.COMMUNICATION) mas não está numerado na arquitetura oficial. Recomenda-se formalizar como **Ag.10 CommunicationAgent** para orquestração de canais (email, WhatsApp, Teams).

**Cards (9 — sendo 1 a criar):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| TPL-001 | Template Abordagem Inicial | É8 | S2 | 🟡 Média | 5 | | Mensagem inicial ao candidato. 🆕 IA: SRV-011 (Email Service Mailgun) |
| TPL-005 | Editor de Templates | É8 | S2 | 🟠 Alta | 8 | | Editor WYSIWYG |
| TPL-006 | Variáveis Dinâmicas | É8 | S2 | 🟡 Média | 5 | | {{nome}}, {{vaga}}, {{link}} |
| TPL-007 | Preview de Template | É8 | S2 | 🟢 Baixa | 3 | | Visualizar com dados reais |
| TRI-002 | Envio Mensagem Inicial | É5 | S2 | 🟡 Média | 5 | | Abordagem do candidato. 🆕 IA: AGT-011 (CommunicationAgent — orquestração) |
| TRI-009 | Templates de Mensagem | É5 | S2 | 🟡 Média | 5 | | Templates para triagem |
| TRI-010 | Envio em Massa/Bulk | É5 | S2 | 🟡 Média | 5 | | Bulk send. 🆕 IA: AGT-011 (CommunicationAgent — bulk) |
| NOT-001 | Sistema Bell | É10 | S3 | 🟡 Média | 5 | | Ícone sino + dropdown. 🆕 IA: SRV-013 (Teams Notification) |
| | | | | **Total** | **41** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa: ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-011 (Ag.10 CommunicationAgent, É15/S2) para orquestração multi-canal. SRV-011 (Email Service Mailgun, É17/S2) para envio de emails. SRV-013 (Teams Notification, É17/S3) para alertas ao consultor.

---

#### Etapa 6B — Follow-up Automático (7 dias)

**Descrição:** Se candidato NÃO abre/clica email, re-envio automático a cada 24h durante 7 dias consecutivos. Após 7 dias sem resposta, candidato vai para status "sem_resposta" e consultor é notificado.

**Bloqueantes:**
- Sistema de tracking abertura/clique (Mailgun webhooks), fila de re-envio automático (cron/job), lógica de parada (abriu/clicou = para), status "sem_resposta" no pipeline

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| ✉️ Email | Candidato | Re-envio do convite a cada 24h (até 7 dias) |
| 📬 Teams | Consultor | "{X} candidatos sem resposta após 7 dias na vaga {vaga}." *(dia 7)* |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.9 TaskPlanner (scheduler follow-up automático), CommunicationAgent (re-envio email)

**Cards (1 existente + 2 a criar — ver [2.8.7](#287-cards-a-criar--gaps-identificados)):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| TRI-007 | Timeout e Retentativas | É5 | S2 | 🟡 Média | 5 | | Automáticas (compartilhado c/ 7A). 🆕 IA: AGT-010 (TaskPlanner — scheduler) |
| | | | | **Total** | **5** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa (FLW-001, FLW-002): ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AUT-001 (Follow-up automático, É19/S2) para lógica de re-envio. AGT-010 (Ag.9 TaskPlanner, É15/S3) para scheduling. AGT-011 (CommunicationAgent, É15/S2) para re-envio de emails.

---

#### Etapa 7 — Triagem WSI

**Descrição:** Conduzida pela LIA via chat web (link do email) ou WhatsApp (se forneceu número). LIA aplica perguntas WSI com agentes coordenados. Score WSI calculado ao final + parecer textual.

**Bloqueantes:**
- ⚠️ **PÁGINA PÚBLICA de triagem via chat web** (SEM LOGIN, identificação via token) — **BLOQUEANTE CRÍTICO**, listar como item separado a construir
- Ag.4 EntrevistadorWSI e Ag.5 AvaliadorWSI funcionais
- Tabelas WSI no banco (sessions, questions, responses, results)
- Cálculo score WSI e geração de parecer

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 🔔 Bell | Consultor | "{nome} iniciou triagem WSI ({vaga})" |

**Agentes:** Ag.0 Orchestrator, Ag.4 EntrevistadorWSI (conduz chat, aplica perguntas), Ag.5 AvaliadorWSI (analisa respostas, calcula score)

**Cards (16 — sendo 2 a criar, 1 novo):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| TRI-001 | Config WhatsApp Business | É5 | S2 | 🟠 Alta | 8 | | Multi-provider abstraction. 🆕 IA: SRV-012 (WhatsApp Service) |
| TRI-003 | Webhook Recebimento | É5 | S2 | 🟡 Média | 5 | | Receber respostas candidato |
| TRI-004 | Fluxo Conversacional LIA | É5 | S2 | 🔴 Muito Alta | 13 | | Core — WSI via conversa natural. 🆕 IA: AGT-007 (EntrevistadorWSI — core), INF-008 (ConversationMemory) |
| TRI-005 | Persistência Conversa | É5 | S2 | 🟡 Média | 5 | | Com metadados. 🆕 IA: PREP-009 (ConversationState), INF-008 (ConversationMemory) |
| TRI-006 | Transcrição no Card | É5 | S2 | 🟠 Alta | 8 | | Monitoramento real-time |
| TRI-008 | Opt-out e Consentimento | É5 | S2 | 🟢 Baixa | 3 | | LGPD. 🆕 IA: TRV-001 (LGPD Básico) |
| TRI-013 | Reporte Problemas Cand. | É5 | S2 | 🟢 Baixa | 3 | | Pelo candidato |
| SCO-001 | Cálculo Score WSI | É6 | S3 | 🔴 Muito Alta | 13 | | Por dimensão e geral. 🆕 IA: SRV-004 (WSI Scoring Engine) |
| SCO-002 | Modelo Big Five | É6 | S3 | 🟠 Alta | 8 | | Comportamental |
| SCO-003 | Avaliação Bloom/Dreyfus | É6 | S3 | 🟠 Alta | 8 | | Nível técnico |
| SCO-004 | Parecer Textual LIA | É6 | S3 | 🟠 Alta | 8 | | Narrativa gerada. 🆕 IA: AGT-001 (Avaliador WSI — parecer), SRV-001 (LLM) |
| AGT-001 | Agente Avaliador WSI | É15 | S3 | 🔴 Muito Alta | 13 | | Core — avaliação candidatos. 🆕 IA: AGT-001 (card IA direto) |
| AGT-004 | Orquestr. Pipeline Chat | É15 | S3 | 🔴 Muito Alta | 13 | | 15 intents, 3 modes. 🆕 IA: AGT-004 (card IA direto), AGT-000 (Orchestrator) |
| TRI-012 | Serviço Pré-Qualificação | É15 | S3 | 🟠 Alta | 8 | | Pré-qualificar antes da triagem. 🆕 IA: AGT-002 (Triagem Curricular) |
| | | | | **Total** | **116** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa (incluindo **BLOQUEANTE CRÍTICO** PUB-001): ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-007 (Ag.4 EntrevistadorWSI, É15/S2) para condução do chat de triagem. AGT-001 (Ag.5 Avaliador WSI, É15/S2) para análise de respostas e scoring. AGT-004 (Ag.0 Orquestrador Pipeline Chat, É15/S2) para roteamento de intents. SRV-002 (WSI Screening Pipeline, É17/S2) e SRV-004 (WSI Scoring Engine, É17/S2) para cálculo de scores. SRV-012 (WhatsApp Service, É17/S2) para canal WhatsApp. INF-008 (ConversationMemory, É16/S2) para persistência de contexto. TRV-001 (LGPD Básico, É20/S1) para consentimento.

---

#### Etapa 7A — Triagem Abandonada

**Descrição:** Candidato inicia triagem mas para de responder. Timeout de 48h sem atividade dispara lembrete automático. Após 2º lembrete sem retorno, alerta ao consultor. Progresso parcial é salvo.

**Bloqueantes:**
- Detecção de inatividade (timeout 48h), salvamento de progresso parcial (respostas já dadas preservadas), job de verificação de timeouts, status "triagem_incompleta" no pipeline

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| ✉️ Email | Candidato | "Você ainda pode completar sua triagem. Clique para continuar." *(1º lembrete — 48h)* |
| ✉️ Email | Candidato | 2º lembrete *(+48h, mesmo canal)* |
| 📬 Teams | Consultor | "{nome} não completou a triagem há 4 dias. Ação necessária." *(após 2º lembrete)* |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.9 TaskPlanner (detecção timeout 48h), CommunicationAgent (envio lembretes), Ag.0 Orchestrator (alerta consultor)

**Cards (1 existente + 3 a criar — ver [2.8.7](#287-cards-a-criar--gaps-identificados)):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| TRI-007 | Timeout e Retentativas | É5 | S2 | 🟡 Média | 5 | | Compartilhado com 6B. 🆕 IA: AGT-010 (TaskPlanner — detecção timeout) |
| | | | | **Total** | **5** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa (TRI-015, TRI-016, TRI-017): ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AUT-002 (Timeout triagem abandonada, É19/S2) para detecção de inatividade. AGT-010 (Ag.9 TaskPlanner, É15/S3) para scheduling de lembretes. AGT-011 (CommunicationAgent, É15/S2) para envio de lembretes. PREP-009 (ConversationState, É14/S0) para salvamento de progresso.

---

#### Etapa 7B — Feedback Pós-Triagem ao Candidato

**Descrição:** Ao finalizar a triagem, Ag.4 EntrevistadorWSI agradece, dá feedback e informa próximos passos ao candidato, no mesmo canal da triagem.

**Bloqueantes:**
- Lógica de encerramento no Ag.4, template de feedback pós-triagem

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 💬 Chat | Candidato | "Obrigado, {nome}! Suas respostas foram registradas. Entraremos em contato com os próximos passos." |
| 📬 Teams | Consultor | "Triagem concluída: {nome}. Score WSI: {X}/5 \| Tier: {tier}. Recomendação: {rec}." + [Ver Detalhes] [Aprovar] [Reprovar] |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.4 EntrevistadorWSI (encerramento chat + feedback), Ag.5 AvaliadorWSI (gerar parecer final), CommunicationAgent (notificação consultor)

**Cards (4 — +1 novo):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| SCO-005 | Visualização Score | É6 | S3 | 🟡 Média | 5 | | Radar chart. 🆕 IA: AGT-001 (Avaliador WSI — visualização score) |
| SCO-006 | Breakdown Dimensões | É6 | S3 | 🟠 Alta | 8 | | Com evidências e justificativas. 🆕 IA: AGT-001 (Avaliador WSI — breakdown) |
| NOT-007 | Notif. Teams | É10 | Pós-MVP | 🟡 Média | 5 | | Depende INT-MSG-* (MS Graph). 🆕 IA: SRV-013 (Teams Notification) |
| | | | | **Total** | **18** | | |

> 🆕 ⚠️ Cards adicionais identificados para esta etapa: ver [2.8.7 Cards a Criar](#287-cards-a-criar--gaps-identificados).

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-007 (Ag.4 EntrevistadorWSI, É15/S2) para encerramento do chat. AGT-001 (Ag.5 Avaliador WSI, É15/S2) para parecer final. AGT-011 (CommunicationAgent, É15/S2) para notificação ao consultor. SRV-013 (Teams Notification, É17/S3) para alertas Teams.

---

#### Etapa 8 — Gate 2: Aprovação de Triados

**Descrição:** Consultor é notificado via Teams quando triagem é concluída. Revisa score WSI + parecer da LIA na plataforma (Kanban). Aprova → Short List. Reprova → LIA envia feedback construtivo.

**Preview do candidato na vaga (mesmas 4 tabs do Funil):**
- Perfil Completo: dados, experiência, skills, educação
- Atividades: timeline (triagens WSI, emails, entrevistas, candidaturas, testes, ofertas + eventos do ATS)
- Arquivos: CVs e documentos anexados
- Pareceres e Análises: análises LIA salvas + opiniões do consultor

**Bloqueantes:**
- WSI Scorecard (detalhamento por bloco), preview do candidato com 4 tabs, ações aprovar/reprovar no card do candidato, Ag.7 AnalistaFeedback, sync status ATS

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| 🔔 Bell | Consultor | "Decisão registrada: {nome} → {Aprovado/Reprovado}" |

**Agentes:** Ag.7 AnalistaFeedback (feedback reprovados), Ag.8 IntegradorATS (sync status ATS), Ag.5 AvaliadorWSI (comparação/ranking)

**Cards (14):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| GAT-002 | Gate 2: Aprovar Triados | É7 | S3 | 🟠 Alta | 8 | | Aprovar/reprovar com base WSI. 🆕 IA: AGT-008 (AnalistaFeedback), AGT-009 (IntegradorATS) |
| GAT-003 | Modal de Reprovação | É7 | S3 | 🟢 Baixa | 3 | | Reutilizado do Gate 1 |
| GAT-004 | Geração Feedback LIA | É7 | S3 | 🟠 Alta | 8 | | Para reprovados |
| GAT-005 | Envio de Feedback | É7 | S3 | 🟡 Média | 5 | | Via email/WhatsApp |
| GAT-008 | Aprendizagem IA | É7 | S3 | 🟠 Alta | 8 | | Padrões aprovação/reprovação. 🆕 IA: LRN-001 (Learning Loop), LRN-005 (Feedback Loop) |
| PRV-001 | Preview Lateral Cand. | É11 | S1 | 🟡 Média | 5 | | Detalhes do candidato |
| PRV-002 | Tab Perfil | É11 | S1 | 🟡 Média | 5 | | Dados básicos, experiência |
| PRV-003 | Tab Atividades | É11 | S1 | 🟡 Média | 5 | | Timeline interações + ATS |
| PRV-004 | Tab Arquivos | É11 | S1 | 🟢 Baixa | 3 | | CVs e documentos |
| PRV-005 | Tab Parecer LIA | É11 | S1 | 🟡 Média | 5 | | Análise gerada IA |
| SCO-005 | Visualização Score | É6 | S3 | 🟡 Média | 5 | | Radar chart. 🆕 IA: AGT-001 (Avaliador WSI) |
| SCO-006 | Breakdown Dimensões | É6 | S3 | 🟠 Alta | 8 | | Com evidências e justificativas. 🆕 IA: AGT-001 (Avaliador WSI — evidências) |
| SCO-007 | Comparação Candidatos | É6 | S3 | 🟠 Alta | 8 | | Lado a lado. 🆕 IA: AGT-001 (Avaliador WSI — comparação lado a lado) |
| SCO-008 | Histórico Scores | É6 | S3 | 🟢 Baixa | 3 | | Para auditoria |
| | | | | **Total** | **79** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-001 (Ag.5 Avaliador WSI, É15/S2) para comparação e ranking. AGT-008 (Ag.7 AnalistaFeedback, É15/S2) para feedback de reprovados. AGT-009 (Ag.8 IntegradorATS, É15/S3) + SRV-014 (ATS Sync, É17/S2) para sync status. SRV-016 (Stage Automation, É17/S3) para transições AI. LRN-001 (Learning Loop, É21/S4) e LRN-005 (Feedback Loop, É21/S4) para aprendizagem de padrões (Alpha 2+).

---

#### Etapa 9A — Agendar Entrevista (se aprovado)

**Descrição:** LIA agenda entrevista via Ag.6 SchedulingAgent (integração Microsoft Graph / Teams). Candidato recebe email + WhatsApp com data/hora e link. Se não encontra horário, alerta consultor para resolução manual.

**Bloqueantes:**
- Integração Microsoft Graph (calendário), Ag.6 SchedulingAgent, criação de evento Teams, disponibilidade do consultor (calendário)

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| ✉️ Email | Candidato | "Entrevista agendada: {data/hora}. Link da reunião: {link}." |
| 📬 Teams | Consultor | "Entrevista agendada: {nome}. Data: {data}. Link: {link}." |
| 📬 Teams | Consultor | "Não foi possível agendar para {nome}. Ajuste calendário ou sugira horário." *(se falha)* |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.6 SchedulingAgent (agendamento inteligente), CommunicationAgent (envio convite email+WhatsApp), Ag.9 TaskPlanner (lembretes automáticos)

**Cards (15):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| AGE-001 | Integração MS Graph | É9 | S2 | 🔴 Muito Alta | 13 | | Calendários + Teams. 🆕 IA: SRV-010 (Scheduling Service + Calendar) |
| AGE-002 | Consulta Disponibilidade | É9 | S2 | 🟡 Média | 5 | | No calendário. 🆕 IA: SRV-010 (Scheduling — disponibilidade) |
| AGE-003 | Sugestão Horários | É9 | S2 | 🟡 Média | 5 | | Timezone + preferências. 🆕 IA: AGT-003 (SchedulingAgent — sugestão inteligente) |
| AGE-004 | Criação Evento Teams | É9 | S2 | 🟡 Média | 5 | | Com link de reunião |
| AGE-005 | Confirmação Candidato | É9 | S2 | 🟡 Média | 5 | | Via email/WhatsApp. 🆕 IA: AGT-011 (CommunicationAgent — envio convite) |
| AGE-006 | Reagendamento | É9 | S2 | 🟡 Média | 5 | | Com nova disponibilidade |
| AGE-007 | Lembretes Automáticos | É9 | S2 | 🟢 Baixa | 3 | | 24h antes. 🆕 IA: AGT-010 (TaskPlanner — lembretes) |
| AGE-008 | Cancelamento | É9 | S2 | 🟢 Baixa | 3 | | Notif. todas as partes |
| AGT-003 | Ag. Agendamento | É15 | S3 | 🟠 Alta | 8 | | Agendamento inteligente. 🆕 IA: AGT-003 (card IA direto) |
| TPL-002 | Template Agendamento | É8 | S2 | 🟢 Baixa | 3 | | Convite para entrevista |
| TPL-003 | Template Confirmação | É8 | S2 | 🟢 Baixa | 3 | | Confirmação entrevista |
| INT-MSG-002 | OAuth Flow MS | É14 | S2 | 🟠 Alta | 8 | | Autenticação OAuth |
| INT-MSG-003 | Calendar API | É14 | S2 | 🟡 Média | 5 | | Ler/criar eventos |
| INT-MSG-004 | Teams Meeting API | É14 | S2 | 🟡 Média | 5 | | Criar reuniões Teams |
| INT-MSG-006 | Token Refresh | É14 | S2 | 🟢 Baixa | 3 | | Automático |
| | | | | **Total** | **79** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-003 (Ag.6 SchedulingAgent, É15/S3) para agendamento inteligente. SRV-010 (Scheduling Service, É17/S3) para integração com calendário. AGT-011 (CommunicationAgent, É15/S2) para envio de convites. AGT-010 (Ag.9 TaskPlanner, É15/S3) para lembretes automáticos. SRV-011 (Email Service, É17/S2) para convite por email.

---

#### Etapa 9B — Enviar Feedback (se reprovado)

**Descrição:** LIA envia feedback automático com áreas de desenvolvimento ao candidato reprovado via email e/ou WhatsApp. Consultor recebe alerta Teams de confirmação.

**Bloqueantes:**
- Ag.7 AnalistaFeedback, template feedback reprovação (pré-configurado), dados do score WSI para gerar feedback relevante

**Alertas:**
| Tipo | Destino | Conteúdo |
|------|---------|----------|
| ✉️ Email | Candidato | Feedback construtivo (áreas de desenvolvimento + dicas + agradecimento) |
| 📬 Teams | Consultor | "Feedback enviado: {nome} ({vaga})." |
| 🔔 Bell | Consultor | Mesma mensagem Teams |

**Agentes:** Ag.7 AnalistaFeedback (geração feedback construtivo), CommunicationAgent (envio email/WhatsApp), Ag.8 IntegradorATS (sync status)

**Cards (4):**
| Card | Título | Épico | Sprint | Complexidade | Pts | Status | Obs/Ajustes Sprint |
|------|--------|-------|--------|:---:|:---:|:---:|------|
| GAT-004 | Geração Feedback LIA | É7 | S3 | 🟠 Alta | 8 | | Reutilizado de Gate 1/Gate 2. 🆕 IA: AGT-008 (AnalistaFeedback — geração) |
| GAT-005 | Envio de Feedback | É7 | S3 | 🟡 Média | 5 | | Via email/WhatsApp. 🆕 IA: AGT-011 (CommunicationAgent), SRV-011 (Email) |
| TPL-004 | Template Pós-Entrevista | É8 | S2 | 🟢 Baixa | 3 | | Feedback após entrevista. 🆕 IA: SRV-011 (Email Service) |
| NOT-001 | Sistema Bell | É10 | S3 | 🟡 Média | 5 | | Notif. "Feedback enviado: {nome}". 🆕 IA: SRV-013 (Teams Notification) |
| | | | | **Total** | **21** | | |

> 🆕 **PRÉ-REQUISITOS IA (INFORMAÇÃO NOVA):** AGT-008 (Ag.7 AnalistaFeedback, É15/S2) para geração de feedback construtivo. AGT-011 (CommunicationAgent, É15/S2) para envio multi-canal. SRV-011 (Email Service, É17/S2) e SRV-012 (WhatsApp Service, É17/S2) para canais de envio. AGT-009 (Ag.8 IntegradorATS, É15/S3) + SRV-014 (ATS Sync, É17/S2) para sync status reprovação.

---

### 2.2.2 Mapa de Agentes IA por Etapa do Alpha 1

> 🆕 **INFORMAÇÃO NOVA (v2.4) — Atualizado:** Adicionados CommunicationAgent (Ag.10), Ag.5 AvaliadorWSI na Etapa 4, Ag.8 na Etapa 2, e roles complementares em etapas de comunicação.

| Etapa | Agente(s) | Papel |
|-------|-----------|-------|
| **Todas** | **Ag.0 Orchestrator** | Coordenação geral, roteamento de intenções, gerenciamento de estado (AGT-000, AGT-004) |
| **Todas** | **Ag.9 TaskPlanner** | Planejamento de tarefas assíncronas, decomposição de ações complexas, scheduling de jobs (AGT-010) |
| 2. Editar Vaga | Ag.8 IntegradorATS | Sync bidirecional com ATS ao editar vaga (AGT-009, SRV-014) |
| 3. Roteiro WSI | JD Generator Service (LLM) | Geração/ajuste de JD a partir dos dados importados do ATS (SRV-005) |
| 3B. Gerar Perguntas | Ag.4 EntrevistadorWSI | Geração de perguntas WSI baseadas no JD (Blocos 2-5) (AGT-007) |
| 4. Buscar Candidatos | Ag.2 SourcingAgent | Busca no banco de talentos, integração Pearch/Apify (AGT-006, SRV-009) |
| 4. Buscar Candidatos | Ag.3 TriagemCurricular | Análise automatizada de CVs dos candidatos encontrados (AGT-002, SRV-007) |
| 4. Buscar Candidatos | **Ag.5 AvaliadorWSI** | Análise, comparação e ranking de candidatos (prompt expandido) (AGT-001, SRV-004) |
| 5. Gate 1 | Ag.7 AnalistaFeedback | Geração de feedback para candidatos reprovados (AGT-008) |
| 5. Gate 1 | Ag.8 IntegradorATS | Sincronização de status com o ATS (Merge) (AGT-009, SRV-014) |
| 6. Contato Email | Ag.0 Orchestrator | Disparo do fluxo de contato (AGT-000, AGT-004) |
| 6. Contato Email | **Ag.10 CommunicationAgent** | Orquestração de envio de email (template + tracking) (AGT-011, SRV-011, SRV-012) |
| 6B. Follow-up | Ag.9 TaskPlanner | Scheduler de re-envio automático a cada 24h (AGT-010) |
| 6B. Follow-up | **Ag.10 CommunicationAgent** | Re-envio de email de follow-up (AGT-011, SRV-011, SRV-012) |
| 7. Triagem WSI | Ag.4 EntrevistadorWSI | Condução do chat, aplicação de perguntas, coleta de respostas (AGT-007) |
| 7. Triagem WSI | Ag.5 AvaliadorWSI | Análise de respostas, cálculo de score WSI, parecer textual (AGT-001, SRV-004) |
| 7A. Abandonada | Ag.9 TaskPlanner | Detecção de timeout (48h), scheduling de lembretes (AGT-010) |
| 7A. Abandonada | **Ag.10 CommunicationAgent** | Envio de lembretes automáticos ao candidato (AGT-011, SRV-011, SRV-012) |
| 7B. Pós-Triagem | Ag.4 EntrevistadorWSI | Encerramento do chat com agradecimento e feedback (AGT-007) |
| 7B. Pós-Triagem | **Ag.5 AvaliadorWSI** | Geração do parecer final para o consultor (AGT-001, SRV-004) |
| 8. Gate 2 | Ag.7 AnalistaFeedback | Geração de feedback para candidatos reprovados (AGT-008) |
| 8. Gate 2 | Ag.8 IntegradorATS | Sincronização de status com o ATS (Merge) (AGT-009, SRV-014) |
| 8. Gate 2 | **Ag.5 AvaliadorWSI** | Comparação e ranking de candidatos triados (AGT-001, SRV-004) |
| 9A. Agendamento | Ag.6 SchedulingAgent | Agendamento de entrevista via Microsoft Graph (AGT-003, SRV-010) |
| 9A. Agendamento | **Ag.10 CommunicationAgent** | Envio de convite email + WhatsApp (AGT-011, SRV-011, SRV-012) |
| 9B. Feedback | Ag.7 AnalistaFeedback | Geração de feedback construtivo para reprovados (AGT-008) |
| 9B. Feedback | **Ag.10 CommunicationAgent** | Envio de feedback via email/WhatsApp (AGT-011, SRV-011, SRV-012) |
| 9B. Feedback | Ag.8 IntegradorATS | Sync status reprovação no ATS (AGT-009, SRV-014) |

> 🆕 **⚠️ RECOMENDAÇÃO (INFORMAÇÃO NOVA): Formalizar CommunicationAgent como Ag.10**
> O `CommunicationAgent` já existe no código (`communication_agent.py`, `AgentType.COMMUNICATION`) e está registrado no `enhanced_registry.py`. Recomenda-se formalizá-lo como **Ag.10** na arquitetura oficial de 11 agentes. Ele é responsável por toda orquestração multi-canal (email Mailgun, WhatsApp, Teams notifications).

---

### 2.2.3 Cards a Criar (sem card Jira existente)

> 🆕 **INFORMAÇÃO NOVA (v2.5) — Centralizado:** Os 10 cards identificados como gaps (sem Jira existente) foram movidos para a seção [2.8.7 Cards a Criar — Gaps Identificados](#287-cards-a-criar--gaps-identificados) para consolidação com o inventário completo.
>
> **Resumo:** 10 cards / 56 pontos — incluindo **PUB-001** (bloqueante crítico para triagem web).

> 🆕 **📌 INFORMAÇÃO NOVA — Cards de Pipeline & Transições (PIP-*):** Além dos cards acima, o sistema de pipeline possui **18 cards dedicados** documentados em `docs/pipeline-transition-cards-jira.md`. Destes, **10 são Alpha 1** (62 pts, S1-S2): PIP-001 (3 Camadas + Catálogo), PIP-002 (action_behavior), PIP-003 (UniversalTransitionModal), PIP-004 (use-transition-context), PIP-005 (Movimentação Livre), PIP-006 (Badges), PIP-007 (TransitionDispatchService), PIP-008 (API Transição), PIP-009 (Pipeline CRUD), PIP-010 (Bulk Actions). Esses cards complementam KAN-001~008 (estrutura Kanban) e GAT-001~008 (Gates) com a infraestrutura de pipeline, transições e disparos automáticos.

**Cards WSI sugeridos (Disclaimer Etapa 3 — pendentes aprovação):**

| # | Funcionalidade | Etapa | Código Sugerido | Complexidade | Pts | Prioridade | Sprint |
|---|----------------|-------|-----------------|:---:|:---:|:---:|:---:|
| 17 | Versionamento de Question Sets | 3 | WSI-007 | 🟠 Alta | 8 | P1 | S2 |
| 18 | Normalização Scores Cross-Version | 3 | WSI-008 | 🟠 Alta | 8 | P2 | S3 |
| 19 | Cutoffs e Decisões Automatizadas | 3/7 | WSI-009 | 🟡 Média | 5 | P1 | S2 |
| 20 | Saturação Inteligente de Pipeline | 7 | WSI-010 | 🟡 Média | 5 | P2 | S3 |
| 21 | Governança Humana (GovernanceRules) | 3 | WSI-011 | 🟠 Alta | 8 | P1 | S2 |
| 22 | Templates Hardcoded WSI | 3 | WSI-012 | 🟡 Média | 5 | P1 | S2 |
| 23 | Ações Afirmativas WSI | 3 | WSI-013 | 🟢 Baixa | 3 | P3 | Pós-MVP |
| 24 | Calibração Contextual Senioridade | 3 | WSI-014 | 🟠 Alta | 8 | P1 | S2 |
| 25 | Multi-Signal Seniority Resolution | 3 | WSI-015 | 🔴 Muito Alta | 13 | P1 | S2 |
| 26 | Triagem por Voz (OpenMic) | 7 | WSI-016 | 🔴 Muito Alta | 13 | P3 | Pós-MVP |
| | | | | **Subtotal WSI** | **76** | | |
| | | | | **Total geral a criar** | **137** | | |

> **Recomendação P1:** Criar WSI-007, WSI-009, WSI-011, WSI-012, WSI-014 e WSI-015 (+47 pts) para o Alpha 1. WSI-014 e WSI-015 já têm código implementado — cards são para tracking.

---

### 2.2.4 Contagem de Cards por Etapa

> **Nota sobre duplicatas:** O quadro abaixo diz "111" na coluna Exist., mas esse total conta duplicatas — o mesmo card aparece em mais de uma etapa (ex: GAT-004 aparece tanto no Gate 1, Gate 2 quanto no Feedback; SCO-005/006 aparecem em Pós-Triagem e Gate 2). **Cards únicos = 101.** Para a análise comparativa com o MVP completo do Jira (141 cards), ver seção [4.1](#41-lista-de-itens-excluídos).

| Etapa | Exist. | Novos | Total | Pts | Agentes | Cards Existentes (Código — É/S) | Cards Novos (Código — É/S) |
|-------|:---:|:---:|:---:|:---:|:---:|------|------|
| 1. Login | 4 | 0 | 4 | 15 | — | VAG-001·002·007·008 (É11/S1) | — |
| 2. Editar Vaga | 4 | 0 | 4 | 21 | Ag.8 | WIZ-008 (É4/S2), VAG-003·004 (É11/S1), NOT-007 (É10/Pós) | — |
| 3. Roteiro WSI | 7 | 0 | 7 | 47 | Ag.4, JD Service | WSI-001·002·003·005·006 (É4/S2), WIZ-012·013 (É4/S2) | — *(ver Disclaimer: WSI-007~016)* |
| 4. Buscar Cand. | 17 | 0 | 17 | 98 | Ag.2, Ag.3, Ag.5 | MAP-001~013 (É3/S1-S2), AGT-002 (É15/S3), INT-APY-001~003 (É14/S3) | — |
| 5. Gate 1 | 19 | 1 | 20 | 96 | Ag.7, Ag.8 | GAT-001·003~007 (É7/S3), KAN-001~004·006~008·011 (É11/S1), TAB-001~005 (É11/S1) | KAN-005 (É11/S2) |
| 6. Contato Email | 8 | 1 | 9 | 44 | Ag.0, Ag.10 | TPL-001·005~007 (É8/S2), TRI-002·009·010 (É5/S2), NOT-001 (É10/S3) | TPL-009 (É8/S2) |
| 6B. Follow-up | 1 | 2 | 3 | 16 | Ag.9, Ag.10 | TRI-007 (É5/S2) | FLW-001 (É5/S2), FLW-002 (É5/S2) |
| 7. Triagem WSI | 14 | 2 | 16 | 134 | Ag.4, Ag.5 | TRI-001·003~006·008·013 (É5/S2), SCO-001~004 (É6/S3), AGT-001·004 (É15/S3), TRI-012 (É15/S3) | PUB-001 (É5/S2), PUB-002 (É5/S2) |
| 7A. Abandonada | 1 | 3 | 4 | 21 | Ag.9, Ag.10 | TRI-007 (É5/S2) | TRI-015 (É5/S3), TRI-016 (É5/S3), TRI-017 (É5/S3) |
| 7B. Pós-Triagem | 3 | 1 | 4 | 21 | Ag.4, Ag.5, Ag.10 | SCO-005·006 (É6/S3), NOT-007 (É10/Pós) | TPL-010 (É8/S3) |
| 8. Gate 2 | 14 | 0 | 14 | 79 | Ag.5, Ag.7, Ag.8 | GAT-002~005·008 (É7/S3), PRV-001~005 (É11/S1), SCO-005~008 (É6/S3) | — |
| 9A. Agendamento | 15 | 0 | 15 | 79 | Ag.6, Ag.9, Ag.10 | AGE-001~008 (É9/S2), AGT-003 (É15/S3), TPL-002·003 (É8/S2), INT-MSG-002~004·006 (É14/S2) | — |
| 9B. Feedback | 4 | 0 | 4 | 21 | Ag.7, Ag.8, Ag.10 | GAT-004·005 (É7/S3), TPL-004 (É8/S2), NOT-001 (É10/S3) | — |
| **TOTAL** | **111** | **10** | **121** | **592** | **11 agentes** | | |

> **Legenda:** É = Épico, S = Sprint, Pós = Pós-MVP. Notação `XXX-001·002·003` = cards XXX-001, XXX-002 e XXX-003 agrupados. Notação `XXX-001~005` = cards XXX-001 a XXX-005 (sequência contínua).
>
> **Nota:** Etapa 3 possui adicionalmente 10 cards WSI sugeridos (WSI-007 a WSI-016, +76 pts) detalhados no Disclaimer da Etapa 3. Se aprovados os 6 cards P1 (+47 pts), o total sobe para **127 cards / 639 pts**. Se aprovados todos os 10 (+76 pts), o total sobe para **131 cards / 668 pts**.

**Legenda de Complexidade:**
- 🟢 Baixa (1-3 pts) — Tarefas simples, componentes UI isolados
- 🟡 Média (5 pts) — Integração moderada, CRUD, hooks
- 🟠 Alta (8 pts) — Lógica complexa, múltiplas dependências
- 🔴 Muito Alta (13+ pts) — Core system, integrações externas, AI pipelines

---

### 2.2.5 Pré-requisitos IA por Semana

> O mapa completo de cards IA organizados por semana, com dependências e sequência de execução, está consolidado na seção [2.8.2 — Roadmap por Semana](#282--roadmap-por-semana--o-que-trabalhar-em-cada-semana). Consulte essa seção para o inventário detalhado.

---

### 2.2.6 Resumo de Alertas por Canal

**📬 Teams → Consultor (8 alertas):**
1. Vaga importada do ATS
2. Candidatos mapeados para vaga
3. Bypass Gate 1 (inscrição via web)
4. Sem resposta após 7 dias de follow-up
5. Triagem abandonada (após 2 lembretes sem retorno)
6. Triagem concluída (score + ações rápidas Adaptive Card)
7. Entrevista agendada (ou falha no agendamento)
8. Feedback de reprovação enviado

**✉️ Email → Candidato (6 tipos):**
1. Contato inicial (convite triagem com link chat web + opção WhatsApp)
2. Follow-up diário (re-envio até 7 dias se não abriu/clicou)
3. Lembrete triagem incompleta (timeout 48h)
4. Feedback reprovação Gate 1
5. Agendamento de entrevista (data/hora + link)
6. Feedback reprovação Gate 2

**🔔 Bell in-app → Consultor:** Espelho de todos os eventos Teams + email enviado + decisões registradas

**Template Teams (Adaptive Card) — Triagem Concluída:**
```
📋 Vaga: {job_title} (ID: {vacancy_id})
👤 Candidato: {candidate_name}
📊 Score WSI: {score}/5 | {tier_emoji} Tier: {tier}
✅ Confiança: {confidence}%
💡 Recomendação: {tier_recommendation}
[Ver Detalhes] [Aprovar] [Reprovar]
```

**Card existente:** NOT-007 (Notificações via Microsoft Teams)
**Infraestrutura:** `teams_service.py:send_adaptive_card()` — já implementado

### 2.3 Itens Temporariamente Excluídos do Alpha 1

O quadro consolidado abaixo lista todos os itens excluídos do cenário Alpha 1: **41 cards** removidos do Jira MVP (Sprints 1-3) e **8 itens estratégicos** excluídos por decisão de escopo. Todos são importantes para versões futuras — a coluna "Retorno" indica em qual fase cada item deve ser reincorporado.

#### 2.3.1 Lista Consolidada de Itens Excluídos

O MVP original do documento `lia-mvp-cards-jira.md` contém **141 cards** distribuídos em 3 sprints. O cenário Alpha 2.2.4 utiliza **101 cards únicos** na coluna "Exist.", representando uma **redução de 41 cards (29,1%)**. Além disso, **1 card pós-MVP foi promovido** (NOT-007), resultando em uma redução líquida de **40 cards** (de 141 para 101). A esta lista somam-se **8 itens estratégicos** excluídos por decisão de escopo.

| # | Card/Ref | Nome | Categoria | Motivo da Exclusão | Retorno |
|---|----------|------|:---------:|--------------------|---------:|
| | | **AUTENTICAÇÃO — É1 (6 cards)** | | | |
| 1 | AUTH-001 | Tela de Login | É1 | Login simplificado (email/senha direto) | Alpha 2 |
| 2 | AUTH-002 | Integração WorkOS SSO | É1 | SSO excluído do Alpha | Alpha 2 |
| 3 | AUTH-003 | Middleware JWT | É1 | Auth simplificada | Alpha 2 |
| 4 | AUTH-004 | Sessão e Refresh Token | É1 | Auth simplificada | Alpha 2 |
| 5 | AUTH-005 | Wildcard SSL + Multi-Brand | É1 | Infraestrutura não priorizada | Alpha 2 |
| 6 | AUTH-006 | Revisão Design Lucas | É1 | Design não priorizado | Alpha 2 |
| | | **INTEGRAÇÕES — É14: WorkOS (7 cards)** | | | |
| 7 | INT-WOS-001 | Configurar WorkOS Account | É14 | WorkOS excluído | Alpha 2 |
| 8 | INT-WOS-002 | SSO SAML/OIDC | É14 | WorkOS excluído | Alpha 2 |
| 9 | INT-WOS-003 | Directory Sync SCIM | É14 | WorkOS excluído | Alpha 2 |
| 10 | INT-WOS-004 | MFA Enforcement | É14 | WorkOS excluído | Alpha 2 |
| 11 | INT-WOS-005 | User Management SDK | É14 | WorkOS excluído | Alpha 2 |
| 12 | INT-WOS-006 | Webhook de Eventos | É14 | WorkOS excluído | Alpha 2 |
| 13 | INT-WOS-007 | Admin Portal | É14 | WorkOS excluído | Alpha 2 |
| | | **INTEGRAÇÕES — É14: Twilio (7 cards)** | | | |
| 14 | INT-TWI-001 | Configurar Twilio Account | É14 | Twilio excluído (possível Gupshup) | Alpha 1 |
| 15 | INT-TWI-002 | Sandbox WhatsApp | É14 | Twilio excluído | Alpha 1 |
| 16 | INT-TWI-003 | Número de Produção | É14 | Twilio excluído | Alpha 1 |
| 17 | INT-TWI-004 | Webhook de Mensagens | É14 | Twilio excluído | Alpha 1 |
| 18 | INT-TWI-005 | Templates Aprovados Meta | É14 | Twilio excluído | Alpha 1 |
| 19 | INT-TWI-006 | Status Delivery Reports | É14 | Twilio excluído | Alpha 1 |
| 20 | INT-TWI-007 | Rate Limiting e Filas | É14 | Twilio excluído | Alpha 1 |
| | | **INTEGRAÇÕES — É14: Infra LLM (6 cards)** | | | |
| 21 | INT-LLM-002 | Cliente Google Gemini | É14 | Infra LLM simplificada | Alpha 2 |
| 22 | INT-LLM-005 | Gestão de Prompts (Versioning) | É14 | Infra LLM simplificada | Alpha 2 |
| 23 | INT-LLM-006 | Cache de Respostas LLM | É14 | Infra LLM simplificada | Alpha 2 |
| 24 | INT-LLM-007 | Monitoramento de Custos | É14 | Infra LLM simplificada | Alpha 2 |
| 25 | INT-LLM-008 | Rate Limiting LLM | É14 | Infra LLM simplificada | Alpha 2 |
| 26 | INT-LLM-009 | Logging de Conversas | É14 | Infra LLM simplificada | Alpha 2 |
| | | **KANBAN / VAGAS — É11 (6 cards)** | | | |
| 27 | KAN-009 | Componentes Kanban Modulares | É15 | Refatoração não essencial | Alpha 2 |
| 28 | KAN-010 | Feedback Implícito em Transições | É11 | Feature avançada | Alpha 2 |
| 29 | KAN-012 | Solicitar Novos Candidatos Refinados | É11 | Feature avançada | Alpha 2 |
| 30 | KAN-013 | Buscar Candidatos Similares | É11 | Feature avançada AI | Alpha 2 |
| 31 | VAG-005 | Duplicar Vaga | É11 | No Alpha vagas vêm do ATS | Alpha 2 |
| 32 | VAG-006 | Arquivar Vaga | É11 | No Alpha vagas vêm do ATS | Alpha 2 |
| | | **NOTIFICAÇÕES — É10 (5 de 6 cards)** | | | |
| 33 | NOT-002 | Notificações Tempo Real (WebSocket) | É10 | Simplificado no Alpha | Alpha 2 |
| 34 | NOT-003 | Preferências de Notificação | É10 | Simplificado no Alpha | Alpha 2 |
| 35 | NOT-004 | Notificações Push (PWA) | É10 | PWA não priorizado | Alpha 2 |
| 36 | NOT-005 | Histórico de Notificações | É10 | Simplificado no Alpha | Alpha 2 |
| 37 | NOT-006 | Badge de Não Lidas | É10 | Simplificado no Alpha | Alpha 2 |
| | | **AGENTES AVANÇADOS — É15 (2 cards)** | | | |
| 38 | DAT-001 | Sistema de Solicitação de Dados | É15 | Feature avançada | Alpha 2 |
| 39 | ENT-001 | Análise de Transcrição Entrevista | É15 | Feature avançada | Alpha 2 |
| | | **TRIAGEM / TEMPLATES — É5/É8 (2 cards)** | | | |
| 40 | TRI-014 | Pesquisa Alternativas Twilio | É5 | Pesquisa já feita/dispensável | — |
| 41 | TPL-008 | Sync Templates WhatsApp com Meta | É8 | Depende de Twilio/provider | Alpha 1 |
| | | **ITENS ESTRATÉGICOS EXCLUÍDOS (8 itens)** | | | |
| 42 | INT-005 | Plugin ATS (WeDo como plugin via Merge) | É14 | Integração ATS não priorizada (21 pts) | Alpha 1 |
| 43 | IMP-001 | Importação Inteligente (CSV/Excel/PDF) | — | Smart Import adiado (8 pts) | Alpha 1 |
| 44 | 58 cards | Configurações Admin (Settings Menu) | É13 | Toda área admin excluída (58 cards) | Alpha 2 |
| 45 | INT-001 | Billing/Stripe | É14 | Teste interno, sem cobrança (13 pts) | Alpha 2 |
| 46 | CFG-005 | Dados da Empresa para LIA | É13 | LIA usa contexto do JD (8 pts) | Alpha 2 |
| 47 | CFG-004 | Hub de Comunicação Multi-canal | É13 | Templates pré-configurados (13 pts) | Alpha 2 |
| 48 | CFG-003 | Configuração de Pipeline Customizado | É13 | Pipeline fixo padrão (8 pts) | Alpha 2 |
| 49 | AGT (Ag.8) | Agente IntegradorATS | É15 | Ponte automática com ATS adiada (13 pts) | Alpha 1 |

**Resumo consolidado:**

| Categoria | Cards | % do MVP Jira |
|-----------|:-----:|:-------------:|
| É14: Integrações — WorkOS (7) + Twilio (7) + LLM (6) | 20 | 14,2% |
| É1: Autenticação (épico inteiro) | 6 | 4,3% |
| É11: Kanban/Vagas avançados | 6 | 4,3% |
| É10: Notificações (5 de 6 cards) | 5 | 3,5% |
| É15: Agentes avançados | 2 | 1,4% |
| É5/É8: Triagem/Templates periféricos | 2 | 1,4% |
| **Subtotal — cards do Jira MVP removidos** | **41** | **29,1%** |
| Itens estratégicos adicionais (fora do Jira MVP) | 8 | — |
| **TOTAL EXCLUÍDOS DO ALPHA** | **49** | — |

> **Card promovido do pós-MVP:** NOT-007 (Notificações via Microsoft Teams), marcado como pós-MVP no Jira, foi promovido para o cenário Alpha por ser necessário nas etapas "Editar Vaga" e "Pós-Triagem". Resultado líquido dos cards Jira: **–40** (de 141 para 101 únicos).
>
> **Onde está o maior corte?** Integrações com providers externos (20 cards = quase metade da redução). No Alpha, o login é simplificado (email/senha direto), WorkOS/SSO é adiado, Twilio é substituído por alternativa mais leve, e a infraestrutura LLM é enxugada. O segundo maior bloco é a autenticação corporativa (6 cards), desnecessária para o teste interno Alpha 1.

#### 2.3.2 Detalhes dos Itens Excluídos

**Item 1: Plugin ATS (INT-005)**
- Integração ATS unificada via Merge (Gupy, Pandapé, Lever, Greenhouse)
- 21 pontos, Sprint 5, essencial para Alpha 1
- Backend já preparado: `lia-agent-system/app/services/ats_clients/` (base, gupy, pandape, stackone, merge)
- Documentação: `docs/MERGE_INTEGRATION_FIELDS_REFERENCE.md`

**Item 2: Importação Inteligente (IMP-001)**
- Smart Import Zone que detecta tipo de arquivo e extrai dados estruturados
- Suporta CSV, Excel, PDF
- Preview antes de importar com mapeamento de campos
- Arquivos base: `jd_import_service.py`, `cv_parser.py`, `template_importer_service.py`, `cv-upload-modal.tsx`

**Item 3: Configurações Admin (58 cards)**
- Documento completo: `docs/configuracoes-admin-cards-jira.md`
- Epics: Setup Institucional, Screening Config, Pipeline & Triagem, Candidatos, Comunicação, etc.
- Inclui: dados da empresa, billing, CRM, integrações, permissões, templates

**Item 4: Billing/Stripe (INT-001)**
- Integração Stripe para assinaturas, faturas, Customer Portal
- ProfitWell (gratuito, nativo Stripe) para métricas SaaS (MRR, Churn, LTV)
- Webhooks: subscription.created/updated/deleted, invoice.paid/failed
- Secrets: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`

**Item 5: Dados da Empresa para LIA (CFG-005)**
- Cadastrar informações da empresa para contextualizar comunicações da LIA
- Campos: valores, cultura, benefícios, tom de voz
- Arquivos: `company_configuration_service.py`, `culture_analyzer_service.py`, `company_scraper_service.py`

**Item 6: Hub de Comunicação (CFG-004)**
- Hub centralizado para templates de email, WhatsApp, notificações, assinaturas e canais
- Layout: Tabs por categoria, lista de templates, editor rich text, preview panel

**Item 7: Pipeline Customizado (CFG-003)**
- Editor de etapas da jornada de recrutamento
- Stage editor, drag-and-drop para reordenar, automation toggles
- Arquivos: `recruitment-stages.ts`, `use-recruitment-stages.ts`, `pipeline_service.py`

**Item 8: Agente IntegradorATS (Ag.8)**
- Agente IA que automatiza a ponte entre WeDo e o ATS do cliente
- Sync automático de dados, tratamento de conflitos, mapeamento inteligente
- Prompt: `ATS_INTEGRATOR_PROMPT`

### 2.4 Restrições Conhecidas no Alpha 1

| # | Restrição | Motivo | Workaround |
|---|-----------|--------|------------|
| 1 | Não cria vagas na WeDo | Vagas vêm do ATS integrado | Editar vagas importadas |
| 2 | Sem SSO/MFA | WorkOS não priorizado para Alpha 1 | Login email/senha |
| 3 | Sem configurações admin | 58 cards excluídos | Configurações pré-definidas |
| 4 | Sem billing/Stripe | Teste interno, sem cobrança | N/A |
| 5 | Sem pipeline customizado | Pipeline fixo padrão | Usar pipeline default |
| 6 | Sem dados empresa para LIA | CFG-005 excluído | LIA usa contexto do JD |
| 7 | Sem hub de comunicação | CFG-004 excluído | Templates pré-configurados |

### 2.5 Estratégia de Contato — Diagrama de Decisão

```
                    ┌───────────────────────┐
                    │ Candidato aprovado     │
                    │ no Gate 1              │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ LIA envia EMAIL       │
                    │ (contato primário)    │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐
        │ Candidato clica   │   │ Candidato fornece │
        │ link do email     │   │ nº celular        │
        └─────────┬─────────┘   └─────────┬─────────┘
                  │                       │
                  ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐
        │ TRIAGEM WSI       │   │ TRIAGEM WSI       │
        │ via CHAT WEB      │   │ via WHATSAPP      │
        └─────────┬─────────┘   └─────────┬─────────┘
                  │                       │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Score WSI calculado   │
                  │ → Gate 2              │
                  └───────────────────────┘
```

### 2.6 Fluxo Especial: Candidato Inscrito via Web

```
        ┌───────────────────────┐
        │ Candidato se inscreve │
        │ via link web          │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ BYPASS Gate 1         │
        │ (triagem automática)  │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ TRIAGEM WSI           │
        │ via CHAT WEB          │
        │ (direto no momento    │
        │  da inscrição)        │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Score WSI calculado   │
        │ → Gate 2              │
        └───────────────────────┘
```

### 2.7 Critérios de Sucesso do Alpha 1

#### Métricas Quantitativas

| # | Métrica | Meta | Como Medir | Frequência |
|---|---------|:----:|------------|:----------:|
| Q1 | Taxa de conclusão da triagem WSI | >70% dos candidatos contatados | (Triagens concluídas / Candidatos que receberam email) × 100 | Semanal |
| Q2 | Tempo médio de triagem via chat web | <25 minutos | Timestamp início → conclusão da sessão de triagem | Por triagem |
| Q3 | Taxa de abertura de email de contato | >50% | Mailgun webhooks (open tracking) | Diária |
| Q4 | Taxa de resposta/engajamento do candidato | >40% | (Candidatos que iniciaram triagem / Emails enviados) × 100 | Semanal |
| Q5 | Score WSI calculado sem erros | 100% accuracy | Validação manual de amostra (20+ triagens) por consultores | Ao final do Alpha |
| Q6 | Tempo médio entre importação da vaga e primeiro contato | <48h | Timestamp import ATS → primeiro email enviado | Por vaga |
| Q7 | Alertas Teams entregues e visualizados | >95% | Delivery receipts + read receipts via Microsoft Graph | Semanal |
| Q8 | Taxa de triagens abandonadas recuperadas via lembrete | >30% | (Triagens retomadas após lembrete / Total de triagens abandonadas) × 100 | Semanal |

#### Métricas Qualitativas

| # | Métrica | Meta | Método de Avaliação |
|---|---------|------|---------------------|
| L1 | Consultores completam fluxo completo (etapas 1-9) sem suporte técnico | 100% dos consultores | Observação direta + registro de tickets de suporte |
| L2 | Feedback dos consultores sobre UX da plataforma | NPS >7 | Questionário NPS aplicado ao final do Alpha 1 |
| L3 | Qualidade do parecer WSI gerado pela LIA | Avaliação ≥4/5 pelos consultores | Consultores avaliam amostra de pareceres (escala 1-5) |
| L4 | Qualidade do feedback enviado a candidatos reprovados | Feedback construtivo e profissional | Revisão manual de 100% dos feedbacks enviados |
| L5 | Relevância das perguntas WSI geradas automaticamente | ≥80% das perguntas consideradas relevantes | Consultores marcam perguntas como "relevante" ou "irrelevante" |

#### Critérios de Go/No-Go para Alpha 2

**✅ Critérios de GO (todos devem ser atendidos):**

| # | Critério | Threshold Mínimo |
|---|----------|:----------------:|
| G1 | Taxa de conclusão de triagem WSI | ≥70% |
| G2 | Score WSI calculado sem erros críticos | 100% |
| G3 | Consultores completam fluxo sem suporte técnico | 100% |
| G4 | NPS dos consultores sobre UX | ≥7 |
| G5 | Alertas Teams entregues | ≥95% |
| G6 | Tempo médio de triagem via chat web | ≤25 min |
| G7 | Zero falhas críticas de segurança ou perda de dados | 0 incidentes |
| G8 | Integração ATS (Merge) estável por 7+ dias consecutivos | 99.5% uptime |

**🚫 Critérios de NO-GO (qualquer um bloqueia avanço):**

| # | Critério | Gatilho | Plano de Remediação |
|---|----------|---------|---------------------|
| N1 | Taxa de conclusão de triagem WSI abaixo do mínimo | <50% | Revisar UX do chat web, simplificar perguntas, adicionar indicadores de progresso |
| N2 | Erros no cálculo do Score WSI | Qualquer erro detectado | Corrigir algoritmo, adicionar testes automatizados, re-validar amostra completa |
| N3 | Consultores não conseguem completar fluxo | >1 consultor bloqueado | Identificar etapa problemática, corrigir UX, criar documentação de apoio |
| N4 | NPS dos consultores abaixo do mínimo | <5 | Sprint de melhorias de UX baseado no feedback coletado |
| N5 | Falha crítica de segurança | Qualquer incidente | Pausar Alpha, corrigir vulnerabilidade, audit de segurança completo |
| N6 | Perda de dados de candidatos ou triagens | Qualquer incidente | Restaurar dados, corrigir causa raiz, implementar backup incremental |
| N7 | Integração ATS instável | Uptime <95% em 7 dias | Investigar falhas Merge, implementar circuit breaker, fallback manual |
| N8 | Emails de contato com taxa de entrega <80% | <80% delivery rate | Revisar configuração Mailgun, SPF/DKIM, domínio de envio |

**Processo de decisão:**
1. Ao final do Alpha 1, compilar relatório com todas as métricas
2. Reunião de Go/No-Go com stakeholders (Product, Tech, Consultoria)
3. Se todos os critérios GO forem atendidos e nenhum NO-GO disparado → **Avançar para Alpha 2**
4. Se algum NO-GO for disparado → **Executar plano de remediação** e re-avaliar em 1 semana

---

---

### 2.8 ⚡ CARDS A IMPLEMENTAR — Inventário Completo para MVP Alpha 1 e Fases Seguintes

> ### 🚀 ESCOPO COMPLETO DE TRABALHO — 3 SEMANAS
>
> Esta seção consolida **todos os cards Jira que o time precisa implementar** para entregar o MVP Alpha 1 em **3 semanas** (168 cards, ~56 cards/semana). É o mapa completo de trabalho, reunindo 4 documentos fonte:
>
> | Documento Fonte | Escopo |
> |----------------|--------|
> | `lia-mvp-cards-jira.md` | Cards de Produto (WIZ, KAN, GAT, NOT) |
> | `pipeline-transition-cards-jira.md` | Cards de Pipeline (PIP) |
> | `lia-ai-architecture-cards-jira.md` | Cards de IA/Agentes (PREP, AGT, INF, SRV, INT-AI, AUT, TRV) |
> | `lia-mvp-cards-jira-v2.md` | Cards de Configuração de Vaga e Triagem (CFG) |
>
> ⚠️ **ATENÇÃO — CARDS DE CONFIGURAÇÃO (CFG-001 A CFG-012) FORA DO PLANEJAMENTO ATUAL:** O DOCUMENTO `lia-mvp-cards-jira-v2.md` CONTÉM **12 CARDS** (68 PONTOS) RELATIVOS À EDIÇÃO DA VAGA (CONFIGURAÇÕES COMO TAB), ATUALIZAÇÕES NO PREVIEW DA VAGA NA TABELA DE VAGAS E AJUSTES NO MENU CONFIGURAÇÕES. ESTES CARDS **PRECISAM SER IMPLEMENTADOS O MAIS BREVE POSSÍVEL**, MAS **NÃO ESTÃO INCLUÍDOS NO PLANEJAMENTO DESTA SESSÃO** (3 SEMANAS / 168 CARDS). ESTE É UM DISCLAIMER INFORMATIVO — O PLANEJAMENTO DE SPRINTS PARA ESTES 12 CARDS SERÁ DEFINIDO SEPARADAMENTE.
>
> **Para que serve:** Qualquer membro do time pode consultar esta seção para saber rapidamente:
> - **Quantos cards faltam** por categoria e por semana
> - **Quais são as dependências** e a ordem de execução (caminho crítico)
> - **Qual a proporção de esforço** entre produto, pipeline e IA
> - **O que fica para depois** do Alpha 1 (fases Alpha 2+)
>
> **Resumo rápido:** Alpha 1 = **168 cards / 1.064 pontos em 3 semanas** (63 🏗️IA / 478 pts + 10 🔀PIP / 62 pts + 95 🖥️Produto / 524 pts) | Alpha 2+ = **58 cards / 369 pontos** | Total = **226 cards / 1.433 pontos**
>
> **Distribuição semanal:**
> | Semana | Foco | Cards | Pontos |
> |:------:|------|:-----:|:------:|
> | **Sem 1** | Produto + Pipeline (UI completa, épicos inteiros) | 105 | 586 |
> | **Sem 2** | IA Core (PREP + INF + SRV core + AGT core) — muito reaproveitamento do protótipo | 40 | 315 |
> | **Sem 3** | IA Complementar (AGT restantes + integrações + automações + calibração) | 23 | 163 |
>
> **Acelerador:** 94% dos cards IA (🟢+🔧) têm código ou lógica de referência no protótipo Replit. Nenhum card parte do zero.

---

#### 2.8.1 🔗 MAPA DE DEPENDÊNCIAS — O QUE VEM ANTES DO QUÊ

> Este mapa mostra a **ordem de execução** dos grupos de cards. Setas sólidas (→) indicam dependência técnica obrigatória. Setas tracejadas (⇢) indicam que o time de UI pode começar assim que os contratos/APIs estiverem definidos.
>
> 🔗 **Versão visual interativa (FigJam):** [Abrir Diagrama de Dependências](https://www.figma.com/online-whiteboard/create-diagram/1cda92a4-4616-4b7d-8a9b-5d0db9ed649d?utm_source=other&utm_content=edit_in_figjam)

---

##### Caminho Crítico — Visão Geral (3 Semanas)

```
SEMANA 1 (Produto + PIP)          SEMANA 2 (IA Core)           SEMANA 3 (IA Complementar)
───────────────────────           ──────────────────           ─────────────────────────

 95 🖥️Produto (É1–É9B)            PREP (14 cards)              AGT-003,008,009,010,011
   │                                │                            (5 agentes restantes)
   ├── É1 VAG (4)                   ├──→ INF (8 cards)                │
   ├── É2 WIZ (3)                   │       │                        └──→ AUT (6 automações)
   ├── É3 WSI (7)                   │       └──→ SRV-001 (LLM)
   ├── É4 MAP (16)                  │              │              SRV-010,013,014,016
   ├── É5 KAN+TAB+PRV (18)         │              └──→ INT-AI-001  (4 serviços integração)
   ├── É5 GAT (6)                   │                                 │
   ├── É6 TPL+TRI (9)              ├──→ SRV-002~009,011,012       INT-AI-002~005,007
   ├── É6B (1)                      │   (11 serviços core)          (5 integrações externas)
   ├── É7 TRI (7)                   │
   ├── É7B SCO (8)                  ├──→ AGT-000 Orchestrator      TRV-003~005
   ├── É8 GAT (2)                   │       │                      (3 calibração WSI)
   ├── É9A AGE (14)                 │       └──→ AGT-001,002,004
   └── É9B TPL (1)                  │            006,007 (6 core)
                                    │
 10 🔀PIP (PIP-001~010)            └──→ TRV-001 (LGPD)
   ├── PIP-001/002 (base)
   ├── PIP-008/009 (API)
   └── PIP-003~007,010 (UI)
```

---

##### Trilha IA/Backend — Sequência (Semanas 2-3)

> ⚡ **Acelerador protótipo:** 94% dos cards IA têm código/lógica do protótipo Replit. PREP e INF são 100% portáveis (Python→Python). Isso permite comprimir em 2 semanas o que normalmente levaria 8+.

```
SEMANA 2 — IA CORE (40 cards / 315 pts)
────────────────────────────────────────────────────────────────────

┌──────────┐     ┌───────────────┐     ┌──────────────┐
│ PREP     │     │ INF-001~005   │     │ SRV-001      │
│ 14 cards │────→│ 008, 012, 014 │────→│ LLM Service  │
│ 71 pts   │     │ 8 cards/56pts │     │ 8 pts        │
│ 🟢100%   │     │ 🟢75% 🔧25%  │     │ 🟢           │
└──────────┘     └───────────────┘     └──────┬───────┘
                                              │
                       ┌──────────────────────┤
                       │                      │
                       ▼                      ▼
                ┌──────────────┐       ┌──────────────┐
                │ INT-AI-001   │       │ AGT-000      │
                │ Gemini API   │       │ Orchestrator │
                │ 8 pts 🔧     │       │ 13 pts 🟢    │
                └──────────────┘       └──────┬───────┘
                                              │
                  ┌───────────────────────────┤
                  │                           │
                  ▼                           ▼
           ┌──────────────┐           ┌───────────┐
           │ SRV-002~009  │           │ AGT-001   │
           │ SRV-011, 012 │           │ 002, 004  │
           │ 11 serviços  │           │ 006, 007  │
           │ 102 pts      │           │ 6 agentes │
           │ 🟢73% 🔧27%  │           │ 55 pts    │
           └──────────────┘           │ 🟢100%    │
                                      └───────────┘
            TRV-001 LGPD (8 pts 🔧 — paralelo com PREP)

SEMANA 3 — IA COMPLEMENTAR (23 cards / 163 pts)
────────────────────────────────────────────────────────────────────

┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ AGT-003, 008  │  │ SRV-010, 013  │  │ INT-AI-002    │
│ 009, 010, 011 │  │ 014, 016      │  │ 003, 004      │
│ 5 agentes     │  │ 4 serviços    │  │ 005, 007      │
│ 40 pts        │  │ 23 pts        │  │ 5 integrações │
│ 🟢60% 🔧40%   │  │ 🔧100%        │  │ 47 pts        │
└──────┬────────┘  └───────────────┘  │ 🔧60% 🆕40%   │
       │                              └───────────────┘
       ▼
┌───────────────┐  ┌───────────────┐
│ AUT-001~006   │  │ TRV-003~005   │
│ 6 automações  │  │ 3 calibração  │
│ 33 pts        │  │ 29 pts        │
│ 🟢33% 🔧67%   │  │ 🟢100%        │
└───────────────┘  └───────────────┘
```

---

##### Trilha UI/Produto — Semana 1 (independente de IA)

> ⚡ **Cards de Produto e Pipeline não dependem de IA.** O time de UI/frontend entrega todas as 95 telas + 10 cards de pipeline na Semana 1, enquanto a IA inicia na Semana 2. As integrações IA são conectadas posteriormente via APIs/contratos.

```
SEMANA 1 — PRODUTO + PIPELINE (105 cards / 586 pts)
────────────────────────────────────────────────────────────────────

┌──────────────────┐
│ É1: Vagas (VAG)  │
│ 4 cards | 15 pts │
└───────┬──────────┘
        │
   ┌────┼────────┐
   │    │        │
   ▼    ▼        ▼
┌────┐┌────┐┌────────┐   ┌────────────────┐
│É2  ││É4  ││ É5     │   │ PIP-001~010    │
│VAG ││MAP ││KAN+TAB │   │ Pipeline       │
│+WIZ││16  ││+PRV    │   │ 10 cards/62 pts│
│3c  ││card││18 cards│   └────────────────┘
│16pt││90pt││80 pts  │
└────┘└────┘└────────┘
                          ┌────────────────┐     ┌────────────────┐
                          │ É3: WSI        │     │ É5: Gate 1     │
                          │ Roteiro WSI    │     │ GAT-001~007    │
                          │ 7 cards/47 pts │     │ 6 cards/34 pts │
                          └───────┬────────┘     └───────┬────────┘
                                  │                      │
                                  ▼                      ▼
                          ┌────────────────┐     ┌────────────────┐
                          │ É6: Email      │     │ É8: Gate 2     │
                          │ TPL + TRI      │     │ GAT-002/008    │
                          │ 9 cards/46 pts │     │ 2 cards/16 pts │
                          └───────┬────────┘     └───────┬────────┘
                                  │                      │
                                  ▼                      ▼
                          ┌────────────────┐     ┌────────────────┐
                          │ É7: Triagem    │     │ É9: Agendamento│
                          │ WhatsApp       │     │ AGE + INT-MSG  │
                          │ 7 cards/45 pts │     │ 15 cards/74 pts│
                          └───────┬────────┘     └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ É7B/É8:Scoring │
                          │ SCO-001~008    │
                          │ 8 cards/61 pts │
                          └────────────────┘

É6B: Follow-up (1 card/5 pts)
É9B: Feedback (1 card/3 pts)
```

---

##### Dependências Críticas entre Etapas (o que bloqueia o quê)

| Etapa Origem | Etapa Destino | Dependência | Tipo |
|:------------:|:-------------:|-------------|:----:|
| — | Produto (Sem 1) | Cards de Produto e Pipeline são **independentes de IA** — podem começar imediatamente | ✅ Sem bloqueio |
| PREP (Sem 2) | INF, TRV-001 | Contratos base (ABCs) necessários para infra IA | 🔴 Bloqueante |
| INF (Sem 2) | SRV-001, AGT-000 | DomainWorkflow + Router necessários para LLM e orquestrador | 🔴 Bloqueante |
| SRV-001 (Sem 2) | INT-AI-001 | LLM Service deve existir antes de configurar Gemini | 🔴 Bloqueante |
| AGT-000 (Sem 2) | AGT-001~011 | Orquestrador central necessário antes de qualquer agente | 🔴 Bloqueante |
| PIP-001/002 (Sem 1) | PIP-003~010 | Pipeline base necessário antes de modais e UI de transição | 🔴 Bloqueante |
| É6 (Sem 1, Email UI) | É7 (Triagem funcional) | Candidato precisa receber convite antes de iniciar triagem | 🟡 Liberação |
| SRV-002/003 (Sem 2) | É3 (WSI funcional) | API de perguntas WSI conecta com UI de roteiro | 🟡 Integração |
| INT-AI-003 (Sem 3) | É6 (Email funcional) | Integração Mailgun conecta com UI de email | 🟡 Integração |
| AGT-007 + SRV-012 (Sem 2-3) | É7 (Triagem funcional) | Agente entrevistador + WhatsApp conectam com UI de triagem | 🟡 Integração |
| SRV-004 (Sem 2) | É7B/É8 (Scores funcionais) | Motor de scoring conecta com UI de resultados | 🟡 Integração |
| INT-AI-005 (Sem 3) | É9 (Agendamento funcional) | Integração MS Graph conecta com UI de agendamento | 🟡 Integração |

> **Nota:** Na Semana 1, toda a UI é construída com dados mockados/stubs. As integrações IA das Semanas 2-3 substituem os stubs por dados reais via APIs.

---

##### Como Organizar o Time — Recomendação (3 Semanas)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SEMANA 1 — PRODUTO + PIPELINE                │
│                        105 cards | 586 pts                          │
│                                                                     │
│   Squad Frontend/UI (foco principal)  │  Squad Backend/IA (prep)    │
│   ──────────────────────────────────  │  ──────────────────────     │
│   É1 VAG (4 cards, 15 pts)           │  Início PREP em paralelo    │
│   É2 VAG+WIZ (3 cards, 16 pts)      │  (definir contratos/ABCs    │
│   É3 WSI UI (7 cards, 47 pts)       │   para desbloquear Sem 2)   │
│   É4 MAP (16 cards, 90 pts)         │                              │
│   É5 KAN+TAB+PRV (18 cards, 80 pts) │  PIP-001~010 Pipeline       │
│   É5 GAT (6 cards, 34 pts)          │  (10 cards, 62 pts)         │
│   É6 TPL+TRI (9 cards, 46 pts)      │                              │
│   É6B Follow-up (1 card, 5 pts)     │                              │
│   É7 TRI (7 cards, 45 pts)          │                              │
│   É7B+É8 SCO (8 cards, 61 pts)      │                              │
│   É8 GAT (2 cards, 16 pts)          │                              │
│   É9A AGE (14 cards, 71 pts)        │                              │
│   É9B TPL (1 card, 3 pts)           │                              │
├─────────────────────────────────────────────────────────────────────┤
│                 SEMANA 2 — IA CORE (reaproveitamento protótipo)      │
│                 40 cards | 315 pts                                   │
│                                                                     │
│   Squad Backend/IA (foco principal)  │  Squad Frontend/UI           │
│   ──────────────────────────────────  │  ──────────────────────     │
│   PREP-001~014 (14 cards, 71 pts)   │  Conectar APIs IA às UIs    │
│   INF-001~005, 008, 012, 014        │  da Semana 1 (substituir    │
│      (8 cards, 56 pts)              │  stubs por chamadas reais)  │
│   SRV-001~009, 011, 012             │                              │
│      (11 cards, 102 pts)            │  Testes de integração        │
│   INT-AI-001 Gemini (8 pts)         │  front↔back                  │
│   AGT-000, 001, 002, 004, 006, 007  │                              │
│      (6 cards, 68 pts)              │                              │
│   TRV-001 LGPD (8 pts)             │                              │
├─────────────────────────────────────────────────────────────────────┤
│             SEMANA 3 — IA COMPLEMENTAR + INTEGRAÇÕES                │
│             23 cards | 163 pts                                      │
│                                                                     │
│   Squad Backend/IA                   │  Squad Frontend/UI           │
│   ──────────────────────────────────  │  ──────────────────────     │
│   AGT-003, 008, 009, 010, 011       │  Integração final:           │
│      (5 agentes, 40 pts)            │  email, WhatsApp, calendar   │
│   SRV-010, 013, 014, 016            │  conectados às UIs           │
│      (4 serviços, 23 pts)           │                              │
│   INT-AI-002~005, 007               │  Testes E2E do fluxo         │
│      (5 integrações, 47 pts)        │  completo Alpha 1            │
│   AUT-001~006                       │                              │
│      (6 automações, 33 pts)         │                              │
│   TRV-003~005                       │                              │
│      (3 calibração, 29 pts)         │                              │
└─────────────────────────────────────────────────────────────────────┘
```

> **Dica para o time:** Sync diário (15 min) entre squads para alinhar quais APIs/contratos estão prontos. Na Semana 1, o backend define os contratos PREP enquanto o frontend constrói toda a UI. Na Semana 2, as APIs reais substituem os stubs. Na Semana 3, integrações externas completam o fluxo.

---

#### 2.8.2 🗺️ ROADMAP POR SEMANA — O QUE TRABALHAR EM CADA SEMANA

> **Estrutura consolidada em 3 Semanas:** O MVP Alpha 1 é entregue em **3 semanas** com épicos completos por semana. **Semana 1** entrega toda a UI (Produto + Pipeline, independente de IA). **Semana 2** entrega a IA core (com alto reaproveitamento do protótipo). **Semana 3** completa com integrações externas e automações.

---

##### LEGENDA

| Ícone | Tipo | Descrição |
|-------|------|-----------|
| 🏗️ IA | Infraestrutura / Agentes / Serviços IA | Backend, agentes, serviços, integrações IA |
| 🖥️ Produto | UI / UX / Frontend | Telas, componentes, interações do usuário |
| 🔀 PIP | Pipeline / Transições | Sistema de pipeline, modais, transições |

> ⚡ **ESTRATÉGIA:** Produto e Pipeline primeiro (Semana 1) porque são independentes de IA. Cards IA concentrados nas Semanas 2-3 com alto reaproveitamento do protótipo (~94% têm código de referência).

---

##### 🔷 SEMANA 1 — PRODUTO + PIPELINE (105 cards | 586 pts)

**Foco:** Toda a UI do MVP Alpha 1 (épicos completos É1–É9B) + sistema de pipeline completo. Sem dependência de IA.
**Total:** 95 🖥️Produto + 10 🔀PIP = 105 cards | 586 pontos

> ⚡ O time de backend pode iniciar a definição de contratos/ABCs (PREP) em paralelo, preparando o terreno para a Semana 2. A UI é construída com stubs/mocks que serão substituídos por APIs reais nas Semanas 2-3.

---

###### É1 — Login + Dashboard de Vagas

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É1 | VAG-001 | Tabela de Vagas | 🖥️ Produto | 8 | Listagem de vagas com título, status, candidatos |
| É1 | VAG-002 | Tabs de Status | 🖥️ Produto | 3 | Filtros: Ativas, Pausadas, Fechadas |
| É1 | VAG-007 | Contador Candidatos | 🖥️ Produto | 2 | Badge com contagem por etapa |
| É1 | VAG-008 | Navegação Vaga→Kanban | 🖥️ Produto | 2 | Link direto para pipeline da vaga |
| | | **Subtotal É1** | | **15** | **4 🖥️Produto** |

---

###### É2 — Editar Vaga

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É2 | VAG-003 | Menu Ações Vaga | 🖥️ Produto | 5 | Menu: editar, pausar, duplicar, arquivar |
| É2 | VAG-004 | Pausar/Ativar Vaga | 🖥️ Produto | 3 | Pausar/ativar com confirmação |
| É2 | WIZ-008 | Form Edição Completa | 🖥️ Produto | 8 | Formulário completo de edição de vaga via modal |
| | | **Subtotal É2** | | **16** | **3 🖥️Produto** |

---

###### É3 — Roteiro WSI

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É3 | WSI-001 | Motor Geração Perguntas | 🖥️ Produto | 13 | Motor WSI por bloco — core do sistema |
| É3 | WSI-002 | Blocos Metodologia WSI | 🖥️ Produto | 8 | Blocos 2-5: empresa, elegibilidade, técnico, comportamental |
| É3 | WSI-003 | Preview de Perguntas | 🖥️ Produto | 5 | Prévia de perguntas antes de aprovar |
| É3 | WSI-005 | Aprovação Perguntas | 🖥️ Produto | 3 | Aprovar perguntas geradas pela IA |
| É3 | WSI-006 | Edição via Prompt Conversacional | 🖥️ Produto | 8 | Ajustar perguntas em linguagem natural |
| É3 | WIZ-012 | Estágio Perguntas WSI | 🖥️ Produto | 5 | UI para configurar perguntas WSI no modal |
| É3 | WIZ-013 | Quality Gates WSI | 🖥️ Produto | 5 | Validação de qualidade mínima das perguntas |
| | | **Subtotal É3** | | **47** | **7 🖥️Produto** |

---

###### É4 — Mapeamento de Candidatos

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É4 | MAP-001 | Lista Candidatos Base | 🖥️ Produto | 5 | Cards da base de candidatos |
| É4 | MAP-002 | Busca Semântica ES+PGV+WRF | 🖥️ Produto | 13 | Core do search semântico multi-motor |
| É4 | MAP-003 | Filtros Avançados | 🖥️ Produto | 8 | 8 categorias de filtros combináveis |
| É4 | MAP-004 | Adicionar Cand. à Vaga | 🖥️ Produto | 5 | Individual + massa (até 100 candidatos) |
| É4 | MAP-005 | Matching Score IA | 🖥️ Produto | 13 | Score candidato×vaga via IA |
| É4 | MAP-006 | Sugestões Proativas LIA | 🖥️ Produto | 8 | Sugestão automática (score > 75) |
| É4 | MAP-007 | Endpoint Busca Paginada | 🖥️ Produto | 5 | 10 por vez, cursor-based |
| É4 | MAP-008 | Paginação On-Demand | 🖥️ Produto | 3 | Botão "Carregar mais 10" |
| É4 | MAP-009 | Exclusão IDs no ES | 🖥️ Produto | 3 | Exclusão transparente de IDs no ES |
| É4 | MAP-010 | Exclusão IDs no PGV | 🖥️ Produto | 3 | Exclusão transparente de IDs no PGVector |
| É4 | MAP-011 | API Feedback Like/Dislike | 🖥️ Produto | 5 | CRUD + unicidade por busca |
| É4 | MAP-012 | Componente Like/Dislike | 🖥️ Produto | 3 | Toggle thumbs up/down no card |
| É4 | INT-APY-001 | Apify Scraper Config | 🖥️ Produto | 5 | Configuração do scraper Apify |
| É4 | INT-APY-002 | Apify Resultados Parser | 🖥️ Produto | 5 | Parser de resultados do Apify |
| É4 | INT-APY-003 | Ordenação por Score | 🖥️ Produto | 3 | Ordenar candidatos por relevância |
| É4 | INT-APY-004 | Dedup Cross-Source | 🖥️ Produto | 3 | Deduplicação entre fontes |
| | | **Subtotal É4** | | **90** | **16 🖥️Produto** |

---

###### É5 — Pipeline Kanban + Preview

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É5 | KAN-001 | Estrutura Kanban 4 Colunas | 🖥️ Produto | 8 | Funil, Triagem, Entrevista, Reprovados |
| É5 | KAN-002 | Card de Candidato | 🖥️ Produto | 5 | 6 ícones de score com modais |
| É5 | KAN-003 | Drag-and-Drop | 🖥️ Produto | 8 | Mover candidatos entre colunas |
| É5 | KAN-004 | Menu Ações Card | 🖥️ Produto | 5 | Ver perfil, agendar, reprovar, mover |
| É5 | KAN-006 | Badge Score WSI | 🖥️ Produto | 2 | Score no card do candidato |
| É5 | KAN-007 | Filtro por Status | 🖥️ Produto | 3 | Filtro dentro do Kanban |
| É5 | KAN-008 | Busca por Nome | 🖥️ Produto | 3 | Pesquisar candidato por nome |
| É5 | KAN-011 | Triagem em Lote | 🖥️ Produto | 5 | Disparar triagem para múltiplos candidatos |
| É5 | TAB-001 | Tabela Candidatos | 🖥️ Produto | 5 | View tabular alternativa ao Kanban |
| É5 | TAB-002 | Colunas Ordenáveis | 🖥️ Produto | 3 | Ordenar por nome, score, data |
| É5 | TAB-003 | Seleção Múltipla | 🖥️ Produto | 3 | Checkboxes para seleção em massa |
| É5 | TAB-004 | Paginação | 🖥️ Produto | 2 | Paginação da tabela de candidatos |
| É5 | TAB-005 | Ações em Massa/Barra | 🖥️ Produto | 5 | Barra flutuante para candidatos selecionados |
| É5 | PRV-001 | Preview Lateral Cand. | 🖥️ Produto | 5 | Detalhes do candidato em painel lateral |
| É5 | PRV-002 | Tab Perfil | 🖥️ Produto | 5 | Dados básicos, experiência, skills |
| É5 | PRV-003 | Tab Atividades | 🖥️ Produto | 5 | Timeline de interações + eventos ATS |
| É5 | PRV-004 | Tab Arquivos | 🖥️ Produto | 3 | CVs e documentos anexados |
| É5 | PRV-005 | Tab Parecer LIA | 🖥️ Produto | 5 | Análise gerada pela IA no preview |
| | | **Subtotal É5 Kanban** | | **80** | **18 🖥️Produto** |

---

###### É5 — Gate 1: Aprovar Mapeados

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É5 | GAT-001 | Gate 1: Aprovar Mapeados | 🖥️ Produto | 8 | Tela de aprovação de candidatos mapeados |
| É5 | GAT-003 | Feedback Conversacional | 🖥️ Produto | 8 | IA aprende com aprovações/rejeições |
| É5 | GAT-004 | Feedback em Massa | 🖥️ Produto | 5 | Aprovar/rejeitar múltiplos de uma vez |
| É5 | GAT-005 | Motivos de Rejeição | 🖥️ Produto | 5 | Dropdown + texto livre para motivos |
| É5 | GAT-006 | Sugestão IA de Aprovação | 🖥️ Produto | 5 | IA sugere quem aprovar/rejeitar |
| É5 | GAT-007 | Auditoria de Decisão | 🖥️ Produto | 3 | Log imutável de quem decidiu o quê |
| | | **Subtotal É5 Gate 1** | | **34** | **6 🖥️Produto** |

---

###### É6 — Contato Email

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É6 | TPL-001 | Template de Email Padrão | 🖥️ Produto | 5 | Template base com merge tags |
| É6 | TPL-005 | Editor de Templates | 🖥️ Produto | 8 | Editor visual WYSIWYG |
| É6 | TPL-006 | Preview com Dados Reais | 🖥️ Produto | 5 | Preview preenchido com dados do candidato |
| É6 | TPL-007 | Variáveis de Template | 🖥️ Produto | 3 | Sistema de merge tags customizáveis |
| É6 | TPL-008 | Templates por Etapa | 🖥️ Produto | 5 | Template diferente por etapa do pipeline |
| É6 | TRI-001 | Envio Individual | 🖥️ Produto | 5 | Enviar email para candidato individual |
| É6 | TRI-002 | Envio em Massa | 🖥️ Produto | 8 | Enviar para múltiplos candidatos |
| É6 | TRI-003 | Status de Envio | 🖥️ Produto | 3 | Rastrear entregue/aberto/clicado |
| É6 | NOT-001 | Bell de Notificações | 🖥️ Produto | 5 | Ícone sino com contador no header |
| | | **Subtotal É6** | | **47** | **9 🖥️Produto** |

---

###### É6B — Follow-up Automático

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É6B | TRI-007 | Config Follow-up | 🖥️ Produto | 5 | Configurar regras de re-envio automático |
| | | **Subtotal É6B** | | **5** | **1 🖥️Produto** |

---

###### É7 — Triagem WSI

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É7 | TRI-004 | Chat WhatsApp Triagem | 🖥️ Produto | 13 | Interface de chat para triagem via WhatsApp |
| É7 | TRI-005 | Chat Web Triagem | 🖥️ Produto | 8 | Alternativa web para triagem |
| É7 | TRI-006 | Consentimento LGPD | 🖥️ Produto | 3 | Tela de consentimento antes da triagem |
| É7 | TRI-008 | Progresso de Triagem | 🖥️ Produto | 5 | Barra de progresso + blocos respondidos |
| É7 | TRI-009 | Timer de Resposta | 🖥️ Produto | 3 | Tempo limite por pergunta |
| É7 | TRI-010 | Retomar Triagem | 🖥️ Produto | 5 | Continuar de onde parou |
| É7 | TRI-011 | Encerrar Triagem | 🖥️ Produto | 8 | Finalizar e calcular score parcial |
| | | **Subtotal É7** | | **45** | **7 🖥️Produto** |

---

###### É7B — Resultado + Feedback WSI

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É7B | SCO-005 | Score Final WSI | 🖥️ Produto | 8 | Score consolidado + breakdown por dimensão |
| É7B | SCO-006 | Breakdown por Dimensão | 🖥️ Produto | 5 | Detalhamento empresa, técnico, comportamental |
| | | **Subtotal É7B** | | **13** | **2 🖥️Produto** |

---

###### É7/É8 — Scoring WSI

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| Scoring | SCO-001 | Big Five Assessment | 🖥️ Produto | 13 | Avaliação de personalidade Big Five |
| Scoring | SCO-002 | Taxonomia de Bloom | 🖥️ Produto | 8 | Classificação de complexidade cognitiva |
| Scoring | SCO-003 | Parecer LIA | 🖥️ Produto | 8 | Parecer narrativo gerado pela IA |
| Scoring | SCO-004 | Ranking de Candidatos | 🖥️ Produto | 5 | Ranking comparativo por vaga |
| Scoring | SCO-007 | Exportar Parecer (PDF) | 🖥️ Produto | 8 | Gerar PDF com parecer completo |
| Scoring | SCO-008 | Histórico de Scores | 🖥️ Produto | 5 | Evolução de scores ao longo do tempo |
| | | **Subtotal Scoring** | | **47** | **6 🖥️Produto** |

---

###### É8 — Gate 2: Aprovar Triados

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É8 | GAT-002 | Gate 2: Aprovar Triados | 🖥️ Produto | 8 | Tela de aprovação pós-triagem WSI |
| É8 | GAT-008 | Aprendizagem IA | 🖥️ Produto | 8 | IA aprende com decisões do recrutador |
| | | **Subtotal É8 Gate 2** | | **16** | **2 🖥️Produto** |

> ℹ️ GAT-003, GAT-004, GAT-005 são reutilizados do É5 Gate 1 — já contabilizados acima.

---

###### É9A — Agendamento de Entrevista

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É9A | AGE-001 | Integração MS Graph | 🖥️ Produto | 13 | Conectar calendário via Microsoft Graph |
| É9A | AGE-002 | Consulta Disponibilidade | 🖥️ Produto | 5 | Verificar horários livres do recrutador |
| É9A | AGE-003 | Sugestão Horários | 🖥️ Produto | 5 | Sugerir melhores horários ao candidato |
| É9A | AGE-004 | Criação Evento Teams | 🖥️ Produto | 5 | Criar reunião no Microsoft Teams |
| É9A | AGE-005 | Confirmação Candidato | 🖥️ Produto | 5 | Confirmar horário com o candidato |
| É9A | AGE-006 | Reagendamento | 🖥️ Produto | 5 | Permitir reagendamento pelo candidato |
| É9A | AGE-007 | Lembretes Automáticos | 🖥️ Produto | 3 | Enviar lembretes antes da entrevista |
| É9A | AGE-008 | Cancelamento | 🖥️ Produto | 3 | Cancelar entrevista com notificação |
| É9A | TPL-002 | Template Agendamento | 🖥️ Produto | 3 | Template de email de agendamento |
| É9A | TPL-003 | Template Confirmação | 🖥️ Produto | 3 | Template de confirmação de entrevista |
| É9A | INT-MSG-002 | OAuth Flow MS | 🖥️ Produto | 8 | Fluxo OAuth para Microsoft Graph |
| É9A | INT-MSG-003 | Calendar API | 🖥️ Produto | 5 | Integração com API de calendário |
| É9A | INT-MSG-004 | Teams Meeting API | 🖥️ Produto | 5 | Integração com API de reuniões Teams |
| É9A | INT-MSG-006 | Token Refresh | 🖥️ Produto | 3 | Renovação automática de tokens OAuth |
| | | **Subtotal É9A** | | **71** | **14 🖥️Produto** |

---

###### É9B — Feedback Final

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| É9B | TPL-004 | Template Pós-Entrevista | 🖥️ Produto | 3 | Template de email pós-entrevista |
| | | **Subtotal É9B** | | **3** | **1 🖥️Produto** |

> ℹ️ GAT-003/004/005 (feedback) e NOT-001 (bell) são reutilizados de É5/É6 — já contabilizados acima.

---

###### Pipeline (PIP-001~010)

| Etapa | Card | Título | Tipo | Pts | O que faz |
|-------|------|--------|------|-----|-----------|
| PIP | PIP-001 | Arquitetura 3 Camadas + Catálogo | 🔀 PIP | 8 | Base do sistema de pipeline |
| PIP | PIP-002 | Motor action_behavior (10 tipos) | 🔀 PIP | 8 | Motor de comportamentos por tipo de ação |
| PIP | PIP-003 | UniversalTransitionModal | 🔀 PIP | 8 | Modal universal para transições de etapa |
| PIP | PIP-004 | use-transition-context Hook | 🔀 PIP | 5 | Hook React para contexto de transição |
| PIP | PIP-005 | Movimentação Livre (Drag-Drop) | 🔀 PIP | 5 | Drag-drop livre entre colunas do pipeline |
| PIP | PIP-006 | Badges nos Cards | 🔀 PIP | 5 | Indicadores visuais nos cards do pipeline |
| PIP | PIP-007 | TransitionDispatchService (L1) | 🔀 PIP | 8 | Serviço de dispatch de transições |
| PIP | PIP-008 | Endpoints de Transição (API) | 🔀 PIP | 5 | API REST para transições de candidatos |
| PIP | PIP-009 | Pipeline CRUD por Vaga | 🔀 PIP | 5 | CRUD para configurar pipeline por vaga |
| PIP | PIP-010 | Barra de Ações em Massa | 🔀 PIP | 5 | Barra para ações em lote no pipeline |
| | | **Subtotal Pipeline** | | **62** | **10 🔀PIP** |

---

###### 📊 TOTAL SEMANA 1

| Tipo | Cards | Pontos |
|------|-------|--------|
| 🖥️ Produto | 95 | 524 |
| 🔀 PIP | 10 | 62 |
| **TOTAL SEMANA 1** | **105** | **586** |

---

##### 🔷 SEMANA 2 — IA CORE (40 cards | 315 pts)

**Foco:** Fundação IA completa — contratos, infraestrutura, serviços core e agentes principais. Alto reaproveitamento do protótipo (~94% tem código de referência).
**Total:** 40 cards 🏗️IA | 315 pontos

> ⚡ **ACELERADOR PROTÓTIPO:** PREP (14 cards) e INF (8 cards) são quase 100% portáveis Python→Python. Os agentes core (AGT-000~007) têm prompts e lógica completos no protótipo. Isso viabiliza 40 cards IA em 1 semana.

---

###### Fundação IA (PREP + INF + SRV-001 + INT-AI-001)

| Etapa | Card | Título | Tipo | Pts | Aprov. |
|-------|------|--------|------|-----|--------|
| Infra | PREP-001 | Estrutura Diretórios DDD | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-002 | Contratos Base (DomainPrompt ABC) | 🏗️ IA | 8 | 🟢 |
| Infra | PREP-003 | DomainWorkflow Pipeline (7 Steps) | 🏗️ IA | 8 | 🟢 |
| Infra | PREP-004 | DomainRegistry + Auto-discovery | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-005 | CascadedRouter (3-Tier Routing) | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-006 | LLM Provider ABC + Factory | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-007 | Prompt System (YAML Loader + Registry) | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-008 | Tool System (Registry + Executor) | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-009 | ConversationState + Memory (Redis + PG) | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-010 | Database Migrations (Schema Base) | 🏗️ IA | 8 | 🔧 |
| Infra | PREP-011 | Mapa de Equivalências Protótipo→Produção | 🏗️ IA | 3 | 📋 |
| Infra | PREP-012 | Dependências entre Domínios (Diagrama) | 🏗️ IA | 2 | 📋 |
| Infra | PREP-013 | Robustness Layer (Concerns/Middleware) | 🏗️ IA | 5 | 🟢 |
| Infra | PREP-014 | Few-Shot Examples Integration | 🏗️ IA | 2 | 🟢 |
| Infra | INF-001 | DomainPrompt ABC + DomainRegistry | 🏗️ IA | 8 | 🟢 |
| Infra | INF-002 | DomainWorkflow (intent→execute→format) | 🏗️ IA | 13 | 🟢 |
| Infra | INF-003 | CascadedRouter (Memory→Fast→LLM) | 🏗️ IA | 8 | 🟢 |
| Infra | INF-004 | FastRouter (keyword patterns) | 🏗️ IA | 5 | 🟢 |
| Infra | INF-005 | EventDispatcher + Pipeline Layer 2 | 🏗️ IA | 8 | 🔧 |
| Infra | INF-008 | ConversationMemory + ReferenceResolver | 🏗️ IA | 8 | 🟢 |
| Infra | INF-012 | Feature Flags Service | 🏗️ IA | 3 | 🟢 |
| Infra | INF-014 | Structured Output Parser | 🏗️ IA | 3 | 🔧 |
| Infra | SRV-001 | LLM Service (Gemini primary) | 🏗️ IA | 8 | 🟢 |
| Infra | INT-AI-001 | Gemini API Setup + Embedding | 🏗️ IA | 8 | 🔧 |
| Infra | TRV-001 | LGPD Básico (consentimento, opt-out) | 🏗️ IA | 8 | 🔧 |
| | | **Subtotal Fundação IA** | | **157** | **25 cards** |

---

###### Serviços Core (SRV-002~009, 011, 012)

| Etapa | Card | Título | Tipo | Pts | Aprov. |
|-------|------|--------|------|-----|--------|
| Serviços | SRV-002 | WSI Screening Pipeline (Blocos 2-5) | 🏗️ IA | 13 | 🟢 |
| Serviços | SRV-003 | WSI Question Generator | 🏗️ IA | 8 | 🟢 |
| Serviços | SRV-004 | WSI Scoring Engine (determinístico) | 🏗️ IA | 13 | 🟢 |
| Serviços | SRV-005 | JD Generator Service | 🏗️ IA | 8 | 🟢 |
| Serviços | SRV-007 | CV Parser + Scoring Service | 🏗️ IA | 8 | 🔧 |
| Serviços | SRV-008 | Embedding Service + Semantic Search | 🏗️ IA | 8 | 🟢 |
| Serviços | SRV-009 | Sourcing Pipeline (ES+PGV+WRF) | 🏗️ IA | 13 | 🟢 |
| Serviços | SRV-011 | Email Service (Mailgun) | 🏗️ IA | 5 | 🔧 |
| Serviços | SRV-012 | WhatsApp Service (multi-provider) | 🏗️ IA | 8 | 🔧 |
| | | **Subtotal Serviços Core** | | **84** | **9 cards** |

---

###### Agentes Core (AGT-000~007)

| Etapa | Card | Título | Tipo | Pts | Aprov. |
|-------|------|--------|------|-----|--------|
| Agentes | AGT-000 | Orchestrator (CascadedRouter + DomainWorkflow) | 🏗️ IA | 13 | 🟢 |
| Agentes | AGT-001 | Ag.5 Avaliador WSI | 🏗️ IA | 13 | 🟢 |
| Agentes | AGT-002 | Ag.3 Triagem Curricular | 🏗️ IA | 8 | 🟢 |
| Agentes | AGT-004 | Ag.0 Orquestrador Pipeline Chat | 🏗️ IA | 13 | 🟢 |
| Agentes | AGT-006 | Ag.2 SourcingAgent | 🏗️ IA | 8 | 🟢 |
| Agentes | AGT-007 | Ag.4 EntrevistadorWSI | 🏗️ IA | 13 | 🟢 |
| | | **Subtotal Agentes Core** | | **68** | **6 cards** |

> ℹ️ AGT-005/JobIntakeAgent movido para Alpha 2+ (wizard conversacional adiado).

---

###### 📊 TOTAL SEMANA 2

| Tipo | Cards | Pontos |
|------|-------|--------|
| 🏗️ IA (Fundação) | 25 | 157 |
| 🏗️ IA (Serviços Core) | 9 | 84 |
| 🏗️ IA (Agentes Core) | 6 | 68 |
| **TOTAL SEMANA 2** | **40** | **315** |*

> *6 cards adicionais incluem TRV-001 (LGPD) contabilizado na Fundação.

---

##### 🔷 SEMANA 3 — IA COMPLEMENTAR + INTEGRAÇÕES (23 cards | 163 pts)

**Foco:** Agentes complementares, integrações externas reais (Merge, Mailgun, Apify, MS Graph, WhatsApp), automações e calibração WSI.
**Total:** 23 cards 🏗️IA | 163 pontos

---

###### Agentes Complementares

| Etapa | Card | Título | Tipo | Pts | Aprov. |
|-------|------|--------|------|-----|--------|
| Agentes | AGT-003 | Ag.6 SchedulingAgent | 🏗️ IA | 8 | 🟢 |
| Agentes | AGT-008 | Ag.7 AnalistaFeedback | 🏗️ IA | 8 | 🟢 |
| Agentes | AGT-009 | Ag.8 IntegradorATS | 🏗️ IA | 8 | 🔧 |
| Agentes | AGT-010 | Ag.9 TaskPlanner | 🏗️ IA | 8 | 🔧 |
| Agentes | AGT-011 | Ag.10 CommunicationAgent | 🏗️ IA | 8 | 🔧 |
| | | **Subtotal Agentes Complementares** | | **40** | **5 cards** |

---

###### Serviços de Integração + Automações + Calibração

| Etapa | Card | Título | Tipo | Pts | Aprov. |
|-------|------|--------|------|-----|--------|
| Serviços | SRV-010 | Scheduling Service + Calendar | 🏗️ IA | 8 | 🔧 |
| Serviços | SRV-013 | Teams Notification Service | 🏗️ IA | 5 | 🔧 |
| Serviços | SRV-014 | ATS Sync Service (Merge.dev) | 🏗️ IA | 8 | 🔧 |
| Serviços | SRV-016 | Stage Automation Engine | 🏗️ IA | 5 | 🟢 |
| Integração | INT-AI-002 | Merge.dev ATS Integration | 🏗️ IA | 13 | 🔧 |
| Integração | INT-AI-003 | Mailgun Email Provider | 🏗️ IA | 5 | 🆕 |
| Integração | INT-AI-004 | Pearch + Apify Sourcing | 🏗️ IA | 8 | 🟢 |
| Integração | INT-AI-005 | Microsoft Graph (Calendar + Teams) | 🏗️ IA | 13 | 🔧 |
| Integração | INT-AI-007 | WhatsApp Business API | 🏗️ IA | 8 | 🆕 |
| Automação | AUT-001 | Follow-up automático 7 dias | 🏗️ IA | 8 | 🔧 |
| Automação | AUT-002 | Timeout triagem abandonada (48h) | 🏗️ IA | 5 | 🔧 |
| Automação | AUT-003 | Auto-pause/complete por status vaga | 🏗️ IA | 5 | 🔧 |
| Automação | AUT-004 | Cascata job_published→sourcing | 🏗️ IA | 5 | 🔧 |
| Automação | AUT-005 | Cascata screening→feedback | 🏗️ IA | 5 | 🟢 |
| Automação | AUT-006 | Cascata stage→interview/rejection | 🏗️ IA | 5 | 🟢 |
| Transversal | TRV-003 | WSI Calibração Contextual Senioridade | 🏗️ IA | 8 | 🟢 |
| Transversal | TRV-004 | Multi-Signal Seniority Resolution | 🏗️ IA | 13 | 🟢 |
| Transversal | TRV-005 | Governança Humana (GovernanceRules) | 🏗️ IA | 8 | 🟢 |
| | | **Subtotal Serviços+Automações+Calibração** | | **129** | **18 cards** |

---

###### 📊 TOTAL SEMANA 3

| Tipo | Cards | Pontos |
|------|-------|--------|
| 🏗️ IA (Agentes Complementares) | 5 | 40 |
| 🏗️ IA (Serviços + Automações + Calibração) | 18 | 123 |
| **TOTAL SEMANA 3** | **23** | **163** |

---

###### 📊 TOTAL GERAL MVP ALPHA 1 (Semana 1 + 2 + 3)

| Tipo | Semana 1 | Semana 2 | Semana 3 | **Total** |
|------|----------|----------|----------|-----------|
| 🖥️ Produto | 95 (524 pts) | — | — | **95 (524 pts)** |
| 🔀 PIP | 10 (62 pts) | — | — | **10 (62 pts)** |
| 🏗️ IA | — | 40 (315 pts) | 23 (163 pts) | **63 (478 pts)** |
| **Total** | **105 (586 pts)** | **40 (315 pts)** | **23 (163 pts)** | **168 (1064 pts)** |

---

##### ⬜ SEMANA 4+ — ALPHA 2 / PÓS-MVP

#### 2.8.3 Tabela Resumo por Etapa

> Visão consolidada de cards por etapa, tipo e semana. Cada card contabilizado **uma única vez** na sua etapa primária.

| Etapa | Descrição | 🖥️Produto | 🏗️IA | 🔀PIP | Total Cards | Total Pts | Semana |
|-------|-----------|-----------|-------|-------|-------------|-----------|--------|
| É1 — Login + Dashboard | Listagem de vagas e navegação | 4 (15) | — | — | 4 | 15 | 1 |
| É2 — Editar Vaga | Menu de ações + form edição | 3 (16) | — | — | 3 | 16 | 1 |
| É3 — Roteiro WSI | Motor perguntas, blocos, preview | 7 (47) | — | — | 7 | 47 | 1 |
| É4 — Mapeamento | Busca, filtros, candidatos, Apify | 16 (90) | — | — | 16 | 90 | 1 |
| É5 — Pipeline Kanban | Kanban, tabela, preview | 18 (80) | — | — | 18 | 80 | 1 |
| É5 — Gate 1 | Aprovação, feedback, massa | 6 (34) | — | — | 6 | 34 | 1 |
| É6 — Contato Email | Templates, envio, bell | 9 (47) | — | — | 9 | 47 | 1 |
| É6B — Follow-up | Retentativas automáticas | 1 (5) | — | — | 1 | 5 | 1 |
| É7 — Triagem WSI | WhatsApp, chat, consentimento | 7 (45) | — | — | 7 | 45 | 1 |
| É7B — Resultado + Feedback | Score, breakdown dimensões | 2 (13) | — | — | 2 | 13 | 1 |
| É7/É8 — Scoring WSI | Big Five, Bloom, parecer | 6 (47) | — | — | 6 | 47 | 1 |
| É8 — Gate 2 | Aprovação triados, aprendizagem | 2 (16) | — | — | 2 | 16 | 1 |
| É9A — Agendamento | MS Graph, calendar, Teams | 14 (71) | — | — | 14 | 71 | 1 |
| É9B — Feedback Final | Template pós-entrevista | 1 (3) | — | — | 1 | 3 | 1 |
| Pipeline (PIP) | Base + modais + transições | — | — | 10 (62) | 10 | 62 | 1 |
| IA Fundação | PREP + INF + SRV-001 + INT-AI-001 + TRV-001 | — | 25 (157) | — | 25 | 157 | 2 |
| IA Serviços Core | SRV-002~009, 011, 012 | — | 9 (84) | — | 9 | 84 | 2 |
| IA Agentes Core | AGT-000, 001, 002, 004, 006, 007 | — | 6 (68) | — | 6 | 68 | 2 |
| IA Agentes Complementares | AGT-003, 008, 009, 010, 011 | — | 5 (40) | — | 5 | 40 | 3 |
| IA Serviços + Integrações | SRV + INT-AI + AUT + TRV (restantes) | — | 18 (123) | — | 18 | 123 | 3 |
| **TOTAL** | | **95 (524)** | **63 (478)** | **10 (62)** | **168** | **1064** | |

> **Legenda da tabela:** Formato `N (P)` = N cards (P pontos). `—` = nenhum card daquele tipo nesta etapa.
>
> **Cards reutilizados** (contabilizados uma vez na etapa primária):
> - GAT-003, GAT-004, GAT-005 → contados em É5 Gate 1, reutilizados em É8 e É9B
> - NOT-001 → contado em É6, reutilizado em É9B
> - TRI-007 → contado em É6B, reutilizado em É7A
> - SCO-005, SCO-006 → contados em É7B, referenciados em É8


---

#### 2.8.4 Cards de Produto e Pipeline — Integrados no Roadmap

> **Os cards de produto e pipeline estão agora integrados diretamente nas tabelas por semana (seção 2.8.2).** Cada card inclui coluna de Tipo (🏗️IA / 🖥️Produto / 🔀PIP) e descrição do que faz.
>
> Para detalhamento completo dos bloqueantes e alertas por etapa, consulte a seção [2.2.1 — Detalhamento por Etapa](#221-detalhamento-por-etapa--bloqueantes-alertas-e-cards).
>
> **Fontes dos cards:**
>
> | Documento Fonte | Prefixos | Tipo |
> |----------------|----------|------|
> | `lia-mvp-cards-jira.md` | WIZ, KAN, GAT, NOT, SCO, TRI, AGE, VAG, TAB, PRV, MAP, INT-MSG, TPL, INT-APY | 🖥️ Produto |
> | `pipeline-transition-cards-jira.md` | PIP-001~010 (Alpha 1) / PIP-011~018 (Alpha 2+) | 🔀 PIP |
> | `lia-ai-architecture-cards-jira.md` | PREP, AGT, INF, SRV, INT-AI, AUT, TRV, LRN, CMP | 🏗️ IA |
> | `lia-mvp-cards-jira-v2.md` | CFG-001~012 (**⚠️ FORA DO PLANEJAMENTO ATUAL**) | ⚙️ CFG |

#### 2.8.5 Inventário Alpha 1 — Cards IA (Agentes, Serviços, Infraestrutura)

> **Legenda da coluna "Aproveitamento":**
> - 🟢 **Aproveitável** — Código/lógica já existe no protótipo, portar para produção com adaptações mínimas
> - 🔧 **Adaptar** — Lógica existe no protótipo, mas precisa adaptação significativa (stack, integrações, infra)
> - 🆕 **Construir** — Funcionalidade nova ou integração externa sem código aproveitável no protótipo
> - 📋 **Doc** — Entregável é documentação/planejamento, não código
>
> **Resumo geral (fonte: `lia-ai-architecture-cards-jira.md` seção 0.1):** ~58% aproveitável direto, ~26% com adaptação, ~16% reimplementar seguindo referência do protótipo. **Nada é do zero** — todo card tem especificação funcional completa nos docs + código de referência no protótipo.

##### Épico É14: Preparação Estrutural (PREP)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| PREP-001 | Estrutura de Diretórios DDD (Produção) | Sem 2 | 5 | 🟢 | Estrutura já documentada, replicar no repo produção |
| PREP-002 | Contratos Base (DomainPrompt ABC) | Sem 2 | 8 | 🟢 | ABC 100% portável (Python→Python no FastAPI) |
| PREP-003 | DomainWorkflow Pipeline (7 Steps) | Sem 2 | 8 | 🟢 | Pipeline 7 nós documentado, adaptar comunicação Rails |
| PREP-004 | DomainRegistry + Auto-discovery | Sem 2 | 5 | 🟢 | Registry Python puro, copiar direto |
| PREP-005 | CascadedRouter (3-Tier Routing) | Sem 2 | 5 | 🟢 | Algoritmo 3-tier portável, adaptar cache Redis prod |
| PREP-006 | LLM Provider ABC + Factory | Sem 2 | 5 | 🟢 | Factory pattern, mesmos SDKs no microsserviço |
| PREP-007 | Prompt System (YAML Loader + Registry) | Sem 2 | 5 | 🟢 | YAML + registry, 100% portável |
| PREP-008 | Tool System (Registry + Executor) | Sem 2 | 5 | 🟢 | Registry Python puro, adaptar scopes produção |
| PREP-009 | ConversationState + Memory (Redis + PG) | Sem 2 | 5 | 🟢 | Lógica existe, trocar dict fallback por Redis real |
| PREP-010 | Database Migrations (Schema Base) | Sem 2 | 8 | 🔧 | Schema documentado, gerar migrations produção (SQLAlchemy) |
| PREP-011 | Mapa de Equivalências Protótipo→Produção | Sem 2 | 3 | 📋 | Doc — mapeamento já parcialmente feito nos cards IA |
| PREP-012 | Dependências entre Domínios (Diagrama) | Sem 2 | 2 | 📋 | Doc — diagrama de dependências já esboçado |
| PREP-013 | Robustness Layer (Concerns/Middleware) | Sem 2 | 5 | 🟢 | Middleware Python puro, portar direto |
| PREP-014 | Few-Shot Examples Integration | Sem 2 | 2 | 🟢 | Exemplos texto puro, copiar integralmente |
| | **Subtotal PREP** | | **71** | | **11🟢 1🔧 2📋** |

##### Épico É15: Agentes IA (AGT)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| AGT-000 | Orchestrator (CascadedRouter + DomainWorkflow) | Sem 2 | 13 | 🟢 | Lógica orquestração existe, adaptar para prod |
| AGT-001 | Ag.5 Avaliador WSI | Sem 2 | 13 | 🟢 | Agente completo no protótipo, prompts portáveis |
| AGT-002 | Ag.3 Triagem Curricular | Sem 2 | 8 | 🟢 | Agente existe, regras WSI portáveis |
| AGT-003 | Ag.6 SchedulingAgent | Sem 3 | 8 | 🟢 | Agente existe, integrar calendar real |
| AGT-004 | Ag.0 Orquestrador Pipeline Chat | Sem 2 | 13 | 🟢 | 15 intents documentados, lógica portável |
| ~~AGT-005~~ | ~~Ag.1 JobIntakeAgent~~ | ~~Sem 2~~ | ~~8~~ | — | **→ MOVIDO PARA ALPHA 2+** (wizard conversacional adiado; Alpha 1 usa importação ATS + modal de edição) |
| AGT-006 | Ag.2 SourcingAgent | Sem 2 | 8 | 🟢 | Agente existe, adaptar integração Pearch |
| AGT-007 | Ag.4 EntrevistadorWSI | Sem 2 | 13 | 🟢 | Agente completo, prompts+fluxo portáveis |
| AGT-008 | Ag.7 AnalistaFeedback | Sem 3 | 8 | 🟢 | Agente existe, lógica feedback portável |
| AGT-009 | Ag.8 IntegradorATS | Sem 3 | 8 | 🔧 | Lógica parcial, integração Merge.dev real a fazer |
| AGT-010 | Ag.9 TaskPlanner | Sem 3 | 8 | 🔧 | Lógica parcial, adaptar para Celery/scheduling |
| AGT-011 | Ag.10 CommunicationAgent | Sem 3 | 8 | 🔧 | Agente registrado, falta orquestração multi-canal real |
| | **Subtotal AGT Alpha 1** | | **108** | | **8🟢 3🔧** *(AGT-005 movido para Alpha 2+)* |

##### Épico É16: Infraestrutura IA (INF)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| INF-001 | DomainPrompt ABC + DomainRegistry | Sem 2 | 8 | 🟢 | Contrato universal, 100% portável Python→Python |
| INF-002 | DomainWorkflow (intent→execute→format) | Sem 2 | 13 | 🟢 | Pipeline 7 nós documentado, adaptar comunicação Rails |
| INF-003 | CascadedRouter (Memory→Fast→LLM) | Sem 2 | 8 | 🟢 | 3-tier algorithm portável, adaptar cache Redis real |
| INF-004 | FastRouter (keyword patterns) | Sem 2 | 5 | 🟢 | Regex patterns universais, copiar direto |
| INF-005 | EventDispatcher + Pipeline Layer 2 | Sem 2 | 8 | 🔧 | Cascatas existem, adaptar para RabbitMQ/Redis pub-sub |
| INF-008 | ConversationMemory + ReferenceResolver | Sem 2 | 8 | 🟢 | Lógica existe, adaptar persistência SQLAlchemy prod |
| INF-012 | Feature Flags Service | Sem 2 | 3 | 🟢 | Feature flags Python puro, copiar direto |
| INF-014 | Structured Output Parser | Sem 2 | 3 | 🔧 | Conceito existe, implementar parser formal |
| | **Subtotal INF Alpha 1** | | **56** | | **6🟢 2🔧** |

##### Épico É17: Serviços de Domínio (SRV)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| SRV-001 | LLM Service (Gemini primary, multi-provider) | Sem 2 | 8 | 🟢 | Factory multi-provider existe, mesmos SDKs |
| SRV-002 | WSI Screening Pipeline (Blocos 2-5) | Sem 2 | 13 | 🟢 | Pipeline completo no protótipo, lógica portável |
| SRV-003 | WSI Question Generator | Sem 2 | 8 | 🟢 | Templates+LLM, prompts 100% portáveis |
| SRV-004 | WSI Scoring Engine (determinístico) | Sem 2 | 13 | 🟢 | Fórmulas matemáticas puras, zero dependência |
| SRV-005 | JD Generator Service | Sem 2 | 8 | 🟢 | Service existe, prompts portáveis |
| SRV-007 | CV Parser + Scoring Service | Sem 2 | 8 | 🔧 | Lógica parcial, adaptar parser PDF/DOCX prod |
| SRV-008 | Embedding Service + Semantic Search | Sem 2 | 8 | 🟢 | Service existe, adaptar Gemini SDK prod |
| SRV-009 | Sourcing Pipeline Service (ES+PGV+WRF) | Sem 2 | 13 | 🟢 | Pipeline documentado, adaptar ES/PGVector prod |
| SRV-010 | Scheduling Service + Calendar | Sem 3 | 8 | 🔧 | Lógica parcial, integrar calendar API real |
| SRV-011 | Email Service (Mailgun) | Sem 2 | 5 | 🔧 | Interface existe, configurar Mailgun prod |
| SRV-012 | WhatsApp Service (multi-provider) | Sem 2 | 8 | 🔧 | Interface existe, integrar WhatsApp API real |
| SRV-013 | Teams Notification Service | Sem 3 | 5 | 🔧 | Interface parcial, integrar MS Graph real |
| SRV-014 | ATS Sync Service (Merge.dev) | Sem 3 | 8 | 🔧 | Lógica parcial, integrar Merge.dev API real |
| SRV-016 | Stage Automation Engine + Pipeline L2 | Sem 3 | 5 | 🟢 | Python puro (2.596L), SubStatusPredictor portável |
| | **Subtotal SRV Alpha 1** | | **118** | | **8🟢 6🔧** |

##### Épico É18: Integrações Externas IA (INT-AI)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| INT-AI-001 | Gemini API Setup + Embedding | Sem 2 | 8 | 🔧 | SDK existe, configurar API keys/quotas prod |
| INT-AI-002 | Merge.dev ATS Integration | Sem 3 | 13 | 🔧 | Interface desenhada, OAuth+config prod a fazer |
| INT-AI-003 | Mailgun Email Provider | Sem 3 | 5 | 🆕 | Integração nova — configurar domínio+templates prod |
| INT-AI-004 | Pearch + Apify Sourcing | Sem 3 | 8 | 🟢 | Service existe (`pearch_service.py`), adaptar keys |
| INT-AI-005 | Microsoft Graph (Calendar + Teams) | Sem 3 | 13 | 🔧 | Interface parcial, OAuth MS Graph a implementar |
| INT-AI-007 | WhatsApp Business API | Sem 3 | 8 | 🆕 | Integração nova — provider API real a configurar |
| | **Subtotal INT-AI Alpha 1** | | **55** | | **1🟢 3🔧 2🆕** |

##### Épico É19: Automações (AUT)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| AUT-001 | Follow-up automático 7 dias | Sem 3 | 8 | 🔧 | Lógica cascata existe, adaptar para Celery scheduling |
| AUT-002 | Timeout triagem abandonada (48h) | Sem 3 | 5 | 🔧 | Lógica existe, adaptar timer prod (Celery beat) |
| AUT-003 | Auto-pause/complete por status vaga | Sem 3 | 5 | 🔧 | Lógica parcial, integrar com pipeline state machine |
| AUT-004 | Cascata job_published → sourcing | Sem 3 | 5 | 🔧 | Event cascade desenhada, adaptar EventDispatcher |
| AUT-005 | Cascata screening→feedback + ReturnEventService | Sem 3 | 5 | 🟢 | ReturnEventService Python puro, 11 eventos portáveis |
| AUT-006 | Cascata stage→interview/rejection + Pipeline L2 | Sem 3 | 5 | 🟢 | WebhookAdapters+idempotência portáveis |
| | **Subtotal AUT Alpha 1** | | **33** | | **2🟢 4🔧** |

##### Épico É20: Transversais (TRV)

| Card | Título | Semana | Pontos | Aprov. | Obs |
|------|--------|:------:|:------:|:------:|-----|
| TRV-001 | LGPD Básico (consentimento, opt-out) | Sem 2 | 8 | 🔧 | Lógica parcial, adequação legal real com DPO |
| TRV-003 | WSI Calibração Contextual Senioridade | Sem 3 | 8 | 🟢 | Analyzer existe (`seniority_jd_analyzer.py`) |
| TRV-004 | Multi-Signal Seniority Resolution | Sem 3 | 13 | 🟢 | Resolver existe, Python puro, portável |
| TRV-005 | Governança Humana (GovernanceRules) | Sem 3 | 8 | 🟢 | GovernanceRules Python puro, portável |
| | **Subtotal TRV Alpha 1** | | **37** | | **3🟢 1🔧** |

> **Total Cards IA Alpha 1: 63 cards / 478 pontos**
> (14 PREP + 11 AGT + 8 INF + 14 SRV + 6 INT-AI + 6 AUT + 4 TRV)
> *(AGT-005/JobIntakeAgent movido para Alpha 2+ — wizard conversacional adiado)*
>
> **Aproveitamento consolidado dos 63 cards IA:**
>
> | Status | Cards | % | Significado |
> |--------|:-----:|:-:|-------------|
> | 🟢 Aproveitável | 39 | 62% | Código/lógica do protótipo portável com adaptações mínimas |
> | 🔧 Adaptar | 20 | 32% | Lógica existe, precisa adaptação para infra/integrações de produção |
> | 🆕 Construir | 2 | 3% | Integrações novas (Mailgun, WhatsApp API) |
> | 📋 Doc | 2 | 3% | Entregáveis de planejamento/documentação |
>
> **Conclusão:** 94% dos cards IA (🟢+🔧) têm código ou lógica de referência no protótipo. Nenhum card parte do zero — todos possuem especificação funcional completa na documentação + código de referência no protótipo Replit.

#### 2.8.6 Gran Total Alpha 1

| Categoria | Cards | Pontos | % do Total |
|-----------|:-----:|:------:|:----------:|
| 🖥️ Produto (VAG+KAN+TAB+PRV+MAP+WSI+WIZ+GAT+TPL+TRI+SCO+AGE+NOT+INT-MSG+INT-APY) | 95 | 524 | 49% |
| 🔀 Pipeline (PIP) | 10 | 62 | 6% |
| 🏗️ IA — Preparação (PREP) | 14 | 71 | 7% |
| 🏗️ IA — Agentes (AGT) | 11 | 108 | 10% |
| 🏗️ IA — Infraestrutura (INF) | 8 | 56 | 5% |
| 🏗️ IA — Serviços (SRV) | 14 | 118 | 11% |
| 🏗️ IA — Integrações (INT-AI) | 6 | 55 | 5% |
| 🏗️ IA — Automações (AUT) | 6 | 33 | 3% |
| 🏗️ IA — Transversais (TRV) | 4 | 37 | 4% |
| **TOTAL ALPHA 1** | **168** | **1.064** | **100%** |

> **Distribuição:** 95 cards 🖥️Produto (524 pts, 49%) + 10 cards 🔀PIP (62 pts, 6%) + 63 cards 🏗️IA (478 pts, 45%).
> *(AGT-005/JobIntakeAgent removido do Alpha 1 — wizard conversacional adiado)*

#### 2.8.7 Inventário Alpha 2+ e Pós-MVP

##### Cards Não-IA — Pós-MVP

| Card | Título | Tipo | Pontos | Justificativa |
|------|--------|------|:------:|---------------|
| WIZ-001 | Interface Chat Conversacional | Frontend | 8 | Wizard conversacional completo — Alpha 2 |
| WIZ-002 | Orquestrador de Intenções | AI | 13 | Intent classifier avançado — Alpha 2 |
| WIZ-003 | Serviço de Insights de Mercado | Backend | 8 | Dados de mercado — Alpha 2 |
| WIZ-004 | Gerador de Job Description (avançado) | AI | 8 | JD via chat — Alpha 2 |
| WIZ-005 | Salvamento de Rascunho | Backend | 3 | Auto-save — Alpha 2 |
| WIZ-006 | Sugestões Clicáveis | Frontend | 5 | Chips contextuais — Alpha 2 |
| WIZ-007 | Preview da Vaga (Live) | Full-Stack | 5 | Preview tempo real — Alpha 2 |
| WIZ-009 | Skip Calibração Conversacional | Full-Stack | 3 | Skip etapas — Alpha 2 |
| WIZ-010 | Estágio de Salário Interativo | Frontend | 5 | UI salário — Alpha 2 |
| WIZ-011 | Estágio de Competências | Frontend | 8 | UI competências — Alpha 2 |
| WIZ-014 | Revisão Metodologia Wizard | Processo | 2 | Validação com especialista |
| KAN-009 | Componentes Kanban Modulares | Frontend | 13 | Refactor modular — Alpha 2 |
| KAN-010 | Feedback Implícito em Transições | Backend | 5 | Feedback automático — Alpha 2 |
| KAN-012 | Solicitar Candidatos Refinados | AI + Full-Stack | 8 | Refinamento IA — Alpha 2 |
| KAN-013 | Buscar Candidatos Similares | AI + Full-Stack | 8 | Busca similar IA — Alpha 2 |
| NOT-002 | Notificações em Tempo Real (WebSocket) | Backend | 8 | Push — Alpha 2 |
| NOT-003 | Preferências de Notificação | Full-Stack | 5 | Config canais — Alpha 2 |
| NOT-004 | Notificações Push (PWA) | Backend | 8 | Service Worker — Alpha 2 |
| NOT-005 | Histórico de Notificações | Full-Stack | 5 | Lista filtrada — Alpha 2 |
| NOT-006 | Badge de Não Lidas | Frontend | 2 | Contador — Alpha 2 |
| NOT-007 | Notificações via Microsoft Teams | Integração | 8 | Teams integration — Alpha 2 |
| CFG-001 | LIA Field Toggles | Frontend | 5 | Controle campos — Alpha 2 |
| CFG-002 | Verificação de Completude | Backend | 3 | Validação — Alpha 2 |
| CFG-003 | Configuração de Jornada | Frontend | 5 | Pipeline customizado — Alpha 2 |
| CFG-004 | Hub de Comunicação | Frontend | 8 | Central multi-canal — Alpha 2 |
| CFG-005 | Dados da Empresa para LIA | Frontend | 5 | Contexto empresa — Alpha 2 |
| | **Subtotal Não-IA Pós-MVP** | | **168** | |

##### Cards PIP — Alpha 2+

| Card | Título | Sprint | Pontos | Depende de |
|------|--------|:------:|:------:|------------|
| PIP-011 | Pipeline Padrão Empresa | S3 | 5 | PIP-009 |
| PIP-012 | Herança Empresa → Vaga | S3 | 5 | PIP-011 |
| PIP-013 | Colunas Customizadas + LIA | S3 | 5 | PIP-009, SRV-016 |
| PIP-014 | TestSendModal | S3 | 5 | PIP-003 |
| PIP-015 | ProposalModal | S3 | 5 | PIP-003 |
| PIP-016 | SchedulingModal Dedicado | S4 | 8 | PIP-003, AGT-003 |
| PIP-017 | Mini-Prompt LLM (L2) | S3 | 5 | PIP-007, SRV-016 |
| PIP-018 | Timeout e Escalação | S4 | 5 | PIP-006, INF-005 |
| | **Subtotal PIP Alpha 2+** | | **43** | |

##### Cards IA — S4+ / Pós-MVP

| Card | Título | Sprint | Pontos | Justificativa |
|------|--------|:------:|:------:|---------------|
| AGT-012 | Ag.11 RecruiterAssistant | S4 | 8 | Assistente proativo — não bloqueante |
| INF-006 | FairnessGuard middleware | S4 | 5 | Compliance avançado |
| INF-007 | FactChecker middleware | S4 | 5 | Compliance avançado |
| INF-009 | SmartExtractor (2-stage) | S4 | 5 | Extração avançada |
| INF-010 | Circuit Breaker + Retry | S4 | 5 | Resiliência avançada |
| INF-011 | Token Tracking + Cost | S4 | 5 | Gestão de custos LLM |
| INF-012 | Feature Flags Service | S4 | 3 | Controle granular |
| INF-013 | Agent Monitoring Service | S4 | 5 | Observabilidade |
| SRV-006 | JD Enrichment Service | S4 | 5 | Enriquecimento JD |
| SRV-015 | Candidate Search Route (WRF) | S4 | 8 | Busca avançada |
| AUT-007 | Cascata candidates→CV screening | S4 | 5 | Automação avançada |
| AUT-008 | Scheduler hourly (auto-completion) | S4 | 3 | Expiração automática |
| TRV-002 | XAI (Explainable AI) básico | S4 | 5 | Explicabilidade |
| INT-AI-006 | Deepgram STT (voz) | Pós-MVP | 8 | Speech-to-Text |
| LRN-001 | Learning Loop Service | S4 | 8 | Aprendizagem padrões |
| LRN-002 | Template Learning Service | S4 | 5 | Aprendizagem templates |
| LRN-003 | Outcome Learning System | S5 | 8 | Aprendizagem resultado |
| LRN-004 | Fine-tuning Data Export | S5 | 5 | Dados fine-tuning |
| LRN-005 | Feedback Loop System | S4 | 8 | Captura feedback |
| CMP-001 | SOX Compliance Engine | S5 | 13 | SOX compliance |
| CMP-002 | EU AI Act Risk Classification | S5 | 13 | EU AI Act |
| CMP-003 | LGPD Avançado (DPO, breach) | S4 | 8 | LGPD completo |
| CMP-004 | Audit Trail Completo | S4 | 8 | Audit trail |
| CMP-005 | Bias Detection + Mitigation | S5 | 13 | Detecção viés |
| | **Subtotal IA Pós-MVP** | | **158** | |

#### 2.8.8 Cards a Criar — Gaps Identificados

> **O que são estes cards?** Durante a análise detalhada das etapas do MVP, foram identificadas **funcionalidades necessárias que ainda não possuem cards Jira** nos documentos fonte. São gaps que o time precisa avaliar, criar no Jira e incluir no planejamento.
>
> Estes cards estavam anteriormente marcados com ⚠️ nas tabelas das etapas. Foram centralizados aqui para facilitar o rastreamento e a decisão de criação.

| # | Card Sugerido | Título | Etapa | Sprint | Complexidade | Pts | Tipo | Obs / Dependência IA |
|:-:|--------------|--------|:-----:|:------:|:---:|:---:|:----:|------|
| 1 | PUB-001 | Página pública chat web (candidato) | É7 | S2 | 🔴 Muito Alta | 13 | A CRIAR | **BLOQUEANTE CRÍTICO** — sem esta página, a triagem via web não funciona |
| 2 | PUB-002 | Autenticação via token JWT (candidato+vaga) | É7 | S2 | 🟡 Média | 5 | A CRIAR | Token JWT sem login. Dependência: PUB-001 |
| 3 | FLW-001 | Follow-up automático 7 dias/email | É6B | S2 | 🟠 Alta | 8 | A CRIAR | Cron/job re-envio 24h × 7 dias. IA: AUT-001 |
| 4 | FLW-002 | Status "sem_resposta" no pipeline | É6B | S2 | 🟢 Baixa | 3 | A CRIAR | Novo status. IA: SRV-016 (Stage Automation) |
| 5 | TRI-015 | Triagem abandonada — lógica de detecção | É7A | S3 | 🟠 Alta | 8 | A CRIAR | Detecção inatividade 48h + lembretes. IA: AUT-002 |
| 6 | TRI-016 | Progresso parcial de triagem | É7A | S3 | 🟡 Média | 5 | A CRIAR | Salvar respostas já dadas. IA: PREP-009 (ConversationState) |
| 7 | TRI-017 | Status "triagem_incompleta" no pipeline | É7A | S3 | 🟢 Baixa | 3 | A CRIAR | Novo status. IA: SRV-016 (Stage Automation) |
| 8 | KAN-005* | SmartTransitionModal (confirmação transições) | É5 | S2 | 🟡 Média | 5 | NOVO | Originalmente KAN-005 (obsoleto) — recriado com escopo diferente |
| 9 | TPL-009 | Template Email Contato Inicial | É6 | S2 | 🟢 Baixa | 3 | NOVO | Template específico para primeiro contato por email |
| 10 | TPL-010 | Template Feedback Pós-Triagem | É7B | S3 | 🟢 Baixa | 3 | NOVO | Mensagem agradecimento + próximos passos |
| | | **TOTAL** | | | | **56** | | |

> **Impacto no escopo:** Se todos os 10 cards forem criados, o Alpha 1 passa de **93 cards / 668 pts** para **103 cards / 724 pts** (+10 cards / +56 pts, aumento de ~8%).
>
> **Priorização sugerida:**
> - **S2 obrigatório:** PUB-001 (bloqueante), PUB-002, FLW-001
> - **S2 desejável:** FLW-002, KAN-005*, TPL-009
> - **S3 desejável:** TRI-015, TRI-016, TRI-017, TPL-010

---

#### 2.8.9 Gran Total Geral (Alpha 1 + Alpha 2+ / Pós-MVP)

| Fase | 🖥️Produto | 🔀PIP | 🏗️IA | Total Cards | Total Pontos |
|------|:---------:|:-----:|:-----:|:-----------:|:------------:|
| **Alpha 1** (Sem 1+2+3) | 95 (524) | 10 (62) | 63 (478) | **168** | **1.064** |
| **Alpha 2+** (Sem 4+) | 26 | 8 | 24 | **58** | **369** |
| **TOTAL GERAL** | **121** | **18** | **87** | **226** | **1.433** |

> **Caminho crítico Alpha 1 (3 semanas):** Sem 1 (Produto + Pipeline, 105 cards, UI completa) → Sem 2 (IA Core, 40 cards, reaproveitamento protótipo) → Sem 3 (IA Complementar, 23 cards, integrações + automações).
>
> **Observação:** O Alpha 1 concentra **74%** do esforço total (1.064 de 1.433 pts). O Alpha 2+ é predominantemente refinamento (learning, compliance, UX avançada).

---

## 3. INTEGRAÇÕES MVP

| Integração | Propósito | Status | Prioridade |
|------------|-----------|--------|------------|
| **Claude (Anthropic)** | LLM para agentes, perguntas, parecer | Pendente | Pós-MVP ⚠️ |
| **Gemini (Google)** | Busca semântica, embeddings, multimodal | Pendente | Alta |
| **OpenAI** | LLM alternativo, fallback, TTS | Pendente | Pós-MVP ⚠️ |
| **WhatsApp (Twilio)** | Comunicação com candidatos | Pendente | Crítica |
| **Microsoft Graph** | Calendário, Teams, Outlook | Pendente | Alta |
| **WorkOS** | SSO, MFA, SCIM | Pendente | Pós-MVP ⚠️ |
| **Pearch** | Busca global de candidatos | Pendente | Alta |
| **Deepgram** | Speech-to-Text (Nova-2) | Pendente | Média |

> **⚠️ Observações Pós-MVP:**
> - **WorkOS** (SSO, MFA, SCIM) — reclassificado como Pós-MVP. No Alpha 1 o login será por email/senha simples. WorkOS será implementado no Alpha 2 para suportar autenticação enterprise de clientes externos.
> - **Claude (Anthropic)** — reclassificado como Pós-MVP. No Alpha 1, os agentes LIA utilizarão Gemini como LLM principal. A integração com Claude será avaliada para Alpha 2 conforme necessidade de capacidade multimodal avançada ou qualidade de raciocínio.
> - **OpenAI** — reclassificado como Pós-MVP. No Alpha 1, Gemini será o LLM único. OpenAI será incorporado no Alpha 2 como fallback, TTS e modelo alternativo para diversificação de providers.

### Caminho Crítico
```
Auth → Criação de Vaga → Roteiro WSI (Modal) → Mapeamento → Perguntas WSI → WhatsApp → Triagem → Score → Gates → Agendamento
```

---

## 5. CAMADA DE IA NO PIPELINE (Layer 2) — STATUS

**Data:** 19/fev/2026
**Status:** ✅ Implementado e testado (19 testes E2E passando)

### 5.1 Funcionalidades Concluídas

| # | Funcionalidade | Descrição | Arquivos Principais |
|---|---------------|-----------|---------------------|
| 1 | **Interpretação inteligente de mini-prompts** | Claude interpreta comandos do recrutador no Kanban (ex: "mover para entrevista e avisar") extraindo ação, candidato, motivo e preferências. Fallback determinístico se LLM indisponível. | `interpret_context_llm_service.py` |
| 2 | **Personalização automática de mensagens** | Mensagens de disparo (email/WhatsApp) personalizadas com contexto do candidato (nome, cargo, tempo na etapa, score WSI). LLM gera variações naturais; fallback usa template padrão. | `TransitionDispatchService` em `domain.py` |
| 3 | **Predição de sub-status por IA** | Ao mover candidato entre etapas, IA sugere o sub-status mais provável (ex: "Aguardando Resposta", "Entrevista Agendada") com score de confiança. Fallback: sub-status padrão da etapa. | `candidate_context_aggregator.py`, `domain.py` |
| 4 | **Inferência de comportamento para colunas customizadas** | Para colunas criadas pelo recrutador, IA infere o tipo de ação esperada (screening, scheduling, evaluation, etc.) analisando nome/descrição. Fallback: tipo "general". | `InferBehaviorService` em `domain.py` |
| 5 | **Domínio de Pipeline com 5 tools** | PipelineTransitionDomain registra 5 ferramentas para o agente LIA: `move_candidate`, `bulk_move_candidates`, `get_stage_suggestions`, `get_candidate_context`, `get_pipeline_overview`. | `domain.py` |
| 6 | **Assistente Kanban com sugestões proativas** | 4 superfícies visuais: (1) badges nos cards (stale/high/low score), (2) painel de sugestões na LIA expandida, (3) mensagem proativa no chat, (4) badge de notificação no header. | `kanban_assistant_service.py`, `KanbanCard.tsx`, `job-kanban-page.tsx` |
| 7 | **Unified LLM Client** | Cliente unificado com retry, timeout, feature flags por capacidade, e fallback automático. | `llm_client.py` |
| 8 | **19 testes E2E** | Cobertura completa: InterpretContextLLM, CandidateContextAggregator, InferBehaviorLLM, PipelineTransitionDomain, KanbanAssistant, feature flags, LLM client. | `test_llm_pipeline_integration.py` |

### 5.2 Garantias de Produção

- **Zero impacto se LLM indisponível**: Todos os serviços têm `try/except` com fallback para lógica determinística (Layer 1 preservado)
- **Feature flags**: `ENABLE_LLM_INTERPRET_CONTEXT`, `ENABLE_LLM_DISPATCH_PERSONALIZATION`, `ENABLE_LLM_INFER_BEHAVIOR`, `ENABLE_LLM_SUBSTATUS_PREDICTION` (todos `True` por padrão, desligáveis individualmente)
- **Backward compatibility**: Campos novos (`ai_powered`, `confidence`, `predicted_sub_status`, `ai_personalized`, `days_in_stage`, `lia_insights`) são todos `Optional` com defaults seguros
- **Frontend seguro**: Usa `?? false` / `?? 0` para evitar false positives em campos de IA

### 5.3 Próximas Etapas (Backlog Pipeline IA)

| # | Item | Descrição | Prioridade | Dependências |
|---|------|-----------|:----------:|-------------|
| P1 | **Rejeição em lote com sub-status individualizado** | Hoje a rejeição em lote aplica o mesmo motivo para todos. IA sugere motivo mais provável por candidato (perfil inadequado, outro selecionado, desistiu, etc.) e gera feedback diferenciado. | Alta | LLM ativo, `CandidateContextAggregator` |
| P2 | **Conectar IA a dados reais** | Serviços prontos mas apontam para simulações. Conectar ao banco real (candidatos, notas de entrevista, scores WSI) para tornar predições e personalizações efetivas em produção. | Crítica | DB com dados de candidatos reais |
| P3 | **Webhooks de retorno** | Endpoints de eventos de retorno (candidato confirmou entrevista, completou teste, etc.) são simulação. Criar adaptadores para receber webhooks reais de ferramentas externas. | Média | Integrações externas ativas |
| P4 | **Dashboard de métricas da IA** | Acompanhar taxa de acerto das predições, uso de fallback vs IA, tempo de resposta, para calibrar thresholds. Métricas: accuracy de sub-status, % personalizações aceitas, latência média LLM. | Média | P2 concluído (dados reais) |
