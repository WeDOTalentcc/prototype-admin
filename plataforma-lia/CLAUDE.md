> ## ⚠️ CANONICAL DE PRODUÇÃO
>
> **Replit `plataforma-lia/` é canonical de produção** (decisão Paulo 2026-05-23). NÃO é legacy.
>
> - Edits aqui = produção viva
> - Fonte de verdade para todo o frontend Next.js — Estúdio de Agentes, triagem candidato chat público, AgentCard (4 canais: WhatsApp + Voice + VoIP), Wizard goal-first, marketplace, dashboards
> - Consome `lia-agent-system` (FastAPI) + `ats_api` (Rails) via proxy Next em `src/app/api/backend-proxy/*`
>
> Ver `/workspace/CLAUDE.md` para racional completo.

---

# CLAUDE.md — Plataforma LIA · Design System Decisions

> Última atualização: 2026-03-29
> Sprints de padronização executados: 1–10

## Stack
- React 19 + Next.js 15 (App Router)
- Tailwind CSS v3 + shadcn/ui
- next/font (Inter, Open Sans, Crimson Text)

## Tokens WeDo DS

### Tipografia
- Font principal: Inter (via `--font-inter`) — body, UI
- Font secundária: Open Sans (via `--font-open-sans`) — headings, navegação
- Font editorial: Crimson Text (via `--font-crimson`) — destaques editoriais
- NUNCA usar `@import` Google Fonts — apenas `next/font`

### Cores
- Primária: `wedo-coral` (#E87575) — CTAs, destaques
- LIA/IA: `wedo-cyan` (#60BED1) — exclusivo para elementos de IA
- Status semânticos: `status-success` (#16A34A), `status-error` (#DC2626), `status-warning` (#D97706)
- `wedo-apoio-*` tokens: deprecated, zero uso, remoção pendente Sprint final
- Dark mode: `dark:bg-gray-800/900`, `dark:text-gray-100/300/400`, `dark:border-gray-700`

### Bordas
- Cards e modais: `rounded-xl` (12px)
- Inputs e badges: `rounded-lg` (8px)
- Elementos circulares: `rounded-full`
- Tokens semânticos: `border-lia-border-subtle` (gray-200/700), `border-lia-border-default` (gray-300/600)

### Sombras
- `shadow-lia-sm`, `shadow-lia-default`, `shadow-lia-md`, `shadow-lia-lg` — definidos em tailwind.config.ts
- `shadow-lia-focus` — focus ring 2px (0 0 0 2px rgba(0,0,0,0.1))
- `shadow-lia-focus-primary` — focus ring coral

### Espaçamento
- Escala Tailwind padrão (múltiplos de 4px)
- Valores arbitrários [Npx] sem canônico: documentados com `// [OPT-022] px arbitrário`
- Layout tokens: `w-panel-sm/md/lg/xl`, `h-chart-sm`, `h-content-md/lg`, `h-card-lg`

### Z-Index Semântico
- `z-base` (0), `z-raised` (10), `z-dropdown` (40), `z-sticky` (50)
- `z-overlay` (60), `z-toast` (100), `z-select` (200)
- `z-backdrop` (9998), `z-modal` (9999), `z-max` (10000)

### Animações / Motion
- `transition-all` proibido — usar `transition-colors`, `transition-opacity`, `transition-transform`
- framer-motion removido — usar `tailwindcss-animate` (animate-in, fade-in, slide-in-from-*)
- Animações Radix (Dialog, Popover, Dropdown): ativas via data-state

### Ícones
- Biblioteca canônica: `lucide-react`
- Tamanho default inline: `w-4 h-4` (16px)
- Tamanho em navegação/standalone: `w-5 h-5` (20px)
- Ícones decorativos: `aria-hidden="true"` obrigatório
- Top 5 ícones por uso: X (87), Loader2 (81), Brain (68), Search (49), AlertCircle (44)

### Componentes UI
- Base: shadcn/ui — importar de `@/components/ui/*`
- Proibido: `.lia-card` CSS class (usar `<Card>` shadcn), `.lia-input` CSS class (usar `<Input>` shadcn)
- Button variants: `primary`, `secondary`, `ghost`, `destructive`, `outline`, `link`
- Button size default: `h-10` (40px)

### globals.css
- Dividido em: `globals.css` (vars + @layer base) + `src/app/styles/{typography,components,animations,dark-mode}.css`
- Alvo: globals.css < 250 linhas

## Dívidas técnicas conhecidas

| Item | OPT | Descrição |
|------|-----|-----------|
| style={{}} dinâmicos | OPT-043 | ~979 ocorrências — LiaSuperPrompt, EAPTabContent, etc. com TODO |
| wedo-apoio-* | OPT-006 | Tokens deprecated — remover em próxima sprint |
| spacing px arbitrário | OPT-022 | pl-[21px] etc. sem canônico Tailwind |

## Comandos úteis

```bash
# Buscar inline styles dinâmicos pendentes
grep -rn "OPT-043.*TODO" src/

# Buscar border-gray residuais
grep -rn "border-gray-" src/ --include="*.tsx" | grep -v "border-gray-[5-9]"

# Verificar tokens deprecated
grep -rn "wedo-apoio" src/

# Build
cd plataforma-lia && npx next build
```
