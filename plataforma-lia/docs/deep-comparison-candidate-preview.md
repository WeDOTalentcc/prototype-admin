# Comparacao Profunda — Candidate Preview
## Vue/Vuetify/Nuxt (Producao) vs React/Tailwind/Next.js (Replit)

**Data:** 2026-04-03
**Fonte Vue:** Repositorio `wedotalent/ats_front` branch `develop` (GitHub API)
**Fonte React:** `plataforma-lia/src/components/candidate-preview/` (Replit)
**Complemento:** `audit-candidate-preview-qa.md` (63 issues mapeados)

---

## 1. MAPEAMENTO DE COMPONENTES — Codigo Real

### 1.1 Arvore de Componentes

```
VUE (Producao)                                  REACT (Replit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pages/user/candidates/[id].vue (102 linhas)     app/funil-de-talentos/page.tsx
features/candidates/preview.vue (855 linhas)    candidate-preview.tsx (858 linhas)
features/candidates/overview.vue (138 linhas)   CandidatePreviewProfileTab.tsx (861 linhas)
features/candidates/lia_assessment.vue (458)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/score_analysis (692)  CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/skills.vue (106)      CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/experiences.vue (134) CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/educations.vue (143)  CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/languages.vue (92)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/remunerations (191)   CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/addresses.vue (96)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/layout.vue (53)       Card/CardHeader/CardTitle (shadcn)
features/candidates/applies.vue (30 linhas)     --- (sem equivalente direto)
features/candidates/files/wrapper.vue (120)     CandidateFilesTab.tsx (774 linhas)
features/candidates/files/uploader.vue (125)    CandidateFilesTab.tsx (embutido)
features/candidates/curriculum_text.vue (513)   --- (sem equivalente; Replit usa FilePreviewModal)
--- (sem equivalente)                           CandidateActivitiesTab.tsx (278 linhas)
--- (sem equivalente)                           CandidateOpinionsTab.tsx (293 linhas)
--- (sem equivalente)                           OpinionCard.tsx
--- (sem equivalente)                           LiaChatModal.tsx
--- (sem equivalente)                           FilePreviewModal.tsx
--- (sem equivalente)                           activities/ActivityTimeline.tsx
--- (sem equivalente)                           activities/ActivityFilters.tsx
--- (sem equivalente)                           activities/ActivityExpandedDetails.tsx (878)
--- (sem equivalente)                           useCandidatePreviewCore.tsx (666 linhas)
--- (sem equivalente)                           useCandidateFiles.tsx
features/lia/candidates/sourced-profile-*       --- (Replit unifica no mesmo preview)
  sourced-profile-preview.vue (236)
  sourced-profile-header.vue (339)
  sourced-profile-overview.vue (183)
  sourced-profile-experience.vue (224)
  sourced-profile-education.vue (158)
  sourced-profile-skills.vue (130)
  sourced-profile-evaluation.vue (195)
  sourced-profile-summary.vue (24)
  sourced-profile-actions.vue (334)
composables/useCandidateFilters.ts (300)        useCandidatePreviewCore.tsx (embutido)
composables/useCandidateMatches.ts (39)         --- (sem equivalente direto)
stores/candidate_feedbacks.ts (80)              useCandidatePreviewCore.tsx (embutido)
```

### 1.2 Contagem Total

| Metrica | Vue (Producao) | React (Replit) |
|---|---|---|
| Arquivos de preview | 30+ | 13 |
| Linhas totais | ~6.345 | ~6.196 |
| Tabs implementadas | 3 (Perfil, Atividades, Arquivos) | 4 (Perfil, Atividades, Arquivos, Pareceres) |
| Modais | 3 (Email, Enrich, AddToJob) | 7+ (LIA, Screening, DISC, BigFive, FilePreview, InsufficientData, LiaChat) |
| Cards de dados | 9 | 9 (embutidos no ProfileTab) |
| Sub-componentes atividades | 0 (tab basica) | 3 (Timeline, Filters, ExpandedDetails) |

---

## 2. COMPARACAO ESTRUTURAL — HEADER DO CANDIDATO

### 2.1 Vue — preview.vue (linhas 140-230)

```vue
<div class="d-flex py-3 px-3 ga-3 border-b border-border-color border-opacity-100">
  <v-avatar size="40">
    <img v-if="candidate_record.avatar_url" :src="candidate_record.avatar_url" />
    <span v-else-if="candidate_record.name" class="f16 text-primary font-weight-medium">
      {{ candidate_record.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() }}
    </span>
  </v-avatar>
  <div>
    <h2 class="f13 font-weight-semibold font-serif">{{ candidate_record.name }}</h2>
    <span class="f9 text-primary border border-primary rounded-pill px-1">{{ candidate_record.id }}</span>
    <!-- Score circular -->
    <v-progress-circular :model-value="candidateScore" :size="28" :width="3" :color="scoreColor">
      <span class="f9 font-weight-bold">{{ candidateScore }}</span>
    </v-progress-circular>
    <!-- Cargo + Empresa -->
    <span class="f11 text-body-light">{{ candidate_record.role_name }}</span>
    <span class="tiny-circle"></span>
    <span>{{ candidate_record.current_company }}</span>
    <!-- Apenas LinkedIn -->
    <Icon name="lucide-linkedin" :color="candidate_record.linkedin ? 'primary' : 'body-light'" />
  </div>
</div>
```

### 2.2 React — candidate-preview.tsx (linhas 220-350, codigo real)

```tsx
<div className="p-3 border-b border-lia-border-subtle bg-lia-bg-primary">
  <div className="flex items-start gap-3 mb-1.5">
    <CandidateAvatar name={c.name} avatarUrl={c.avatar_url} size="lg" showRing />
    <div className="flex-1 min-w-0">
      {/* Row 1: Nome + Short ID + Seniority + Experiencia + LGPD */}
      <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
        <h3 className={`${textStyles.title} truncate`}>{c.name}</h3>
        <Badge className="text-micro font-mono bg-lia-bg-tertiary">
          {generateShortId(c.name, c.id)}
        </Badge>
        {c.seniority_level && <Badge className={badgeStyles.warning}>{c.seniority_level}</Badge>}
        {c.years_of_experience && <Badge>{c.years_of_experience} anos</Badge>}
        {/* Badge LGPD: consentimento comunicacao */}
        {c.communication_consent !== undefined && (
          <Badge className={c.communication_consent ? 'bg-status-success/10' : 'bg-status-error/10'}>
            {c.communication_consent ? <CheckCircle /> : <AlertCircle />} LGPD
          </Badge>
        )}
      </div>
      {/* Row 2: Cargo • Empresa • Segmento */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <p className={textStyles.bodySmall}>{c.position || 'Cargo nao informado'}</p>
        <span>•</span>
        <p>{c.current_company || 'Empresa'}</p>
        {c.industry && <><span>•</span><p>{c.industry}</p></>}
      </div>
    </div>
    {/* Botoes header: LIA Analysis + Expand + Close */}
    <div className="flex items-center gap-1">
      <LiaAnalysisModal><Button><Brain className="w-5 h-5 text-wedo-cyan" /></Button></LiaAnalysisModal>
      <Button onClick={onOpenFullPage}><Expand /></Button>
      <Button onClick={onClose}><X /></Button>
    </div>
  </div>
  {/* Row 3: Datas */}
  <div className="flex items-center gap-2 flex-wrap">
    {createdAt && <span><Calendar /> Cadastrado em {formatDate(createdAt)}</span>}
    {updatedAt && <span><Clock /> Atualizado em {formatDate(updatedAt)}</span>}
    {lastContactedAt && <span><Mail /> Ultimo contato {formatDate(lastContactedAt)}</span>}
  </div>
  {/* Row 4: Indicadores especiais (Open to Work, Top University, etc.) */}
  {/* Row 5: Localizacao + Redes sociais expandidas */}
  {/* Row 6: Scores LIA/Fit + Contato (email, telefone) */}
  {/* Row 7: Botoes de acao inline */}
</div>
```

**NOTA:** O header React real e significativamente mais complexo que o resumo acima. Inclui 7 "rows" de informacao: nome/badges, cargo/empresa, datas, indicadores especiais (Open to Work, Top University, Decision Maker, LCNU), localizacao + redes, scores + contato, e botoes de acao.

### 2.3 DIFERENCAS CRITICAS DO HEADER

| Aspecto | Vue (Producao) | React (Replit) | Impacto |
|---|---|---|---|
| **Avatar** | `v-avatar size="40"`, iniciais inline | `CandidateAvatar` com `showRing` para status, `size="lg"` | Ring de status ausente |
| **ID Badge** | Mostra ID numerico raw (`4681`) | `generateShortId(name, id)` → `A72E80` formato alfanumerico mono | UX confusa com ID numerico |
| **Badges extras** | Nenhum | Seniority level + Anos experiencia + LGPD consent | **3 badges ausentes** |
| **Indicadores** | Nenhum | Open to Work, Top University, Decision Maker, LCNU | **4 indicadores ausentes** |
| **Redes sociais** | Apenas LinkedIn | LinkedIn + GitHub + StackOverflow + X + Portfolio | 4 redes ausentes |
| **Datas** | Nenhuma data exibida | Cadastrado, Atualizado, Ultimo contato com icones | Info temporal ausente |
| **Scores header** | Score circular `v-progress-circular` (apenas 1) | LIA Score + Fit Score lado a lado com cores | Vue tem 1, React tem 2 |
| **Contato direto** | Nenhum no header | Email + telefone copiaveis inline no header | **Ausente** |
| **Localizacao** | Nao exibida no header | Cidade, Estado, Pais com icone MapPin | **Ausente** |
| **Cargo/Empresa** | `<span class="tiny-circle">` separador | `•` bullet + segmento/industria | React inclui industria |
| **Padding** | `py-3 px-3` (12px) | `p-3` (12px) | Equivalente |
| **Tipografia** | `f13 font-weight-semibold font-serif` | `textStyles.title` (sans-serif) | Serif vs Sans-serif |

### 2.4 CORRECAO SUGERIDA — Header Vue

```vue
<!-- ANTES: preview.vue linhas 140-180 -->
<!-- DEPOIS: Adicionando datas, redes sociais e ID formatado -->
<div class="d-flex py-2 px-2 ga-2 border-b border-border-color border-opacity-100">
  <v-avatar size="40" class="position-relative">
    <!-- Avatar com ring de status -->
    <div
      v-if="candidateStatus"
      class="position-absolute rounded-circle"
      :class="`border-2 border-${statusColor}`"
      style="inset: -2px; z-index: 1;"
    />
    <img v-if="candidate_record.avatar_url" :src="candidate_record.avatar_url" />
    <span v-else class="f16 text-primary font-weight-medium d-flex align-center justify-center w-100 h-100"
      style="background-color: rgba(var(--v-theme-primary), 0.2)">
      {{ getInitials(candidate_record.name) }}
    </span>
  </v-avatar>
  <div class="flex-grow-1" style="min-width: 0;">
    <div class="d-flex align-center ga-1 flex-wrap mb-0">
      <h2 class="f12 font-weight-semibold text-on-surface">{{ candidate_record.name }}</h2>
      <span class="f8 font-mono text-primary border border-primary border-opacity-100 rounded-pill px-1"
        style="background-color: rgba(var(--v-theme-primary), 0.15);">
        {{ formatShortId(candidate_record.id) }}
      </span>
    </div>
    <p class="f10 text-body-light mb-1">
      {{ candidate_record.role_name }}
      <span class="mx-1">•</span>
      {{ candidate_record.current_company }}
    </p>
    <!-- NOVO: Datas -->
    <div class="d-flex align-center ga-2 f9 text-body-light mb-1">
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-calendar" size="10" color="body-light" />
        Cadastrado em {{ formatDate(candidate_record.created_at) }}
      </span>
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-clock" size="10" color="body-light" />
        Atualizado em {{ formatDate(candidate_record.updated_at) }}
      </span>
    </div>
    <!-- NOVO: Redes sociais expandidas -->
    <div class="d-flex align-center ga-1">
      <Icon name="lucide-linkedin" size="14"
        :color="candidate_record.linkedin ? 'primary' : 'body-light'"
        :clickable="!!candidate_record.linkedin"
        @click="openUrl(candidate_record.linkedin)" />
      <Icon name="lucide-github" size="14"
        :color="candidate_record.github ? 'on-surface' : 'body-light'"
        :clickable="!!candidate_record.github"
        @click="openUrl(candidate_record.github)" />
      <Icon name="lucide-globe" size="14"
        :color="candidate_record.portfolio ? 'on-surface' : 'body-light'"
        :clickable="!!candidate_record.portfolio"
        @click="openUrl(candidate_record.portfolio)" />
    </div>
  </div>
</div>
```

```js
// Adicionar ao <script setup> de preview.vue:
function formatShortId(id) {
  if (!id) return ''
  const hash = String(id).split('').reduce((a, c) => ((a << 5) - a + c.charCodeAt(0)) | 0, 0)
  const hex = Math.abs(hash).toString(16).toUpperCase().padStart(6, '0').slice(0, 6)
  return hex.slice(0, 2).replace(/[0-9]/g, c => String.fromCharCode(65 + Number(c))) + hex.slice(2, 6)
}

function openUrl(url) {
  if (url) window.open(url.startsWith('http') ? url : `https://${url}`, '_blank')
}
```

---

## 3. COMPARACAO — TABS E NAVEGACAO

### 3.1 Vue — preview.vue (linhas 260-300)

```vue
<div class="candidate-preview-tabs">
  <v-tabs v-model="active_tab" grow density="compact" class="f11 font-weight-medium">
    <v-tab value="profile">
      <Icon name="lucide-user" size="14" class="mr-1" />Perfil Completo
    </v-tab>
    <v-tab value="activities">
      <Icon name="lucide-clock" size="14" class="mr-1" />Atividades
    </v-tab>
    <v-tab value="files">
      <Icon name="lucide-file-text" size="14" class="mr-1" />Arquivos
    </v-tab>
    <v-tab value="curriculum">
      <Icon name="lucide-file" size="14" class="mr-1" />Curriculo
    </v-tab>
  </v-tabs>
</div>
```

### 3.2 React — candidate-preview.tsx (linhas 300-340)

```tsx
<div className="flex border-b border-lia-border-subtle bg-lia-bg-primary sticky top-0 z-10">
  {['perfil', 'atividades', 'arquivos', 'pareceres'].map((tab) => (
    <button key={tab}
      onClick={() => setActiveTab(tab)}
      className={`flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium
        border-b-2 transition-colors ${
          activeTab === tab
            ? 'border-lia-btn-primary-bg text-lia-text-primary bg-lia-bg-secondary'
            : 'border-transparent text-lia-text-tertiary hover:text-lia-text-secondary'
        }`}
    >
      {tabIcons[tab]} {tabLabels[tab]}
      {tab === 'pareceres' && opinionsCount > 0 && (
        <Badge className="text-micro px-1 py-0 ml-1">{opinionsCount}</Badge>
      )}
    </button>
  ))}
</div>
```

### 3.3 DIFERENCAS CRITICAS DAS TABS

| Aspecto | Vue (Producao) | React (Replit) | Impacto |
|---|---|---|---|
| **Numero de tabs** | 4 (Perfil, Atividades, Arquivos, Curriculo) | 4 (Perfil, Atividades, Arquivos, Pareceres) | Tab "Pareceres" **ausente** no Vue; tab "Curriculo" **ausente** no React |
| **Tab Pareceres** | **NAO EXISTE** | Historico de pareceres LIA + Analises com subtabs | **Critico** — perda de historico |
| **Badge de contagem** | Nenhuma tab mostra contador | Tab Pareceres mostra `opinionsCount` | Info util ausente |
| **Componente** | `v-tabs` Vuetify com `grow density="compact"` | `button` customizado com Tailwind | Vuetify fornece animacao built-in |
| **Sticky** | CSS manual `.candidate-preview-tabs { position: sticky }` | Tailwind `sticky top-0 z-10` | Equivalente |

### 3.4 CORRECAO SUGERIDA — Tab Pareceres no Vue

```vue
<!-- Adicionar ao v-tabs em preview.vue -->
<v-tab value="opinions">
  <Icon name="lucide-brain" size="14" class="mr-1" />
  Pareceres
  <v-chip v-if="opinionsCount > 0" size="x-small" color="primary" variant="tonal" class="ml-1 f9">
    {{ opinionsCount }}
  </v-chip>
</v-tab>

<!-- Adicionar ao v-window -->
<v-window-item value="opinions">
  <CandidateOpinionsTab
    :candidate="candidate_record"
    :opinions-history="opinionsHistory"
    :is-loading="isLoadingOpinions"
  />
</v-window-item>
```

---

## 4. COMPARACAO — TAB PERFIL / OVERVIEW

### 4.1 Estrutura Vue — overview.vue

O Vue organiza o conteudo em **grid de 1 coluna** com cards separados:

```
overview.vue
  ├── LiaAssessment (Parecer LIA — 458 linhas)
  ├── ScoreAnalysis (Score — 692 linhas, condicional)
  ├── Skills (106 linhas)
  ├── Experiences (134 linhas)
  ├── Educations (143 linhas)
  ├── Languages (92 linhas)
  ├── Remunerations (191 linhas)
  └── Addresses (96 linhas)
```

### 4.2 Estrutura React — CandidatePreviewProfileTab.tsx

O React **embute tudo** em um unico componente (861 linhas) com densidade maior:

```
CandidatePreviewProfileTab.tsx
  ├── ExperienceHighlightCard (card destaque)
  ├── Card "Parecer LIA" (inline, ~150 linhas)
  │   ├── Score circular SVG
  │   ├── WSI badge
  │   ├── Dimensoes com progress bars
  │   ├── Resumo/Highlights/Red Flags
  │   └── Botao "Analisar com LIA"
  ├── Card "Mapa de Skills" (~80 linhas)
  │   ├── Chips com cores por nivel
  │   └── Barras de proficiencia
  ├── Card "Experiencia Profissional" (~90 linhas)
  ├── Card "Formacao Academica" (~60 linhas)
  ├── Card "Idiomas" (~40 linhas)
  ├── Card "Remuneracao" (~80 linhas)
  │   ├── Salario atual + pretensao
  │   ├── Modelo (CLT/PJ/Freelance)
  │   └── Moeda formatada
  └── Card "Endereco" (~30 linhas)
```

### 4.3 DIFERENCAS NO CONTEUDO DO PERFIL

| Card | Vue (Producao) | React (Replit) | Delta |
|---|---|---|---|
| **Parecer LIA** | `lia_assessment.vue` (458 linhas) — Score circular `v-progress-circular size=72`, Recomendacao chip, WSI chip, Dimensoes com `v-progress-linear`, Highlights/Red Flags, Skills agrupadas por tipo | `CandidatePreviewProfileTab` — Score SVG customizado `w-7 h-7`, WSI badge, Dimensoes com barras Tailwind `h-1`, Highlights/Red Flags colapsaveis, Botao re-analise | Vue mais detalhado com 458 vs ~150 linhas; React mais compacto |
| **Score Analysis** | `score_analysis.vue` (692 linhas!) — Card separado com score detalhado, metodo de scoring, requisitos expandiveis, metricas de confianca | **Nao existe como card separado** — embutido no Parecer LIA no React | Vue tem score analysis independente e mais rico |
| **Skills** | `skills.vue` (106 linhas) — Chips `v-chip` com cores por `level` (strong/mentioned/learning) | Inline — Chips com cores por nivel + barras de proficiencia | React adiciona barras visuais |
| **Experiences** | `experiences.vue` (134 linhas) — Busca API `/users/experiences` ou usa data local, formatacao `Mmm/YYYY` | Inline ~90 linhas — Dados do candidato direto, formato similar | Equivalente funcional |
| **Educations** | `educations.vue` (143 linhas) — Busca API `/users/educations`, mostra tipo formacao | Inline ~60 linhas — Dados diretos | Vue busca API separada |
| **Languages** | `languages.vue` (92 linhas) — Chips com nivel (nativo/avancado/etc) | Inline ~40 linhas — Lista simples | Equivalente |
| **Remunerations** | `remunerations.vue` (191 linhas) — **Muito detalhado**: salario base, anualizado (13.33x), componentes variaveis, beneficios com valor/dia vs /mes, subtotal, total anual com card verde | Inline ~80 linhas — Salario atual + pretensao + modelo simples | **Vue significativamente superior** em detalhamento salarial |
| **Addresses** | `addresses.vue` (96 linhas) — Busca API `/users/addresses` ou usa data local | Inline ~30 linhas — Dados diretos | Vue busca API separada |
| **ExperienceHighlight** | **Nao existe** | `ExperienceHighlightCard` no topo do perfil | Feature exclusiva React |

### 4.4 INSIGHT IMPORTANTE

O **card de Remuneracao** do Vue (`remunerations.vue`) e **significativamente mais completo** que o React:
- Calcula remuneracao anualizada (13.33x)
- Lista componentes variaveis (bonus, PLR, etc.)
- Mostra beneficios com valor diario vs mensal
- Subtotais por categoria
- Card de "Remuneracao Total Anual" com destaque visual

Esta e uma area onde o **Vue e superior** e o React deveria adaptar.

### 4.5 INSIGHT — Score Analysis

O **card de Score Analysis** do Vue (`score_analysis.vue`, 692 linhas) e o componente mais complexo do preview inteiro. Inclui:
- Score circular com confianca
- Metodo de scoring (LIA/WSI/Manual)
- Resumo one-liner
- Pontos positivos/negativos com contagem
- Skills principais com cores
- Requisitos da vaga com status met/partial/not_met
- Detalhes expandiveis por requisito com prioridade e confianca
- Grid de skills matched vs missing

O React **nao tem equivalente direto** como card separado — esta informacao esta parcialmente no Parecer LIA.

---

## 5. COMPARACAO — TAB ATIVIDADES

### 5.1 Vue — Atividades (BASICA)

O Vue **nao tem componente dedicado de atividades** no preview. O `applies.vue` (30 linhas) e apenas:

```vue
<!-- features/candidates/applies.vue -->
<template>
  <div class="pa-3">
    <AppliesTable :candidate_id="candidate_record.id" />
  </div>
</template>
```

Nao ha timeline, filtros, ou expansao de detalhes.

### 5.2 React — Atividades (RICA)

O React tem **3 sub-componentes** para atividades:

```
CandidateActivitiesTab.tsx (278 linhas)
  ├── ActivityFilters.tsx — Filtros por tipo + periodo + view mode
  │   Tipos: todos, emails, entrevistas, lia, candidaturas, testes, ofertas, avaliacoes
  │   Periodos: todos, 7 dias, 30 dias, 3 meses
  │   Views: timeline, lista
  ├── ActivityTimeline.tsx — Timeline visual com dots coloridos
  │   Cada atividade tem: icone, titulo, timestamp, badge de tipo, preview
  │   Click expande para detalhes
  └── ActivityExpandedDetails.tsx (878 linhas!) — Detalhes expandidos
      Tipos suportados:
      - email-sent: preview do email, destinatario, assunto
      - interview-scheduled: data, hora, participantes, link
      - video-interview: player de video, transcricao, highlights
      - lia-analysis: parecer completo com metricas
      - assessment: resultado de avaliacao
      - job-application: vaga aplicada, status, data
      - rubric_evaluation: rubrica com scores por criterio
      - test-result: resultado de teste tecnico/comportamental
      - onboarding: checklist de onboarding
      - screening-audio/video: player com transcricao e perguntas
      - disc-assessment: modal DISC completo
      - big-five: modal Big Five completo
```

### 5.3 DELTA CRITICO

**NOTA IMPORTANTE:** O React usa **dados demo** (`getDemoActivities()`) na tab Atividades. Os 15+ tipos de atividade listados abaixo sao **aspiracionais** — o backend nao tem endpoint real de timeline. O Vue `applies.vue` usa `AppliesTable` que busca dados **reais** de candidaturas do backend.

**O Vue nao tem (mas o React tem como UI pronta para backend futuro):**
- Timeline visual de atividades (UI implementada, dados mock)
- Filtros por tipo/periodo (UI implementada)
- Detalhes expandidos (878 linhas de UI)
- Suporte a 15+ tipos de atividade (UI)
- Modais de screening (audio/video com transcricao)
- DISC Assessment modal
- Big Five modal
- Rubric evaluation details

**O Vue TEM que o React nao tem:**
- `AppliesTable` com dados reais de candidaturas
- Integracao com backend existente de applies

### 5.4 CORRECAO SUGERIDA — Atividades Vue (Estrutura)

```vue
<!-- NOVO: features/candidates/activities/ActivityFilters.vue -->
<template>
  <div class="d-flex align-center ga-2 flex-wrap">
    <v-chip-group v-model="selectedFilter" mandatory selected-class="text-primary">
      <v-chip v-for="filter in filters" :key="filter.value" :value="filter.value"
        size="small" variant="tonal" class="f10">
        <Icon :name="filter.icon" size="12" class="mr-1" />
        {{ filter.label }}
        <span v-if="filter.count > 0" class="ml-1 f9">({{ filter.count }})</span>
      </v-chip>
    </v-chip-group>
    <v-select v-model="periodFilter" :items="periods" density="compact"
      variant="outlined" class="f10" style="max-width: 140px;" hide-details />
  </div>
</template>
```

```vue
<!-- NOVO: features/candidates/activities/ActivityTimeline.vue -->
<template>
  <div class="d-flex flex-column">
    <div v-for="activity in activities" :key="activity.id"
      class="d-flex ga-3 position-relative mb-4 cursor-pointer"
      @click="$emit('expand', activity.id)">
      <!-- Timeline line -->
      <div class="d-flex flex-column align-center" style="width: 24px;">
        <div class="rounded-circle d-flex align-center justify-center"
          :style="{ backgroundColor: getBgColor(activity.color), width: '24px', height: '24px' }">
          <Icon :name="activity.icon" size="12" :color="activity.color" />
        </div>
        <div v-if="!isLast(activity)" class="flex-grow-1" style="width: 2px; background: rgb(var(--v-theme-border-color));" />
      </div>
      <!-- Content -->
      <div class="flex-grow-1 pb-2">
        <div class="d-flex align-center justify-space-between">
          <span class="f11 font-weight-medium">{{ activity.title }}</span>
          <span class="f9 text-body-light">{{ formatRelativeTime(activity.timestamp) }}</span>
        </div>
        <v-chip size="x-small" :color="activity.chipColor" variant="tonal" class="mt-1 f9">
          {{ activity.typeLabel }}
        </v-chip>
        <p v-if="activity.preview" class="f10 text-body-light mt-1">{{ activity.preview }}</p>
      </div>
    </div>
  </div>
</template>
```

---

## 6. COMPARACAO — TAB ARQUIVOS

### 6.1 Vue — files/wrapper.vue (120 linhas)

```vue
<!-- Funcionalidade basica: lista de arquivos com download -->
<ul class="d-flex flex-column ga-2 pa-3">
  <li v-for="file in files" :key="file.id"
    class="px-3 py-4 border border-border-color rounded-lg d-flex align-start ga-2">
    <Icon :name="icons[file.file_type]" size="14" color="body-light" />
    <div>
      <p class="f11">{{ file.name }}</p>
      <p class="f10 text-body-light">{{ file.file_type }}</p>
    </div>
    <Icon name="lucide-download" size="14" @click="downloadFile(file)" clickable />
  </li>
</ul>
```

**API Vue:** `GET /users/data_files?where[reference_type]=Candidate&where[reference_id]={id}`

### 6.2 React — CandidateFilesTab.tsx (774 linhas)

```tsx
// Funcionalidade rica: categorias, drag-drop, upload, preview, tags, delete
<div>
  {/* Header com botao Adicionar */}
  <Button onClick={triggerUpload}>Adicionar Arquivo</Button>

  {/* Categorias automaticas (Curriculos, Certificados, Videos, etc.) */}
  <div className="flex gap-1 flex-wrap">
    {fileCategories.map(cat => <Badge onClick={() => setSelectedCategory(cat)}>{cat.icon} {cat.label} ({cat.count})</Badge>)}
  </div>

  {/* Drag and Drop Area */}
  <div onDragOver={...} onDrop={handleDrop}>
    Arraste arquivos aqui ou clique para adicionar
  </div>

  {/* Lista de arquivos com: preview, download, delete, tags, tamanho, data */}
  {candidateFiles.map(file => (
    <div>
      <FileIcon />
      <span>{file.name}</span>
      <Badge>{file.category}</Badge>
      <span>{formatFileSize(file.size)}</span>
      <span>{formatRelativeTime(file.date)}</span>
      <Button onClick={() => preview(file)}><Eye /></Button>
      <Button onClick={() => download(file)}><Download /></Button>
      <Button onClick={() => deleteFile(file)}><Trash2 /></Button>
    </div>
  ))}

  {/* FilePreviewModal — preview inline de PDFs, imagens, videos */}
  <FilePreviewModal file={selectedFile} type={previewType} />
</div>
```

### 6.3 DIFERENCAS TAB ARQUIVOS

| Feature | Vue (120 linhas) | React (774 linhas) | Delta |
|---|---|---|---|
| **Upload** | `uploader.vue` separado (125 linhas), botao simples | Inline drag-drop + click, progress bar | React UX melhor |
| **Categorias** | Nenhuma | 7 categorias automaticas com icones e contagem | **Ausente** |
| **Preview** | Download apenas (abre em nova aba) | Modal inline com viewer PDF/imagem/video | **Ausente** |
| **Delete** | Nao implementado | Botao com confirmacao | **Ausente** |
| **Tags** | Nao implementado | Tags automaticas por tipo | **Ausente** |
| **Tamanho** | Nao exibido | `formatFileSize()` | **Ausente** |
| **Data relativa** | Nao exibida | `formatRelativeTime()` | **Ausente** |
| **Drag & Drop** | Nao implementado | Area visual com feedback | **Ausente** |
| **File type icons** | Map basico de MIME types | Icones por categoria (Curriculo, Certificado, Video, Audio) | Parcial |

### 6.4 CORRECAO SUGERIDA — Arquivos Vue (Enriquecimento)

```vue
<!-- Melhorar features/candidates/files/wrapper.vue -->
<template>
  <div class="pa-3">
    <!-- Header com botao -->
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="d-flex align-center ga-2">
        <Icon name="lucide-file-text" size="14" />
        <p class="f12 font-weight-medium">Arquivos e Documentos</p>
        <v-chip size="x-small" variant="tonal">{{ files.length }}</v-chip>
      </div>
      <v-btn size="small" variant="tonal" color="primary" @click="triggerUpload">
        <Icon name="lucide-plus" size="12" class="mr-1" />
        Adicionar
      </v-btn>
    </div>

    <!-- NOVO: Categorias -->
    <div class="d-flex ga-1 flex-wrap mb-3">
      <v-chip v-for="cat in categories" :key="cat.value"
        :variant="selectedCategory === cat.value ? 'flat' : 'outlined'"
        size="x-small" @click="toggleCategory(cat.value)" class="cursor-pointer">
        {{ cat.icon }} {{ cat.label }} ({{ cat.count }})
      </v-chip>
    </div>

    <!-- NOVO: Drag & Drop -->
    <div class="border-dashed border-2 rounded-lg pa-4 text-center mb-3 cursor-pointer"
      :class="isDragging ? 'border-primary bg-primary-lighten-5' : 'border-border-color'"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop">
      <Icon name="lucide-upload" size="20" color="body-light" class="mb-1" />
      <p class="f10 text-body-light">Arraste arquivos aqui</p>
    </div>

    <!-- Lista melhorada -->
    <div v-for="file in filteredFiles" :key="file.id"
      class="d-flex align-center ga-2 pa-2 border border-border-color rounded-lg mb-2">
      <Icon :name="getFileIcon(file)" size="16" :color="getCategoryColor(file)" />
      <div class="flex-grow-1">
        <p class="f11 text-on-surface">{{ file.name }}</p>
        <div class="d-flex align-center ga-2 f9 text-body-light">
          <span>{{ formatFileSize(file.size) }}</span>
          <span>{{ formatRelativeTime(file.created_at) }}</span>
        </div>
      </div>
      <v-btn icon variant="text" size="x-small" @click="previewFile(file)">
        <Icon name="lucide-eye" size="14" />
      </v-btn>
      <v-btn icon variant="text" size="x-small" @click="downloadFile(file)">
        <Icon name="lucide-download" size="14" />
      </v-btn>
    </div>
  </div>
</template>
```

---

## 7. COMPARACAO — TAB PARECERES (EXCLUSIVA REACT)

### 7.1 React — CandidateOpinionsTab.tsx (293 linhas)

Esta tab **nao existe no Vue** e contem:

1. **Subtabs**: "Pareceres da LIA" e "Analises"
2. **Historico de pareceres**: Lista cronologica de todos os pareceres gerados
3. **OpinionCard**: Card expandivel com score, recomendacao, texto completo, botao copiar
4. **Analises salvas**: Analises do candidato versus vagas especificas
5. **Acoes**: Copiar parecer, deletar analise, expandir/colapsar

### 7.2 CORRECAO SUGERIDA — Tab Pareceres Vue

```vue
<!-- NOVO: features/candidates/opinions/CandidateOpinionsTab.vue -->
<template>
  <div class="pa-3">
    <!-- Subtabs -->
    <v-tabs v-model="subTab" density="compact" class="mb-3">
      <v-tab value="pareceres" class="f10">
        <Icon name="lucide-brain" size="12" class="mr-1" color="wedo-cyan" />
        Pareceres da LIA
        <v-chip v-if="opinions.length" size="x-small" color="primary" variant="tonal" class="ml-1">
          {{ opinions.length }}
        </v-chip>
      </v-tab>
      <v-tab value="analises" class="f10">
        <Icon name="lucide-file-text" size="12" class="mr-1" />
        Analises
      </v-tab>
    </v-tabs>

    <v-window v-model="subTab">
      <v-window-item value="pareceres">
        <div v-if="loading" class="d-flex flex-column ga-3">
          <v-skeleton-loader v-for="i in 2" :key="i" type="card" />
        </div>
        <div v-else-if="opinions.length === 0" class="text-center py-6">
          <Icon name="lucide-brain" size="32" color="body-light" class="mb-2" />
          <p class="f12 text-body-light">Nenhum parecer gerado ainda</p>
        </div>
        <OpinionCard v-for="opinion in opinions" :key="opinion.id"
          :opinion="opinion"
          :expanded="expandedId === opinion.id"
          @toggle="expandedId = expandedId === opinion.id ? null : opinion.id"
          @copy="copyOpinion" />
      </v-window-item>

      <v-window-item value="analises">
        <!-- Analises por vaga -->
        <AnalysisCard v-for="analysis in analyses" :key="analysis.id"
          :analysis="analysis" @delete="deleteAnalysis" @copy="copyAnalysis" />
      </v-window-item>
    </v-window>
  </div>
</template>
```

---

## 8. COMPARACAO — BOTOES DE ACAO

### 8.1 Vue — preview.vue (linhas 230-260)

```vue
<div class="d-flex align-center ga-1 py-1 px-3 border-b border-border-color">
  <v-menu>
    <template #activator="{ props }">
      <v-btn v-bind="props" size="small" variant="tonal" color="primary" class="f11">
        <Icon name="lucide-ellipsis" size="14" />
      </v-btn>
    </template>
    <v-list density="compact">
      <v-list-item @click="openFullPage"><v-list-item-title>Abrir Completo</v-list-item-title></v-list-item>
      <v-list-item @click="addToJob"><v-list-item-title>Adicionar a Vaga</v-list-item-title></v-list-item>
      <v-list-item @click="sendEmail"><v-list-item-title>Enviar Email</v-list-item-title></v-list-item>
      <v-list-item @click="startEnrich"><v-list-item-title>Enriquecer</v-list-item-title></v-list-item>
    </v-list>
  </v-menu>
  <!-- Botoes individuais -->
  <v-tooltip location="bottom" v-for="action in quickActions">
    <template #activator="{ props }">
      <v-btn v-bind="props" icon variant="text" size="small" @click="action.handler">
        <Icon :name="action.icon" size="16" />
      </v-btn>
    </template>
    <span>{{ action.tooltip }}</span>
  </v-tooltip>
</div>
```

### 8.2 React — candidate-preview.tsx (linhas 280-350)

```tsx
<div className="flex items-center gap-1 py-1 px-2 border-b border-lia-border-subtle bg-lia-bg-primary">
  {/* Botoes de contato: Email, WhatsApp */}
  <Tooltip><TooltipTrigger>
    <Button size="sm" variant="ghost" onClick={() => onSendEmail?.(candidate)}>
      <Mail className="w-3.5 h-3.5" />
    </Button>
  </TooltipTrigger><TooltipContent>Enviar Email</TooltipContent></Tooltip>

  <Tooltip><TooltipTrigger>
    <Button size="sm" variant="ghost" onClick={() => onSendWhatsApp?.(candidate)}>
      <MessageCircle className="w-3.5 h-3.5" />
    </Button>
  </TooltipTrigger><TooltipContent>WhatsApp</TooltipContent></Tooltip>

  {/* Triagem, Agendamento, Feedback, Adicionar a Vaga, Favoritar */}
  {/* Botao LIA Chat - exclusivo */}
  <Button onClick={() => setShowLiaModal(true)}>
    <Brain className="w-3.5 h-3.5" /> Perguntar a LIA
  </Button>

  {/* Menu dropdown com mais opcoes */}
  <DropdownMenu>
    <DropdownMenuTrigger><MoreVertical /></DropdownMenuTrigger>
    <DropdownMenuContent>
      <DropdownMenuItem>Abrir Pagina Completa</DropdownMenuItem>
      <DropdownMenuItem>Adicionar a Lista</DropdownMenuItem>
      <DropdownMenuItem>Imprimir / Exportar</DropdownMenuItem>
      <DropdownMenuSeparator />
      <DropdownMenuItem>Favoritar</DropdownMenuItem>
      <DropdownMenuItem>Compartilhar</DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</div>
```

### 8.3 DIFERENCAS NOS BOTOES

| Botao/Acao | Vue | React | Delta |
|---|---|---|---|
| **Email** | Via menu dropdown | Botao direto com icone | React mais acessivel |
| **WhatsApp** | Nao implementado | Botao direto | **Ausente** |
| **Triagem WSI** | Nao implementado | Botao com callback | **Ausente** |
| **Agendamento** | Nao implementado | Botao com callback | **Ausente** |
| **Feedback** | Nao implementado | Botao com callback | **Ausente** |
| **LIA Chat** | Nao implementado | Botao "Perguntar a LIA" abre modal de chat | **Ausente** — feature principal |
| **Adicionar a Vaga** | Menu dropdown item | Menu dropdown item | Equivalente |
| **Enriquecer** | Menu dropdown + dialog de confirmacao com creditos | Nao implementado | **Vue tem, React nao** |
| **Favoritar** | Nao implementado | Toggle com coracao | **Ausente** |
| **Compartilhar** | Nao implementado | Menu dropdown item | **Ausente** |
| **Navegacao prev/next** | Nao implementado | Setas `<` `>` com indice `1 de 42` | **Ausente** |

---

## 9. COMPARACAO — MODAIS

### 9.1 Modais Vue (3 modais)

| Modal | Componente | Funcionalidade |
|---|---|---|
| **SendEmailDialog** | Componente externo importado | Enviar email ao candidato |
| **Enrich Confirm** | Inline `v-dialog` | Confirmar uso de creditos para enriquecimento |
| **Add to Job** | Inline `v-dialog` | Selecionar vaga + processo seletivo |

### 9.2 Modais React (7+ modais)

| Modal | Componente | Funcionalidade |
|---|---|---|
| **LIA Chat** | `LiaChatModal.tsx` | Chat conversacional com a LIA sobre o candidato |
| **LIA Analysis** | `lia-analysis-modal.tsx` (dynamic import) | Detalhes da analise LIA com metricas |
| **Screening Media** | `screening-media-modal.tsx` (dynamic import) | Player audio/video + transcricao + perguntas |
| **DISC Assessment** | `disc-assessment-modal.tsx` (dynamic import) | Resultado completo DISC com grafico |
| **Big Five** | `big-five-modal.tsx` (dynamic import) | Resultado Big Five com radar chart |
| **File Preview** | `FilePreviewModal.tsx` | Preview inline de PDF/imagem/video |
| **Insufficient Data** | `insufficient-data-modal.tsx` | Alerta de dados insuficientes para analise |
| **Update Opinion Alert** | `AlertDialog` (shadcn) | Confirmar re-geracao de parecer |
| **Delete Analysis Alert** | `AlertDialog` (shadcn) | Confirmar exclusao de analise |

### 9.3 MODAIS AUSENTES NO VUE (Criticas)

1. **LiaChatModal** — Chat com a LIA. Permite perguntas livres sobre o candidato, historico de conversa, sugestoes de perguntas. **Feature mais importante ausente.**

2. **ScreeningMediaModal** — Player de audio/video de triagem com transcricao segmentada, perguntas respondidas, highlights automaticos. **Essencial para fluxo de triagem.**

3. **DISC/BigFive Modals** — Resultados de assessments comportamentais com visualizacao grafica. **Necessario para avaliacao completa.**

4. **FilePreviewModal** — Preview inline sem sair do preview. **UX significativamente melhor que "abrir em nova aba".**

---

## 10. COMPARACAO — LOGICA / STATE MANAGEMENT

### 10.1 Vue — State Management

```
preview.vue (script setup)
  ├── Props: candidate_id, candidate_record (recebidos do pai)
  ├── Refs locais: active_tab, showEnrichConfirm, showAddToJobDialog...
  ├── Computed: candidateScore, scoreColor, hasScore
  ├── Watch: candidate_record (recarrega dados)
  └── Methods: openFullPage, sendEmail, confirmEnrich, saveAddToJob

overview.vue (script setup)
  ├── Props: candidate_record, is_fullscreen
  ├── Reactive: candidate = reactive(setCandidate())
  ├── Watch: candidate_record.ai_feedback
  └── Computed: hasScoreAnalysis

Cada card (experiences, educations, etc.):
  ├── Props: candidate
  ├── onMounted: fetch dados via $axios
  └── Refs locais para dados
```

### 10.2 React — State Management

```
candidate-preview.tsx
  └── useCandidatePreviewCore(candidate) — 666 linhas de logica centralizada
      ├── States: activeTab, showLiaModal, liaConversation, selectedFile...
      ├── States: opinionsData, isLoadingOpinions, opinionsHistory...
      ├── States: screeningModalOpen, discModalOpen, bigFiveModalOpen...
      ├── Effects: useEffect para carregar opinions, analyses, messages
      ├── Handlers: sendLiaMessage, generateNewOpinion, handleAnalyzeWithLia
      ├── Handlers: handleCopyOpinion, handleDeleteAnalysis, handleAnalysisTransport
      ├── Formatters: formatAnalysisDate, formatCurrency, generateShortId
      └── Return: 40+ states + handlers exportados
```

### 10.3 DIFERENCAS ARQUITETURAIS

| Aspecto | Vue | React | Impacto |
|---|---|---|---|
| **Centralizacao** | Estado distribuido entre 10+ componentes | Estado centralizado em `useCandidatePreviewCore` | Vue mais modular mas fragmentado |
| **Data fetching** | Cada card faz `$axios.get()` no `onMounted` | Hook centralizado faz todos os fetches | Vue: N+1 requests; React: batch |
| **Opinoes/Pareceres** | Nao implementado | Fetch completo com historico | **Gap critico** |
| **Chat LIA** | Nao implementado | Gerenciado no core hook | **Gap critico** |
| **Screensing data** | Nao implementado | Modais com data completa | **Gap critico** |
| **Error handling** | `toast.error()` por componente | Centralizado no hook | Vue inconsistente |

---

## 11. COMPARACAO — APIs BACKEND

### 11.1 Endpoints Vue (observados no codigo)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /users/data_files` | files/wrapper.vue | Buscar arquivos do candidato |
| `GET /users/experiences` | cards/experiences.vue | Buscar experiencias |
| `GET /users/educations` | cards/educations.vue | Buscar formacoes |
| `GET /users/skill_relationships` | cards/skills.vue | Buscar skills |
| `GET /users/addresses/Candidate/{id}` | cards/addresses.vue | Buscar enderecos |
| `GET /users/candidates/{id}/calculate_remunerations` | cards/remunerations.vue | Calcular remuneracao |
| `GET /users/candidates/{id}/calculate_benefits` | cards/remunerations.vue | Calcular beneficios |
| `GET /users/languages` | cards/languages.vue (presumido) | Buscar idiomas |

### 11.2 Endpoints React (observados no codigo real)

**NOTA:** O React usa `/api/backend-proxy/...` como proxy para o backend FastAPI. As URLs abaixo sao as URLs reais do frontend.

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /api/backend-proxy/opinions/candidate/{id}/summary?company_id=...` | useCandidatePreviewCore | Resumo pareceres |
| `POST /api/backend-proxy/opinions/generate` | useCandidatePreviewCore | Gerar novo parecer |
| `GET /api/backend-proxy/opinions/candidate/{id}/history` | useCandidatePreviewCore | Historico de pareceres |
| `GET /api/backend-proxy/analyses/candidate/{id}` | useCandidatePreviewCore | Analises salvas |
| `DELETE /api/backend-proxy/analyses/{aid}` | useCandidatePreviewCore | Deletar analise |
| `POST /api/backend-proxy/lia/chat` | useCandidatePreviewCore | Chat com LIA |
| `GET {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Buscar arquivos |
| `POST {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Upload de arquivo |
| `DELETE {BACKEND_URL}/api/v1/candidates/{id}/files/{fid}` | useCandidateFiles | Deletar arquivo |

**IMPORTANTE:** A tab Atividades (`CandidateActivitiesTab.tsx`) usa **dados demo** via `getDemoActivities()` controlados por `NEXT_PUBLIC_USE_DEMO_DATA`. Nao ha endpoint real de atividades implementado no backend. O Vue `applies.vue` (30 linhas) usa `AppliesTable` que ja busca dados reais de candidaturas.

### 11.3 ENDPOINTS AUSENTES NO BACKEND VUE

| Endpoint Necessario | Prioridade | Descricao |
|---|---|---|
| `GET /opinions/history` | **Critico** | Historico de pareceres LIA |
| `POST /opinions/generate` | **Critico** | Gerar novo parecer |
| `POST /lia/chat` | **Critico** | Chat conversacional com LIA |
| `GET /activities` (timeline) | **Alto** | Timeline de atividades do candidato |
| `DELETE /files/{id}` | **Medio** | Deletar arquivo do candidato |
| `GET /analyses` | **Alto** | Analises salvas por vaga |

---

## 12. COMPARACAO — CSS / DESIGN TOKENS

### 12.1 Sistema de Cores

| Token React | Uso | Equivalente Vue |
|---|---|---|
| `--lia-bg-primary` | Fundo principal | `rgb(var(--v-theme-surface))` |
| `--lia-bg-secondary` | Fundo secundario | `rgb(var(--v-theme-background))` |
| `--lia-bg-tertiary` | Fundo terciario | `bg-border-color` (nao ideal) |
| `--lia-text-primary` | Texto principal | `text-on-surface` |
| `--lia-text-secondary` | Texto secundario | `text-body-medium` |
| `--lia-text-tertiary` | Texto terciario | `text-body-light` |
| `--lia-border-subtle` | Borda sutil | `border-border-color border-opacity-100` |
| `--wedo-cyan` | Cor LIA | `wedo-cyan` (custom) |
| `--wedo-purple` | Cor brand | `primary` |
| `--status-success` | Verde sucesso | `success` / `green` |
| `--status-error` | Vermelho erro | `error` / `red` |
| `--status-warning` | Amarelo alerta | `warning` / `amber` |

### 12.2 Tipografia

| Classe React | Tamanho | Classe Vue Equivalente |
|---|---|---|
| `text-micro` / `textStyles.micro` | 9px | `f9` |
| `text-xs` / `textStyles.caption` | 10px | `f10` |
| `textStyles.body` | 11px | `f11` |
| `textStyles.label` | 12px | `f12` |
| `text-sm` | 14px | `f13` / `f14` |
| `textStyles.sectionTitle` | 13px | `f13 font-weight-semibold` |

### 12.3 Espacamento

| Padrao React | Valor | Padrao Vue |
|---|---|---|
| `p-2.5` | 10px | `pa-3` (12px) — **2px maior** |
| `gap-1.5` | 6px | `ga-2` (8px) — **2px maior** |
| `space-y-3` | 12px | `v-row` / `mb-3` (12px) — equivalente |
| `rounded-md` | 6px | `rounded-lg` (8px) — **2px maior** |
| `border-b` | 1px | `border-b` — equivalente |

**Conclusao:** O Vue usa espacamento sistematicamente ~20% maior que o React, resultando em menor densidade de informacao.

---

## 13. COMPARACAO — ICONS

### 13.1 Mapeamento de Icones

| Funcao | React (lucide-react) | Vue (mdi + lucide custom) | Status |
|---|---|---|---|
| Brain/LIA | `Brain` (lucide) | `lucide-brain` (custom Icon) | OK |
| Score | SVG inline | `v-progress-circular` | Diferente impl |
| Check | `CheckCircle` (lucide) | `mdi-check` (MDI) | Biblioteca diferente |
| Alert | `AlertCircle` (lucide) | `mdi-alert` (MDI) | Biblioteca diferente |
| LinkedIn | `Linkedin` (lucide) | `lucide-linkedin` (custom) | OK |
| GitHub | `Code` (lucide) | Nao existe no preview | **Ausente** |
| Download | `Download` (lucide) | `lucide-download` (custom) | OK |
| File | `FileText` (lucide) | `lucide-file-text` (custom) | OK |
| Upload | `Upload` (lucide) | Nao existe | **Ausente** |
| Eye/Preview | `Eye` (lucide) | Nao existe | **Ausente** |
| Trash/Delete | `Trash2` (lucide) | Nao existe | **Ausente** |
| Star/Favorito | `Heart` (lucide) | Nao existe | **Ausente** |
| WhatsApp | `MessageCircle` (lucide) | Nao existe | **Ausente** |
| Calendar | `Calendar` (lucide) | Nao existe no preview | **Ausente** |
| Clock | `Clock` (lucide) | Nao existe no preview | **Ausente** |
| Dollar | `DollarSign` (lucide) | `mdi-currency-usd` (MDI) | Biblioteca diferente |
| Gift | `Gift` (lucide) | `mdi-gift-outline` (MDI) | Biblioteca diferente |

### 13.2 NOTA IMPORTANTE

O Vue usa um componente `Icon` customizado (`~/components/ui/icon/icon.vue`) que suporta tanto `lucide-*` quanto `mdi-*`. A biblioteca MDI (Material Design Icons) e nativa do Vuetify. O React usa lucide-react exclusivamente.

Para consistencia visual, o Vue deveria migrar para Lucide em novos componentes, mantendo MDI apenas onde Vuetify exige.

---

## 14. FEATURES EXCLUSIVAS POR PLATAFORMA

### 14.1 Features que SÓ EXISTEM NO VUE

| Feature | Componente | Descricao |
|---|---|---|
| **Enriquecimento** | `preview.vue` dialog | Enriquecer perfil com creditos (email, telefone) |
| **Busca IA** | `preview.vue` dialog | Gerar perfil IA para candidatos sem origem IA |
| **Remuneracao detalhada** | `remunerations.vue` (191 linhas) | Calculo completo: salario base, anualizado 13.33x, componentes variaveis, beneficios valor/dia vs /mes, subtotais, total anual |
| **Score Analysis separado** | `score_analysis.vue` (692 linhas) | Analise de score detalhada com requisitos, confianca, metodo de scoring |
| **Curriculo como tab** | `curriculum_text.vue` (513 linhas) | Tab dedicada para texto do curriculo |
| **Sourced Profile** | `sourced-profile-*.vue` (9 arquivos) | Preview especifico para candidatos de sourcing LIA |
| **Candidatos similares** | `similar_candidates_modal.vue` | Modal de candidatos similares |

### 14.2 Features que SÓ EXISTEM NO REACT

| Feature | Componente | Descricao |
|---|---|---|
| **LIA Chat** | `LiaChatModal.tsx` | Chat conversacional com IA sobre o candidato |
| **Tab Pareceres** | `CandidateOpinionsTab.tsx` (293 linhas) | Historico de pareceres + analises salvas |
| **Timeline Atividades** | `ActivityTimeline.tsx` + `ActivityExpandedDetails.tsx` (878 linhas) | Timeline visual com 15+ tipos de atividade expandiveis |
| **Filtros Atividades** | `ActivityFilters.tsx` | Filtros por tipo + periodo + modo visualizacao |
| **File Preview Modal** | `FilePreviewModal.tsx` | Preview inline de PDFs, imagens, videos |
| **Drag & Drop Upload** | `CandidateFilesTab.tsx` | Area drag-drop com progress bar |
| **Categorias Arquivo** | `useCandidateFiles.tsx` | Categorizacao automatica de arquivos |
| **DISC Modal** | `disc-assessment-modal.tsx` | Resultado DISC com grafico radar |
| **Big Five Modal** | `big-five-modal.tsx` | Resultado Big Five com visualizacao |
| **Screening Media** | `screening-media-modal.tsx` | Player audio/video com transcricao |
| **Navegacao candidatos** | `candidate-preview.tsx` | Setas prev/next com `1 de 42` |
| **ExperienceHighlight** | `experience-highlight-card.tsx` | Card destaque de experiencia no topo |
| **ID alfanumerico** | `generateShortId()` | `A72E80` em vez de `4681` |
| **Favoritar** | `candidate-preview.tsx` | Toggle favorito com coracao |

---

## 15. PLANO DE CONVERGENCIA — PRIORIDADES

### Sprint 1 — Critico (1-2 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 1 | Tab Pareceres | 3 dias | Criar `CandidateOpinionsTab.vue` com historico + subtabs |
| 2 | LIA Chat Modal | 3 dias | Criar `LiaChatModal.vue` com chat conversacional |
| 3 | Timeline Atividades | 4 dias | Criar `ActivityTimeline.vue` + `ActivityFilters.vue` + `ActivityExpandedDetails.vue` |
| 4 | Header enriquecido | 1 dia | Adicionar datas, redes sociais, ID formatado |
| 5 | Backend Opinions API | 2 dias | Endpoints para historico, geracao, chat |

### Sprint 2 — Alto (1-2 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 6 | File Preview Modal | 2 dias | Preview inline de PDFs/imagens/videos |
| 7 | Drag & Drop Upload | 1 dia | Area drag-drop com progress |
| 8 | Categorias Arquivo | 1 dia | Categorizacao automatica + filtros |
| 9 | Screening Modal | 3 dias | Player audio/video com transcricao |
| 10 | DISC/BigFive Modals | 2 dias | Modais de assessment comportamental |

### Sprint 3 — Medio (1 semana)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 11 | Navegacao prev/next | 0.5 dia | Setas com indice `1 de N` |
| 12 | Favoritar | 0.5 dia | Toggle favorito |
| 13 | WhatsApp/Contato | 1 dia | Botoes diretos de contato |
| 14 | ExperienceHighlight | 1 dia | Card destaque no topo do perfil |
| 15 | Density pass | 1 dia | Reduzir padding 20% em todos os cards |

### Sprint 4 — Preservar do Vue

| # | Item | Descricao |
|---|---|---|
| P1 | Remuneracao detalhada | **MANTER** — significativamente superior ao React |
| P2 | Score Analysis | **MANTER** — 692 linhas de analise que o React nao tem |
| P3 | Enriquecimento | **MANTER** — feature exclusiva com gestao de creditos |
| P4 | Sourced Profile | **MANTER** — preview especifico para sourcing |
| P5 | Curriculo tab | **MANTER** — tab dedicada (React usa FilePreview) |

---

## 16. METRICAS FINAIS

| Metrica | Vue (Producao) | React (Replit) | Gap |
|---|---|---|---|
| Linhas de codigo preview | 6.345 | 6.196 | +2.4% Vue |
| Tabs | 4 | 4 | Diferentes: Curriculo vs Pareceres |
| Modais | 3 | 9 | **-6 modais** |
| Tipos atividade | 0 | 15+ | **-15 tipos** |
| Botoes acao | 4 | 10+ | **-6 botoes** |
| Redes sociais | 1 | 5 | **-4 redes** |
| Cards dados perfil | 9 | 9 | Equivalente |
| APIs chamadas | 8 | 10+ | **-2 endpoints** |
| Features exclusivas Vue | 7 | 0 | Vue tem features unicas |
| Features exclusivas React | 0 | 14 | **-14 features** |

**Conclusao:** Apesar de ter quase a mesma quantidade de codigo, o Vue foca em **profundidade de dados** (remuneracao detalhada, score analysis) enquanto o React foca em **amplitude de funcionalidades** (atividades, pareceres, chat, modais). A convergencia ideal preserva as forcas de ambos.
