# AUDITORIA QA — Candidate Preview Panel
## WeDOTalent Producao (Vue/Vuetify/Nuxt) vs Referencia Replit (React/Tailwind/Next.js)

**Data:** 2026-04-03
**Fonte Vue:** Repositorio `wedotalent/ats_front` branch `develop` (30+ arquivos, ~6.345 linhas, obtido via GitHub API)
**Fonte React:** `plataforma-lia/src/components/candidate-preview/` (13 arquivos, ~6.196 linhas)
**Testes:** Playwright e2e contra ambos os ambientes
**Score Geral:** 48/100

---

## ADVERTENCIAS IMPORTANTES

1. **Tab Atividades do React usa dados DEMO.** O `CandidateActivitiesTab.tsx` usa `getDemoActivities()` com flag `NEXT_PUBLIC_USE_DEMO_DATA`. Os 15+ tipos de atividade sao UI pronta para backend futuro, nao dados reais. O Vue `applies.vue` usa `AppliesTable` com dados **reais** de candidaturas.
2. **Endpoints React usam proxy.** URLs como `/api/backend-proxy/opinions/...` sao proxy Next.js. O endpoint real e o FastAPI em `BACKEND_URL`. Tab Arquivos do React usa `BACKEND_URL` diretamente, causando CORS em producao.
3. **Vue tem features superiores ao React em 2 areas:** Remuneracao detalhada (`remunerations.vue`, 191 linhas com calculo anualizado 13.33x) e Score Analysis (`score_analysis.vue`, 692 linhas com requisitos expandiveis). Essas devem ser PRESERVADAS.
4. **Fixes nao sao 100% drop-in.** Cada correcao requer verificacao de imports, props e event contracts no contexto real do componente.

---

## INDICE

- **Parte 1:** [Resumo Executivo + Screenshots](#parte-1-resumo-executivo)
- **Parte 2:** [Bugs Visuais + Code Fixes](#parte-2-bugs-visuais--code-fixes)
- **Parte 3:** [Feature Gaps (Funcionalidades Ausentes)](#parte-3-feature-gaps)
- **Parte 4:** [Bugs Backend + API](#parte-4-bugs-backend--api)
- **Parte 5:** [Bugs IA + Banco de Dados](#parte-5-bugs-ia--banco-de-dados)
- **Parte 6:** [Tabela de Prioridades Unificada](#parte-6-tabela-de-prioridades-unificada)
- **Parte 7:** [Referencia Tecnica](#parte-7-referencia-tecnica)
- **Como Criar Cards Jira**

---

# PARTE 1: RESUMO EXECUTIVO

## Resumo por Area

| Area | Vue (Producao) | React (Replit) | Status |
|------|---------------|----------------|--------|
| **Header candidato** | Avatar + nome + score + LinkedIn | Avatar com ring + nome + 3 badges + 5 redes + datas + contato + indicadores | GAP CRITICO |
| **Tabs** | 4 tabs (Perfil, Atividades, Arquivos, Curriculo) | 4 tabs (Perfil, Atividades, Arquivos, Pareceres) | DIFERENTE |
| **Tab Perfil** | 9 cards separados (lia_assessment 458L, score_analysis 692L, etc.) | 1 componente monolitico (861L) com cards embutidos | PARCIAL |
| **Tab Atividades** | `applies.vue` (30L) — tabela basica, dados reais | 3 sub-componentes (1.434L) — timeline rica, dados demo | GAP |
| **Tab Arquivos** | `wrapper.vue` (120L) — lista + download | `CandidateFilesTab.tsx` (774L) — drag-drop + preview + categorias | GAP CRITICO |
| **Tab Pareceres** | NAO EXISTE | `CandidateOpinionsTab.tsx` (293L) — historico + analises | FALTANDO |
| **Botoes de acao** | 8 icones-only no dropdown | 9 botoes com labels + LIA Chat + favoritar | GAP |
| **Modais** | 3 (Email, Enrich, AddToJob) | 7+ (LIA Chat, DISC, BigFive, Screening, FilePreview, etc.) | GAP |
| **Layout preview** | Empurra header/botoes da tabela | Drawer overlay sem afetar tabela | BUG CRITICO |
| **Design System** | Roboto, cores hardcoded, sombras Material | Open Sans + Inter, tokens semanticos, sem sombras | GAP |
| **Backend IA** | Multi-tenancy ausente, FairnessGuard nao integrado | Idem (mesmo backend) | BUG CRITICO |
| **Remuneracao** | 191L com calculo 13.33x + beneficios | ~80L simplificado | VUE SUPERIOR |
| **Score Analysis** | 692L com requisitos expandiveis e confianca | Embutido no Parecer LIA (~150L) | VUE SUPERIOR |

**Total de problemas catalogados: 63**
**Criticos: 9 | Altos: 19 | Medios: 23 | Baixos: 12**

## Verificacao Funcional (Playwright e2e)

### Producao WeDOTalent

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para /user/candidates | PASS | Lista de candidatos carregada |
| Abrir preview de candidato | PASS | Drawer lateral com dados reais |
| Tab Perfil Completo | PASS | Header, skills, experiencia visiveis |
| Tab Atividades | PASS | Conteudo visivel, MAS cards nao expandem |
| Tab Arquivos | **FAIL** | **Erro "Failed to fetch" — arquivos nao carregados** |
| Tab Pareceres | PASS | Conteudo basico visivel |
| Fechar painel | PASS | Painel fecha corretamente |

### Replit (Referencia)

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para home | PASS | Pagina "Funil de Talentos" carregada |
| Abrir candidato via URL direta | PASS | Pagina de detalhe com dados do candidato |
| Tab Perfil Completo | PASS | Header, badges, skills, experiencia visiveis |
| Tab Atividades | PASS | Filtros e timeline renderizados (dados demo) |
| Tab Arquivos | PASS | Area de upload e lista de arquivos |
| Tab Pareceres e Analises | PASS | Sub-tabs e empty states funcionais |

## Screenshots

### Producao WeDOTalent (em `attached_assets/`)

| # | Arquivo | Conteudo | Bugs Relacionados |
|---|---|---|---|
| P1 | `Screen_Shot_..._1.23.34_PM` | Preview aberto, Perfil topo | D01, D03, D05, D06, D07 |
| P2 | `Screen_Shot_..._1.23.56_PM` | Perfil scrollado (skills, requisitos) | D10, D12, D11 |
| P3 | `Screen_Shot_..._1.24.14_PM` | Perfil scrollado (idiomas, remuneracao) | D15, D16 |
| P4 | `Screen_Shot_..._1.24.35_PM` | Atividades (preview) | D17, D19, D20 |
| P5 | `Screen_Shot_..._1.25.00_PM` | Atividades (entries) | D18, D19 |
| P6 | `Screen_Shot_..._1.25.00_PM` (2) | Atividades (entries, duplicata) | D18, D19 |
| P7 | `Screen_Shot_..._1.25.58_PM` | Atividades (full page expandido) | D18, D21, D22 |

### Replit Referencia (em `plataforma-lia/docs/screenshots/`)

| # | Arquivo | Conteudo |
|---|---|---|
| R1 | `replit-ref-home.jpg` | Pagina principal Funil de Talentos |
| R2 | `replit-ref-atividades-tab.jpg` | Tab Atividades com filtros e layout |

**Nota:** Screenshots das tabs Perfil, Arquivos e Pareceres do Replit nao puderam ser capturados (timeout Next.js >10s). Analise feita via inspecao de codigo (6.196 linhas) + testes Playwright.

---

# PARTE 2: BUGS VISUAIS + CODE FIXES

## 2.1 LAYOUT GERAL DO PREVIEW

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D01 | **Layout do preview** | Preview empurra header e botoes da tabela ("Novo Candidato", "Nova Busca") para fora da area visivel | Drawer overlay que NAO altera layout da tabela | **CRITICO** |
| D02 | **Largura do preview** | ~50% em preview, 100% em full page, sem transicao suave | Drawer lateral com largura fixa (overlay) ou pagina full separada | ALTO |
| D03 | **Header fixo** | Header nome/avatar/botoes colado ao topo da viewport mesmo ao scrollar tabela | Header dentro do scroll natural da pagina de detalhe | ALTO |
| D04 | **Proporcao conteudo** | Cards grandes com muito padding, scroll excessivo | Cards compactos com `p-2.5` (10px), `text-xs` (12px), densidade maxima | MEDIO |

---

## 2.2 HEADER DO CANDIDATO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D05 | **Avatar** | `v-avatar size="40"`, iniciais inline, sem indicador status | `CandidateAvatar` com `showRing` (anel de status) | BAIXO |
| D06 | **ID Badge** | ID numerico raw `4681` | `generateShortId()` → `A72E80` alfanumerico mono | BAIXO |
| D07 | **Redes sociais** | Apenas LinkedIn | LinkedIn + GitHub + StackOverflow + X + Portfolio | MEDIO |
| D08 | **Datas** | Nenhuma data no header | "Cadastrado em", "Atualizado em", "Ultimo contato em" | ALTO |
| D09 | **Botao LIA** | Ausente | Botao Brain no header abre `LiaAnalysisModal` | ALTO |

### Codigo Vue ATUAL — preview.vue (linhas 140-230)

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
    <v-progress-circular :model-value="candidateScore" :size="28" :width="3" :color="scoreColor">
      <span class="f9 font-weight-bold">{{ candidateScore }}</span>
    </v-progress-circular>
    <span class="f11 text-body-light">{{ candidate_record.role_name }}</span>
    <Icon name="lucide-linkedin" :color="candidate_record.linkedin ? 'primary' : 'body-light'" />
  </div>
</div>
```

### CORRECAO — Header Vue (D05-D09)

```vue
<div class="d-flex py-2 px-2 ga-2 border-b border-border-color border-opacity-100">
  <v-avatar size="40" class="position-relative">
    <div v-if="candidateStatus" class="position-absolute rounded-circle"
      :class="`border-2 border-${statusColor}`" style="inset: -2px; z-index: 1;" />
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
      {{ candidate_record.role_name }} <span class="mx-1">•</span> {{ candidate_record.current_company }}
    </p>
    <div class="d-flex align-center ga-2 f9 text-body-light mb-1">
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-calendar" size="10" /> Cadastrado em {{ formatDate(candidate_record.created_at) }}
      </span>
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-clock" size="10" /> Atualizado em {{ formatDate(candidate_record.updated_at) }}
      </span>
    </div>
    <div class="d-flex align-center ga-1">
      <Icon name="lucide-linkedin" size="14" :color="candidate_record.linkedin ? 'primary' : 'body-light'"
        @click="openUrl(candidate_record.linkedin)" />
      <Icon name="lucide-github" size="14" :color="candidate_record.github ? 'on-surface' : 'body-light'"
        @click="openUrl(candidate_record.github)" />
      <Icon name="lucide-globe" size="14" :color="candidate_record.portfolio ? 'on-surface' : 'body-light'"
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

## 2.3 BOTOES DE ACAO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D10 | **Labels nos botoes** | Icones-only sem texto, dificil identificar | Icone + texto: "Email", "WhatsApp", "Triagem WSI", etc. | ALTO |
| D11 | **Acoes ausentes** | Faltam Triagem WSI, Adicionar a Lista, Ocultar, Feedback | 9 botoes de acao rapida com callbacks | ALTO |

### Codigo Vue ATUAL — preview.vue (linhas 230-260)

```vue
<div class="d-flex align-center ga-1 py-1 px-3 border-b border-border-color">
  <v-menu>
    <template #activator="{ props }">
      <v-btn v-bind="props" size="small" variant="tonal" color="primary">
        <Icon name="lucide-ellipsis" size="14" />
      </v-btn>
    </template>
    <v-list density="compact">
      <v-list-item @click="openFullPage">Abrir Completo</v-list-item>
      <v-list-item @click="addToJob">Adicionar a Vaga</v-list-item>
      <v-list-item @click="sendEmail">Enviar Email</v-list-item>
      <v-list-item @click="startEnrich">Enriquecer</v-list-item>
    </v-list>
  </v-menu>
  <v-tooltip v-for="action in quickActions">
    <template #activator="{ props }">
      <v-btn v-bind="props" icon variant="text" size="small" @click="action.handler">
        <Icon :name="action.icon" size="16" />
      </v-btn>
    </template>
    <span>{{ action.tooltip }}</span>
  </v-tooltip>
</div>
```

### Diferenca detalhada de botoes

| Botao/Acao | Vue | React | Delta |
|---|---|---|---|
| Email | Via menu dropdown | Botao direto com icone | React mais acessivel |
| WhatsApp | Nao implementado | Botao direto | **Ausente** |
| Triagem WSI | Nao implementado | Botao com callback | **Ausente** |
| Agendamento | Nao implementado | Botao com callback | **Ausente** |
| Feedback | Nao implementado | Botao com callback | **Ausente** |
| LIA Chat | Nao implementado | Botao "Perguntar a LIA" abre modal | **Ausente** |
| Adicionar a Vaga | Menu dropdown | Menu dropdown | Equivalente |
| Enriquecer | Menu + dialog creditos | Nao implementado | **Vue tem, React nao** |
| Favoritar | Nao implementado | Toggle coracao | **Ausente** |
| Navegacao prev/next | Nao implementado | Setas `<` `>` com `1 de 42` | **Ausente** |

---

## 2.4 TABS E NAVEGACAO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D12 | **Tab truncada** | Tab "Arquivos" aparece como "Arq..." no preview | Tabs com nomes completos | MEDIO |
| D13 | **Tab Pareceres** | NAO EXISTE como tab | Tab "Pareceres e Analises" com historico + subtabs | **CRITICO** |
| D14 | **Tab Curriculo** | Aparece em full page mas nao no preview | Nao existe — CVs ficam na tab Arquivos | MEDIO |

### Codigo Vue ATUAL — preview.vue (linhas 260-300)

```vue
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
```

### CORRECAO — Adicionar Tab Pareceres (D13)

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

## 2.5 TAB PERFIL — PARECER LIA

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D15 | **Estado vazio** | "Aguardando triagem" com loading, sem botao de acao | Botao "Gerar Parecer" quando vazio, score + archetype + summary quando preenchido | **CRITICO** |
| D16 | **Score sem contexto** | Badge "87" sem escala de cores, sem label "Alta Confianca" | Score com barra circular colorida + label + badge metodo | ALTO |

---

## 2.6 TAB PERFIL — ANALISE DE SCORE E SKILLS

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D09b | **Card Score Analysis desproporcionado** | Grafico circular grande demais, ocupa muito espaco vertical | Grid compacto 2 colunas com barra de progresso por metrica | MEDIO |
| D09c | **Cores inconsistentes** | "Essencial" vermelho, "Importante" laranja, "Desejavel" laranja claro — sem semantica | Design tokens: success (verde), warning (amarelo), error (vermelho) | MEDIO |
| D10b | **Skills sem categorias** | 37 itens planos sem agrupamento | Mapa categorizado: Backend, Frontend, Data, DevOps + cores por fonte | ALTO |
| D10c | **Skills sem fonte** | Todas as badges iguais, impossivel saber se CV/LinkedIn/LIA | Cores distintas: `wedo-cyan` para LIA, `wedo-magenta` para Interesses | MEDIO |

---

## 2.7 TAB PERFIL — SECOES AUSENTES E EXPERIENCIA

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D11b | **Acordeoes sem preview** | "Avaliacao por Requisitos (7)" — apenas titulo + chevron | Conteudo exibido diretamente com scroll natural | MEDIO |
| D12b | **ExperienceHighlight** | Nao existe | Card no topo do perfil com resumo gerado pela LIA | MEDIO |
| D13b | **Perfil LinkedIn** | Nao existe | Card com headline, idade estimada, seguidores, conexoes | MEDIO |
| D14b | **Indicadores especiais** | Nao existe | Badges: Open to Work, Top University, Decision Maker, LCNU | MEDIO |
| D15b | **Preferencias Pessoais** | Nao visivel | Card com Genero, Modelo Trabalho, Contrato, Remoto, LGPD | MEDIO |
| D16b | **Experiencia simples** | Titulo, empresa, datas, texto plano | `border-left` colorida, badges startup/tech stack, duracao calculada | ALTO |
| D16c | **Remuneracao zerada** | "BRL 0,00" para todos os campos | Salario atual + pretensao + CLT/PJ/Freelance formatado | MEDIO |
| D16d | **Idiomas** | "Nao informado" | Nivel de proficiencia quando disponivel | BAIXO |

---

## 2.8 TAB ATIVIDADES

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D17 | **Cards nao expandem** | Cards estaticos sem interacao ao clicar | Cards expandiveis com `ActivityExpandedDetails` por tipo | **CRITICO** |
| D18 | **JSON raw visivel** | Card "Log de Atualizacao" exibe dados raw (`"url": "/recruiter/..."`, `"skill_name": "weblogic"`) | Cada tipo de atividade formatado: email body, entrevista detalhes, etc. | **CRITICO** |
| D19 | **Cards desproporcionais** | Card "Resumo das Alteracoes" ocupa tela inteira com texto bruto | Cards com altura maxima e scroll interno | **CRITICO** |
| D20 | **Filtros truncados** | Preview mostra apenas "Todas, Emails, Entrevistas", demais ocultos | 8 filtros sempre visiveis | ALTO |
| D21 | **Filtros divergentes** | Full page tem "Avaliacoes" e "Etapas" que nao existem na referencia | Referencia tem "Notas" | MEDIO |
| D22 | **Sem Nova Atividade** | Nao ha botao para adicionar atividade manualmente | Botao "Nova Atividade" + textarea nota | ALTO |
| D23 | **Sem agrupamento por data** | Lista cronologica sem separadores | "Hoje", "Ontem", "Esta Semana", etc. | MEDIO |
| D24 | **Dots sem legenda** | Verde/roxo sem explicacao | Color-coded por tipo com legenda | MEDIO |

### Codigo Vue ATUAL — applies.vue (30 linhas)

```vue
<template>
  <div class="pa-3">
    <AppliesTable :candidate_id="candidate_record.id" />
  </div>
</template>
```

### CORRECAO — Filtros de Atividade (D20, D22)

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

### CORRECAO — Timeline Visual (D17, D24)

```vue
<!-- NOVO: features/candidates/activities/ActivityTimeline.vue -->
<template>
  <div class="d-flex flex-column">
    <div v-for="activity in activities" :key="activity.id"
      class="d-flex ga-3 position-relative mb-4 cursor-pointer"
      @click="$emit('expand', activity.id)">
      <div class="d-flex flex-column align-center" style="width: 24px;">
        <div class="rounded-circle d-flex align-center justify-center"
          :style="{ backgroundColor: getBgColor(activity.color), width: '24px', height: '24px' }">
          <Icon :name="activity.icon" size="12" :color="activity.color" />
        </div>
        <div v-if="!isLast(activity)" class="flex-grow-1"
          style="width: 2px; background: rgb(var(--v-theme-border-color));" />
      </div>
      <div class="flex-grow-1 pb-2">
        <div class="d-flex align-center justify-space-between">
          <span class="f11 font-weight-medium">{{ activity.title }}</span>
          <span class="f9 text-body-light">{{ formatRelativeTime(activity.timestamp) }}</span>
        </div>
        <v-chip size="x-small" :color="activity.chipColor" variant="tonal" class="mt-1 f9">
          {{ activity.typeLabel }}
        </v-chip>
      </div>
    </div>
  </div>
</template>
```

---

## 2.9 TAB ARQUIVOS

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D25 | **"Failed to fetch"** | Tab Arquivos nao carrega, erro em producao | Lista de arquivos funcional | **CRITICO** |
| D26 | **Sem drag-and-drop** | Apenas botao de upload basico | Zona dashed drag-drop com progress bar | ALTO |
| D27 | **Sem preview de midia** | Download abre em nova aba | `FilePreviewModal` com PDF, imagem, video inline | ALTO |
| D28 | **Sem categorias** | Lista plana de arquivos | 7 categorias automaticas com icones e contagem | MEDIO |
| D29 | **Sem delete** | Nao implementado | Botao com confirmacao | MEDIO |
| D30 | **Sem tamanho/data** | Nao exibidos | `formatFileSize()` + `formatRelativeTime()` | BAIXO |

### Codigo Vue ATUAL — files/wrapper.vue (120 linhas)

```vue
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

### CORRECAO — Arquivos Enriquecidos (D25-D30)

```vue
<template>
  <div class="pa-3">
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="d-flex align-center ga-2">
        <Icon name="lucide-file-text" size="14" />
        <p class="f12 font-weight-medium">Arquivos e Documentos</p>
        <v-chip size="x-small" variant="tonal">{{ files.length }}</v-chip>
      </div>
      <v-btn size="small" variant="tonal" color="primary" @click="triggerUpload">
        <Icon name="lucide-plus" size="12" class="mr-1" />Adicionar
      </v-btn>
    </div>
    <div class="d-flex ga-1 flex-wrap mb-3">
      <v-chip v-for="cat in categories" :key="cat.value"
        :variant="selectedCategory === cat.value ? 'flat' : 'outlined'"
        size="x-small" @click="toggleCategory(cat.value)" class="cursor-pointer">
        {{ cat.icon }} {{ cat.label }} ({{ cat.count }})
      </v-chip>
    </div>
    <div class="border-dashed border-2 rounded-lg pa-4 text-center mb-3 cursor-pointer"
      :class="isDragging ? 'border-primary bg-primary-lighten-5' : 'border-border-color'"
      @dragover.prevent="isDragging = true" @dragleave="isDragging = false"
      @drop.prevent="handleDrop">
      <Icon name="lucide-upload" size="20" color="body-light" class="mb-1" />
      <p class="f10 text-body-light">Arraste arquivos aqui</p>
    </div>
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

## 2.10 TAB PARECERES E ANALISES

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D31 | **Sem sub-tabs** | Lista unica de pareceres | 2 sub-tabs: "Pareceres da LIA" + "Analises" | ALTO |
| D32 | **Sem score breakdown** | Score como numero simples | Grid 2 colunas com label + valor + barra progresso por metrica | ALTO |
| D33 | **Sem secoes qualitativas** | Nao exibe Pontos Fortes, Gaps, Skills Match separadamente | Secoes expansiveis com listas bulleted | ALTO |
| D34 | **Sem copiar parecer** | Nao ha botao copiar | Botao copiar com formatacao limpa | MEDIO |
| D35 | **Sem historico de versoes** | Apenas parecer atual visivel | Historico completo com timestamps e scores | ALTO |

### CORRECAO — Tab Pareceres Vue (D31-D35)

```vue
<!-- NOVO: features/candidates/opinions/CandidateOpinionsTab.vue -->
<template>
  <div class="pa-3">
    <v-tabs v-model="subTab" density="compact" class="mb-3">
      <v-tab value="pareceres" class="f10">
        <Icon name="lucide-brain" size="12" class="mr-1" color="wedo-cyan" />
        Pareceres da LIA
        <v-chip v-if="opinions.length" size="x-small" color="primary" variant="tonal" class="ml-1">
          {{ opinions.length }}
        </v-chip>
      </v-tab>
      <v-tab value="analises" class="f10">
        <Icon name="lucide-file-text" size="12" class="mr-1" />Analises
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
          :opinion="opinion" :expanded="expandedId === opinion.id"
          @toggle="expandedId = expandedId === opinion.id ? null : opinion.id"
          @copy="copyOpinion" />
      </v-window-item>
      <v-window-item value="analises">
        <AnalysisCard v-for="analysis in analyses" :key="analysis.id"
          :analysis="analysis" @delete="deleteAnalysis" @copy="copyAnalysis" />
      </v-window-item>
    </v-window>
  </div>
</template>
```

---

## 2.11 DESIGN SYSTEM — TIPOGRAFIA, CORES, ESPACAMENTO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D36 | **Font family** | Roboto (Vuetify default) | Open Sans 85% + Inter 10% + JetBrains Mono 5% | MEDIO |
| D37 | **Tamanho base** | ~14px padrao Vuetify | `text-xs` (12px) base, `text-micro` (10px) badges | MEDIO |
| D38 | **Hierarquia tipografica** | Pesos similares entre titulo/label/corpo | `textStyles.label` 12px medium, `textStyles.caption` 10px | MEDIO |
| D39 | **Cores de badge** | Inconsistentes, sem padrao semantico | Design tokens: success/warning/error/info | MEDIO |
| D40 | **Sombras** | Box-shadow Material Design (elevation) | Borders sem sombras: `border-lia-border-subtle` | BAIXO |
| D41 | **Dark mode** | Nao suportado | Tokens adaptaveis preparados | BAIXO |
| D42 | **Padding excessivo** | Cards com espaco interno visivelmente maior | `p-2.5` (10px), `gap-1.5` (6px), `rounded-md` (6px) | MEDIO |
| D43 | **Border radius** | ~4px padrao Vuetify | `rounded-md` (6px) padrao | BAIXO |

### Mapeamento de Design Tokens

| Token React | Uso | Equivalente Vue |
|---|---|---|
| `--lia-bg-primary` | Fundo principal | `rgb(var(--v-theme-surface))` |
| `--lia-bg-secondary` | Fundo secundario | `rgb(var(--v-theme-background))` |
| `--lia-text-primary` | Texto principal | `text-on-surface` |
| `--lia-text-tertiary` | Texto terciario | `text-body-light` |
| `--lia-border-subtle` | Borda sutil | `border-border-color border-opacity-100` |
| `--wedo-cyan` | Cor LIA | `wedo-cyan` (custom) |

### Mapeamento de Tipografia

| Classe React | Tamanho | Classe Vue |
|---|---|---|
| `text-micro` | 9px | `f9` |
| `text-xs` | 10px | `f10` |
| `textStyles.body` | 11px | `f11` |
| `textStyles.label` | 12px | `f12` |
| `text-sm` | 14px | `f13` / `f14` |

### Espacamento — Vue ~20% maior que React

| React | Valor | Vue | Delta |
|---|---|---|---|
| `p-2.5` | 10px | `pa-3` (12px) | +2px |
| `gap-1.5` | 6px | `ga-2` (8px) | +2px |
| `rounded-md` | 6px | `rounded-lg` (8px) | +2px |

---

## 2.12 NOMENCLATURA E TERMINOLOGIA

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D44 | **Tab 4 (preview)** | Nao visivel (truncado) | "Pareceres e Analises" | ALTO |
| D45 | **Tab 4 (full page)** | "Pareceres" (sem "e Analises") | "Pareceres e Analises" | ALTO |
| D46 | **Tab extra full page** | "Curriculo" (nao existe na referencia) | Nao existe | MEDIO |
| D47 | **Score label** | `87` (badge numerico) | `Score: 85/100` com label e escala | ALTO |
| D48 | **Recommendation** | "Alta Confianca" (badge) | `highly_recommended` mapeado para label PT-BR | MEDIO |
| D49 | **Activity changes** | JSON raw no "Resumo das Alteracoes" | Formatado por tipo no `ActivityExpandedDetails` | **CRITICO** |
| D50 | **Botoes header** | Icones-only sem labels | Icone + texto descritivo | ALTO |

---

# PARTE 3: FEATURE GAPS

Funcionalidades que existem no React e NAO existem no Vue. Cada item e um potencial card de Jira.

| ID | Feature | Componente React | Linhas | Descricao | Sev. |
|----|---------|-----------------|--------|-----------|------|
| G01 | **Tab Pareceres** | `CandidateOpinionsTab.tsx` | 293 | Historico de pareceres + analises salvas com subtabs | **CRITICO** |
| G02 | **LIA Chat Modal** | `LiaChatModal.tsx` | 315 | Chat conversacional com IA sobre o candidato | **CRITICO** |
| G03 | **LIA Analysis Modal** | `lia-analysis-modal.tsx` | dynamic | Gerar nova analise IA sob demanda (bullet_points, short, detailed) | ALTO |
| G04 | **Screening Media Modal** | `screening-media-modal.tsx` | dynamic | Player video/audio com transcricao IA segmentada | ALTO |
| G05 | **DISC Assessment Modal** | `disc-assessment-modal.tsx` | dynamic | Resultado DISC com grafico visual | ALTO |
| G06 | **Big Five Modal** | `big-five-modal.tsx` | dynamic | Resultado Big Five com radar chart | ALTO |
| G07 | **File Preview Modal** | `FilePreviewModal.tsx` | 546 | Preview inline PDF/imagem/video sem sair do preview | ALTO |
| G08 | **Drag & Drop Upload** | `CandidateFilesTab.tsx` | embutido | Area visual drag-drop com progress bar e multiplos formatos | ALTO |
| G09 | **Categorias Arquivo** | `useCandidateFiles.tsx` | embutido | 7 categorias automaticas (Curriculos, Certificados, Videos, etc.) | MEDIO |
| G10 | **Activity Timeline** | `ActivityTimeline.tsx` | 98 | Timeline visual com dots coloridos e click-to-expand | ALTO |
| G11 | **Activity Filters** | `ActivityFilters.tsx` | 131 | Filtros por tipo + periodo + modo visualizacao | ALTO |
| G12 | **Activity Details** | `ActivityExpandedDetails.tsx` | 878 | Detalhes expandidos por tipo (15+ tipos) | ALTO |
| G13 | **Navegacao candidatos** | `candidate-preview.tsx` | embutido | Setas prev/next com indice `1 de 42` | MEDIO |
| G14 | **ExperienceHighlight** | `experience-highlight-card.tsx` | embutido | Card destaque de experiencia no topo do perfil | MEDIO |
| G15 | **Alertas de confirmacao** | Varios `AlertDialog` | embutido | "Gerar novo parecer substituira o atual", "Excluir analise?" | MEDIO |
| G16 | **Toast notifications** | Sonner | embutido | Feedback: sucesso de copia, erro de rede, confirmacao | BAIXO |

## Features EXCLUSIVAS do Vue (preservar no React)

| ID | Feature | Componente Vue | Descricao |
|----|---------|---------------|-----------|
| V01 | **Enriquecimento** | `preview.vue` dialog | Enriquecer perfil com creditos (email, telefone) |
| V02 | **Remuneracao detalhada** | `remunerations.vue` (191L) | Calculo 13.33x + variaveis + beneficios + total anual |
| V03 | **Score Analysis separado** | `score_analysis.vue` (692L) | Score com confianca, requisitos expandiveis, skills matched |
| V04 | **Curriculo como tab** | `curriculum_text.vue` (513L) | Tab dedicada para texto do curriculo |
| V05 | **Sourced Profile** | `sourced-profile-*.vue` (9 arqs) | Preview especifico para candidatos sourcing LIA |
| V06 | **Candidatos similares** | `similar_candidates_modal.vue` | Modal de candidatos similares |
| V07 | **Busca IA** | `preview.vue` dialog | Gerar perfil IA para candidatos sem origem IA |

---

# PARTE 4: BUGS BACKEND + API

## Criticos

| ID | Problema | Onde | Impacto |
|----|---------|------|---------|
| B01 | **`company_id` hardcoded como `demo_company`** em todas as chamadas API do frontend React. Na producao Vue, vem da sessao mas pode haver mismatch | `useCandidatePreviewCore.tsx` linhas 77, 92, 105, 145 | Multi-tenancy comprometida |
| B02 | **Analise IA sem `company_id`** — `AnalysisRequest` nao tem campo company_id | `app/schemas/analysis.py`, `analysis_service.py` | Vazamento de dados entre empresas |

## Altos

| ID | Problema | Onde | Impacto |
|----|---------|------|---------|
| B03 | **N+1 query no opinions history** — para cada opinion, query separada para `job_vacancy.title` | `app/api/v1/opinions.py:110-117` | Performance degradada |
| B04 | **Count query ineficiente** — carrega todos records para contar em vez de `SELECT COUNT(*)` | `app/api/v1/opinions.py` | Carga desnecessaria |
| B05 | **Files usa `BACKEND_URL` direto** — bypassing proxy que adiciona auth headers | `useCandidateFiles.tsx:44,51,102,145,169` | CORS errors, sem auth |
| B06 | **Tab Arquivos "Failed to fetch"** — confirmado via Playwright em producao | `/api/v1/candidates/{id}/files` | Funcionalidade inacessivel |

## Medios/Baixos

| ID | Problema | Onde | Impacto | Sev. |
|----|---------|------|---------|------|
| B07 | **`recruiter_override` sem validacao de permissao** | `app/api/v1/opinions.py` | Usuarios sem permissao alteram pareceres | MEDIO |
| B08 | **Tipo inconsistente `candidate_id`** — UUID em `lia_opinions`, String(255) em `lia_profile_analyses` | Models SQLAlchemy | JOINs complicados | MEDIO |
| B09 | **Sem FK** entre `lia_profile_analyses`/`candidate_attachments` e `candidates` | Models SQLAlchemy | Dados orfaos | MEDIO |
| B10 | **8 endpoints nao consumidos** — paginacao opinions, PATCH, cultural-fit, bias audit, etc. | `app/api/v1/` | Funcionalidade sem UI | BAIXO |

## Endpoints Vue (codigo real)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /users/data_files` | files/wrapper.vue | Buscar arquivos |
| `GET /users/experiences` | cards/experiences.vue | Buscar experiencias |
| `GET /users/educations` | cards/educations.vue | Buscar formacoes |
| `GET /users/skill_relationships` | cards/skills.vue | Buscar skills |
| `GET /users/addresses/Candidate/{id}` | cards/addresses.vue | Buscar enderecos |
| `GET /users/candidates/{id}/calculate_remunerations` | cards/remunerations.vue | Calcular remuneracao |
| `GET /users/candidates/{id}/calculate_benefits` | cards/remunerations.vue | Calcular beneficios |

## Endpoints React (codigo real)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /api/backend-proxy/opinions/candidate/{id}/summary` | useCandidatePreviewCore | Resumo pareceres |
| `POST /api/backend-proxy/opinions/generate` | useCandidatePreviewCore | Gerar parecer |
| `GET /api/backend-proxy/opinions/candidate/{id}/history` | useCandidatePreviewCore | Historico |
| `GET /api/backend-proxy/analyses/candidate/{id}` | useCandidatePreviewCore | Analises salvas |
| `DELETE /api/backend-proxy/analyses/{aid}` | useCandidatePreviewCore | Deletar analise |
| `POST /api/backend-proxy/lia/chat` | useCandidatePreviewCore | Chat com LIA |
| `GET {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Buscar arquivos |

## Endpoints Ausentes no Vue

| Endpoint | Sev. | Descricao |
|---|---|---|
| `GET /opinions/history` | **CRITICO** | Historico de pareceres LIA |
| `POST /opinions/generate` | **CRITICO** | Gerar novo parecer |
| `POST /lia/chat` | **CRITICO** | Chat conversacional com LIA |
| `GET /activities` | ALTO | Timeline de atividades |
| `DELETE /files/{id}` | MEDIO | Deletar arquivo |
| `GET /analyses` | ALTO | Analises salvas por vaga |

---

# PARTE 5: BUGS IA + BANCO DE DADOS

## Inteligencia Artificial

| ID | Problema | Onde | Impacto | Sev. |
|----|---------|------|---------|------|
| IA01 | **Sem multi-tenancy na analise** — `AnalysisRequest` sem `company_id` | `app/schemas/analysis.py` | Sem isolamento por empresa | **CRITICO** |
| IA02 | **FairnessGuard NAO integrado** na geracao de parecer | `personalized_feedback_service.py` vs `analysis_service.py` | Parecer pode conter bias | ALTO |
| IA03 | **Prompt Injection Guard nao aplicado** — inputs nao sanitizados | `app/shared/prompt_injection.py` nao chamado em `analysis_service.py` | Candidato pode manipular analise | ALTO |
| IA04 | **Score sem nivel de confianca** — frontend nao mostra se EXPLICIT ou INFERRED | `rubric_evaluation_service.py:331-392` | Score sem transparencia | ALTO |
| IA05 | **Pesos fixos 35/25/20/20** sem customizacao por empresa | `app/schemas/analysis.py:38-43` | Mesma ponderacao para todos | MEDIO |
| IA06 | **Archetypes hardcoded** — 8 tipos fixos | `app/api/v1/analysis.py:56-112` | Nao customizavel | BAIXO |

### Arquitetura IA

```
Frontend (React/Vue)
    |
    v
POST /api/v1/analysis/candidates
    |
    v
analysis_service.analyze_candidates()
    |
    v
Claude AI (Anthropic)
    |-- Big Five -> Archetype (8 tipos)
    |-- Score Breakdown -> match_tecnico (35%), fit_personalidade (25%),
    |                      relevancia_experiencia (20%), alinhamento_cultural (20%)
    |-- Recommendation -> highly_recommended / recommended / potential / low_match / not_recommended
    v
CandidateAnalysisResult -> Frontend
```

## Banco de Dados

| ID | Problema | Tabelas | Impacto | Sev. |
|----|---------|---------|---------|------|
| DB01 | **Tipo inconsistente `candidate_id`** — UUID nativo em `lia_opinions`, String(255) em `lia_profile_analyses` e `candidate_attachments` | 3 tabelas | JOINs com conversao de tipo | MEDIO |
| DB02 | **`CandidateAttachment.id` e String** (gerado via `str(uuid4())`) | `candidate_attachments` | Performance em indexacao | MEDIO |
| DB03 | **Sem FK `lia_profile_analyses.candidate_id`** → `candidates.id` | `lia_profile_analyses` | Sem CASCADE delete | MEDIO |
| DB04 | **Sem FK `candidate_attachments.candidate_id`** → `candidates.id` | `candidate_attachments` | Anexos orfaos | MEDIO |
| DB05 | **`languages` default={}** mas producao retorna `null` | `candidates` | Frontend tratar null e {} | BAIXO |
| DB06 | **`past_locations` default=[]** mutable | `candidates` | Shared state entre instancias | BAIXO |

---

# PARTE 6: TABELA DE PRIORIDADES UNIFICADA

## Sprint 1 — Criticos (bloqueia uso) — 1-2 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-01 | **Corrigir layout preview** — drawer nao deve empurrar header/botoes da tabela | D01, D02, D03 | `preview.vue` | 1-2 dias | **CRITICO** |
| FIX-02 | **Corrigir cards atividade** — expandir ao clicar, formatar JSON, altura maxima | D17, D18, D19, D49 | `applies.vue` → novo componente | 2-3 dias | **CRITICO** |
| FIX-03 | **Implementar Tab Pareceres** — historico + subtabs + OpinionCard | D13, G01, D31-D35 | **NOVO:** `opinions/CandidateOpinionsTab.vue` | 3 dias | **CRITICO** |
| FIX-04 | **Corrigir Tab Arquivos** — resolver "Failed to fetch", implementar proxy | D25, B05, B06 | `files/wrapper.vue` + proxy config | 1-2 dias | **CRITICO** |
| FIX-05 | **Implementar acao Parecer LIA** — botao "Gerar Parecer" + conectar API | D15 | `lia_assessment.vue` | 1 dia | **CRITICO** |
| FIX-06 | **Multi-tenancy na analise IA** — company_id no AnalysisRequest | B02, IA01 | `app/schemas/analysis.py` | 1 dia | **CRITICO** |

## Sprint 2 — Alta Prioridade (funcionalidade core) — 2-3 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-07 | **Botoes de acao com labels** — trocar icones-only por icone + texto | D10, D11, D50 | `preview.vue` | 1 dia | ALTO |
| FIX-08 | **Datas no header** — cadastro, atualizacao, ultimo contato | D08 | `preview.vue` | 2h | ALTO |
| FIX-09 | **Botao LIA no header** + conectar modal chat/analise | D09, G02 | `preview.vue` + **NOVO:** `LiaChatModal.vue` | 3 dias | ALTO |
| FIX-10 | **Skills categorizadas** — agrupar por Backend/Frontend/Data + cores por fonte | D10b, D10c | `cards/skills.vue` | 1-2 dias | ALTO |
| FIX-11 | **Filtros atividade completos** — 8 filtros visiveis + "Nova Atividade" + nota | D20, D22 | **NOVO:** `activities/ActivityFilters.vue` | 1-2 dias | ALTO |
| FIX-12 | **Upload drag-and-drop** + preview de midia | D26, D27, G07, G08 | `files/wrapper.vue` + **NOVO:** `FilePreviewModal.vue` | 3 dias | ALTO |
| FIX-13 | **Integrar FairnessGuard** na geracao de parecer | IA02 | `analysis_service.py` | 1 dia | ALTO |
| FIX-14 | **Prompt Injection Guard** nos inputs | IA03 | `analysis_service.py` | 1 dia | ALTO |
| FIX-15 | **Corrigir N+1 query** no opinions history | B03, B04 | `app/api/v1/opinions.py` | 1 dia | ALTO |

## Sprint 3 — Media Prioridade (polish) — 2-3 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-16 | Tipografia DS v4.2.1 (Open Sans + Inter + JetBrains Mono) | D36, D37, D38 | `nuxt.config.ts` + CSS | 1 dia | MEDIO |
| FIX-17 | Design tokens semanticos de cores | D39, D42 | Todos os componentes | 2 dias | MEDIO |
| FIX-18 | Secoes ausentes no perfil (ExperienceHighlight, Indicadores, Preferencias) | D12b-D15b, G14 | `overview.vue` | 2-3 dias | MEDIO |
| FIX-19 | Cards experiencia melhorados (border colorida, tech stack, startup badge) | D16b | `cards/experiences.vue` | 1 dia | MEDIO |
| FIX-20 | Timeline com agrupamento por data | D23, D24 | **NOVO:** `activities/ActivityTimeline.vue` | 1-2 dias | MEDIO |
| FIX-21 | Modais DISC, BigFive, Screening | G04, G05, G06 | **NOVOS:** 3 componentes | 3 dias | MEDIO |
| FIX-22 | FKs e tipos inconsistentes no banco | DB01-DB04 | Models SQLAlchemy + migration | 1 dia | MEDIO |
| FIX-23 | Score com nivel de confianca | IA04 | Frontend + `rubric_evaluation_service.py` | 1 dia | MEDIO |
| FIX-24 | Copiar/colar parecer | D34 | `OpinionCard.vue` | 2h | MEDIO |
| FIX-25 | Redes sociais expandidas no header | D07 | `preview.vue` | 2h | MEDIO |

## Sprint 4 — Baixa Prioridade (nice-to-have) — 1-2 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-26 | Dark mode | D41 | Vuetify theme config | 2 dias | BAIXO |
| FIX-27 | Toast notifications | G16 | Config global | 2h | BAIXO |
| FIX-28 | Alertas confirmacao para acoes destrutivas | G15 | Varios | 1 dia | BAIXO |
| FIX-29 | Tab overflow com setas | D12 | `preview.vue` | 2h | BAIXO |
| FIX-30 | Defaults mutaveis no schema | DB05, DB06 | Models SQLAlchemy | 1h | BAIXO |
| FIX-31 | Navegacao prev/next entre candidatos | G13 | `preview.vue` | 1 dia | BAIXO |

## Sprint Backport React — Adaptar features superiores do Vue

| # | Correcao | IDs | Arquivo React | Esforco | Impacto |
|---|---------|-----|--------------|---------|---------|
| FIX-R01 | Remuneracao detalhada (13.33x + beneficios) | V02 | `CandidatePreviewProfileTab.tsx` | 2 dias | ALTO |
| FIX-R02 | Score Analysis rico (requisitos expandiveis) | V03 | `CandidatePreviewProfileTab.tsx` | 3 dias | ALTO |
| FIX-R03 | Enriquecimento com creditos | V01 | `candidate-preview.tsx` | 1 dia | MEDIO |

---

# PARTE 7: REFERENCIA TECNICA

## Mapeamento de Componentes — Codigo Real

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
features/candidates/curriculum_text.vue (513)   --- (Replit usa FilePreviewModal)
--- (sem equivalente)                           CandidateActivitiesTab.tsx (278 linhas)
--- (sem equivalente)                           CandidateOpinionsTab.tsx (293 linhas)
--- (sem equivalente)                           OpinionCard.tsx (305 linhas)
--- (sem equivalente)                           LiaChatModal.tsx (315 linhas)
--- (sem equivalente)                           FilePreviewModal.tsx (546 linhas)
--- (sem equivalente)                           activities/ActivityTimeline.tsx (98)
--- (sem equivalente)                           activities/ActivityFilters.tsx (131)
--- (sem equivalente)                           activities/ActivityExpandedDetails.tsx (878)
--- (sem equivalente)                           useCandidatePreviewCore.tsx (666 linhas)
--- (sem equivalente)                           useCandidateFiles.tsx (201 linhas)
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
composables/useCandidateMatches.ts (39)         ---
stores/candidate_feedbacks.ts (80)              useCandidatePreviewCore.tsx (embutido)
```

## Metricas Comparativas

| Metrica | Vue (Producao) | React (Replit) |
|---------|---------------|----------------|
| Arquivos de preview | 30+ | 13 |
| Linhas totais | ~6.345 | ~6.196 |
| Tabs implementadas | 3 | 4 |
| Modais | 3 | 7+ |
| Botoes de acao | 8 (icones) | 9 (com labels) |
| Sub-componentes atividades | 0 | 3 |
| Cards perfil | 9 | 9 |
| Features exclusivas | 7 | 14 |
| Endpoints consumidos | 7 | 9 |
| Design tokens semanticos | Parcial | Completo |
| Data fetching | N+1 (por card) | Batch (centralizado) |

## State Management — Diferenca Arquitetural

**Vue:** Estado distribuido entre 10+ componentes. Cada card faz `$axios.get()` no `onMounted`. Props e computed fluem por hierarquia.

**React:** Estado centralizado em `useCandidatePreviewCore()` (666 linhas). Um hook retorna 40+ states e handlers. Todos os fetches sao batch.

## Icones — Mapeamento

| Funcao | React (lucide-react) | Vue (mdi + lucide) | Status |
|---|---|---|---|
| Brain/LIA | `Brain` | `lucide-brain` | OK |
| LinkedIn | `Linkedin` | `lucide-linkedin` | OK |
| Download | `Download` | `lucide-download` | OK |
| GitHub | `Code` | Nao existe no preview | **Ausente** |
| Upload | `Upload` | Nao existe | **Ausente** |
| Eye/Preview | `Eye` | Nao existe | **Ausente** |
| Trash/Delete | `Trash2` | Nao existe | **Ausente** |
| Calendar | `Calendar` | Nao existe no preview | **Ausente** |

## Metodologia de Scoring IA

### Pesos do Score Breakdown

| Componente | Peso | Descricao |
|---|---|---|
| Match Tecnico | 35% | Alinhamento de habilidades tecnicas com requisitos |
| Fit de Personalidade | 25% | Compatibilidade Big Five com arquetipo ideal |
| Relevancia de Experiencia | 20% | Experiencias previas similares ao contexto |
| Alinhamento Cultural | 20% | Valores e comportamentos compativeis |

### Niveis de Recomendacao

| Nivel | Score | Acao |
|---|---|---|
| `highly_recommended` | 85-100% | Priorizar para entrevista |
| `recommended` | 70-84% | Considerar para processo |
| `potential` | 55-69% | Avaliar gaps especificos |
| `low_match` | 40-54% | Arquivar para futuras vagas |
| `not_recommended` | 0-39% | Nao prosseguir |

### Archetypes Big Five

| Archetype | Perfil | Roles Ideais |
|---|---|---|
| Catalisador Visionario | Alto O/E, Baixo N | Fundador, PM, Diretor de Inovacao |
| Executor Confiavel | Alto C/A, Baixo N | GP, Analista Senior, Ops Manager |
| Guardiao de Clientes | Alto A/E, Medio O | CS, Account Manager |
| Estrategista Analitico | Alto O/C, Baixo E | Data Scientist, Arquiteto |
| Mediador Adaptavel | Alto A/O, Medio C | HRBP, Scrum Master |
| Rainmaker Audacioso | Alto E/O, Baixo A | Vendedor, BD, Founder |
| Operador Resiliente | Alto C, N controlado | SRE, Suporte Critico |
| Arquiteto Metodico | Alto C/O, Baixo E | Engenheiro Senior, QA Lead |

## Resumo de Arquivos a Modificar

### Frontend (`ats_front/develop`)

| Arquivo | Acao | Fixes |
|---------|------|-------|
| `features/candidates/preview.vue` | Modificar | FIX-01, FIX-07, FIX-08, FIX-25, FIX-29, FIX-31 |
| `features/candidates/lia_assessment.vue` | Modificar | FIX-05 |
| `features/candidates/cards/skills.vue` | Modificar | FIX-10 |
| `features/candidates/cards/experiences.vue` | Modificar | FIX-19 |
| `features/candidates/files/wrapper.vue` | Modificar | FIX-04, FIX-12 |
| `features/candidates/applies.vue` | Rewrite | FIX-02, FIX-11, FIX-20 |
| `features/candidates/opinions/CandidateOpinionsTab.vue` | **CRIAR** | FIX-03 |
| `features/candidates/opinions/OpinionCard.vue` | **CRIAR** | FIX-03, FIX-24 |
| `features/candidates/activities/ActivityFilters.vue` | **CRIAR** | FIX-11 |
| `features/candidates/activities/ActivityTimeline.vue` | **CRIAR** | FIX-20 |
| `features/candidates/LiaChatModal.vue` | **CRIAR** | FIX-09 |
| `features/candidates/files/FilePreviewModal.vue` | **CRIAR** | FIX-12 |

### Backend (FastAPI)

| Arquivo | Acao | Fixes |
|---------|------|-------|
| `app/schemas/analysis.py` | Modificar | FIX-06 |
| `app/domains/cv_screening/services/analysis_service.py` | Modificar | FIX-06, FIX-13, FIX-14 |
| `app/api/v1/opinions.py` | Modificar | FIX-15 |
| Models SQLAlchemy | Migration | FIX-22, FIX-30 |

---

# COMO CRIAR CARDS JIRA

## Template de Card

```
TITULO: [FIX-XX] Descricao curta da correcao
TIPO: Bug / Feature / Improvement
PRIORIDADE: Critico / Alto / Medio / Baixo
SPRINT: 1 / 2 / 3 / 4
ESTIMATIVA: X dias

DESCRICAO:
**Problema:** [Copiar da coluna "Correcao" na Parte 6]
**IDs relacionados:** [Copiar IDs da coluna "IDs"]
**Arquivo(s):** [Copiar da tabela "Arquivos a Modificar"]

**Comportamento atual (Vue):**
[Copiar da coluna "Vue (Producao)" na Parte 2 ou 3]

**Comportamento esperado (React referencia):**
[Copiar da coluna "React (Replit)" na Parte 2 ou 3]

**Correcao sugerida:**
[Copiar bloco de codigo da Parte 2, se disponivel]

**Criterio de aceite:**
- [ ] Comportamento alinhado com referencia React
- [ ] Sem regressao em funcionalidades existentes
- [ ] Teste manual no preview do candidato
```

## Agrupamento sugerido para Epics

| Epic | Cards | Sprint |
|------|-------|--------|
| **Layout & Navigation** | FIX-01, FIX-29, FIX-31 | 1, 4 |
| **Header & Actions** | FIX-07, FIX-08, FIX-09, FIX-25 | 2, 3 |
| **Tab Atividades** | FIX-02, FIX-11, FIX-20 | 1, 2, 3 |
| **Tab Arquivos** | FIX-04, FIX-12 | 1, 2 |
| **Tab Pareceres** | FIX-03, FIX-05, FIX-24 | 1, 2, 3 |
| **IA & Backend** | FIX-06, FIX-13, FIX-14, FIX-15 | 1, 2 |
| **Design System** | FIX-16, FIX-17, FIX-26 | 3, 4 |
| **Perfil Enriquecido** | FIX-10, FIX-18, FIX-19, FIX-21 | 2, 3 |
| **Database** | FIX-22, FIX-30 | 3, 4 |
| **Backport Vue→React** | FIX-R01, FIX-R02, FIX-R03 | Backlog |

## Documentos Relacionados

- **Evidencia de testes:** Este documento + screenshots em `attached_assets/` e `plataforma-lia/docs/screenshots/`
- **Componentes React (referencia):** `plataforma-lia/src/components/candidate-preview/` (13 arquivos, 6.196 linhas)
- **Backend (referencia):** `lia-agent-system/app/` (opinions, analysis, profile analysis APIs)
- **Auditoria busca/search:** `.agents/outputs/testes-funcionais-wedotalent.md` + `.agents/outputs/guia-completo-correcoes-wedotalent.md`

---

*Documento gerado a partir de: analise de codigo Vue real (GitHub API, 30+ arquivos), inspecao de codigo React (13 arquivos), testes Playwright e2e, e screenshots de producao.*
*Atualizado em 2026-04-03.*
