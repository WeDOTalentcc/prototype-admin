---
applyTo: "plataforma-lia/src/**/*.tsx"
---

# Styling — Tailwind + shadcn + Design System WeDO

Fonte canônica do Design System: **`plataforma-lia/CLAUDE.md`** (tokens, tipografia, sombras, z-index, motion). Este arquivo cobre a prática: como escrever classes, compor variantes, lidar com dark mode.

## O helper `cn()`

Usar **sempre** quando compor classes condicionais ou aceitar `className` de fora. Está em `@/lib/utils` (clsx + tailwind-merge).

```tsx
// ✅
import { cn } from '@/lib/utils'

<Button
  className={cn(
    'gap-2',
    variant === 'primary' && 'bg-wedo-cyan',
    className,  // sempre por último — permite override
  )}
/>
```

```tsx
// ❌ concat manual
className={`${base} ${variant === 'primary' ? 'bg-wedo-cyan' : ''} ${className}`}

// ❌ sem cn() — tailwind-merge não resolve conflitos
className={`px-4 ${props.className}`}
```

**Regra**: se o componente aceita `className` prop, passe por `cn()` e coloque `className` **por último** para permitir override correto via tailwind-merge.

## Ordem de classes

Ordene por agrupamento semântico — não alfabético:

1. Layout (`flex`, `grid`, `block`, `relative`)
2. Box model (`w-*`, `h-*`, `p-*`, `m-*`, `gap-*`)
3. Tipografia (`text-*`, `font-*`, `leading-*`)
4. Cor / fundo (`bg-*`, `text-*`, `border-*`)
5. Borda / radius (`rounded-*`, `border-*`)
6. Efeitos (`shadow-*`, `opacity-*`)
7. Transição (`transition-*`, `duration-*`)
8. Estados (`hover:*`, `focus:*`, `disabled:*`)
9. Dark mode (`dark:*`)
10. Responsivo (`sm:*`, `md:*`, `lg:*`)

```tsx
// ✅
<div className="flex items-center gap-3 px-4 py-2 text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-subtle rounded-lg transition-colors hover:bg-lia-interactive-hover dark:bg-lia-bg-elevated" />
```

Não precisamos de prettier-plugin-tailwindcss; escreva na ordem manualmente.

## Design tokens

Use **tokens semânticos**, nunca hex hardcoded em JSX:

```tsx
// ✅ tokens
<div className="bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle" />
<button className="bg-wedo-cyan hover:bg-wedo-cyan-dark" />  // LIA/IA exclusivo
<span className="text-status-success" />

// ❌ hex
<div className="bg-[#60BED1] text-[#111827]" />
<div style={{ color: '#E87575' }} />
```

Fonte de verdade dos tokens: `tailwind.config.ts` e `design-tokens.css`. Antes de criar um novo, verifique se já existe um `lia-*`, `wedo-*` ou `status-*` que sirva.

### Quando usar `wedo-cyan`

**Exclusivamente** para elementos relacionados a IA/LIA (chat do LIA, badges "IA", botões de ação assistida). Nunca para CTAs genéricos — esses usam `bg-lia-btn-primary-bg` via `<Button variant="primary">`.

### Cores críticas

| Token | Uso |
|---|---|
| `bg-lia-bg-primary/secondary/tertiary/elevated` | fundos em camadas |
| `text-lia-text-primary/secondary/tertiary/disabled` | hierarquia de texto |
| `border-lia-border-subtle/default/medium/strong` | bordas |
| `text-status-success/error/warning` | semântica (sucesso, erro, aviso) |
| `bg-wedo-cyan` | **só** LIA/IA |
| `bg-wedo-coral` | CTAs primários brand |

## Inline styles

**Proibidos** salvo três exceções justificadas:

1. Valores dinâmicos de layout que Tailwind não cobre (ex: `width` em px calculado).
2. Valores vindos de config do usuário (ex: cor custom de avatar).
3. Animações interpoladas por lib (raro).

Quando precisar, comente com o motivo:

```tsx
// ✅ justificado
<div
  style={{ width: previewWidth }}  // [resize-handler] px dinâmico via drag
  className="h-full bg-lia-bg-primary"
/>

// ❌
<div style={{ padding: 16, color: '#111' }} />
```

> ⚠️ Há ~979 ocorrências de `style={{}}` dinâmico marcadas como OPT-043 em `plataforma-lia/CLAUDE.md`. Não as use como precedente — são dívida.

## shadcn/ui como base

Componentes primitivos vivem em `src/components/ui/`. **Nunca** importe de `@radix-ui/*` direto em componentes de domínio — passe sempre pelo wrapper shadcn.

```tsx
// ✅
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

// ❌
import * as Dialog from '@radix-ui/react-dialog'
```

Se precisar estender um primitivo, **não** duplique — edite `ui/*.tsx` (adicione variante via cva) ou crie um wrapper em `components/<feature>/`:

```tsx
// ✅ wrapper específico da feature
export function KanbanDialog(props: DialogProps) {
  return (
    <Dialog {...props}>
      <DialogContent className="max-w-4xl h-[80vh]">
        {props.children}
      </DialogContent>
    </Dialog>
  )
}
```

## Transições — `transition-colors` vs `transition-all`

**Regra**: `transition-all` é proibido (causa text blur em camadas GPU). Use o tipo específico:

```tsx
// ✅
className="transition-colors duration-200 hover:bg-lia-interactive-hover"
className="transition-opacity duration-150"
className="transition-transform duration-200 hover:scale-105"

// ❌
className="transition-all duration-200"
```

> ⚠️ ~797 ocorrências de `transition-all` existem no repo (OPT-028). Não migrar em massa — corrigir ao tocar o arquivo.

## Dark mode

Dark mode é **obrigatório** em todo componente. Os tokens `lia-*` já resolvem automaticamente via CSS vars. Só adicione `dark:` quando não estiver usando um token que mude sozinho.

```tsx
// ✅ tokens (resolvem light/dark automaticamente)
<div className="bg-lia-bg-primary text-lia-text-primary border-lia-border-subtle" />

// ✅ quando precisa overrides específicos
<div className="bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100" />

// ❌ esqueceu do dark mode
<div className="bg-white text-black" />
```

## Responsividade

Mobile-first: sem prefixo = mobile. Adicione `sm:`, `md:`, `lg:`, `xl:` para breakpoints maiores.

```tsx
// ✅
<div className="flex flex-col gap-2 md:flex-row md:gap-4 lg:gap-6" />

// ❌ mobile pensado depois
<div className="flex flex-row gap-6 sm:flex-col sm:gap-2" />
```

Layout tokens semânticos (ver `tailwind.config.ts`): `w-panel-sm/md/lg/xl`, `h-chart-sm`, `h-content-md/lg`, `h-card-lg`. Use antes de inventar `w-[350px]`.

## Z-index

Tokens semânticos — nunca `z-[N]` arbitrário.

| Token | Valor | Uso |
|---|---|---|
| `z-base` | 0 | layers base |
| `z-raised` | 10 | cards elevados |
| `z-dropdown` | 40 | selects, popovers |
| `z-sticky` | 50 | headers fixos |
| `z-overlay` | 60 | sub-modais |
| `z-toast` | 100 | notificações |
| `z-select` | 200 | Select dentro de modal |
| `z-modal` | 9999 | Dialog primário |
| `z-max` | 10000 | emergências |

## Radius

Tokens DS (ver `plataforma-lia/CLAUDE.md`):

- Cards/modais: `rounded-xl`
- Inputs/badges: `rounded-lg`
- Chips/pills: `rounded-full`
- Primitivos shadcn padrão: `rounded-md` (preservado por compat)

## Animação

Use `tailwindcss-animate` (já instalado) ou keyframes em `tailwind.config.ts`. **Não adicionar `framer-motion`** — foi removido do projeto.

```tsx
// ✅
<div className="animate-in fade-in slide-in-from-bottom-4 duration-300" />
<div className="animate-fade-in-up" />  // keyframe WeDO
```

## Ícones (lucide-react)

- Inline em texto: `w-4 h-4`.
- Standalone / navegação: `w-5 h-5`.
- Decorativo: `aria-hidden="true"`.
- Cor segue contexto (`text-lia-text-secondary`, `text-status-error`).

```tsx
// ✅
<div className="flex items-center gap-2 text-lia-text-secondary">
  <Search className="w-4 h-4" aria-hidden="true" />
  <span>Buscar</span>
</div>
```

## Rules

- **`cn()` sempre** que componha classes ou aceite `className` prop — e `className` por último.
- **Tokens > hex**. Sem `bg-[#...]`, `color: '#...'`, `style={{ color: '...' }}`.
- **`wedo-cyan` exclusivo para LIA/IA**.
- **`transition-colors`/`-opacity`/`-transform`** — nunca `transition-all`.
- **Dark mode obrigatório** — prefira tokens `lia-*` que resolvem sozinhos.
- **Mobile-first**: sem prefixo = mobile.
- **Z-index via token** (`z-modal`, `z-toast`), nunca `z-[N]`.
- **Shadcn wrappers**, nunca `@radix-ui/*` direto no domínio.
- **Sem inline styles** salvo valor dinâmico com comentário explicando.
- **Sem `framer-motion`** — usar `tailwindcss-animate` + keyframes do DS.
