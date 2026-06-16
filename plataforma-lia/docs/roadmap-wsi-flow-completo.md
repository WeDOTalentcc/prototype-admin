# Roadmap Completo: Fluxo Criação de Vaga → Triagem WSI

> **Plataforma LIA — WeDO Talent**
> Documento consolidado com mapeamento real de todos os campos, componentes, APIs e arquivos de referência.
> Última atualização: Abril 2026

---

## Índice

- [FASE 0 — Pré-Requisitos (Configurações da Empresa)](#fase-0--pré-requisitos-configurações-da-empresa)
- [FASE 1 — Criação Manual da Vaga](#fase-1--criação-manual-da-vaga)
- [FASE 2 — Configuração Completa da Vaga (JobEditTab)](#fase-2--configuração-completa-da-vaga-jobedit-tab)
- [FASE 3 — Configurações de Triagem WSI (ScreeningConfigManager)](#fase-3--configurações-de-triagem-wsi-screeningconfigmanager)
- [FASE 4 — Enriquecimento do Job Description](#fase-4--enriquecimento-do-job-description)
- [FASE 5 — Geração de Perguntas WSI](#fase-5--geração-de-perguntas-wsi)
- [FASE 6 — Publicação da Vaga](#fase-6--publicação-da-vaga)
- [FASE 7 — Busca e Adição de Candidatos](#fase-7--busca-e-adição-de-candidatos)
- [FASE 8 — Disparo da Triagem](#fase-8--disparo-da-triagem)
- [FASE 9 — Triagem do Candidato (WSI Interview Graph)](#fase-9--triagem-do-candidato-wsi-interview-graph)
- [FASE 10 — Scoring Determinístico](#fase-10--scoring-determinístico)
- [FASE 11 — Ranking e Recomendação](#fase-11--ranking-e-recomendação)
- [FASE 12 — Outputs Pós-Triagem](#fase-12--outputs-pós-triagem)
- [Mapa de Arquivos Completo](#mapa-de-arquivos-completo)

---

## FASE 0 — Pré-Requisitos (Configurações da Empresa)

Antes de criar qualquer vaga, o administrador configura dados globais da empresa no menu **Configurações > Setup Empresa** (`/admin/setup-empresa`). Esses dados alimentam os formulários de criação.

| Seção | Campos/Dados | Fonte de Dados |
|-------|-------------|----------------|
| **Departamentos** | Lista de departamentos (id, nome) | `GET /api/backend-proxy/company/departments/` |
| **Benefícios** | Nome, categoria (Saúde, Alimentação, Transporte, Educação, Financeiro, Qualidade de Vida, Família, Segurança), tipo de valor (monetário/percentual/informativo), elegibilidade por senioridade/departamento, destaque | `GET /api/backend-proxy/benefits/templates` |
| **Cultura/EVP** | Missão, visão, valores, tagline, Employee Value Proposition | Enriquecimento via IA: `POST /api/backend-proxy/company/enrich` (puxa de LinkedIn/Glassdoor) |
| **Jornada de Recrutamento** | Etapas do pipeline (stages), sub-status, SLA por etapa, comportamento de ação, canal padrão, templates de pipeline | `GET /api/v1/recruitment-stages/stages`, `POST /api/v1/company/pipeline-templates/seed-defaults` |

**Arquivos de referência:**
- `plataforma-lia/src/app/admin/setup-empresa/page.tsx`
- `plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx`
- `plataforma-lia/src/components/settings/StageCard.tsx`
- `lia-agent-system/libs/models/lia_models/recruitment_stages.py`
- `lia-agent-system/app/api/v1/recruitment_stages.py`

---

## FASE 1 — Criação Manual da Vaga

### Etapa 1.1: Acesso à criação

- **Tela:** Página de Vagas (`/vagas`)
- **Botão:** "Nova Vaga" (canto superior direito)
- **Componente:** `jobs-page.tsx` → abre `CreateJobModal`

### Etapa 1.2: Seleção do modo de criação

O modal apresenta duas opções:
1. **"Criar com a LIA"** → fluxo conversacional com IA (wizard)
2. **"Criar manualmente"** → formulário manual ← este fluxo

### Etapa 1.3: Dados iniciais (Modal CreateJobModal — step `manual-form`)

| Campo | Tipo | Obrigatório | Fonte |
|-------|------|-------------|-------|
| Título da Vaga | Input texto | Sim | Livre |
| Departamento | Select dropdown | Não | Puxa de Configurações → Departamentos. Se não houver, exibe input livre |
| Modelo de Trabalho | Select | Não | Constantes: Remoto, Híbrido, Presencial |
| Forma de Contratação | Select | Não | Constantes: CLT, PJ, Estágio, Temporário, Freelancer |
| Gestor Responsável | Input texto | Sim | Livre |
| Email do Gestor | Input email | Sim | Livre |

**Ação:** Botão "Criar e Configurar" → chama `liaApi.createJobVacancy()`, cria a vaga com status "Rascunho" (Draft) e navega para a tela de configuração (Kanban da vaga).

**Arquivos:**
- `plataforma-lia/src/components/modals/create-job-modal.tsx`
- `plataforma-lia/src/components/pages/jobs/useJobsStatusHandlers.ts`
- `plataforma-lia/src/stores/job-ui-store.ts`

---

## FASE 2 — Configuração Completa da Vaga (JobEditTab)

Após clicar "Criar e Configurar", o sistema navega para o Kanban da vaga e automaticamente abre a aba **"Configurações"** (detecta `jobCreationMode` no store). O formulário completo é renderizado pelo componente `JobEditTab`.

### Arquitetura da Tela

A tela tem **layout split-panel**:
- **Sidebar esquerda** (220px): navegação entre seções com indicador ✓ de completude
- **Painel direito**: conteúdo da seção ativa, com modo leitura/edição (botões "Editar" / "Salvar" / "Cancelar")

**Acesso:** Tab "Configurações" no header da vaga (`KanbanJobHeader.tsx`) → `activeTab === 'edit'` → renderiza `<JobEditTab>`

A sidebar divide-se em **dois grupos**:

### Grupo 1: Configurações da Vaga (4 seções)

Definidas em `SECTIONS` de `job-edit-tab.constants.ts`.

---

#### Seção 2.1: Informações Gerais (`info-geral` → `JobInfoGeralSection.tsx`)

**Sub-grupo: Gestão**

| Campo | Tipo | Opções |
|-------|------|--------|
| Status | Select | Rascunho, Ativa, Paralisada, Concluída, Cancelada |
| Prioridade | Select | Alta, Média, Baixa |
| Nível de Urgência | Select | 1-Baixa, 2-Moderada, 3-Média, 4-Alta, 5-Crítica |
| Triagem | Badge clicável | Mostra status da triagem; clique navega para seção "configuracoes" |

**Sub-grupo: Identificação**

| Campo | Tipo | Placeholder | WSI ⚡ |
|-------|------|-------------|--------|
| Título da Vaga | Input | "Ex: Analista de Sistemas Sênior" | Sim |
| Departamento | Input | "Ex: Tecnologia" | Sim |
| Localização | Input | "Ex: São Paulo, SP" | Sim |

**Sub-grupo: Classificação**

| Campo | Tipo | Opções | WSI ⚡ |
|-------|------|--------|--------|
| Modelo de Trabalho | Select | Presencial, Remoto, Híbrido (mostra padrão empresa se configurado) | Sim |
| Tipo de Contrato | Select | CLT, PJ, Estágio, Temporário, Freelancer, Aprendiz + tipos empresa | Sim |
| Nível (Senioridade) | Select | Estágio, Júnior, Pleno, Sênior, Lead, Gerente, Diretor | Sim |

**Sub-grupo: Prazos & Timeline**

| Campo | Tipo |
|-------|------|
| Data de Abertura | Date |
| Prazo Final | Date |
| Prazo Triagem | Date |
| Prazo Shortlist | Date |
| Prazo Fechamento | Date |

**Sub-grupo: Descrição da Vaga**

| Campo | Tipo | Detalhes | WSI ⚡ |
|-------|------|----------|--------|
| Descrição da Vaga | Textarea | 16 rows, min 280px | Sim |

**Sub-grupo: Idiomas** ⚡

Cada idioma é uma linha com 3 campos:

| Campo | Tipo | Opções |
|-------|------|--------|
| Idioma | Select | 16 opções: Inglês, Espanhol, Francês, Alemão, Italiano, Mandarim, Japonês, Coreano, Português, Russo, Árabe, Hindi, Holandês, Sueco, Turco, Outro |
| Nível | Select | Básico, Intermediário, Avançado, Fluente, Nativo |
| Obrigatório | Switch | Sim / Não |

Botão: **"+ Adicionar Idioma"** (apenas em modo edição)

**Sub-grupo: Ações Afirmativas** ⚡

| Campo | Tipo | Condição | Opções |
|-------|------|----------|--------|
| Vaga Afirmativa | Switch | — | on/off |
| Critério Principal | Select | Sempre visível | Gênero, Raça/Etnia, PCD, LGBTQIA+, 50+, Refugiado, Indígena, Outro |
| Critério Secundário | Select | Se afirmativa ativa | Mesmas opções |
| Descrição | Input | Se afirmativa ativa | "Ex: Mulheres negras, PCD motora" |
| Exige Documentação | Switch | Se afirmativa ativa | on/off |
| Tipos de Documento | Input | Se exige documentação | "Ex: laudo_pcd, autodeclaracao_racial" |

**Sub-grupo: Mercado-Alvo**

| Campo | Tipo | Placeholder |
|-------|------|-------------|
| Setor | Input | "Ex: Tecnologia" |
| Segmento | Input | "Ex: Fintechs" |
| Público-Alvo | Textarea (2 rows) | "Descreva o perfil ideal do candidato..." |

**Sub-grupo: Canais de Publicação**

| Canal | Tipo |
|-------|------|
| LinkedIn | Switch |
| Website Corporativo | Switch |
| Indeed | Switch |

**Sub-grupo: Link Público** (somente se vaga publicada)

| Elemento | Descrição |
|----------|-----------|
| Link da vaga | Texto + botões "Copiar" / "Abrir" |

> ⚡ = Campo marcado com `<ScreeningBadge/>` na UI — alimenta o enriquecimento do JD e a geração de perguntas WSI

---

#### Seção 2.2: Pessoas (`pessoas` — inline no `JobEditTab.tsx`)

| Sub-grupo | Campo | Tipo |
|-----------|-------|------|
| **Recrutador** | Nome | Input |
| | Email | Input email |
| **Gestor da Vaga** | Nome | Input |
| | Email | Input email |

---

#### Seção 2.3: Processo Seletivo (`processo` → `JobProcessSection.tsx`)

| Elemento | Descrição |
|----------|-----------|
| Lista de etapas (ordenáveis) | Cada etapa: nome, SLA (dias), tipo (Manual/Automatizado/Híbrido/Personalizado), categoria (Sistema/Padrão/Custom) |
| Stages com assistência LIA | Badge "LIA" em etapas automatizadas |
| Botão "Adicionar etapa" | Input nome + configs |
| Arrastar para reordenar | Drag-and-drop |
| Remover etapa | Botão excluir |

Templates disponíveis: `PipelineTemplate` do backend (`GET /api/v1/company/pipeline-templates`)

Cada etapa tem:
- `stageName` — nome editável
- `sla` — SLA em dias (opções: 1, 2, 3, 5, 7, 10, 14)
- `type` — Auto / Manual / Híbrido
- `order` — posição na sequência

---

#### Seção 2.4: Remuneração (`remuneracao` → `JobRemuneracaoSection.tsx`)

| Campo | Tipo | Detalhes |
|-------|------|----------|
| Salário Mínimo | Number | Mostra símbolo de moeda (CURRENCY_SYMBOL) |
| Salário Máximo | Number | — |
| Bônus Mínimo | Number | Opcional |
| Bônus Máximo | Number | Opcional |
| Benefícios | Lista de badges | Sugestões da empresa + adição manual |

**Painel extra:** `compensation-analysis-panel.tsx` — análise de remuneração em tempo real comparando com: (1) Política da empresa, (2) Benchmark de mercado, (3) Histórico interno.

---

### Grupo 2: Configurações de Triagem (3 seções)

Definidas em `SCREENING_SECTIONS` (importado de `@/components/screening-config`), renderizadas pelo `ScreeningConfigContent`.

> As seções de triagem são detalhadas na **FASE 3** abaixo.

---

**Arquivos de referência — Fase 2:**

| Componente | Arquivo |
|------------|---------|
| Tab header com botão "Configurações" | `plataforma-lia/src/components/pages/job-kanban/KanbanJobHeader.tsx` |
| Roteamento da tab | `plataforma-lia/src/components/pages/job-kanban/KanbanPageContent.tsx` |
| Container principal (split-panel) | `plataforma-lia/src/components/jobs/JobEditTab.tsx` |
| Constantes das seções e campos | `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.constants.ts` |
| Hook com lógica | `plataforma-lia/src/components/jobs/job-edit-tab/useJobEditTab.ts` |
| Tipos TypeScript | `plataforma-lia/src/components/jobs/job-edit-tab/job-edit-tab.types.ts` |
| Informações Gerais (27+ campos) | `plataforma-lia/src/components/jobs/job-edit-tab/JobInfoGeralSection.tsx` |
| Processo Seletivo (etapas/SLA) | `plataforma-lia/src/components/jobs/job-edit-tab/JobProcessSection.tsx` |
| Remuneração | `plataforma-lia/src/components/jobs/job-edit-tab/JobRemuneracaoSection.tsx` |
| Header de seção (Editar/Salvar) | `plataforma-lia/src/components/jobs/job-edit-tab/JobSectionHeader.tsx` |
| Badge de screening ⚡ | `plataforma-lia/src/components/jobs/job-edit-tab/ScreeningBadge.tsx` |
| Modal confirmação status | `plataforma-lia/src/components/jobs/job-edit-tab/StatusChangeConfirmModal.tsx` |

---

## FASE 3 — Configurações de Triagem WSI (ScreeningConfigManager)

Após preencher os campos da vaga, o recrutador acessa a seção de **Configurações de Triagem** na mesma tela (Grupo 2 da sidebar). Este componente é o `ScreeningConfigManager`.

### Seção 3.1: Configurações do Roteiro (`configuracoes` → `SCMSectionConfiguracoes.tsx`)

**Sub-grupo: Status e Ativação**

| Elemento | Descrição |
|----------|-----------|
| Status da Triagem | Badge: Não configurada / Não iniciada / Ativa / Pausada / Concluída |
| Toggle Ativar/Pausar | Switch que abre modal de confirmação (`showScreeningToggleConfirm`) |
| Validação | Não permite ativar se houver menos de 3 perguntas configuradas |

**Sub-grupo: Canal de Triagem**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| Chat Web | Toggle | Portal de carreiras |
| WhatsApp | Toggle | WhatsApp Business |
| Ligação Telefônica | Toggle | Chamada de voz via Twilio |
| VoIP Web | Toggle (disabled) | Em breve — coming soon |
| Canal Principal | Select | Define o canal prioritário |
| Ordem de Fallback | Lista arrastável | Sequência de canais alternativos |

**Sub-grupo: Automação WSI / Scoring**

| Campo | Tipo | Opções |
|-------|------|--------|
| Score Mínimo (Preset) | Select | Rigoroso (≥ 4.2), Recomendado (≥ 3.8), Flexível (≥ 3.0) |
| Controle de Paralização (Auto-Approval Limit) | Select | Conservador (5 candidatos), Recomendado (10), Autônomo (25) |
| Timeout de Resposta | Number | Default: 48 horas |
| Máximo de Retentativas | Number | Default: 2x |

**Sub-grupo: Agendamento Automático**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| Ativar agendamento automático | Switch | Agenda entrevista automaticamente após aprovação |
| Score mínimo para auto-agendar | Select preset | Threshold independente |
| Provedor de Calendário | Select | Microsoft / Google |
| Horários disponíveis | Config | Horas disponíveis para agendamento |
| Duração da entrevista | Number | Em minutos |

### Seção 3.2: Descrição do Cargo (`descricao` → `SCMSectionDescricao.tsx`)

Painel de avaliação do JD para triagem — mostra a qualidade da descrição e requisitos técnicos/comportamentais que alimentam as perguntas WSI. Inclui indicadores de completude e sugestões de melhoria.

### Seção 3.3: Perguntas de Triagem (`perguntas` → `SCMSectionPerguntasEdit.tsx`)

| Elemento | Descrição |
|----------|-----------|
| "Gerar WSI Compacto" | ~7 perguntas (4 técnicas + 3 comportamentais), ~12 min |
| "Gerar WSI Completo" | ~12 perguntas (7 técnicas + 5 comportamentais), ~22 min (requer ≥5 skills técnicas) |
| Barra de progresso | Análise → Critérios → Metodologias → Resultado |
| "Editar Perguntas" | Reordenar, excluir, adicionar customizadas ou do banco |
| Blocos WSI | Elegibilidade / Técnico / Comportamental |

**Arquivos:**
- `plataforma-lia/src/components/screening-config/ScreeningConfigManager.tsx`
- `plataforma-lia/src/components/screening-config/SCMSectionConfiguracoes.tsx`
- `plataforma-lia/src/components/screening-config/SCMSectionDescricao.tsx`
- `plataforma-lia/src/components/screening-config/SCMSectionPerguntasEdit.tsx`
- `plataforma-lia/src/components/screening-config/hooks/useScreeningConfigManagerCore.tsx`
- `plataforma-lia/src/hooks/useScreeningConfig.ts`
- **API:** `GET/PUT /api/backend-proxy/jobs/{id}/screening-config`

---

## FASE 4 — Enriquecimento do Job Description

Antes de gerar perguntas, a LIA enriquece o JD rascunho para garantir qualidade suficiente.

### Etapa 4.1: Input

Título da vaga, departamento, senioridade, descrição básica preenchidos na Fase 2.

### Etapa 4.2: Processamento pelo JdEnrichmentService

O serviço enriquece em paralelo:

| Componente | Serviço | Output |
|------------|---------|--------|
| Responsabilidades | `ResponsibilitiesCatalogService` | Lista de deveres alinhados ao cargo/senioridade |
| Skills Técnicas | `SkillsCatalogService` + `MarketBenchmarkService` | Mínimo 9 skills técnicas (obrigatórias + desejáveis + tendências de mercado) |
| Competências Comportamentais | Baseado em área/liderança | Mínimo 5 competências mapeadas para Big Five (OCEAN) |
| Remuneração | `MarketBenchmarkService` | Faixa salarial (min/max/mediana) + sugestão de bônus |
| Calibração Dreyfus | Automática por senioridade | Junior→2, Pleno→3, Senior→4, Lead/Esp→5 |

### Etapa 4.3: WSI Quality Score

Cálculo de 0.0 a 1.0 avaliando se o JD tem dados suficientes para gerar perguntas de alta qualidade:
- Presença de todas as seções obrigatórias
- Mínimo 9 skills técnicas
- Mínimo 5 competências comportamentais

### Etapa 4.4: Revisão pelo recrutador

O recrutador revisa e aceita/rejeita as sugestões de enriquecimento na interface.

**Arquivos:**
- `lia-agent-system/app/domains/job_management/services/jd_enrichment_service.py`
- `lia-agent-system/app/prompts/shared/agent_prompts.yaml` (chave: `job_planner`)

---

## FASE 5 — Geração de Perguntas WSI

### Etapa 5.1: Seleção do modo de geração

Na seção de Perguntas de Triagem, o recrutador escolhe:

| Botão | Quantidade | Duração estimada | Requisito |
|-------|-----------|-----------------|-----------|
| "Gerar WSI Compacto" | ~7 perguntas (4 técnicas + 3 comportamentais) | ~12 min para o candidato | — |
| "Gerar WSI Completo" | ~12 perguntas (7 técnicas + 5 comportamentais) | ~22 min para o candidato | Mínimo 5 skills técnicas no JD |

Barra de progresso multi-step: **Análise → Critérios → Metodologias → Resultado**

### Etapa 5.2: Aplicação dos 4 Frameworks

O `WSIQuestionGenerator` aplica simultaneamente:

| Framework | Aplicação | Calibração por Senioridade |
|-----------|-----------|---------------------------|
| **CBI** (Competency-Based Interviewing) | Estrutura STAR para evidências comportamentais | — |
| **Bloom's Taxonomy** (revisada, 6 níveis) | Profundidade cognitiva das perguntas | Junior=Recordar/Compreender, Pleno=Aplicar/Analisar, Senior=Avaliar/Criar |
| **Dreyfus** (5 estágios) | Complexidade técnica esperada | Junior=Iniciante Avançado(2), Pleno=Competente(3), Senior=Proficiente(4), Lead=Especialista(5) |
| **Big Five/OCEAN** | Perguntas situacionais para traits comportamentais | Junior=2 traits principais, C-Level=5 traits |

### Etapa 5.3: Organização em Blocos WSI

| Bloco | Tipo | Conteúdo |
|-------|------|----------|
| Bloco 2 | Elegibilidade | Perguntas padrão da empresa, knock-out questions (relocação, salário) |
| Bloco 3 | Técnico | Investigação de skills via Bloom/Dreyfus |
| Bloco 4 | Comportamental/Fit | Baseado em Big Five + CBI (STAR) |

### Etapa 5.4: Validação FairnessGuard (3 camadas)

| Camada | Método | Ação |
|--------|--------|------|
| L1 — Viés Explícito | Regex alta precisão | **BLOQUEIA** (gênero, idade, raça, religião) |
| L2 — Viés Implícito | Proxies socioeconômicos, estéticos | **ALERTA** |
| L3 — Viés Semântico | Análise LLM contextual (setor-dependente) | **CONTEXTUAL** |

### Etapa 5.5: Sistema de Fallback (2 níveis)

| Nível | Quando | O que faz |
|-------|--------|-----------|
| Pipeline Fallback | Sem perguntas salvas | Gera via WSIService com base no JD |
| Hardcoded Fallback | Pipeline falha | Perguntas universais embutidas no código |
| Retry com hint | Pergunta falha na validação | Regenera até 3x com `improvement_hint` |
| Manual Review Flag | Todas as retries falham | Marca `needs_manual_review=True` |

### Etapa 5.6: Edição pelo recrutador

Botão "Editar Perguntas" → Interface para reordenar, excluir, adicionar perguntas customizadas ou do banco de perguntas.

**Arquivos:**
- `plataforma-lia/src/components/screening-config/SCMSectionPerguntasEdit.tsx`
- `lia-agent-system/app/domains/cv_screening/services/wsi_service.py`
- `lia-agent-system/app/domains/cv_screening/constants/wsi_constants.py`
- `lia-agent-system/app/shared/compliance/fairness_guard.py`

---

## FASE 6 — Publicação da Vaga

### Etapa 6.1: Botão "Publicar"

No header do Kanban, o recrutador clica "Publicar":

1. Auto-salva todos os campos no backend
2. Gera link público de candidatura
3. Atualiza status da vaga para "Ativa"
4. Exibe mensagem de sucesso com link compartilhável

**Arquivo:** `plataforma-lia/src/components/pages/job-kanban/hooks/useKanbanPublishing.ts`

---

## FASE 7 — Busca e Adição de Candidatos

### Etapa 7.1: Busca no Funil de Talentos (`/funil`)

| Modo | Descrição | Custo |
|------|-----------|-------|
| Busca Local | Base interna da empresa | Gratuito |
| Busca Global | Pearch AI — 800M+ perfis | Consome créditos |
| Híbrida | Ambas simultaneamente | — |

**Interface de Busca (SmartSearchInput):**
- Input de linguagem natural (ex: "Desenvolvedor Python sênior em SP")
- Claude Sonnet extrai entidades: skills, localização, senioridade, título
- Context Pills editáveis para refinar a interpretação
- Seletor de Fonte (Local / Global / Híbrido)
- Staging de candidatos globais: Candidatos do Pearch ficam em `external_candidate_profiles` até o recrutador agir

### Etapa 7.2: Adicionar Candidatos à Vaga (AddToJobModal)

1. Selecionar candidatos no funil (seleção múltipla — bulk actions)
2. Clicar "Adicionar à Vaga"
3. No modal: buscar e selecionar vaga aberta, verificação de duplicata automática, selecionar etapa inicial (default: "Triagem")

**API:** `POST /api/backend-proxy/search/vacancy/{jobId}/add-candidates`

**Arquivos:**
- `plataforma-lia/src/components/search/smart-search-input.tsx`
- `plataforma-lia/src/hooks/use-talent-funnel.ts`
- `plataforma-lia/src/components/modals/add-to-job-modal.tsx`

---

## FASE 8 — Disparo da Triagem

### Etapa 8.1: Seleção de candidatos para triagem

No Kanban da vaga, o recrutador seleciona candidatos na etapa "Triagem" e dispara o envio.

### Etapa 8.2: Mecanismo de disparo

- Via drag-and-drop no Kanban → abre `UniversalTransitionModal`
- Via modal de convite WSI (`wsi-triagem-invite-modal.tsx`)
- LIA Auto → `TransitionChatPanel` onde o recrutador conversa com a LIA sobre critérios

### Etapa 8.3: Envio ao candidato

A LIA envia convite nos canais configurados (Fase 3, Seção 3.1):
- E-mail com link para chat de triagem
- WhatsApp Business (se habilitado)
- Ligação telefônica via Twilio (se habilitado)

**Arquivos:**
- `plataforma-lia/src/components/kanban/components/UniversalTransitionModal.tsx`
- `plataforma-lia/src/components/wsi/wsi-triagem-invite-modal.tsx`

---

## FASE 9 — Triagem do Candidato (WSI Interview Graph)

### Etapa 9.1: Candidato acessa a triagem

- Via link recebido (email/WhatsApp) → página pública PUB-001
- **API:** `POST /api/v1/wsi/interview-graph/sessions` → inicia sessão

### Etapa 9.2: Gate 1 — Consentimento LGPD

`ConsentCheckerService` verifica consentimento antes de prosseguir.

### Etapa 9.3: Entrevista por blocos (máquina de estados WSIInterviewGraph)

O LangGraph `StateGraph` conduz a entrevista:

```
init → load_context → generate_question ↔ validate_response → score_response → advance → (loop) → generate_feedback → complete
```

| Nó | Função |
|----|--------|
| `load_context` | Carrega perguntas do DB (`job_screening_questions`), fallback para WSIService/hardcoded |
| `generate_question` | Apresenta pergunta atual ao candidato |
| `validate_response` | Segurança (`PromptInjectionGuard`), PII Masking (`strip_pii_for_llm_prompt`), `FairnessGuard` |
| `score_response` | Scoring determinístico via `calculate_wsi_deterministic` |
| `advance` | Avança para próxima pergunta ou finaliza |
| `generate_feedback` | Calcula WSI final, gera recomendação |

**PII Masking:** Dados pessoais são anonimizados ANTES de qualquer análise por LLM.

**Arquivo principal:** `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`

---

## FASE 10 — Scoring Determinístico

### Etapa 10.1: Extração (LLM)

Para cada resposta, o LLM extrai:
- Autodeclaração de nível
- Contexto e evidências
- Keywords técnicas
- Métricas citadas
- Componentes STAR (Situação, Tarefa, Ação, Resultado)

### Etapa 10.2: Cálculo (100% determinístico)

**Fórmula para perguntas técnicas:**
```
Score = (0.35 × Autodeclaração) + (0.40 × Qualidade do Contexto) + (0.25 × Alinhamento Bloom)
```

**Fórmula para perguntas comportamentais:**
```
Score = (0.35 × Estrutura STAR) + (0.40 × Sinais de Trait/Contexto) + (0.25 × Alinhamento Bloom)
```

Componente STAR — peso do "Action" (A) = 40% (maior peso)

### Etapa 10.3: Ajustes pós-cálculo

| Ajuste | Condição | Efeito |
|--------|----------|--------|
| Bônus Humildade | Autodeclaração modesta MAS contexto expert | +bônus |
| Penalidade Inflação | Autodeclaração alta MAS contexto fraco | -penalidade |
| Penalidade Resposta Genérica | Sem evidências concretas | -penalidade |

Score final: clamped entre **1.0 e 5.0**

### Etapa 10.4: WSI Final (Global)

```
WSI Final = (Peso Técnico × Média Técnica) + (Peso Comportamental × Média Comportamental)
```

Distribuição típica: **70% técnico / 30% comportamental** (ajustável por senioridade — seniors recebem mais peso comportamental)

**Arquivo:** `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py`

---

## FASE 11 — Ranking e Recomendação

### Etapa 11.1: Ranking Unificado (LIAScoreService)

```
Ranking_Score = (Rubricas_Score × W_rubricas) + (WSI_Score × W_wsi)
              + (Prerequisites_Score × W_prereq) + (Recency_Boost × W_recency)
              + Calibration_Adjustment) × Completeness_Factor
```

| Componente | Peso típico |
|------------|------------|
| CV Rubrics | 40% |
| WSI Score | 25% |
| Prerequisites | 20% |
| Recency Boost | 15% (+100 pontos se ativo nos últimos 7 dias) |

### Etapa 11.2: Recomendação automática ("Opinião da LIA")

| WSI Final | Classificação | Label |
|-----------|--------------|-------|
| ≥ 3.75 (7.5/10) | Aprovado / Top Talent | `highly_recommended` |
| 3.0 – 3.74 | Review | `review_required` |
| < 3.0 | Não Aprovado | `not_recommended` |

**Nenhum candidato é aprovado automaticamente** — o recrutador tem a decisão final no Kanban. A recomendação aparece como "Opinião da LIA" e pode ser confirmada ou sobrescrita (`recruiter_override_reason`).

**Arquivos:**
- `lia-agent-system/app/services/lia_score_service.py`
- `lia-agent-system/app/api/v1/opinions.py`

---

## FASE 12 — Outputs Pós-Triagem

### 12A: Parecer para o Recrutador (7 seções)

1. Resumo executivo
2. Experiência profissional
3. Competências técnicas
4. Competências comportamentais
5. Resultados da triagem
6. Pontos fortes / Pontos de atenção
7. Recomendação final

- Gerado por LLM sintetizando CV + scores WSI + transcrição + contexto da vaga
- `FairnessGuard` valida o texto contra viés
- Modelo: `LiaOpinion` com campos: `summary`, `strengths`, `concerns`, `gaps`, `technical_analysis`, `behavioral_analysis`, `recommendation`

### 12B: Feedback Personalizado para o Candidato

- **Qualitativo** — NUNCA revela scores numéricos
- Baseado em Bloom/Dreyfus para enquadrar sugestões de desenvolvimento
- Calibração de tom por senioridade: Estágio=Encorajador, Senior=Profissional, Diretor=Executivo
- **Proibições:** Nunca expõe Big Five traits, Red Flags ou scores numéricos
- 3 formatos: Email (completo), WhatsApp (condensado), Web Chat (interativo)

> **Ponto a corrigir identificado:** O tom do feedback varia com a decisão (aprovado=entusiasta, reprovado=respeitoso). Como o candidato não sabe a decisão no momento da triagem, o tom deveria ser neutro/construtivo para todos.

**Arquivos:**
- `lia-agent-system/app/domains/cv_screening/services/wsi_feedback_generator.py`
- `lia-agent-system/app/domains/cv_screening/services/personalized_feedback_service.py`

---

## Mapa de Arquivos Completo

### Frontend (`plataforma-lia/src/`)

| Fase | Arquivo Principal |
|------|-------------------|
| 1 — Criação | `components/modals/create-job-modal.tsx`, `components/pages/jobs/useJobsStatusHandlers.ts` |
| 2 — Tab Configurações (container) | `components/jobs/JobEditTab.tsx` |
| 2 — Tab header | `components/pages/job-kanban/KanbanJobHeader.tsx` |
| 2 — Roteamento tab | `components/pages/job-kanban/KanbanPageContent.tsx` |
| 2 — Constantes/campos | `components/jobs/job-edit-tab/job-edit-tab.constants.ts` |
| 2 — Hook lógica | `components/jobs/job-edit-tab/useJobEditTab.ts` |
| 2.1 — Informações Gerais | `components/jobs/job-edit-tab/JobInfoGeralSection.tsx` |
| 2.3 — Processo Seletivo | `components/jobs/job-edit-tab/JobProcessSection.tsx` |
| 2.4 — Remuneração | `components/jobs/job-edit-tab/JobRemuneracaoSection.tsx` |
| 2 — UI helpers | `job-edit-tab/JobSectionHeader.tsx`, `ScreeningBadge.tsx`, `StatusChangeConfirmModal.tsx` |
| 3 — Config Triagem | `components/screening-config/ScreeningConfigManager.tsx`, `SCMSectionConfiguracoes.tsx` |
| 3 — Descrição JD | `components/screening-config/SCMSectionDescricao.tsx` |
| 5 — Geração Perguntas | `components/screening-config/SCMSectionPerguntasEdit.tsx` |
| 6 — Publicação | `components/pages/job-kanban/hooks/useKanbanPublishing.ts` |
| 7 — Busca Candidatos | `components/search/smart-search-input.tsx`, `hooks/use-talent-funnel.ts`, `components/modals/add-to-job-modal.tsx` |
| 8 — Disparo | `components/kanban/components/UniversalTransitionModal.tsx`, `components/wsi/wsi-triagem-invite-modal.tsx` |

### Backend (`lia-agent-system/`)

| Fase | Arquivo Principal |
|------|-------------------|
| 0 — Setup Empresa | `app/api/v1/recruitment_stages.py`, `libs/models/lia_models/recruitment_stages.py` |
| 4 — Enriquecimento JD | `app/domains/job_management/services/jd_enrichment_service.py` |
| 5 — Geração Perguntas | `app/domains/cv_screening/services/wsi_service.py`, `app/domains/cv_screening/constants/wsi_constants.py` |
| 5 — FairnessGuard | `app/shared/compliance/fairness_guard.py` |
| 9 — Entrevista WSI | `app/domains/cv_screening/agents/wsi_interview_graph.py` |
| 10 — Scoring | `app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| 11 — Ranking | `app/services/lia_score_service.py`, `app/api/v1/opinions.py` |
| 12 — Feedback | `app/domains/cv_screening/services/wsi_feedback_generator.py`, `app/domains/cv_screening/services/personalized_feedback_service.py` |
| Prompts | `app/prompts/shared/agent_prompts.yaml` |
