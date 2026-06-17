# Scripts de Automação Jira — Documentação Completa

> **Plataforma LIA / WeDOTalent** — Análise técnica automatizada de cards Jira com Claude AI  
> Versão: 3.0 | DS LIA v4.2.1 | Spec Driven Development | claude-sonnet-4-6

---

## Visão Geral

Dois scripts Python que transformam cards Jira com texto livre em análises técnicas estruturadas, prontas para ser usadas como contexto por Cursor, Claude Code ou qualquer AI coder.

| Script | Arquivo | Escopo | Quando usar |
|--------|---------|--------|-------------|
| **Script 1** | `scripts/jira-fetch-analyze.py` | Funcionalidade + Design (todos os layers) | Card misto: bugs, funcionalidades incompletas, problemas visuais |
| **Script 2** | `scripts/jira-audit-design.py` | Design exclusivo (Vue vs React) | Card de design/UI: divergências visuais Vue vs React |

### O que os scripts fazem

O fluxo é em dois tempos distintos:

**Fase 1 — Replit lê e coleta tudo** (os scripts Python fazem isso):
1. Lê o card Jira — transcrição completa, resumo, link BetterBugs
2. Acessa a URL pública do BetterBugs e extrai screenshots, logs, vídeo, info do browser
3. Lê arquivos de código real de todos os layers:
   - Frontend React diretamente no Replit (fonte da verdade DS LIA)
   - Frontend Vue, v5 e qualquer outro repo necessário via GitHub API (`WeDOTalent/*`)
   - Backend Python, Agentes IA, Integrações — diretamente no Replit
4. Monta um contexto unificado com tudo que foi coletado

**Fase 2 — Claude analisa e publica em 2 partes** (recebe tudo pronto e gera):
5. Gera JSON estruturado com issues, ANTES/DEPOIS, spec-driven e mais
6. **Parte 1:** Replit APPENDA a análise principal na description (conteúdo original preservado) → `PUT /issue/{key}`
7. **Parte 2:** Replit posta design issues + critérios + DoD como comentário → `POST /issue/{key}/comment`

---

## Estratégia de 2 Partes — v3.0

### Por que 2 partes?

Cards com muitas issues + code blocks ANTES/DEPOIS em múltiplos layers consumiam todo o budget de 16k tokens do Claude, truncando o JSON antes de chegar em design issues, critérios de aceite e DoD. A solução é dividir o output em duas publicações Jira distintas.

### Descrição do card (Parte 1 — PUT)

Conteúdo que vai direto na **descrição do card**:

| Script 1 (`jira-fetch-analyze.py`) | Script 2 (`jira-audit-design.py`) |
|-------------------------------------|-----------------------------------|
| Issues funcionais (F01–Fxx) com code blocks ANTES/DEPOIS por layer | Issues de design (01–xx) com code blocks Vue vs React |
| Resumo + arquivos de referência + action items | Vuetify defaults + alertas |
| Conteúdo original do card **preservado acima** via ADF | Conteúdo original do card **preservado acima** via ADF |

### Comentário do card (Parte 2 — POST)

Conteúdo que vai no **comentário** (área sem limite de espaço):

| Script 1 | Script 2 |
|----------|----------|
| Issues de design (D01–Dxx) | Comportamento Esperado (DADO/QUANDO/ENTÃO) |
| Critérios de aceite | Fora de Escopo |
| Definition of Done | Impacto em Outros Sistemas |
| | Definition of Done + Critérios de Aceite |

### Preservação de conteúdo existente

**Regra absoluta:** os scripts NUNCA apagam conteúdo do card. O fluxo é:

```
existing_nodes = card["fields"]["description"]["content"]  # ADF atual
new_nodes = build_analysis_adf(...)["content"]            # Nova análise

merged = existing_nodes + [separator_rule, separator_heading, separator_rule] + new_nodes
PUT /issue/{key}  →  merged (todo o histórico preservado)
```

O separador visual (`──────`) deixa claro onde termina o conteúdo original e onde começa a análise gerada automaticamente.

---

## Pré-requisitos e Configuração

### Integrações necessárias (Replit)
- **Jira** — integração Replit configurada (OAuth)
- **Anthropic** — integração Replit configurada (modelo: `claude-sonnet-4-6`, via proxy `AI_INTEGRATIONS_ANTHROPIC_BASE_URL`)
- **GitHub** — secret `GITHUB_PAT_WEDOTALENT` com acesso a toda a org `WeDOTalent` (wedo-nuxt, v5, e qualquer outro repo necessário)

### Constantes principais (topo dos scripts)
```python
CLOUD_ID = "8cf762f8-6a44-47de-8915-6b3dc0cd2715"  # ID da workspace Jira WeDOTalent
GITHUB_ORG = "WeDOTalent"          # Organização GitHub — todos os repos acessíveis
GITHUB_VUE_REPO = "wedo-nuxt"      # Repo Vue padrão (pode ser sobrescrito por repo)
GITHUB_BRANCH = "main"
WORKSPACE_ROOT = "/home/runner/workspace"
```

> **Nota sobre GitHub:** O PAT `GITHUB_PAT_WEDOTALENT` tem acesso a toda a organização `WeDOTalent`.
> O Replit pode ler arquivos de qualquer repo — `wedo-nuxt`, `v5`, ou qualquer outro —
> passando o parâmetro `repo="WeDOTalent/nome-do-repo"` na função `fetch_github_file()`.
> O `wedo-nuxt` é apenas o repo padrão para Vue; o código Python pode buscar em qualquer repo da org.

---

## Script 1 — `jira-fetch-analyze.py`

### O que faz

Análise **completa multi-layer**: lê a transcrição do card, visita código em todos os layers
(React, Vue, Backend, IA, Integrações, Banco de Dados) e gera um card estruturado com:

- Issues de funcionalidade com código ANTES/DEPOIS por layer
- Issues de design Vue vs React com ANTES/DEPOIS
- Alertas de Vuetify defaults divergentes do DS LIA
- Spec driven: Comportamento Esperado (DADO/QUANDO/ENTÃO), Fora de Escopo, Definition of Done
- Impacto em outros sistemas, Critérios de Qualidade IA (se agentes envolvidos)

### Como usar

```bash
# Uso básico (busca arquivos automaticamente por keywords)
python3 scripts/jira-fetch-analyze.py WT-1637

# Dry-run (mostra resultado sem publicar no Jira)
python3 scripts/jira-fetch-analyze.py WT-1637 --dry-run

# Forçar arquivos específicos
python3 scripts/jira-fetch-analyze.py WT-1637 \
  --react-file plataforma-lia/src/components/ui/sidebar.tsx \
  --vue-file components/ui/menu/AppSidebar.vue \
  --backend-file lia-agent-system/app/api/v1/jobs.py

# Múltiplos arquivos por layer
python3 scripts/jira-fetch-analyze.py WT-1637 \
  --react-file plataforma-lia/src/components/sidebar.tsx \
  --react-file plataforma-lia/src/components/header.tsx \
  --vue-file components/ui/menu/sidebar.vue \
  --backend-file lia-agent-system/app/api/v1/jobs.py
```

### Fluxo detalhado (7 passos — v3.0)

```
─── FASE 1: Replit lê e coleta ─────────────────────────────────────────────

[1/7] Replit busca credenciais Jira (via integração OAuth configurada no Repl)

[2/7] Replit busca o card WT-XXXX na API do Jira:
      → lê summary + description completa (transcrição)
      → extrai nós ADF existentes (transcrição, screenshots, BetterBugs)
      → esses nós serão PRESERVADOS — a análise é APPENDADA, nunca sobrescrita
      → extrai keywords, caminhos de arquivo mencionados, URLs .vue

[3/7] Replit lê código React diretamente no próprio ambiente:
      → arquivos passados via --react-file (leitura direta do filesystem)
      → busca automática por keywords nos diretórios React do Replit

[4/7] Replit lê código Backend + IA + Integrações (também no filesystem local):
      → arquivos passados via --backend-file
      → busca automática por keywords em backend, agentes IA, integrações

[5/7] Replit lê código Vue (e qualquer outro repo) via GitHub API:
      → arquivos passados via --vue-file (qualquer repo: wedo-nuxt, v5, etc.)
      → arquivos .vue mencionados na transcrição → buscados via GitHub API
      → busca automática por keywords no GitHub (repo padrão: wedo-nuxt)

─── FASE 2: Claude analisa e publica em 2 partes ────────────────────────────

[6/7] Parte 1 — Descrição (issues de funcionalidade com código ANTES/DEPOIS):
      Replit detecta URL BetterBugs → acessa e extrai conteúdo público
      Claude Parte 1: gera issues funcionais (F01-Fxx) com code blocks por layer
      Replit: existing_nodes + separator + nova análise → PUT /issue/{key}

[7/7] Parte 2 — Comentário (design + critérios + DoD):
      Claude Parte 2: gera issues de design, critérios de aceite e DoD
      Replit: converte para ADF e posta como comentário → POST /issue/{key}/comment
      Resultado: tudo visível no card sem exceder CONTENT_LIMIT_EXCEEDED do Jira
```

### Layers de código coletados pelo Replit

O Replit (scripts Python) busca e lê os arquivos de cada layer antes de enviar para o Claude.

| Layer | Label no Card | Onde o Replit busca | Extensões |
|-------|--------------|---------------------|-----------|
| Frontend React | `⚛️ Frontend React` | Replit: `plataforma-lia/src` | `.tsx .ts .css` |
| Backend Python | `🐍 Backend Python` | Replit: `lia-agent-system/app/api` `app/domains` `app/services` | `.py` |
| Agentes IA | `🤖 Agente IA` | Replit: `lia-agent-system/app/domains` `app/graph` | `.py` |
| Integrações | `🔌 Integração` | Replit: `plataforma-lia/src/lib` `app/api` `lia-agent-system/app/integrations` | `.ts .py` |
| Vue / qualquer repo | `🟢 Vue` | GitHub API: `WeDOTalent/wedo-nuxt`, `WeDOTalent/v5`, ou qualquer outro repo da org | `.vue` |

> **GitHub:** O Replit acessa via GitHub API qualquer repo da org `WeDOTalent`.
> O padrão é `wedo-nuxt`, mas via `--vue-file` você pode apontar para qualquer repo:
> ```bash
> # Arquivo do repo v5
> python3 scripts/jira-fetch-analyze.py WT-1637 --vue-file pages/pipeline/index.vue
> ```
> A função `fetch_github_file(path, repo="WeDOTalent/v5")` aceita qualquer repo da org.

### Estrutura do JSON gerado pelo Claude

```json
{
  "titulo_auditoria": "String descritiva do que foi analisado",
  "resumo": "2-3 parágrafos: contexto, o que foi analisado, o que precisa ser feito",
  "betterbugs_link": "https://app.betterbugs.io/... | null",
  "arquivos_de_referencia": [
    {
      "path": "plataforma-lia/src/components/ui/sidebar.tsx",
      "layer": "Frontend React",
      "descricao": "Componente de sidebar — fonte da verdade de design"
    }
  ],
  "comportamento_esperado": [
    {
      "dado": "que o recrutador está na tela de pipeline",
      "quando": "clica no botão de expandir menu",
      "entao": "o menu lateral expande de 64px para 240px com animação suave",
      "e": "o estado persiste ao navegar entre páginas"
    }
  ],
  "fora_de_escopo": [
    "Refatoração do backend de jobs",
    "Mudanças na lógica de permissões"
  ],
  "issues_funcionalidade": [
    {
      "numero": "F01",
      "titulo": "Menu lateral não persiste estado expandido/colapsado",
      "tipo": "bug",
      "descricao": "Ao navegar entre páginas, o estado do menu volta para colapsado...",
      "layers_afetados": ["Frontend React", "Vue"],
      "blocos_de_codigo": [
        {
          "layer": "Frontend React",
          "arquivo": "plataforma-lia/src/components/ui/sidebar.tsx",
          "linguagem": "tsx",
          "antes_label": "React atual — INCORRETO",
          "antes": "const [open, setOpen] = useState(false) // sem persistência",
          "depois_label": "React corrigido",
          "depois": "const [open, setOpen] = useLocalStorage('sidebar-open', true)"
        },
        {
          "layer": "Vue",
          "arquivo": "components/ui/menu/AppSidebar.vue",
          "linguagem": "vue",
          "antes_label": "Vue atual — INCORRETO",
          "antes": "const isOpen = ref(false)",
          "depois_label": "Vue corrigido",
          "depois": "const isOpen = useLocalStorage('sidebar-open', true)"
        }
      ]
    }
  ],
  "issues_design": [
    {
      "numero": "D01",
      "titulo": "Sidebar com 256px — deveria ser 240px (DS LIA)",
      "descricao": "Vuetify Navigation Drawer usa 256px por default, DS LIA exige 240px",
      "arquivo_react": "plataforma-lia/src/components/ui/sidebar.tsx",
      "arquivo_vue": "components/ui/menu/AppSidebar.vue",
      "antes_label": "Vue atual — INCORRETO",
      "antes_codigo": "<v-navigation-drawer>",
      "depois_label": "Vue corrigido — DS LIA",
      "depois_codigo": "<v-navigation-drawer width=\"240\">",
      "linguagem": "vue",
      "warning": "⚠️ 16px de diferença quebra o alinhamento de toda a área de conteúdo"
    }
  ],
  "vuetify_defaults": [
    {
      "componente": "v-navigation-drawer",
      "titulo": "v-navigation-drawer — width 256px (default) vs 240px (DS LIA)",
      "default_vuetify": "256px",
      "react_correto": "w-60 = 240px (className no Sidebar React)",
      "impacto": "16px de diferença — conteúdo desalinhado em todas as telas",
      "fix_local": "<v-navigation-drawer width=\"240\">",
      "fix_global": "VNavigationDrawer: { width: 240 }"
    }
  ],
  "vuetify_ts_code": "createVuetify({\n  defaults: {\n    VIcon: { size: '16' },\n    VBtn: { variant: 'flat', size: 'small' },\n    VCard: { elevation: 0 },\n    VNavigationDrawer: { width: 240 },\n  }\n})",
  "impacto_outros_sistemas": [
    {
      "sistema": "Layout principal (AppLayout.vue)",
      "descricao": "Mudança de width do drawer afeta o margin-left do conteúdo — revisar variável CSS --sidebar-width"
    }
  ],
  "criterios_qualidade_ia": [
    {
      "agente": "WSI Interview Graph",
      "comportamento_esperado": "Gera perguntas de entrevista alinhadas ao perfil WSI do candidato",
      "nunca_deve": "Gerar perguntas genéricas não relacionadas ao perfil WSI",
      "como_validar": "Rodar test_wsi_questions.py com perfil mock e verificar que 100% das perguntas referenciam dimensões WSI",
      "modelo": "claude-sonnet-4",
      "temperatura": "0.3",
      "metricas": "Relevância > 90%, tempo de resposta < 3s"
    }
  ],
  "arquivos_de_referencia": [...],
  "arquivos_para_modificar": [
    {
      "path": "components/ui/menu/AppSidebar.vue",
      "layer": "Vue",
      "motivo": "Corrigir width para 240px e adicionar persistência de estado"
    }
  ],
  "action_items": [
    "[ ] [Vue] Corrigir width de 256px para 240px no AppSidebar.vue",
    "[ ] [Vue] Adicionar useLocalStorage para persistir estado expandido/colapsado",
    "[ ] [Global] Atualizar vuetify.ts com VNavigationDrawer: { width: 240 }"
  ],
  "criterios_de_aceite": [
    "[Design] Menu lateral aparece com 240px exatos — não 256px",
    "[UX] Estado do menu persiste ao navegar entre páginas",
    "[Vue] Comportamento idêntico ao componente React equivalente"
  ],
  "definition_of_done": [
    "[ ] Todas as issues desta auditoria corrigidas e verificadas",
    "[ ] vuetify.ts atualizado com defaults DS LIA",
    "[ ] PR revisado por outro dev",
    "[ ] Sem regressão visual nas telas adjacentes",
    "[ ] PR linkado a este card com checklist preenchido"
  ]
}
```

### Estrutura do Card Jira Gerado (ADF)

O card é sobrescrito com esta estrutura em Atlassian Document Format:

```
H1: [Título da auditoria]
P:  Card: WT-XXXX | Gerado em: DD/MM/YYYY
P:  [Resumo em parágrafos]
P:  🐛 BetterBugs: [link clicável]
───────────────────────────────────────────────
H2: 🎯 Comportamento Esperado (Spec Driven)
P:  [Explicação sobre uso como contexto para AI coder]
[Code blocks em gherkin: DADO/QUANDO/ENTÃO por comportamento]
───────────────────────────────────────────────
H2: 🚫 Fora de Escopo
P:  [Explicação: previne escopo creep]
• [Item 1 — o que NÃO será feito]
• [Item 2...]
───────────────────────────────────────────────
H2: 📁 Arquivos de Referência
• [layer] caminho/do/arquivo — descrição
───────────────────────────────────────────────
H2: ⚙️ Issues de Funcionalidade
P:  [Instrução de uso]
  H3: F01 — [Título da issue]
  P:  Tipo: bug | Layer(s): Frontend React, Vue
  P:  [Descrição detalhada]
    H4: ⚛️ Frontend React — caminho/arquivo.tsx
    P:  React atual — INCORRETO:
    [Code block tsx]
    P:  React corrigido:
    [Code block tsx]
    H4: 🟢 Vue — components/caminho.vue
    [Code block vue ANTES/DEPOIS]
───────────────────────────────────────────────
H2: 🎨 Issues de Design
  H3: D01 — [Título]
  P:  Vue vs React — [descrição]
  P:  Vue atual — INCORRETO:
  [Code block vue]
  P:  Vue corrigido — DS LIA:
  [Code block vue]
  P:  ⚠️ [Aviso de impacto]
───────────────────────────────────────────────
H2: ⚠️ ALERTA VUETIFY DEFAULTS
P:  [Explicação sistêmica dos defaults]
  H3: [Nome do componente]
  • Vuetify default implícito: [valor]
  • React/Replit (correto): [valor]
  • Impacto visual: [descrição]
  • Fix local: [código]
  • Fix global (vuetify.ts): [código]
  H3: Como atualizar o vuetify.ts
  [Code block typescript completo]
───────────────────────────────────────────────
H2: 🗂️ Arquivos a Modificar
• [layer] caminho/arquivo — motivo
───────────────────────────────────────────────
H2: 💥 Impacto em Outros Sistemas
P:  [Instrução: validar antes do PR]
• [Sistema] — [como é afetado]
───────────────────────────────────────────────
H2: 🤖 Critérios de Qualidade IA  (apenas se há issues de IA)
P:  [Instrução: usar como contexto de prompt engineering]
  H3: 🤖 [Nome do agente]
  • Comportamento esperado: [spec]
  • NUNCA deve: [limitações]
  • Como validar: [teste concreto]
  • Modelo: claude-sonnet-4
  • Temperatura: 0.3
  • Métricas: [métricas quantitativas]
───────────────────────────────────────────────
H2: 📋 Action Items
• [ ] [Layer] Ação concreta e verificável
───────────────────────────────────────────────
H2: ✅ Critérios de Aceite
P:  [Instrução: deve ser verificável como checkbox]
• [Área] Critério objetivo
───────────────────────────────────────────────
H2: 🏁 Definition of Done
P:  [Instrução: checklist obrigatório antes do PR]
• [ ] Item de checklist
───────────────────────────────────────────────
P:  Referência: React/Replit é sempre a fonte da verdade...
```

---

## Script 2 — `jira-audit-design.py`

### O que faz

Auditoria **exclusiva de design**: foca em divergências visuais Vue vs React, Vuetify defaults
problemáticos, e spec-driven dos comportamentos visuais. Gera issues numeradas (01–15)
com código ANTES/DEPOIS concreto.

**Use quando:** o card é especificamente sobre problemas visuais/UI — botões errados,
ícones do tamanho errado, bordas incorretas, cores fora do padrão DS LIA, espaçamentos
divergentes, etc.

### Como usar

```bash
# Uso básico
python3 scripts/jira-audit-design.py WT-1637

# Dry-run
python3 scripts/jira-audit-design.py WT-1637 --dry-run

# Com arquivos específicos
python3 scripts/jira-audit-design.py WT-1637 \
  --vue-file components/ui/menu/AppSidebar.vue \
  --react-file plataforma-lia/src/components/ui/sidebar.tsx

# Múltiplos arquivos
python3 scripts/jira-audit-design.py WT-1637 \
  --vue-file components/ui/menu/AppSidebar.vue \
  --vue-file components/ui/AppHeader.vue \
  --react-file plataforma-lia/src/components/ui/sidebar.tsx
```

### Fluxo detalhado (6 passos — v3.0)

```
─── FASE 1: Replit lê e coleta ─────────────────────────────────────────────

[1/6] Replit busca credenciais Jira (via integração OAuth configurada no Repl)

[2/6] Replit busca o card WT-XXXX na API do Jira:
      → lê transcrição completa + keywords
      → extrai nós ADF existentes (screenshots, transcrição, links)
      → esses nós serão PRESERVADOS — auditoria é APPENDADA, nunca sobrescrita
      → extrai arquivos .vue mencionados no texto

[3/6] Replit lê código React diretamente no filesystem local:
      → arquivos passados via --react-file
      → busca automática por keywords em plataforma-lia/src

[4/6] Replit lê código Vue (e qualquer outro repo) via GitHub API:
      → arquivos passados via --vue-file (qualquer repo da org WeDOTalent)
      → arquivos .vue mencionados na transcrição → buscados via GitHub API
      → busca automática por keywords no GitHub (repo padrão: wedo-nuxt)

─── FASE 2: Claude analisa e publica em 2 partes ────────────────────────────

[5/6] Descrição — Issues de design com código ANTES/DEPOIS + Vuetify defaults:
      Replit detecta URL BetterBugs → acessa e extrai conteúdo público
      Claude gera issues de design numeradas (01-xx) + alerts Vuetify defaults
      Replit: existing_nodes + separator + auditoria → PUT /issue/{key}

[6/6] Comentário — Comportamento Esperado, Fora de Escopo, DoD, Critérios:
      Replit converte seções complementares para ADF
      Posta como comentário → POST /issue/{key}/comment
      Resultado: card completo sem exceder CONTENT_LIMIT_EXCEEDED do Jira
```

### Estrutura do JSON gerado pelo Claude

```json
{
  "tela": "Menu Lateral / Sidebar",
  "issues": [
    {
      "numero": "01",
      "titulo": "Ícones com 24px — deveria ser 16px (DS LIA)",
      "categoria": "icone",
      "descricao": "v-icon sem size usa o default Vuetify de 24px. DS LIA exige 16px (w-4 h-4 no React).",
      "arquivo_vue": "components/ui/menu/AppSidebar.vue",
      "arquivo_react": "plataforma-lia/src/components/ui/sidebar.tsx",
      "antes_label": "Vue atual — INCORRETO",
      "antes_codigo": "<v-icon>mdi-home</v-icon>",
      "depois_label": "Vue corrigido — DS LIA",
      "depois_codigo": "<v-icon size=\"16\">mdi-home</v-icon>",
      "linguagem": "vue",
      "regra_ds": "Ícones: sempre 16px (w-4 h-4). NUNCA usar default 24px do Vuetify.",
      "severidade": "alta"
    }
  ],
  "vuetify_defaults": [
    {
      "componente": "v-icon",
      "titulo": "v-icon — size ausente",
      "default_vuetify": "24px (Material Design)",
      "react_correto": "w-4 h-4 = 16px",
      "impacto": "Todos os ícones 8px maiores — quebra ritmo visual do DS LIA",
      "fix_local": "<v-icon size=\"16\">mdi-*</v-icon>",
      "fix_global": "VIcon: { size: '16' }"
    }
  ],
  "vuetify_ts_code": "createVuetify({\n  defaults: {\n    VIcon: { size: '16' },\n    VBtn: { variant: 'flat', size: 'small' },\n    VCard: { elevation: 0 },\n  }\n})",
  "comportamento_esperado": [
    {
      "dado": "que o designer está implementando o componente AppSidebar.vue",
      "quando": "renderiza o componente na tela",
      "entao": "o resultado visual é idêntico ao sidebar React do Replit",
      "e": "ícones com 16px, botões flat, largura 240px, border-radius 8px"
    }
  ],
  "fora_de_escopo": [
    "Lógica de navegação e rotas",
    "Integração com API de permissões",
    "Comportamento de collapse em mobile"
  ],
  "impacto_outros_sistemas": [
    {
      "sistema": "AppHeader.vue",
      "descricao": "Usa os mesmos v-icon sem size — corrigir aqui serve de exemplo para o header"
    }
  ],
  "definition_of_done": [
    "[ ] Todas as 12 issues corrigidas e verificadas visualmente",
    "[ ] vuetify.ts atualizado com VIcon size=16, VBtn variant=flat",
    "[ ] AppSidebar.vue revisado por outro dev",
    "[ ] Screenshot tirado e comparado com o React — diferença zero",
    "[ ] PR linkado a WT-1637 com checklist preenchido"
  ]
}
```

### Estrutura do Card Jira Gerado (ADF)

```
H1: Auditoria DS LIA v4.2.1 — [Nome da Tela]
P:  Card Jira: WT-XXXX
P:  Tela: [nome]
P:  Arquivos auditados: [lista]
[Intro com regra metodológica: Sem '[VER NO PROD]'...]
───────────────────────────────────────────────
H2: 🎯 Comportamento Esperado (Spec Driven)
P:  [Instrução de uso como contexto para AI coder]
[Code blocks gherkin: DADO/QUANDO/ENTÃO]
───────────────────────────────────────────────
H2: 🚫 Fora de Escopo
P:  [Instrução: previne escopo creep]
• [O que NÃO será corrigido]
───────────────────────────────────────────────
H2: Issues Identificadas
P:  [Instrução de uso]
  H3: 01 — [Título da Issue]
  P:  [Descrição + regra DS LIA violada]
  P:  Vue atual — INCORRETO:
  [Code block vue]
  P:  Vue corrigido — DS LIA:
  [Code block vue]
  H3: 02 — [...]
  ...
───────────────────────────────────────────────
H2: ⚠️ ALERTA VUETIFY DEFAULTS
P:  [Instrução sistêmica]
  H3: Defaults identificados nesta auditoria
    H4: v-icon — size ausente
    • Vuetify default implícito: 24px
    • React/Replit (correto): w-4 h-4 = 16px
    • Impacto visual: [descrição]
    • Fix local: <v-icon size="16">mdi-*</v-icon>
    • Fix global (vuetify.ts): VIcon: { size: '16' }
  H3: Como atualizar o vuetify.ts
  [Code block typescript]
───────────────────────────────────────────────
H2: 💥 Impacto em Outros Sistemas
P:  [Instrução: revisar antes do PR]
• [Sistema] — [como afeta]
───────────────────────────────────────────────
H2: 🏁 Definition of Done
P:  [Instrução: checklist obrigatório]
• [ ] Item de checklist específico desta auditoria
───────────────────────────────────────────────
P:  Referência: React/Replit é sempre a fonte da verdade de design...
```

---

## Integração BetterBugs

### Como funciona

O BetterBugs é uma ferramenta de bug reporting que grava sessões com screenshots, vídeo, console logs e network logs. Os links gerados são **públicos** e acessíveis sem autenticação.

Ambos os scripts **acessam automaticamente** o link BetterBugs encontrado na transcrição do card e passam o conteúdo para o Claude como contexto visual adicional.

### Detecção automática da URL

```python
# Padrões detectados:
https://app.betterbugs.io/...
https://betterbugs.io/...
```

O script usa regex para encontrar a URL na transcrição do card. Não é necessário que esteja em nenhum formato especial — se o texto contiver uma URL betterbugs.io, ela será detectada.

### O que é extraído

O fetcher tenta múltiplas estratégias em ordem:

| Estratégia | O que busca | Quando funciona |
|-----------|-------------|-----------------|
| `__NEXT_DATA__` (Next.js) | JSON com todos os dados da sessão | Se o BetterBugs usa Next.js SSR |
| `window.__INITIAL_STATE__` | Estado inicial da SPA | Se injetado no HTML |
| API direta (`/api/session/{id}`) | JSON estruturado com todos os dados | Se a API é pública |
| Meta tags (Open Graph) | Título, descrição, preview | Sempre disponível |
| Texto visível da página | Texto extraído do HTML renderizado | Se não é SPA pura |

### Como aparece no prompt do Claude

```
## EVIDÊNCIAS BETTERBUGS (screenshots, vídeo, console logs, network logs — contexto visual real):

[BetterBugs] Conteúdo extraído de: https://app.betterbugs.io/session/abc123

### 📋 Dados da sessão BetterBugs (Next.js)
{
  "session": {
    "title": "Sidebar menu não expande",
    "url": "https://app.wedotalent.com/dashboard",
    "browser": "Chrome 124",
    "os": "macOS 14.4",
    "consoleLogs": [...],
    "networkLogs": [...],
    "screenshots": [...]
  }
}

### 🔗 Meta informações da página
Título: BetterBugs — Sidebar menu não expande
OG Description: Gravação de sessão reportando sidebar não expandindo...
```

### Fallback quando não há conteúdo extraível

Se o BetterBugs usa uma SPA pura sem SSR, o Claude recebe:

```
[BetterBugs] Página acessível mas sem conteúdo extraível (SPA pura).
URL: https://app.betterbugs.io/session/abc123
NOTA: screenshots e vídeo disponíveis no link — analise a transcrição descrevendo o visível.
```

Nesse caso, o Claude usa a descrição textual do bug na transcrição como referência visual.

### Output no card Jira

O link BetterBugs aparece no topo do card como referência clicável:

```
🐛 BetterBugs: https://app.betterbugs.io/session/abc123
```

---

## Templates de Cards Jira — Exemplos Reais

### Template Script 1 — Card de Funcionalidade + Design

**Cenário:** Card sobre problemas no menu lateral (sidebar) da plataforma.

---

**Card Jira antes do script (transcrição original):**

```
MENU LATERAL | logo wedo menu lateral esquerdo + botao expandir menu lateral esquerdo

Problemas reportados:
- Ícone brain LIA no topo do menu lateral não aparece quando o menu está colapsado
- Botão de expandir/colapsar menu não tem ícone chevron, só muda o texto
- Menu lateral mantém 256px mesmo quando configurado para 240px
- Ícones dos itens de menu aparecem com 24px em vez de 16px
- Estado colapsado/expandido não persiste ao navegar entre páginas
- Logo WeDO aparece cortada no canto superior esquerdo quando o menu está colapsado

Link BetterBugs: https://app.betterbugs.io/session/wedo-sidebar-123abc
```

---

**Card Jira depois do Script 1 (resumo estrutural):**

```
H1: MENU LATERAL — Auditoria Completa: Sidebar LIA | Ícone Brain + Botão Expand + Estado
Card: WT-1637 | Gerado em: 23/03/2026

[Resumo: 3 parágrafos descrevendo o contexto, problemas encontrados e o que precisa ser feito]
🐛 BetterBugs: https://app.betterbugs.io/session/wedo-sidebar-123abc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Comportamento Esperado (Spec Driven)

[Code block gherkin]
DADO que o recrutador está em qualquer tela da plataforma
QUANDO o menu lateral está colapsado
ENTÃO o ícone brain LIA aparece com 16px centralizado na coluna de 64px
E o logo WeDO aparece completo (não cortado)

[Code block gherkin]
DADO que o recrutador clica no botão de toggle do menu
QUANDO o menu estava colapsado (64px)
ENTÃO o menu expande suavemente para 240px (não 256px)
E o estado persiste ao navegar para outras páginas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 Fora de Escopo

• Comportamento do menu em dispositivos mobile (< 768px)
• Refatoração da lógica de permissões de menu por role
• Mudanças na paleta de cores do menu (já está correta)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 Arquivos de Referência

• [Frontend React] plataforma-lia/src/components/ui/sidebar.tsx — Sidebar React (fonte da verdade)
• [Vue] components/ui/menu/AppSidebar.vue — Sidebar Vue (a ser corrigido)
• [Vue] components/ui/menu/SidebarItem.vue — Itens do menu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ Issues de Funcionalidade

  F01 — Ícone brain LIA some no estado colapsado
  Tipo: bug | Layers: Frontend React, Vue
  [Descrição: o ícone usa v-if="!isCollapsed" em vez de mostrar versão reduzida]

  ⚛️ Frontend React — plataforma-lia/src/components/ui/sidebar.tsx
  React atual — INCORRETO:
  [Code block] {isCollapsed ? null : <BrainIcon />}
  React corrigido:
  [Code block] <BrainIcon className={isCollapsed ? 'w-4 h-4' : 'w-6 h-6'} />

  🟢 Vue — components/ui/menu/AppSidebar.vue
  Vue atual — INCORRETO:
  [Code block] <v-icon v-if="!isCollapsed">mdi-brain</v-icon>
  Vue corrigido:
  [Code block] <v-icon :size="isCollapsed ? '16' : '24'">mdi-brain</v-icon>

  F02 — Estado colapsado não persiste entre navegações
  Tipo: bug | Layers: Frontend React, Vue
  [...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 Issues de Design

  D01 — Sidebar com 256px — DS LIA exige 240px
  [ANTES Vue] <v-navigation-drawer>
  [DEPOIS Vue] <v-navigation-drawer width="240">
  ⚠️ 16px de diferença quebra alinhamento de todo o conteúdo

  D02 — Ícones de menu com 24px (default Vuetify) — DS LIA exige 16px
  [ANTES] <v-icon>mdi-home</v-icon>
  [DEPOIS] <v-icon size="16">mdi-home</v-icon>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ ALERTA VUETIFY DEFAULTS

  v-navigation-drawer — width 256px vs 240px DS LIA
  • Vuetify default implícito: 256px
  • React/Replit (correto): w-60 = 240px
  • Fix local: <v-navigation-drawer width="240">
  • Fix global (vuetify.ts): VNavigationDrawer: { width: 240 }

  v-icon — size 24px vs 16px DS LIA
  • Vuetify default implícito: 24px
  • React/Replit (correto): w-4 h-4 = 16px
  • Fix local: <v-icon size="16">mdi-*</v-icon>
  • Fix global (vuetify.ts): VIcon: { size: '16' }

  Como atualizar o vuetify.ts:
  [Code block typescript]
  createVuetify({
    defaults: {
      VIcon: { size: '16' },
      VBtn: { variant: 'flat', size: 'small' },
      VCard: { elevation: 0 },
      VNavigationDrawer: { width: 240, permanent: true },
    }
  })

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗂️ Arquivos a Modificar

• [Vue] components/ui/menu/AppSidebar.vue — Corrigir width, ícones, persistência
• [Vue] components/ui/menu/SidebarItem.vue — Corrigir size dos v-icon
• [Global] plugins/vuetify.ts — Adicionar defaults VNavigationDrawer, VIcon

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💥 Impacto em Outros Sistemas

• AppLayout.vue — margin-left do conteúdo calculado com base no width do drawer
• AppHeader.vue — usa mesmos v-icon sem size — aproveitar para corrigir também

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Action Items

• [ ] [Vue] Corrigir v-navigation-drawer width para 240px em AppSidebar.vue
• [ ] [Vue] Adicionar size="16" em todos os v-icon do SidebarItem.vue
• [ ] [Vue] Implementar persistência de estado com useLocalStorage
• [ ] [Vue] Corrigir visibilidade do ícone brain no estado colapsado
• [ ] [Global] Atualizar vuetify.ts com defaults VNavigationDrawer e VIcon

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Critérios de Aceite

• [Design] Sidebar aparece com 240px exatos — confirmado com DevTools
• [Design] Ícones de menu com 16px — não 24px
• [UX] Ícone brain LIA visível tanto expandido quanto colapsado
• [UX] Estado do menu persiste ao navegar entre Dashboard, Pipeline, Candidatos
• [Vue] Resultado visual idêntico ao React/Replit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 Definition of Done

• [ ] Todas as issues F01, F02, D01, D02 corrigidas
• [ ] vuetify.ts atualizado com os 4 defaults listados
• [ ] Screenshot tirado e comparado com React — zero divergência
• [ ] PR aprovado por 1 reviewer
• [ ] Sem regressão em AppLayout.vue e AppHeader.vue
• [ ] PR linkado a WT-1637 com checklist preenchido
```

---

### Template Script 2 — Card de Design Exclusivo

**Cenário:** Card específico de auditoria de design do WSI Report.

---

**Card Jira antes do script (transcrição original):**

```
WSI REPORT | Problemas visuais na tela de relatório WSI

- Botões de ação com variant="elevated" (sombra indevida) — deveria ser flat
- Cards do relatório com elevation=2 — DS LIA exige elevation=0
- Tipografia usando Roboto em vez de Open Sans (85% do corpo)
- Border-radius dos cards com 4px — DS LIA exige 8px
- Badges de score com cor cyan em elementos que não são LIA
- Tabela de resultados com border-radius 12px nos inputs — DS LIA exige rounded-xl (12px) ✓ mas nos cards errado

Link BetterBugs: https://app.betterbugs.io/session/wsi-report-456def
```

---

**Card Jira depois do Script 2 (resumo estrutural):**

```
H1: Auditoria DS LIA v4.2.1 — WSI Report
Card Jira: WT-1842
Tela: WSI Report
Arquivos auditados: components/wsi/WsiReport.vue, components/wsi/WsiScoreCard.vue

[Intro com regra metodológica]
🐛 BetterBugs: https://app.betterbugs.io/session/wsi-report-456def

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Comportamento Esperado (Spec Driven)

[Code block gherkin]
DADO que o recrutador está visualizando o relatório WSI de um candidato
QUANDO a tela é renderizada
ENTÃO os cards do relatório aparecem sem sombra (elevation=0, border border-gray-200)
E os botões de ação aparecem sem sombra (variant="flat")
E o texto do relatório usa Open Sans 85% do conteúdo
E todos os border-radius são 8px (rounded-md)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 Fora de Escopo

• Lógica de cálculo dos scores WSI
• Integração com API de relatórios
• Comportamento da tela em mobile
• Exportação de PDF do relatório

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issues Identificadas
[Sem '[VER NO PROD]'. Sem 'verificar'. Cada Issue com Antes/Depois concreto.]

  H3: 01 — Botões de ação com variant="elevated" — DS LIA exige flat
  [Regra violada: VBtn deve usar variant="flat" conforme DS LIA]
  Vue atual — INCORRETO:
  [Code block] <v-btn variant="elevated" color="primary">Exportar</v-btn>
  Vue corrigido — DS LIA:
  [Code block] <v-btn variant="flat" color="primary">Exportar</v-btn>

  H3: 02 — Cards com elevation=2 — DS LIA exige elevation=0
  Vue atual — INCORRETO:
  [Code block] <v-card elevation="2">
  Vue corrigido — DS LIA:
  [Code block] <v-card :elevation="0" class="border border-gray-200">

  H3: 03 — Tipografia usando Roboto — DS LIA exige Open Sans 85%
  Vue atual — INCORRETO:
  [Code block] <p style="font-family: Roboto">Score WSI: 78</p>
  Vue corrigido — DS LIA:
  [Code block] <p class="font-sans">Score WSI: 78</p>

  H3: 04 — Border-radius 4px nos cards — DS LIA exige 8px (rounded-md)
  [...]

  H3: 05 — Badges cyan em elementos não-LIA — viola regra 90/10
  [...]

  [... até issue 12]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ ALERTA VUETIFY DEFAULTS

  H3: Defaults identificados nesta auditoria
    H4: v-btn — variant="elevated" (default) vs flat (DS LIA)
    • Vuetify default: elevated (com sombra)
    • React/Replit: bg-gray-900 text-white sem sombra
    • Fix global: VBtn: { variant: 'flat' }

    H4: v-card — elevation=1 (default) vs elevation=0 (DS LIA)
    • Vuetify default: elevation=1
    • React/Replit: shadow-none + border border-gray-200
    • Fix global: VCard: { elevation: 0 }

  H3: Como atualizar o vuetify.ts
  [Code block typescript]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💥 Impacto em Outros Sistemas

• WsiCompetencyDetail.vue — usa os mesmos v-card e v-btn
• CandidateReportView.vue — herda estilos do WsiReport

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 Definition of Done

• [ ] Todas as 12 issues desta auditoria corrigidas e verificadas visualmente
• [ ] vuetify.ts atualizado com VBtn variant=flat, VCard elevation=0
• [ ] WsiReport.vue revisado por outro dev ou designer
• [ ] Screenshot tirado e comparado com o React — diferença zero
• [ ] Sem regressão visual em WsiCompetencyDetail.vue e CandidateReportView.vue
• [ ] PR linkado a WT-1842 com checklist preenchido
```

---

## Referência DS LIA v4.2.1

### Regras críticas (fonte da verdade: React/Replit)

| Elemento | React (correto) | Vuetify default (incorreto) | Fix Vuetify |
|----------|----------------|---------------------------|-------------|
| Ícones | `w-4 h-4` = 16px | 24px | `VIcon: { size: '16' }` |
| Botões primários | `bg-gray-900` sem sombra | `variant="elevated"` | `VBtn: { variant: 'flat' }` |
| Cards | `shadow-none border border-gray-200` | `elevation: 1` | `VCard: { elevation: 0 }` |
| Sidebar largura | `w-60` = 240px | 256px | `VNavigationDrawer: { width: 240 }` |
| Border-radius | `rounded-md` = 8px | 4px | adicionar `rounded-md` nas classes |
| Inputs border-radius | `rounded-xl` = 12px | 4px | `VTextField: { class: 'rounded-xl' }` |
| Sidebar comportamento | `permanent` | `temporary` | `VNavigationDrawer: { permanent: true }` |
| Cyan (#60BED1) | Apenas ícone brain LIA, badges LIA | — | regra de uso, não default |
| Tipografia corpo | Open Sans 85% | Roboto (Material) | CSS global font-family |

### vuetify.ts completo (baseline DS LIA)

```typescript
import { createVuetify } from 'vuetify'

export default createVuetify({
  defaults: {
    VIcon: { size: '16' },
    VBtn: { variant: 'flat', size: 'small' },
    VCard: { elevation: 0 },
    VNavigationDrawer: { width: 240, permanent: true },
    VTextField: { variant: 'outlined', density: 'compact' },
    VSelect: { variant: 'outlined', density: 'compact' },
    VChip: { size: 'small' },
    VDivider: { color: 'gray-200' },
  }
})
```

---

## FAQ e Troubleshooting

### "Arquivo Vue não encontrado no GitHub"
Verifique se o path é relativo à raiz do repo `wedo-nuxt`. Use `--vue-file` com o caminho correto:
```bash
# Errado
--vue-file /components/ui/sidebar.vue

# Correto
--vue-file components/ui/menu/AppSidebar.vue
```

### "BetterBugs: SPA pura sem conteúdo extraível"
Normal para SPAs sem SSR. O Claude ainda recebe a transcrição completa do card. Para maximizar o contexto, inclua na transcrição uma descrição detalhada do que está visível nos screenshots.

### "0 issues de funcionalidade geradas"
O card pode ser puramente de design. Use o Script 2 (`jira-audit-design.py`) que é especializado nisso.

### "Análise muito genérica"
Passe os arquivos específicos via `--react-file` e `--vue-file`. A auto-detecção por keywords pode não encontrar o arquivo certo se os nomes não coincidem com o vocabulário do card.

### "Erro de autenticação Jira"
As integrações Replit (Jira e Anthropic) precisam estar ativas. Rode o script dentro do ambiente Replit, não localmente.

### Como escolher entre Script 1 e Script 2?

| Situação | Script |
|---------|--------|
| Card tem bugs funcionais (coisas não funcionam) | Script 1 |
| Card tem problemas de design + funcionalidade | Script 1 |
| Card tem agentes IA com comportamento incorreto | Script 1 |
| Card é SOMENTE sobre aparência visual (Vue vs React) | Script 2 |
| Quer auditoria visual mais profunda e detalhada | Script 2 |
| Já rodou Script 1 e quer complementar o design | Script 2 |

---

## Versionamento

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | Inicial | Script 1 básico com issues funcionalidade + design |
| 1.5 | — | Script 2 criado (design-only) |
| 2.0 | 23/03/2026 | BetterBugs content fetching; seções spec-driven: Comportamento Esperado, Fora de Escopo, Impacto em Outros Sistemas, Critérios de Qualidade IA, Definition of Done |
