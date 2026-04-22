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

## HMR-resilience (Task #801) — guide

Resumo das 5 causas raiz tratadas (audit 2026-04-22):

- **C1 (hook):** `useCandidatesList` agora preserva `candidates`/`total` em erro
  transiente de rede e auto-retenta com backoff `[1s, 3s, 8s]`. Expõe
  `isTransientRetrying` para a UI mostrar banner discreto sem esconder a lista.
- **C2 (services/lia-api/base.ts):** `fetchWithRetry` propaga **mensagem fixa**
  `"Network unavailable (transient)"` ao envelopar `TypeError("Failed to fetch")`,
  preservando o original em `cause`. Nunca propague a string crua — o dev-overlay
  do Next.js casa com ela e ressuscita o sintoma da Task #728.
- **C3 (lib/auth/dev-auto-login.ts):** auto-login do demo retenta com backoff
  `[1, 2, 4, 8, 16]s` (~31s total) durante cold-start do backend. Sem isso o
  front-end fica órfão de token nos primeiros segundos.
- **C4 (hooks):** todos os pollers (`use-hitl-pending`, `use-notifications` etc.)
  devem usar `fetchWithRetry`, **não** `fetch()` cru. Sinalizado via ESLint
  `no-restricted-syntax` em `src/hooks/**` e `src/components/**` cobrindo tanto
  `fetch(...)` quanto `window.fetch(...)` / `globalThis.fetch(...)`. Severidade
  atual `warn` enquanto a Task #803 migra os ~250 hooks/components legados;
  quando #803 fechar, elevar para `error`.
- **C5 (rotas paralelas):** consolidação do proxy em `/api/backend-proxy/*` —
  rota duplicada `/api/lia/[...path]` é tratada em Task #802.

### Regras invioláveis

1. **Nunca** zerar listas/contadores ao receber `transientNetworkError` ou
   `status === 0` — preservar último snapshot e auto-retentar.
2. **Nunca** chamar `fetch()` direto em `src/hooks/**` ou `src/components/**`.
   Use `liaApi.*` (preferível) ou `fetchWithRetry` (para rotas custom).
3. **Nunca** propagar `err.message` cru de erro transiente — wrappear em
   `HttpError(0, 'Network unavailable (transient)', { transientNetworkError: true })`.
4. UX em erro de rede: banner discreto (`aria-live="polite"`) + lista preservada;
   só renderizar empty-state em 401/403/500+.

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
