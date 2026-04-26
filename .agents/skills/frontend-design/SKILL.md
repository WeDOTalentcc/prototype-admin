---
name: frontend-design
description: "Create distinctive, production-grade frontend interfaces with high design quality. Use when building web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics. Adapted from Anthropic's frontend-design skill with LIA DS v4.2.1 integration."
---

# Frontend Design — Interfaces Distintivas e Production-Grade

Esta skill guia a criacao de interfaces frontend distintivas e production-grade que evitam a estetica generica de "AI slop". Implementa codigo real funcional com atencao excepcional a detalhes esteticos e escolhas criativas.

> **Origem:** Adaptada de [anthropics/claude-code frontend-design](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md)
> **Integracao LIA:** Funciona em conjunto com `design-standardize` (DS v4.2.1) — esta skill define a intencao estetica, `design-standardize` garante conformidade com tokens e regras do DS.

## Quando ativar

- Quando o usuario disser "quero algo bonito", "quero algo diferente", "marcante", "profissional", "wow" ou "que se destaque"
- Ao criar tela de entrada ou branding (login, onboarding, landing, hero, pitch deck visual)
- Ao prototipar variantes visuais no canvas (mockup-sandbox) antes de comprometer-se com uma direcao
- Ao decidir tom estetico ANTES de implementar (atua como PASSO 0 do `design-standardize`)
- Quando a interface precisa se destacar (demo para cliente, showcase, apresentacao publica)
- Ao escolher direcao tipografica, cromatica ou de motion para componente especial (animacao, transicao, easter egg)
- Ao criar componente de marketing dentro do app (banner promocional, tour interativo)

## Quando NAO ativar

- Interface interna repetitiva (Kanban, tabela, settings, formulario CRUD) -> `design-standardize` e principal
- Componente que tem regra rigida do DS v4.2.1 (botao primario, card padrao) -> `design-standardize` aplica direto
- Refactor de tela existente sem nova intencao estetica -> `design-standardize`
- Padronizacao visual em projeto Vue/Vuetify -> `vue-vuetify-standardize` (esta skill so complementa intencao)
- Quando o usuario pediu padronizacao ("aplica DS"), nao criacao distintiva


## Integracao com Ecossistema LIA

| Skill | Relacao |
|-------|---------|
| **design-standardize** | Esta skill fornece o "PASSO 0 — Intencao Estetica" expandido; `design-standardize` aplica tokens e regras |
| **feature-audit** | Dimensao 3 (UI/UX) pode usar criterios desta skill para avaliar qualidade estetica |
| **feature-impact** | Dimensao 1 (Frontend) pode referenciar esta skill para decisoes de design |
| **vue-migration-prep** | Decisoes esteticas devem ser portaveis — evitar tecnicas React-only |
| **design-patterns** | Patterns de composicao (Compound Components, Render Props) para componentes visuais complexos |

---

## Design Thinking

Antes de codificar, entender o contexto e comprometer-se com uma direcao estetica CLARA:

### 1. Proposito
Que problema esta interface resolve? Quem a usa?

### 2. Tom Estetico
Escolher uma direcao. Exemplos de espectro:

| Direcao | Caracteristicas | Quando usar |
|---------|----------------|-------------|
| Brutalmente minimal | Espaco negativo generoso, tipografia como elemento principal, cores quase ausentes | Dashboards executivos, ferramentas de foco |
| Refinado/luxo | Tipografia elegante, animacoes suaves, gradientes sutis, sombras precisas | Apresentacoes a clientes, landing pages |
| Editorial/magazine | Layout assimetrico, tipografia ousada, hierarquia visual forte | Portfolios, showcases de dados |
| Industrial/utilitario | Densidade funcional, bordas definidas, informacao compacta | Ferramentas internas de alta performance |
| Organico/natural | Cantos arredondados, cores suaves, transicoes fluidas | Onboarding, experiencias de candidato |
| Soft/pastel | Tons suaves, sombras difusas, sensacao acolhedora | Interfaces de comunicacao, chat |

### 3. Restricoes
Requisitos tecnicos (framework, performance, acessibilidade, DS v4.2.1).

### 4. Diferenciacao
O que torna esta interface INESQUECIVEL? Qual e a coisa que alguem vai lembrar?

**CRITICAL**: Escolha uma direcao conceitual clara e execute-a com precisao. Maximalismo ousado e minimalismo refinado funcionam — a chave e intencionalidade, nao intensidade.

---

## Regra de Complexidade de Implementacao

**IMPORTANTE: A complexidade do codigo deve corresponder a visao estetica.**

| Visao | Implementacao |
|-------|--------------|
| **Maximalista** | Codigo elaborado: animacoes extensas, efeitos em camadas, gradientes complexos, hover states ricos, staggered reveals |
| **Minimalista/refinado** | Codigo contido: precisao em spacing, tipografia impecavel, detalhes sutis, menos e mais. Elegancia vem da execucao, nao da quantidade |
| **Industrial/utilitario** | Codigo denso e funcional: tabelas compactas, inline data, zero decoracao desnecessaria |

Nao colocar codigo maximalista numa interface minimal. Nao simplificar demais uma interface que pede impacto. O codigo serve a visao, nao o contrario.

---

## Frontend Aesthetics Guidelines

### Tipografia

**Regra:** Fontes devem ter carater e intencao. Nunca defaultar.

**Fontes BANIDAS** (overused por IA, evitar em contextos de branding):
- ~~Inter~~ (exceto em dados/tabelas no contexto LIA, onde e obrigatorio)
- ~~Roboto~~
- ~~Arial~~
- ~~Space Grotesk~~ (overused por AI tools)
- ~~System UI generico~~

**Pares que funcionam** (para telas de branding/entrada):

```
Display + Body:
- Playfair Display + Source Sans 3
- DM Serif Display + DM Sans
- Libre Baskerville + Open Sans
- Sora + Inter (quando Inter e body, nao display)
- Source Serif 4 + Open Sans (padrao LIA branding)
```

**No contexto LIA interfaces internas:**
Open Sans (UI geral, 85%) + Inter (dados/tabelas, 10%) + JetBrains Mono (codigo, 5%) sao OBRIGATORIOS.

### Cor & Tema

- Comprometer-se com uma paleta coesa usando CSS variables
- Cores dominantes com acentos afiados superam paletas timidas e uniformemente distribuidas
- **Variar entre dark/light themes** em diferentes geracoes — nao defaultar sempre para light
- **No contexto LIA:** 90% monocromatico (gray-50 a gray-900) + 10% acento WeDo (#60BED1 cyan). Telas de branding tem mais liberdade

**Paleta WeDo completa:**

```css
--wedo-cyan: #60BED1;        /* Acento principal */
--wedo-cyan-light: #8DD4E2;  /* Hover, highlights */
--wedo-cyan-dark: #3A9BB0;   /* Active, pressed */
--surface-primary: #FAFBFC;  /* Background principal (light) */
--surface-elevated: #FFFFFF;  /* Cards, modais */
--text-primary: #111827;     /* gray-900 */
--text-secondary: #6B7280;   /* gray-500 */
--border-default: #E5E7EB;   /* gray-200 */
```

### Motion & Animacao

- Usar animacoes para efeitos e micro-interacoes com proposito
- Priorizar solucoes CSS-only para HTML basico; Framer Motion para React
- Focar em momentos de alto impacto: uma carga de pagina bem orquestrada com reveals escalonados (animation-delay) cria mais encantamento do que micro-interacoes dispersas
- Usar scroll-triggering e hover states que surpreendem
- **No contexto LIA:** Respeitar tokens de motion do DS (micro 100ms, fast 150ms, normal 200ms, slow 300ms, emphasis 500ms). Proibido: bounce, elastic, rotacao continua

**Exemplos de motion com proposito:**

```tsx
// Staggered entrance — alto impacto, baixo esforco
<div className="space-y-4">
  {items.map((item, i) => (
    <motion.div
      key={item.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: i * 0.05, duration: 0.3 }}
    >
      {item.content}
    </motion.div>
  ))}
</div>

// Hover state que surpreende — escala + sombra
<motion.div
  whileHover={{ scale: 1.02, boxShadow: "0 8px 30px rgba(0,0,0,0.08)" }}
  transition={{ duration: 0.2 }}
  className="cursor-pointer rounded-md border p-4"
>
  {children}
</motion.div>

// Page load reveal — fade + slide coordenados
<motion.section
  initial={{ opacity: 0, y: 40 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
>
  <h1 className="text-4xl font-light tracking-tight">
    {title}
  </h1>
</motion.section>
```

### Composicao Espacial

- Layouts inesperados, assimetria, sobreposicao, fluxo diagonal
- Elementos que quebram o grid; espaco negativo generoso OU densidade controlada
- **No contexto LIA:** Interfaces internas usam grid 12 colunas com gap-6. Telas de branding podem quebrar o grid

**Exemplos de composicao com codigo:**

```tsx
// Layout assimetrico — dois paineis com proporcoes desiguais
<div className="grid grid-cols-12 min-h-screen">
  <div className="col-span-5 bg-gray-950 flex items-center justify-center p-12">
    {/* Painel esquerdo: branding, ilustracao */}
  </div>
  <div className="col-span-7 flex items-center justify-center p-16">
    {/* Painel direito: conteudo principal */}
  </div>
</div>

// Card com overlap — elemento que "quebra" o container
<div className="relative pt-8">
  <div className="absolute -top-4 left-6 z-10">
    <Badge className="bg-wedo-cyan text-white shadow-lg">Destaque</Badge>
  </div>
  <Card className="border-0 shadow-md">
    {/* conteudo */}
  </Card>
</div>

// Espaco negativo generoso — respiracao visual
<section className="py-24 px-8 max-w-2xl mx-auto">
  <h2 className="text-3xl font-light mb-16 tracking-tight">
    Menos e mais
  </h2>
  <div className="space-y-12">
    {/* Conteudo esparso, intencional */}
  </div>
</section>
```

### Backgrounds & Detalhes Visuais

- Criar atmosfera e profundidade em vez de defaultar para cores solidas
- Gradient meshes, texturas de ruido, padroes geometricos, transparencias em camadas, grain overlays
- **No contexto LIA:** Backgrounds animados e glassmorphism APENAS em telas de entrada (ver Padroes Atmosfericos em `design-standardize`)

**Exemplos de backgrounds com codigo:**

```tsx
// Gradient mesh sutil — profundidade sem ser obvio
<div className="relative overflow-hidden bg-gray-50">
  <div className="absolute inset-0 opacity-30">
    <div className="absolute top-0 -left-4 w-72 h-72 bg-cyan-100 rounded-full mix-blend-multiply filter blur-xl" />
    <div className="absolute top-0 -right-4 w-72 h-72 bg-gray-200 rounded-full mix-blend-multiply filter blur-xl" />
    <div className="absolute -bottom-8 left-20 w-72 h-72 bg-cyan-50 rounded-full mix-blend-multiply filter blur-xl" />
  </div>
  <div className="relative z-10">{children}</div>
</div>

// Grain overlay — textura que adiciona sofisticacao
<div className="relative">
  {children}
  <div
    className="absolute inset-0 pointer-events-none opacity-[0.03]"
    style={{
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
    }}
  />
</div>
```

---

## Anti-Patterns: "AI Slop" a Evitar

NUNCA usar esteticas genericas de IA:

| Anti-Pattern | Problema | Alternativa |
|-------------|----------|-------------|
| Inter/Roboto/Arial em tudo | Generico, sem personalidade | Fontes com carater adequado ao contexto |
| Gradiente roxo em fundo branco | Cliche absoluto de IA | Paletas com personalidade e intencao |
| Layouts previsiveis (card grid simetrico) | Sem impacto visual | Assimetria, hierarquia, elementos que quebram expectativa |
| Mesmo design em todo output | Falta de criatividade | Cada interface deve ter identidade propria |
| Sombras excessivas em tudo | Visual "inflado" | Sombras intencionais, apenas onde agregam |
| Cantos ultra-arredondados em tudo | "Blobby", infantil | Raios adequados ao contexto |
| Gradientes como decoracao | Sem funcao semantica | Gradientes com proposito (profundidade, direcao, hierarquia) |
| "Purple gradient hero" | Template IA generico | Composicao espacial intencional com a paleta do contexto |
| `font-bold` em tudo | Hierarquia achatada | `font-light` para titulos grandes, `font-medium` para enfase, `font-semibold` seletivo |
| `rounded-full` em tudo | Aparencia inflada | `rounded-md` (8px padrao DS), `rounded-lg` seletivo |

---

## Componentes shadcn/Radix Disponiveis

Inventario dos componentes UI ja instalados no projeto (usar estes, NAO criar do zero):

**Mais usados (Top 10):**

| Componente | Import | Uso Principal |
|-----------|--------|--------------|
| `Button` | `@/components/ui/button` | Acoes primarias/secundarias/ghost/outline |
| `Badge` | `@/components/ui/badge` | Status, tags, contadores |
| `Card` | `@/components/ui/card` | Containers com borda e padding |
| `Dialog` | `@/components/ui/dialog` | Modais e confirmacoes |
| `Select` | `@/components/ui/select` | Dropdowns de selecao |
| `Input` | `@/components/ui/input` | Campos de texto |
| `Textarea` | `@/components/ui/textarea` | Campos de texto multi-linha |
| `Label` | `@/components/ui/label` | Labels de formulario |
| `Popover` | `@/components/ui/popover` | Menus e tooltips ricos |
| `DropdownMenu` | `@/components/ui/dropdown-menu` | Menus de contexto |

**Especializados LIA:**

| Componente | Funcao |
|-----------|--------|
| `StatusBadge` | Badge com cores semanticas por status de vaga/candidato |
| `EmptyState` | Estado vazio padronizado com icone, titulo, descricao e acao |
| `LiaIcon` | Icone animado da LIA (cerebro cyan) |
| `PromptSuggestionsDock` | Sugestoes de prompt no chat |
| `PipelineStagesCarousel` | Carousel de etapas do funil |
| `AudioPlayer` / `AudioRecordButton` | Reproducao e gravacao de audio |
| `Skeleton` | Loading placeholders |
| `Toast` / `Toaster` | Notificacoes temporarias |

**Regra:** Sempre verificar se ja existe um componente antes de criar. Rodar `ls plataforma-lia/src/components/ui/` para ver a lista completa.

---

## Responsividade

### Breakpoints (Tailwind padrao)

| Prefixo | Largura | Dispositivo |
|---------|---------|-------------|
| (nenhum) | < 640px | Mobile |
| `sm:` | >= 640px | Mobile landscape |
| `md:` | >= 768px | Tablet |
| `lg:` | >= 1024px | Desktop |
| `xl:` | >= 1280px | Desktop grande |

### Regras de Responsividade LIA

1. **Mobile-first**: Escrever estilos base para mobile, usar prefixos para expandir
2. **Sidebar colapsa em mobile**: Menu lateral vira drawer/sheet em `< lg`
3. **Tabelas viram cards**: Em `< md`, tabelas de dados viram lista de cards empilhados
4. **Chat ocupa tela cheia**: Em `< lg`, o chat da LIA ocupa 100% do viewport
5. **Paineis laterais**: Em `< xl`, paineis de preview colapsam ou viram modais
6. **Tipografia escala**: Titulos reduzem em mobile (`text-2xl md:text-3xl lg:text-4xl`)

**Exemplo de grid responsivo:**

```tsx
// Grid que adapta de 1 a 3 colunas
<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
  {items.map(item => (
    <Card key={item.id} className="p-4 md:p-6">
      {item.content}
    </Card>
  ))}
</div>

// Sidebar + conteudo responsivo
<div className="flex flex-col lg:flex-row min-h-screen">
  <aside className="w-full lg:w-64 xl:w-72 border-b lg:border-b-0 lg:border-r">
    {navigation}
  </aside>
  <main className="flex-1 p-4 md:p-6 lg:p-8">
    {content}
  </main>
</div>
```

---

## Checklist de Qualidade Estetica

Antes de entregar qualquer interface, verificar:

- [ ] **Tem ponto de vista estetico claro?** — Nao e generico, tem intencao
- [ ] **A tipografia e intencional?** — Fontes escolhidas por razao, nao por default
- [ ] **A paleta e coesa?** — Cores trabalham juntas, nao sao aleatorias
- [ ] **Ha hierarquia visual?** — O olho sabe para onde ir primeiro, segundo, terceiro
- [ ] **Os espacamentos sao deliberados?** — Nao e "padding 16px em tudo"
- [ ] **As animacoes agregam?** — Motion com proposito, nao decoracao gratuita
- [ ] **E memoravel?** — Alguem lembraria desta interface amanha?
- [ ] **E funcional?** — Beleza nao sacrifica usabilidade
- [ ] **E acessivel?** — WCAG 2.1 AA (contraste 4.5:1, focus visible, aria-labels)
- [ ] **E portavel?** — Decisoes esteticas sobrevivem a migracao Vue (evitar tecnicas React-only)
- [ ] **E responsiva?** — Funciona em mobile (< 640px), tablet (768px) e desktop (1280px+)
- [ ] **Complexidade corresponde a visao?** — Codigo maximalista para visao maximalista, contido para minimal

---

## Contexto LIA: Dois Modos de Design

### Modo 1: Telas de Entrada / Branding
Login, onboarding, landing, welcome, 404, maintenance.

**Liberdade:** Alta. Composicao atmosferica, tipografia de impacto, backgrounds em camadas, glassmorphism.
**Referencia:** CloudsBackground, layout dois paineis, headline `text-5xl font-light`.
**Fontes extras permitidas:** Source Serif 4 (branding "LIA"), fontes display.
**Animacoes:** Framer Motion, SVG animados, parallax sutil.
**DS override:** `rounded-2xl`, `shadow-2xl`, gradientes em background — PERMITIDOS aqui.

**Exemplo de tela de entrada:**

```tsx
<div className="grid grid-cols-1 lg:grid-cols-12 min-h-screen">
  {/* Painel esquerdo — branding */}
  <div className="hidden lg:flex lg:col-span-5 bg-gray-950 items-center justify-center relative overflow-hidden">
    <div className="absolute inset-0 opacity-20">
      <CloudsBackground />
    </div>
    <div className="relative z-10 text-center px-12">
      <LiaIcon className="w-16 h-16 mx-auto mb-8" />
      <h1 className="text-5xl font-light text-white tracking-tight mb-4">
        LIA
      </h1>
      <p className="text-lg text-gray-400 font-light">
        Inteligencia que transforma recrutamento
      </p>
    </div>
  </div>
  {/* Painel direito — formulario */}
  <div className="col-span-1 lg:col-span-7 flex items-center justify-center p-8 lg:p-16">
    <div className="w-full max-w-md space-y-8">
      {/* Formulario aqui */}
    </div>
  </div>
</div>
```

### Modo 2: Interface Interna da Plataforma
Kanban, tabelas, modais, settings, chat, candidatos.

**Liberdade:** Restrita. Previsibilidade e feature.
**Foco:** Clareza, densidade funcional, consistencia.
**Tokens obrigatorios:** DS v4.2.1 (ver `design-standardize`).
**Onde esta skill agrega:** Micro-interacoes cuidadosas, transicoes fluidas, hierarquia tipografica, composicao de empty states, qualidade dos icones, atencao a detalhes de espacamento.

**Padroes visuais da interface interna:**

```tsx
// Header de pagina padrao
<div className="flex items-center justify-between px-4 py-3 border-b">
  <div className="flex items-center gap-3">
    <IconComponent className="w-5 h-5 text-gray-500" />
    <h1 className="text-lg font-semibold text-gray-900">Titulo da Pagina</h1>
  </div>
  <Button size="sm">
    <Plus className="w-4 h-4 mr-2" />
    Nova Acao
  </Button>
</div>

// Tabs de navegacao padrao
<nav className="flex items-center space-x-6 border-b px-4">
  {tabs.map(tab => (
    <button
      key={tab.id}
      className={cn(
        "py-2 border-b-2 text-sm transition-colors",
        active === tab.id
          ? "border-gray-900 text-gray-950 font-semibold"
          : "border-transparent text-gray-600 hover:text-gray-900"
      )}
    >
      {tab.label}
      {tab.count !== undefined && (
        <Badge variant="secondary" className="ml-2 text-xs">
          {tab.count}
        </Badge>
      )}
    </button>
  ))}
</nav>

// Empty state com personalidade
<EmptyState
  icon={<Briefcase className="w-12 h-12 text-gray-300" />}
  title="Nenhuma vaga cadastrada"
  description="Crie sua primeira vaga para comecar a atrair candidatos."
  action={{
    label: "Criar primeira vaga",
    onClick: () => handleCreate()
  }}
  className="py-24"
/>
```

---

## Uso em Outros Ambientes

| Ambiente | Como Usar |
|----------|-----------|
| **Claude Code / Replit Agent** | Ativa automaticamente ao criar interfaces web |
| **Cursor IDE** | Mencione `@.agents/skills/frontend-design/SKILL.md` |
| **Com design-standardize** | Esta skill define intencao -> `design-standardize` aplica tokens |
| **Com feature-audit** | Dimensao 3 usa checklist estetico desta skill |
