# TEMPLATE — Saída do script jira-fetch-analyze.py
# Card de exemplo: WT-1637 — Menu Lateral + Triagem WSI
# Gerado por: python3 scripts/jira-fetch-analyze.py WT-1637 --vue-file components/ui/menu/sidebar.vue
# ─────────────────────────────────────────────────────────────────────────────
# Escopo: Funcionalidade + Design (TODOS os layers)
# Inclui: blocos de código por layer (Backend 🐍, IA 🤖, Integração 🔌,
#          Banco 🗄️, React ⚛️, Vue 🟢), Vuetify defaults, bloco vuetify.ts
# ─────────────────────────────────────────────────────────────────────────────


# MENU LATERAL + WSI — Auditoria Completa: Funcionalidade + Design DS LIA v4.2.1

Card: WT-1637  |  Gerado em: 21/03/2026

O card reporta quatro problemas: (1) sidebar visível apenas no hover; (2) logo sobreposto ao
expandir; (3) classificação de competências do WSI retornando em inglês (hardcoded) em vez
de português; (4) média progressiva do grafo WSI calculada incorretamente. A análise
consultou todos os layers: frontend React/Replit, Vue/GitHub, backend Python, agente IA
wsi_interview_graph.py e hook de estado.

Cada issue de funcionalidade detalha TODOS os layers afetados com código ANTES/DEPOIS
específico por layer. Cada issue de design inclui ANTES (Vue incorreto) → DEPOIS (Vue correto).

🐛 BetterBugs: https://app.betterbug.io/issue/xyz123

─────────────────────────────────────────────────────────────────

## 📁 Arquivos de Referência

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Sidebar principal (fonte da verdade)
• [Frontend React] plataforma-lia/src/hooks/use-sidebar.ts — Hook de estado colapsado/expandido
• [Agente IA] lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py — Grafo WSI principal
• [Backend Python] lia-agent-system/app/domains/cv_screening/services/wsi_report_generator.py — Geração de relatório WSI
• [Vue/GitHub] components/ui/menu/sidebar.vue — Sidebar Vue a ser corrigido
• [Vue/GitHub] components/screening/wsi-report.vue — Exibição do relatório WSI no Vue

─────────────────────────────────────────────────────────────────

## ⚙️ Issues de Funcionalidade

Problemas funcionais identificados na transcrição: erros, comportamentos incorretos,
features incompletas, integrações, lógica de IA e banco de dados.
Cada issue detalha TODOS os layers afetados (Backend Python 🐍, Agente IA 🤖,
Integração 🔌, Banco de Dados 🗄️, Frontend React ⚛️, Vue 🟢) com código ANTES/DEPOIS
específico por layer.

─────────────────────────────────────────────────────────────────

### Issue F01 — Competências WSI classificadas em inglês (hardcoded) [BUG]

Layers afetados: **Agente IA, Backend Python, Vue**

O WSIReportGenerator classifica competências comportamentais como "communication",
"leadership", "teamwork" (inglês hardcoded) em vez de "comunicação", "liderança",
"trabalho em equipe". O bug está na função `_classify_competency` do agente IA —
o mapeamento de categorias está em inglês e nunca foi traduzido.

#### 🤖 Agente IA
Arquivo: `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`

**Lógica de IA atual — INCORRETA:**
```python
BEHAVIORAL_CATEGORIES = {
    "communication": ["verbal", "written", "listening", "presentation"],
    "leadership": ["management", "delegation", "motivation", "vision"],
    "teamwork": ["collaboration", "cooperation", "conflict", "support"],
    "problem_solving": ["analytical", "creative", "decision", "critical"],
}

def _classify_competency(self, competency_name: str) -> str:
    name_lower = competency_name.lower()
    for category, keywords in BEHAVIORAL_CATEGORIES.items():
        if any(kw in name_lower for kw in keywords):
            return category  # retorna em inglês
    return "other"
```

**lógica corrigida:**
```python
BEHAVIORAL_CATEGORIES = {
    "comunicacao": {
        "label": "Comunicação",
        "keywords": ["verbal", "written", "listening", "presentation",
                     "comunicação", "verbal", "escrita", "apresentação"]
    },
    "lideranca": {
        "label": "Liderança",
        "keywords": ["management", "delegation", "motivation", "vision",
                     "liderança", "gestão", "delegação", "motivação"]
    },
    "trabalho_equipe": {
        "label": "Trabalho em Equipe",
        "keywords": ["collaboration", "cooperation", "teamwork",
                     "colaboração", "cooperação", "equipe", "time"]
    },
    "resolucao_problemas": {
        "label": "Resolução de Problemas",
        "keywords": ["analytical", "creative", "decision", "critical",
                     "analítico", "criativo", "decisão", "crítico"]
    },
}

def _classify_competency(self, competency_name: str) -> str:
    name_lower = competency_name.lower()
    for key, data in BEHAVIORAL_CATEGORIES.items():
        if any(kw in name_lower for kw in data["keywords"]):
            return data["label"]  # retorna label em português
    return "Outros"
```

#### 🐍 Backend Python
Arquivo: `lia-agent-system/app/domains/cv_screening/services/wsi_report_generator.py`

**Código atual — INCORRETO:**
```python
def generate_competency_section(self, competencies: list) -> dict:
    classified = {}
    for comp in competencies:
        category = self.agent._classify_competency(comp["name"])
        if category not in classified:
            classified[category] = []
        classified[category].append(comp)
    return classified
    # classified.keys() = ["communication", "leadership", ...] — inglês
```

**deve ficar assim:**
```python
def generate_competency_section(self, competencies: list) -> dict:
    classified = {}
    for comp in competencies:
        label = self.agent._classify_competency(comp["name"])
        # label já vem em português do agente corrigido
        if label not in classified:
            classified[label] = []
        classified[label].append(comp)
    return classified
    # classified.keys() = ["Comunicação", "Liderança", ...] — português ✓
```

#### 🟢 Vue
Arquivo: `components/screening/wsi-report.vue`

**Vue atual — INCORRETO:**
```vue
<template v-for="(comps, category) in competencyGroups" :key="category">
  <h4 class="text-subtitle-2 font-weight-bold mb-2">
    {{ category }}
    <!-- Exibe "communication", "leadership" — inglês do backend -->
  </h4>
</template>
```

**Vue corrigido:**
```vue
<template v-for="(comps, category) in competencyGroups" :key="category">
  <h4 class="text-subtitle-2 font-weight-bold mb-2">
    {{ category }}
    <!-- Agora exibe "Comunicação", "Liderança" — português do backend corrigido -->
  </h4>
</template>
<!-- Nenhuma tradução local necessária: correção feita no agente IA -->
```

─────────────────────────────────────────────────────────────────

### Issue F02 — Média progressiva do grafo WSI calculada incorretamente [BUG]

Layers afetados: **Agente IA, Backend Python, Frontend React, Vue**

O grafo WSI recalcula a média geral com todos os nós a cada novo ponto, em vez de
usar rolling window. O resultado é que candidatos com notas baixas no início nunca
"recuperam" a média mesmo com excelentes respostas subsequentes.

#### 🤖 Agente IA
Arquivo: `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py`

**Lógica de IA atual — INCORRETA:**
```python
def _calculate_wsi_average(self, state: WSIState) -> float:
    scores = [node["score"] for node in state["completed_nodes"]]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)  # média simples — afetada por outliers iniciais
```

**lógica corrigida:**
```python
ROLLING_WINDOW = 5  # últimas 5 competências

def _calculate_wsi_average(self, state: WSIState) -> float:
    scores = [node["score"] for node in state["completed_nodes"]]
    if not scores:
        return 0.0
    # Rolling window: usa apenas as últimas N respostas para refletir
    # a performance recente, não a cumulativa desde o início
    window = scores[-ROLLING_WINDOW:]
    return round(sum(window) / len(window), 2)
```

#### 🐍 Backend Python
Arquivo: `lia-agent-system/app/domains/cv_screening/services/wsi_report_generator.py`

**Código atual — INCORRETO:**
```python
def build_wsi_graph_data(self, session: WSISession) -> dict:
    points = []
    for i, node in enumerate(session.completed_nodes):
        avg = sum(n["score"] for n in session.completed_nodes[:i+1]) / (i + 1)
        points.append({"x": i + 1, "y": avg, "label": node["competency"]})
    return {"points": points, "type": "progressive_avg"}
```

**deve ficar assim:**
```python
ROLLING_WINDOW = 5

def build_wsi_graph_data(self, session: WSISession) -> dict:
    points = []
    for i, node in enumerate(session.completed_nodes):
        window = session.completed_nodes[max(0, i - ROLLING_WINDOW + 1):i + 1]
        avg = round(sum(n["score"] for n in window) / len(window), 2)
        points.append({"x": i + 1, "y": avg, "label": node["competency"]})
    return {"points": points, "type": "rolling_avg", "window": ROLLING_WINDOW}
```

#### ⚛️ Frontend React
Arquivo: `plataforma-lia/src/components/screening/WSIProgressChart.tsx`

**React atual — INCORRETO:**
```tsx
// Tooltip do gráfico não distingue média simples de rolling
<Tooltip
  formatter={(value) => [`${value}`, 'Média WSI']}
/>
```

**React corrigido:**
```tsx
<Tooltip
  formatter={(value, name, props) => {
    const window = props?.payload?.window
    const label = window ? `Média WSI (últimas ${window} respostas)` : 'Média WSI'
    return [`${value}`, label]
  }}
/>
```

#### 🟢 Vue
Arquivo: `components/screening/wsi-progress-chart.vue`

**Vue atual — INCORRETO:**
```vue
<apexchart
  type="line"
  :options="chartOptions"
  :series="[{ name: 'Média WSI', data: graphPoints }]"
/>

<script setup>
// tooltip sem distinção de tipo de média
const chartOptions = {
  tooltip: { y: { formatter: (val) => val.toFixed(1) } }
}
</script>
```

**Vue corrigido:**
```vue
<apexchart
  type="line"
  :options="chartOptions"
  :series="[{ name: rollingLabel, data: graphPoints }]"
/>

<script setup>
const props = defineProps({ graphData: Object })

const rollingLabel = computed(() =>
  props.graphData?.window
    ? `Média WSI (últimas ${props.graphData.window} respostas)`
    : 'Média WSI'
)

const chartOptions = computed(() => ({
  tooltip: {
    y: { formatter: (val) => `${val.toFixed(1)} / 10.0` }
  }
}))
</script>
```

─────────────────────────────────────────────────────────────────

### Issue F03 — Sidebar invisível por padrão (expand-on-hover) [BUG]

Layers afetados: **Frontend React, Vue**

O sidebar usa expand-on-hover no Vuetify. O React usa permanent — sempre visível,
alternando entre colapsado e expandido via botão chevron explícito.

#### ⚛️ Frontend React
Arquivo: `plataforma-lia/src/components/ui/sidebar.tsx`

**React atual — INCORRETO:**
```tsx
// React já está correto — sidebar sempre montado no DOM
// Garantir apenas que não existe onMouseEnter controlando isCollapsed
```

**React corrigido:**
```tsx
// Sem alteração — verificar apenas que useSidebar não usa hover events
const { isCollapsed, setIsCollapsed } = useSidebar()
// isCollapsed muda APENAS via botão chevron onClick
```

#### 🟢 Vue
Arquivo: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-navigation-drawer
  expand-on-hover
  :rail="isRail"
  :rail-width="64"
  v-model="drawer"
  @mouseenter="isHovered = true"
  @mouseleave="isHovered = false"
>
```

**Vue corrigido:**
```vue
<v-navigation-drawer
  permanent
  :rail="isRail"
  :rail-width="64"
  :width="240"
  v-model="drawer"
>
<!-- Remover @mouseenter, @mouseleave e isHovered por completo -->
```

─────────────────────────────────────────────────────────────────

## 🎨 Issues de Design (DS LIA v4.2.1)

Problemas visuais identificados nos elementos mencionados na transcrição.
Cada issue mapeia ANTES (Vue atual incorreto) → DEPOIS (Vue corrigido conforme DS LIA).
React/Replit = fonte da verdade absoluta.
Para auditoria de design ainda mais aprofundada, usar jira-audit-design.py.

### Issue D01 — Border radius dos itens incorreto (12px vs 8px)

Itens usam rounded-12px (12px custom). DS LIA v4.2.1 exige 8px universal.

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-list-item class="rounded-12px py-2">
```

**deve ficar assim — React/DS LIA:**
```vue
<v-list-item class="rounded-lg py-2" style="border-radius: 8px !important;">
```

⚠️ rounded-12px viola a regra de 8px universal. Aparece em todos os itens de navegação.

─────────────────────────────────────────────────────────────────

### Issue D02 — Ícones 14px (deve ser 16px)

DS LIA v4.2.1: todos os ícones de interface SEMPRE 16px (w-4 h-4).

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<Icon :name="item.icon" size="14" customClasses="mx-1" />
```

**deve ficar assim — React/DS LIA:**
```vue
<Icon :name="item.icon" size="16" customClasses="mx-1" />
```

⚠️ 14px vs 16px — sistemático em todos os ícones de navegação.

─────────────────────────────────────────────────────────────────

### Issue D03 — Tipografia sem font-size explícito (13px, line-height 1.25)

DS LIA v4.2.1: texto de navegação 13px, line-height 1.25. Vuetify usa 14px por padrão.

Ref React: `plataforma-lia/src/components/ui/sidebar-nav.tsx`
Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-list-item :title="showOnOpenNavigation ? item.label : ''">
  <!-- font-size não especificado → Vuetify aplica 14px -->
</v-list-item>
```

**deve ficar assim — React/DS LIA:**
```vue
<v-list-item
  :title="!isRail ? item.label : ''"
  style="font-size: 13px; line-height: 1.25;"
>
```

─────────────────────────────────────────────────────────────────

### Issue D04 — Largura sidebar expandido não especificada (256px Vuetify vs 240px DS LIA)

DS LIA: sidebar expandido = 240px. Sem width explícito, Vuetify usa 256px.

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<v-navigation-drawer :rail-width="64" :rail="isRail">
  <!-- sem width → Vuetify usa 256px por padrão -->
```

**deve ficar assim — React/DS LIA:**
```vue
<v-navigation-drawer :rail-width="64" :width="240" :rail="isRail" permanent>
```

⚠️ 16px de largura extra → layout da página desloca 16px para a direita.

─────────────────────────────────────────────────────────────────

### Issue D05 — Label MENU controlado por hover; letter-spacing excessivo

DS LIA: elementos condicionais controlados por isRail. letter-spacing máximo 0.05em.

Arquivo Vue: `components/ui/menu/sidebar.vue`

**Vue atual — INCORRETO:**
```vue
<p class="f12 text-body-dark font-weight-medium pt-4 pb-3 px-4"
   style="letter-spacing: 0.2em"
   v-if="showOnOpenNavigation">
  MENU
</p>
```

**deve ficar assim — React/DS LIA:**
```vue
<p v-if="!isRail"
   class="text-xs text-grey-darken-1 font-weight-medium pt-4 pb-3 px-4"
   style="letter-spacing: 0.05em;">
  MENU
</p>
```

⚠️ showOnOpenNavigation depende de hover (isHovered). Após corrigir para permanent, deve usar !isRail.

─────────────────────────────────────────────────────────────────

## ⚠️ ALERTA VUETIFY DEFAULTS — Para dev / ClaudeCode / Cursor

Causa raiz sistêmica: os problemas abaixo não são erros isolados — são causados por
defaults implícitos do Vuetify que divergem do DS LIA (React/Replit = fonte da verdade).
Corrija localmente E atualize o vuetify.ts (global defaults) para evitar reincidência.

### v-icon — size ausente

- Vuetify default implícito: 24px (Material Design default)
- React/Replit (correto): w-4 h-4 = 16px
- Impacto visual: ícones 8px maiores que o esperado em toda a navegação
- Fix local: `<v-icon size="16">mdi-*</v-icon>`
- Fix global (vuetify.ts): `VIcon: { size: '16' }`

### v-navigation-drawer — width ausente

- Vuetify default implícito: 256px
- React/Replit (correto): 240px (w-60)
- Impacto visual: layout da página desloca 16px para a direita
- Fix local: `:width="240"`
- Fix global (vuetify.ts): `VNavigationDrawer: { width: 240 }`

### v-btn — variant ausente

- Vuetify default implícito: elevated (box-shadow visível)
- React/Replit (correto): flat (sem sombra)
- Impacto visual: botões do toggle com sombra indevida
- Fix local: `<v-btn variant="flat" size="small">`
- Fix global (vuetify.ts): `VBtn: { variant: 'flat', size: 'small' }`

### v-card — elevation ausente

- Vuetify default implícito: 1 (box-shadow sutil)
- React/Replit (correto): 0 (flat, sem sombra)
- Impacto visual: cards do relatório WSI com sombra indevida
- Fix local: `<v-card elevation="0" class="border border-grey-lighten-3">`
- Fix global (vuetify.ts): `VCard: { elevation: 0 }`

### Como atualizar o vuetify.ts

```typescript
// plugins/vuetify.ts (ou config/vuetify.config.ts)

createVuetify({
  defaults: {
    VIcon:             { size: '16' },
    VTextField:        { density: 'compact', variant: 'outlined' },
    VSelect:           { density: 'compact', variant: 'outlined' },
    VAutocomplete:     { density: 'compact', variant: 'outlined' },
    VBtn:              { variant: 'flat', size: 'small' },
    VCard:             { elevation: 0 },
    VNavigationDrawer: { width: 240 },
    VTabs:             { density: 'compact' },
  },
})
```

─────────────────────────────────────────────────────────────────

## 🗂️ Arquivos a Modificar

• [Agente IA] lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py — Corrigir BEHAVIORAL_CATEGORIES para português + rolling window na média
• [Backend Python] lia-agent-system/app/domains/cv_screening/services/wsi_report_generator.py — Corrigir build_wsi_graph_data para rolling average + labels PT
• [Frontend React] plataforma-lia/src/components/screening/WSIProgressChart.tsx — Atualizar tooltip para exibir "últimas N respostas"
• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Verificar que isCollapsed não depende de hover
• [Vue] components/ui/menu/sidebar.vue — Corrigir permanent, largura 240px, logo, tipografia, border-radius, ícones
• [Vue] components/screening/wsi-report.vue — Adaptar exibição de categorias (agora em português)
• [Vue] components/screening/wsi-progress-chart.vue — Atualizar label da série e tooltip rolling window
• [Vue/Global] plugins/vuetify.ts — Adicionar defaults DS LIA (VIcon, VBtn, VCard, VNavigationDrawer)

─────────────────────────────────────────────────────────────────

## 📋 Action Items

• [ ] [Agente IA] Substituir BEHAVIORAL_CATEGORIES em inglês por versão PT com labels e keywords bilíngues
• [ ] [Agente IA] Implementar rolling window (N=5) na função _calculate_wsi_average
• [ ] [Backend] Atualizar build_wsi_graph_data para usar rolling average e retornar campo "window"
• [ ] [Backend] Verificar que generate_competency_section propaga labels em português
• [ ] [Frontend React] Atualizar tooltip do WSIProgressChart para mostrar "últimas N respostas"
• [ ] [Vue] Corrigir exibição de categorias WSI (de inglês hardcoded para português do backend)
• [ ] [Vue] Atualizar wsi-progress-chart.vue: label da série + tooltip rolling window
• [ ] [Vue] Remover expand-on-hover → permanent no v-navigation-drawer
• [ ] [Vue] Remover isHovered e showOnOpenNavigation — usar isRail diretamente
• [ ] [Vue] Adicionar :width="240" explícito
• [ ] [Vue] Corrigir border-radius 12px → 8px, ícones 14px → 16px, font-size 13px
• [ ] [Vue/Global] Atualizar vuetify.ts com defaults DS LIA completos

─────────────────────────────────────────────────────────────────

## ✅ Critérios de Aceite

• [IA] _classify_competency retorna "Comunicação", "Liderança", etc. — nunca "communication", "leadership"
• [IA] Média WSI usa rolling window de 5 — candidatos com melhora recente refletem nota atual corretamente
• [Backend] /api/wsi/report retorna competency groups com keys em português
• [Backend] /api/wsi/graph retorna campo "window": 5 junto com os points
• [Frontend React] Tooltip do gráfico exibe "Média WSI (últimas 5 respostas)"
• [Vue] wsi-report.vue exibe "Comunicação", "Liderança" — nunca inglês
• [Vue] wsi-progress-chart.vue exibe label e tooltip com "últimas 5 respostas"
• [Sidebar] Menu visível permanentemente sem precisar de hover
• [Sidebar] Alternância colapsado ↔ expandido via botão chevron — nunca por hover
• [Sidebar] Largura expandido: exatamente 240px; colapsado: 64px
• [Design] Border radius dos itens: 8px; ícones: 16px; font-size: 13px
• [Design] Label MENU: letter-spacing 0.05em; controlado por !isRail
• [Vue/Global] vuetify.ts atualizado com todos os defaults DS LIA
• [Regressão] Nenhuma outra tela regrediu após as correções dos defaults globais

─────────────────────────────────────────────────────────────────

> Referência: React/Replit é sempre a fonte da verdade de design e funcionalidade.
> Para auditoria de design exclusiva e mais completa, usar jira-audit-design.py.
