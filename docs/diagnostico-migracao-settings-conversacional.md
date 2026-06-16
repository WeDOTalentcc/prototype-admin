# Diagnostico: Migracao do Menu Configuracoes para Modelo Conversacional

**Data:** 14/04/2026  
**Versao:** 4.0 (FINAL — consolidado apos discussoes)  
**Escopo:** Plataforma LIA - Menu Configuracoes

---

## 1. Resumo Executivo

O menu Configuracoes atual possui **7 hubs** baseados em formularios/tabs tradicionais
com 25+ subsecoes. A proposta e migrar para um modelo **Conversational-First** onde
a LIA conduz o preenchimento de dados da empresa via chat, seguindo o padrao ja
implementado com sucesso no **HiringPoliciesHub**.

**Filosofia central:** O recrutador nao preenche formularios — ele conversa com a LIA,
que faz perguntas, sugere valores, e preenche automaticamente. Interfaces CRUD visuais
(pipeline, screening, templates, usuarios) permanecem como estao.

### Decisoes Tomadas

1. **"Minha Empresa"** se torna conversacional (chat lateral + cards), absorvendo TUDO conversacional incluindo Politicas de Recrutamento
2. **Templates, Pipeline, Screening, Integracoes, Comunicacao/Alertas** permanecem como estao
3. **Usuarios e Departamentos** ficam juntos como item de menu (CRUD)
4. **"Recrutamento" desaparece do menu** — Pipeline e Screening viram itens proprios, Politicas vao para "Minha Empresa"
5. **O chat NÃO e duplicado** — usa o UnifiedChat lateral em modo contextual
6. **Dados criticos sao classificados** em 4 tiers de mutabilidade
7. **RBAC ja existe** com 5 niveis (admin, manager, senior_recruiter, recruiter, intern)

---

## 2. Menu Final: ANTES vs DEPOIS

### ANTES (7 itens, 25+ subsecoes)

```
Empresa & Equipe
  > Dados da Empresa
  > Departamentos
  > Tech Stack
  > Beneficios
  > Usuarios
Recrutamento
  > Pipeline
  > Screening
  > Politicas de Contratacao
Comunicacao & Alertas
  > Templates
  > Assinatura
  > Horarios LGPD
  > Alertas
Planejamento
  > Workforce Planning
  > Metas Recrutadores
  > Alertas (duplicado)
Busca Global
  > Limites
  > Opcoes
  > Custos
Integracoes
  > Modelos IA
  > ATS
  > Calendario
  > Comunicacao
  > CRM/HRIS
  > MCPs & APIs
Fairness & Compliance
  > Dashboard
  > Auditoria
  > Studio
  > Export
```

### DEPOIS (7 itens, sem subsecoes)

```
Minha Empresa          → NOVO (chat lateral + cards de TUDO que e conversacional)
Pipeline               → Mantem como esta (CRUD visual)
Screening              → Mantem como esta (CRUD visual)
Templates & Assinatura → Mantem como esta (interface dedicada, assinatura na mesma tela)
Comunicacao & Alertas  → Mantem como esta (alertas, briefing, horarios LGPD)
Usuarios & Depart.     → Mantem (CRUD, agora juntos)
Integracoes            → Mantem como esta
```

**O que SAIU do menu:**
- **Recrutamento** (item inteiro) → Politicas de Contratacao migram para "Minha Empresa" (cards)
- GoalsPlanningHub (workforce planning) → absorvido por "Minha Empresa" (card)
- Busca Global → absorvida: status/creditos podem aparecer em card dentro de Integracoes ou Visao Geral
- Fairness & Compliance → status pode aparecer como card em Visao Geral ou manter
- Todas as subsecoes de "Empresa & Equipe" (cultura, tech stack, beneficios) → dentro dos cards de "Minha Empresa"

**Nota:** Pipeline e Screening, que antes ficavam dentro de "Recrutamento", agora
sao itens proprios do menu. Politicas de Contratacao (HiringPoliciesHub), que ja
era conversacional, migra para dentro de "Minha Empresa" como mais um grupo de cards.

**Nota 2:** O item "Visao Geral" (cards read-only para fairness, busca global) e opcional.
Se preferir, fairness pode continuar como item separado ou ficar como card informativo
dentro de outro item. A decisao e de produto.

---

## 3. Estrutura Visual

### Como funciona o HiringPoliciesHub hoje (padrao de referencia)

```
+-----------------------------------------------------------------------+
|  Politicas de Contratacao                        78% configurado  [==] |
+-----------------------------------------------------------------------+
|                                |                                      |
|  CHAT LIA (60%)                |  CARDS DE DADOS (40%)                |
|                                |                                      |
|  +---------------------------+ |  +--------------------------------+  |
|  | Ola! Sou a Lia.           | |  | Regras de Pipeline     [Config]|  |
|  | Posso ajudar a configurar | |  |   Min entrevistas: 2           |  |
|  | suas politicas...         | |  |   Aprovacao oferta: Sim   [ed] |  |
|  +---------------------------+ |  |   Auto-rejeicao: Nao     [ed] |  |
|  |                           | |  +--------------------------------+  |
|  | LIA: Quantas entrevistas  | |  | Agendamento          [Pendente]|  |
|  | minimas voce exige?       | |  |   Janela: 9h-18h              |  |
|  |                           | |  |   Buffer: 30min               |  |
|  | Voce: No minimo 2         | |  +--------------------------------+  |
|  |                           | |  | Comunicacao          [Pendente]|  |
|  | LIA: Perfeito! Atualizei  | |  |   Follow-up auto: Sim         |  |
|  | "Min entrevistas" para 2. | |  |   Prazo resposta: 48h         |  |
|  +---------------------------+ |  +--------------------------------+  |
|  | [Envie mensagem para LIA] | |  | Automacoes           [Pendente]|  |
+-----------------------------------------------------------------------+
```

### Tela "Minha Empresa" — Chat Lateral + Cards (NOVO)

A pagina "Minha Empresa" mostra cards com todos os dados. O chat lateral da LIA
(UnifiedChat) detecta que o recrutador esta nessa pagina e muda automaticamente
para o agente `company_settings`. Nao ha chat duplicado.

```
+--------+----------------------------------------------+---------+
| MENU   |  Minha Empresa              52% config [===] | CHAT    |
|        +----------------------------------------------| LIA     |
|        |                                              | (modo   |
| Minha  |  +--------------------+ +------------------+ | config) |
| Empresa|  | Dados Basicos [Co] | | Cultura    [Pe]  | |         |
|        |  |  Nome: WeDo Talent | |  Missao: --      | | Ola!    |
| Pipeli.|  |  CNPJ: 12.345...   | |  Visao: --       | | Vamos   |
|        |  |  Website: wedo...  | |  Valores: --     | | complet.|
| Screen.|  |  Setor: Tech  [ed] | +------------------+ | o perfil|
|        |  +--------------------+ +------------------+ |         |
| Templa.|  | Tech Stack    [Pe] | | Beneficios [Pe]  | | Qual o  |
|        |  |  Frontend: --      | |  VR: --          | | nome    |
| Comun. |  |  Backend: --       | |  Plano: --       | | oficial?|
|        |  +--------------------+ +------------------+ |         |
| Usuar. |  +--------------------+ +------------------+ |         |
| Depart.|  | Politicas Recr[Co] | | Workforce   [Pe] | |         |
|        |  |  Min entrev.: 2    | |  2026: 0 vagas   | |         |
| Integr.|  |  Aprov oferta: Sim | |  [Importar plan.]| |         |
|        |  |  Auto-rejeicao: N  | +------------------+ |         |
|        |  |  Agendamento: Conf | +------------------+ |         |
|        |  |  Automacoes: Pend  | | Documentos  [Pe] | |         |
|        |  +--------------------+ |  Handbook: --    | |         |
|        |                         |  Org chart: --   | |         |
|        |                         +------------------+ | [enviar]|
+--------+----------------------------------------------+---------+
```

**Como funciona:**
- O recrutador abre "Minha Empresa" e ve todos os cards com status
- O chat lateral (UnifiedChat) ja presente na plataforma detecta a pagina
- LIA muda para modo `settings_config` e carrega historico de configuracao
- Conforme o recrutador conversa, os cards atualizam em tempo real
- Cada campo tem icone de lapis para edicao manual direta
- Quando o recrutador sai da pagina, o chat volta ao modo geral

**Cards disponiveis (todos colapsaveis):**
- Dados Basicos (nome, CNPJ, website, setor, tamanho, logo)
- Cultura & EVP (missao, visao, valores, DEI, sustentabilidade)
- Tech Stack (frontend, backend, infra, ferramentas, cultura eng.)
- Beneficios (pacote completo com elegibilidade)
- Politicas de Recrutamento (regras pipeline, agendamento, comunicacao, automacoes — migrado do HiringPoliciesHub)
- Workforce Planning (plano anual + botao importar planilha)
- Documentos (handbook, org chart, compensacao — com anonimizacao FairnessGuard)

**Nota sobre Politicas de Recrutamento:** Hoje o HiringPoliciesHub tem seu
proprio chat embutido + cards. Na migracao, os cards de politicas passam
a ser mais um bloco no painel direito de "Minha Empresa", e o chat e o
mesmo UnifiedChat lateral (que ja roteava para o agente `hiring_policy`).
O agente `company_settings` absorve as tools de politicas ou redireciona
para o `hiring_policy` conforme o contexto da conversa.

### Demais Telas — SEM MUDANCA

| Tela | O que ve o recrutador |
|------|----------------------|
| Pipeline | Interface CRUD: etapas com drag & drop, SLAs, cores, sub-status |
| Screening | Interface CRUD: perguntas eliminatorias, banco de perguntas |
| Templates & Assinatura | Editor visual de templates + assinatura na mesma tela |
| Comunicacao & Alertas | Tabs: alertas, briefing LIA, horarios LGPD, digest |
| Usuarios & Departamentos | CRUD: tabela de usuarios + gestao de departamentos |
| Integracoes | Cards de status + configuracao de API keys, OAuth |

---

## 4. Decisao: Chat Lateral vs Chat Embutido

### Opcoes Analisadas

| Opcao | Descricao | Problema |
|-------|-----------|----------|
| A — Sem chat | So cards, recrutador abre chat lateral quando quer | Perde experiencia de onboarding guiado |
| B — Chat embutido | Chat dentro da pagina (como HiringPoliciesHub) | Duplica chat — ja existe lateral |
| C — Hibrido (ESCOLHIDA) | Chat lateral muda de contexto automaticamente | Sem duplicacao, experiencia fluida |

### Opcao C: Como Funciona

A plataforma ja possui o **UnifiedChat** — chat lateral da LIA que aparece em
todas as paginas (sidebar, floating ou fullscreen). Ele ja suporta context switching
(`general`, `job_chat`, `talent_chat`, `kanban_chat`).

Ao acessar "Minha Empresa", o UnifiedChat:
1. Detecta `page_type: company_settings`
2. Troca para agente `company_settings`
3. Carrega historico separado de configuracao
4. Exibe suggestions de setup ("Completar perfil", "Importar planilha", "Analisar website")
5. Cards na area principal atualizam em tempo real conforme a conversa

Ao sair da pagina, o chat volta ao modo geral. O historico de configuracao
fica preservado para quando o recrutador voltar.

**Excecao:** O HiringPoliciesHub ja tem chat embutido e funciona bem.
Pode continuar como esta (nao precisa migrar para chat lateral) ou
ser migrado para o mesmo padrao no futuro. Decisao nao-urgente.

---

## 5. Sistema de Permissoes (RBAC) — JA EXISTE

O RBAC ja esta implementado na plataforma com 5 niveis:

| Nivel | Role | Acesso |
|-------|------|--------|
| 5 | **admin** | Acesso total (`*` em `*`) |
| 4 | **manager** | Gestao completa de candidatos, vagas, relatorios, configuracoes |
| 3 | **senior_recruiter** | Gestao de candidatos, vagas proprias |
| 2 | **recruiter** | Acesso restrito a vagas atribuidas |
| 1 | **intern** | Apenas leitura em vagas/candidatos atribuidos |

### Implementacao existente:

**Backend (lia-agent-system):**
- `AuthEnforcementMiddleware` valida JWT, extrai `company_id` e `role`
- Multi-tenancy estrita (header `X-Company-ID` deve bater com JWT)
- `tool_permissions.yaml` controla quais tools cada nivel pode usar
- Human-In-The-Loop para acoes destrutivas (rejeitar candidato, fechar vaga)

**Frontend (plataforma-lia):**
- `PermissionManager` em `src/utils/permissions.ts`
- Hook `usePermissions()` para show/hide de componentes
- `canAccessPage(page)` e `canUseLiaAction(actionId)` para gating
- Middleware Next.js para protecao de rotas

### Aplicacao na Migracao de Configuracoes

| Funcionalidade | Quem pode | Quem NAO pode |
|---------------|-----------|---------------|
| Minha Empresa (preencher dados) | admin, manager | recruiter, intern |
| Templates (editar) | admin, manager, senior_recruiter | intern |
| Pipeline (editar etapas) | admin, manager | recruiter, intern |
| Screening (editar perguntas) | admin, manager | recruiter, intern |
| Usuarios (criar/editar) | admin | todos os outros |
| Departamentos (criar/editar) | admin, manager | recruiter, intern |
| Integracoes (API keys, OAuth) | admin | todos os outros |
| Alertas (toggles pessoais) | todos | — |
| Dados TIER 1 (alterar apos setup) | admin (com confirmacao dupla) | todos os outros |

**Nao precisa criar nada novo para RBAC.** O sistema ja existe e e robusto.
Basta usar os helpers existentes (`canAccessPage`, `usePermissions`) nas novas
telas e registrar as permissoes dos novos agentes em `tool_permissions.yaml`.

---

## 6. Classificacao de Dados: Imutaveis vs Mutaveis

Uma vez que dados alimentam agentes, modelos de decisao e workflows, alterar
esses dados pode quebrar processos em andamento.

### TIER 1: Dados Fundacionais (IMUTAVEIS apos setup inicial)

Alteracao requer admin + confirmacao dupla.

| Dado | Impacto se Alterado |
|------|---------------------|
| Nome da empresa | Aparece em TODOS os emails, templates, relatorios |
| CNPJ | Vinculado a tenant, cobranca, compliance |
| Dominio/Website | Usado para matching, analise Apify |
| Pipeline de etapas | Candidatos em andamento vinculados a etapas |
| Perguntas eliminatorias | Candidatos ja triados com base nessas perguntas |

### TIER 2: Dados Estruturais (MUTAVEIS com validacao)

LIA exibe warning antes de salvar + log de auditoria.

| Dado | Frequencia de Mudanca | Validacao |
|------|----------------------|-----------|
| Cultura (missao, visao, valores) | Raramente (anual) | "Isso muda como avalio candidatos. Confirma?" |
| Tech Stack | Periodicamente | Atualiza criterios de matching tecnico |
| Beneficios | Periodicamente | Atualiza o que LIA comunica aos candidatos |
| Departamentos | Quando empresa cresce | Verificar vagas/candidatos vinculados |
| Faixas salariais | Anualmente | Impacta salary benchmark |
| Workforce planning | Trimestral/anual | Recalcular metas |
| Politicas de contratacao | Quando politica muda | Adaptar autonomia da LIA |

### TIER 3: Dados Operacionais (LIVREMENTE MUTAVEIS)

Alteracao direta, sem confirmacao extra.

| Dado | Motivo |
|------|--------|
| Templates de email (corpo/assunto) | Afetam apenas futuras mensagens |
| Assinatura | Estetico |
| Horarios de envio LGPD | Ajuste sem afetar processos |
| Alertas e briefing (toggles) | Preferencia pessoal |
| Logo da empresa | Estetico |
| Descricao da empresa | Informativo |

### TIER 4: Dados Somente Leitura (NAO editaveis pelo recrutador)

| Dado | Quem Edita |
|------|-----------|
| Integracoes (API keys, OAuth) | Admin |
| Limites de Busca Global | Admin/CS |
| Fairness score | Sistema (automatico) |
| Configuracao de modelos IA | Admin |

### Implementacao no Agente

```
Tool: save_company_field
  1. Recebe campo e novo valor
  2. Consulta tier do campo
  3. TIER 1 (imutavel): Ja preenchido? → "Campo protegido. Contate admin."
  4. TIER 2 (validacao): Ha dependencias? → Warning + aguarda confirmacao
  5. TIER 3 (livre): Salva diretamente
  6. TIER 4 (read-only): "Gerenciado pelo admin."
```

---

## 7. Features Especiais

### 7.1 Upload de Documentos com Anonimizacao FairnessGuard

**Fluxo conversacional:**
1. Recrutador: "Quero enviar nosso handbook"
2. LIA: "Envie o arquivo que eu analiso e extraio os dados relevantes."
3. Recrutador envia PDF/DOCX
4. Backend processa:
   - Extrai texto do documento
   - FairnessGuard Layer 1: remove termos discriminatorios
   - FairnessGuard Layer 2: sinaliza termos proxy
   - Hashing SHA-256 de PII
   - Extrai dados estruturados (missao, valores, beneficios)
5. LIA: "Encontrei a missao, 5 valores e 12 beneficios. Preencho?"

**Documentos suportados:** Handbook, org chart, tabela de beneficios,
plano de compensacao, planilha de headcount.

### 7.2 Scraping de Website via Apify

**Ja implementado** — endpoint `POST /api/v1/company/culture-profile/analyze-direct`.
Na migracao, a interface muda de botao para conversa:

1. LIA: "Quer que eu analise o site da empresa para preencher automaticamente?"
2. Recrutador: "Sim, wedotalent.com"
3. Apify scrapa paginas sobre, carreiras, cultura
4. LIA: "Encontrei: setor Tech, 200 funcionarios, 8 valores. Confirma?"

### 7.3 Workforce Planning via Planilha

1. LIA: "Como quer configurar o planejamento?"
   - "Importar planilha Excel/CSV"
   - "Preencher juntos por departamento"
2. Se planilha: Upload via SmartImportZone → `POST /api/v1/workforce/entries/import`
3. Se manual: LIA pergunta departamento por departamento

---

## 8. Inventario Tecnico dos Hubs Atuais

### 8.1 Empresa & Equipe (CompanyTeamHub)

**Arquivo:** `plataforma-lia/src/components/settings/CompanyTeamHub.tsx`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Dados da Empresa | `GET/PUT /api/v1/company/profile` | Real | Card em "Minha Empresa" |
| Cultura | `GET/PUT /api/v1/company/culture-profile` | Real | Card em "Minha Empresa" |
| Analise Website | `POST /api/v1/company/culture-profile/analyze-direct` | Real | Tool do agente |
| Tech Stack | Dentro de culture-profile | Real | Card em "Minha Empresa" |
| Departamentos | `CRUD /api/v1/company/departments` | Real | "Usuarios & Departamentos" |
| Aprovadores | `CRUD /api/v1/company/approvers` | Real | "Usuarios & Departamentos" |
| Beneficios | `CRUD /api/v1/company/benefits` | Real | Card em "Minha Empresa" |
| Usuarios | `CRUD /api/v1/company/users` | Real | "Usuarios & Departamentos" |

### 8.2 Recrutamento (RecruitmentHub)

**Arquivo:** `plataforma-lia/src/components/settings/RecruitmentHub.tsx`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Pipeline | CRUD via backend-proxy | Real | Item proprio no menu (Pipeline) |
| Screening | CRUD via backend-proxy | Real | Item proprio no menu (Screening) |
| Politicas | `POST /api/v1/company-hiring-policy/{id}/chat` | Real + Chat | Card em "Minha Empresa" (migrado) |

### 8.3 Comunicacao & Alertas (CommunicationHub)

**Arquivo:** `plataforma-lia/src/components/settings/communication-hub/`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Templates | `GET/PUT /api/v1/email-templates` | Real | Mantem (Templates & Assinatura) |
| Ajuste IA | `POST /api/v1/email-templates/adjust` | Real | Mantem |
| Assinatura | `GET/PUT /api/v1/company/communication-settings` | Real | Mantem (mesma tela de Templates) |
| Horarios LGPD | Mesmo endpoint | Real | Mantem (Comunicacao & Alertas) |
| Alertas | `GET/PUT /api/v1/alerts/config` | Real | Mantem (Comunicacao & Alertas) |
| Briefing LIA | Dentro de alerts/config | Real | Mantem |
| Digest Semanal | `GET/PUT /api/v1/digest/weekly/preferences` | Real | Mantem |

### 8.4 Planejamento (GoalsPlanningHub)

**Arquivo:** `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Workforce Planning | `GET/PUT /api/v1/workforce` | Real | Card em "Minha Empresa" |
| Import Planilha | `POST /api/v1/workforce/entries/import` | Real | Tool do agente |
| Alertas | `GET/PUT /api/v1/alerts/config` | Real (duplicado) | Unificado em Comunicacao |
| Metas Recrutadores | `POST /api/v1/goals/import` | Real | Dashboard operacional (fora de Config) |

### 8.5 Busca Global (GlobalSearchHub)

**Arquivo:** `plataforma-lia/src/components/settings/GlobalSearchHub.tsx`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Limites | `GET/PUT /api/v1/company/global-search-settings` | Real | Admin / Visao Geral |
| Opcoes | Mesmo endpoint | Real | Admin |
| Custos | Mesmo endpoint | Real | Admin |

### 8.6 Integracoes (IntegrationsHub)

**Arquivo:** `plataforma-lia/src/components/settings/IntegrationsHub.tsx`

| Categoria | Status Real | Destino |
|-----------|-------------|---------|
| Modelos IA (Gemini, Claude, OpenAI) | Operacional | Mantem |
| ATS (Gupy, Pandape, Merge.dev) | Operacional | Mantem |
| Calendario (Google, Microsoft) | Operacional (OAuth) | Mantem |
| Teams | Operacional (webhook) | Mantem |
| WhatsApp, Email/SMTP | coming_soon | Mantem |
| CRM/HRIS (Salesforce, SAP, Workday) | Placeholder | Mantem |

### 8.7 Fairness & Compliance (FairnessComplianceHub)

**Arquivo:** `plataforma-lia/src/components/settings/FairnessComplianceHub.tsx`

| Subsecao | Endpoint Backend | Status | Destino |
|----------|-----------------|--------|---------|
| Dashboard | `GET /api/v1/fairness-report/summary` | Real | Visao Geral ou mantem |
| Auditoria | `GET /api/v1/audit-logs` | Real | Admin |
| Studio | `GET /api/v1/custom-agents/studio-compliance-summary` | Real | Admin |
| Export | `GET /api/v1/fairness-report/export` | Real | Admin |

---

## 9. Progresso do Setup (Settings Progress)

**Backend:** `lia-agent-system/app/api/v1/settings_progress.py`

| Secao | Peso Atual | Calculo Atual | Problema |
|-------|------------|---------------|----------|
| Empresa & Equipe | 30% | Media de 5 checks reais | OK |
| Recrutamento | 25% | Templates + SLAs + Automacoes | OK |
| Comunicacao | 20% | **Hardcoded 100%** | Nao reflete realidade |
| Planejamento | 15% | **Hardcoded 100%** | Nao reflete realidade |
| Busca Global | 10% | 100% se settings existem | OK |

**Acao necessaria:** Recalcular Comunicacao e Planejamento com base em campos
efetivamente preenchidos. Na migracao, o agente `company_settings` pode reportar
progresso real via tool `get_company_completion`.

---

## 10. Riscos e Consideracoes

### Riscos Tecnicos

| Risco | Mitigacao |
|-------|----------|
| Duplicacao de alertas (Goals e Communication usam `/alerts/config`) | Unificar em Comunicacao & Alertas |
| Progress hardcoded em 100% para 2 secoes | Recalcular com base em dados reais |
| Upload de documentos grandes (timeout) | Processar async com status de progresso |
| Context switching do UnifiedChat | Testar transicao fluida entre modos |

### Riscos de UX

| Risco | Mitigacao |
|-------|----------|
| Recrutador acostumado com formularios | Manter edicao via lapis nos cards |
| Chat lateral pode nao ser descoberto | Sugestao de onboarding na primeira visita |
| Muitos cards na tela de "Minha Empresa" | Todos colapsaveis, mostrar so pendentes |

### Dependencias Criticas

- **FairnessGuard** — ja existe, precisa de wrapper para processamento de documentos
- **Apify** — ja integrado via endpoint `analyze-direct`
- **LangGraphReActBase** — framework maduro, usado por hiring_policy
- **UnifiedChat** — ja suporta context switching (adicionar `settings_config`)
- **RBAC** — ja implementado com 5 niveis + PermissionManager

---

## 11. Esforco Estimado

| Fase | Descricao | Estimativa |
|------|-----------|------------|
| **Fase 1** | Agente `company_settings` (backend: domain, tools, router) | 3-4 dias |
| **Fase 2** | Frontend "Minha Empresa" (cards + integracao com UnifiedChat) | 3-4 dias |
| **Fase 3** | Juntar Usuarios + Departamentos em uma tela | 1-2 dias |
| **Fase 4** | Mover Assinatura para tela de Templates | 1 dia |
| **Fase 5** | Context switching no UnifiedChat (`settings_config`) | 1-2 dias |
| **Fase 6** | Upload de documentos + FairnessGuard wrapper | 2-3 dias |
| **Fase 7** | Refatorar menu lateral (nova navegacao) | 1-2 dias |
| **Fase 8** | Recalcular settings progress (tirar hardcodes) | 1 dia |
| **Fase 9** | Testes e ajustes | 2-3 dias |
| **Total** | | 15-22 dias |

---

## 12. Proximo Passo

Apos aprovacao deste diagnostico:

1. Completar agente `company_settings` no backend (domain.py, tools, config, router)
2. Adicionar context type `settings_config` ao UnifiedChat
3. Criar componente "Minha Empresa" com cards + integracao chat lateral
4. Unificar Usuarios + Departamentos em uma tela
5. Mover Assinatura para tela de Templates
6. Refatorar `settings-page-enhanced.tsx` com novo menu
7. Recalcular progress (remover hardcodes)
8. Testes end-to-end

---

## Apendice A: Mapa de Endpoints

```
EMPRESA (usados pelo agente company_settings):
  /api/v1/company/profile                          GET, POST, PUT
  /api/v1/company/culture-profile                   GET, PUT
  /api/v1/company/culture-profile/analyze-direct    POST (Apify)
  /api/v1/company/departments                       GET, POST
  /api/v1/company/departments/{id}                  PUT, DELETE
  /api/v1/company/departments/{id}/members          GET
  /api/v1/company/members/{id}                      POST, PUT, DELETE
  /api/v1/company/approvers                         GET, POST
  /api/v1/company/approvers/{id}                    PUT, DELETE
  /api/v1/company/benefits                          GET, POST
  /api/v1/company/benefits/{id}                     PUT, DELETE
  /api/v1/company/users                             GET, POST
  /api/v1/company/users/{id}                        PUT, DELETE
  /api/v1/workforce                                 GET, PUT
  /api/v1/workforce/entries/import                  POST
  /api/v1/benefits/templates                        GET

RECRUTAMENTO:
  /api/v1/company-hiring-policy/{id}/chat           POST (ReAct agent)

COMUNICACAO:
  /api/v1/email-templates                           GET
  /api/v1/email-templates/{id}                      PUT
  /api/v1/email-templates/adjust                    POST (LLM)
  /api/v1/company/communication-settings            GET, PUT
  /api/v1/alerts/config                             GET, PUT
  /api/v1/digest/weekly/preferences                 GET, PUT

INTEGRACOES:
  /api/v1/llm-config                                GET, PUT
  /api/v1/calendar/health                           GET
  /api/v1/calendar/google/auth-url                  GET
  /api/v1/ats/connections                           GET
  /api/v1/integrations/status                       GET

COMPLIANCE:
  /api/v1/fairness-report/summary                   GET
  /api/v1/fairness-report/export                    GET
  /api/v1/audit-logs                                GET
  /api/v1/custom-agents/studio-compliance-summary   GET

PROGRESSO:
  /api/v1/settings/progress                         GET
  /api/v1/settings/saturation                       GET, PUT

BUSCA GLOBAL:
  /api/v1/company/global-search-settings            GET, PUT

METAS:
  /api/v1/goals/import                              POST
  /api/v1/goals/by-user/{id}                        GET
```

## Apendice B: Arquivos-Chave

```
HUBS ATUAIS:
  plataforma-lia/src/components/settings/CompanyTeamHub.tsx
  plataforma-lia/src/components/settings/RecruitmentHub.tsx
  plataforma-lia/src/components/settings/HiringPoliciesHub.tsx
  plataforma-lia/src/components/settings/communication-hub/
  plataforma-lia/src/components/settings/GoalsPlanningHub.tsx
  plataforma-lia/src/components/settings/GlobalSearchHub.tsx
  plataforma-lia/src/components/settings/IntegrationsHub.tsx
  plataforma-lia/src/components/settings/FairnessComplianceHub.tsx

HOOKS:
  plataforma-lia/src/hooks/settings/useCompanyData.ts
  plataforma-lia/src/hooks/settings/useDepartmentManagement.ts
  plataforma-lia/src/hooks/settings/use-user-management.ts
  plataforma-lia/src/hooks/company/use-hiring-policies.ts
  plataforma-lia/src/components/settings/communication-hub/useCommunicationHub.ts
  plataforma-lia/src/components/settings/useGoalsPlanningHub.ts

PAGINA PRINCIPAL:
  plataforma-lia/src/components/pages/settings-page-enhanced.tsx

UNIFIED CHAT:
  plataforma-lia/src/components/unified-chat/UnifiedChat.tsx
  plataforma-lia/src/contexts/lia-float-context.tsx
  plataforma-lia/src/hooks/chat/useChatMessages.ts

RBAC:
  plataforma-lia/src/utils/permissions.ts
  plataforma-lia/src/middleware.ts
  lia-agent-system/app/middleware/auth_enforcement.py
  lia-agent-system/app/tools/tool_permissions.yaml

BACKEND AGENTE (referencia):
  lia-agent-system/app/domains/hiring_policy/domain.py
  lia-agent-system/app/domains/hiring_policy/agents/policy_react_agent.py
  lia-agent-system/app/domains/hiring_policy/agents/policy_tool_registry.py
  lia-agent-system/app/api/v1/hiring_policy.py

BACKEND ROUTING:
  lia-agent-system/app/orchestrator/cascaded_router.py
  lia-agent-system/app/orchestrator/domain_mappings.py
  lia-agent-system/app/orchestrator/config/domain_routing.yaml
```
