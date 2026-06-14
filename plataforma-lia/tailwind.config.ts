import type { Config } from "tailwindcss";

export default {
    darkMode: ["class"],
    content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        'lia-focus': '0 0 0 2px rgba(0,0,0,0.1)',
        'lia-focus-primary': '0 0 0 2px var(--wedo-coral)',
        'lia-sm':      'var(--lia-shadow-sm)',
        'lia-default': 'var(--lia-shadow-default)',
        'lia-md':      'var(--lia-shadow-md)',
        'lia-lg':      'var(--lia-shadow-lg)',
      },
      fontSize: {
        'xs':       ['var(--font-size-xs)',      { lineHeight: 'var(--line-height-normal)' }],
        'micro':    ['var(--font-size-micro)',    { lineHeight: 'var(--line-height-tight)' }],
        'sm-ui':    ['var(--font-size-sm-ui)',    { lineHeight: 'var(--line-height-normal)' }],
        'base-ui':  ['var(--font-size-base-ui)',  { lineHeight: 'var(--line-height-relaxed)' }],
      },
      colors: {
        // ──────────────────────────────────────────────
        // DS CANONICAL "Quiet Operator" — DESIGN.md 2026-05-26
        // Fonte de verdade: plataforma-lia/DESIGN.md frontmatter `colors:`
        // 10 cinza stops (paper→ink) + 7 acentos funcionais wired top-level
        // como hex literais (suportam opacity modifiers: bg-graphite/80).
        // Sensor: scripts/check_ds_tokens_canonical.mjs garante sync com DESIGN.md.
        // ──────────────────────────────────────────────
        // Cinza scale (10 stops)
        'paper':     '#FFFFFF',
        'chalk':     '#F9FAFB',
        'powder':    '#F3F4F6',
        'mist':      '#E5E7EB',
        'pebble':    '#D1D5DB',
        'fog':       '#9CA3AF',
        'ash':       '#6B7280',
        'slate':     '#4B5563',
        'graphite':  '#1F2937',
        'ink':       '#030712',
        // Acentos funcionais canonical
        'lia-cyan-hover': '#4DA8BB',
        'coral-quiet':    '#C74446',
        'forest-green':   '#5DA47A',
        'amber-warning':  '#D19960',
        'insight-purple': '#9860D1',
        'alert-magenta':  '#D160AB',
        // ──────────────────────────────────────────────
        // AGENT CATEGORY ACCENT — Fase 3 Sprint 5 (2026-05-30, decisão Paulo)
        // O 10% de cor com propósito (90/10 Rule) CONTIDO ao avatar do agente.
        // Paleta DESSATURADA / editorial (muted, nunca primárias 500). CYAN
        // EXCLUÍDO — reservado à assistente da plataforma (white-label).
        // Single source de mapeamento categoria→token: lib/agent-studio/category-accent.ts.
        // DESIGN.md "Agent category accent" documenta a regra. Suportam opacity
        // modifier (bg-agent-cat-screening/12) pro fundo tonal do avatar.
        // ──────────────────────────────────────────────
        'agent-cat-screening':     '#5B7290',  // Triagem — slate-blue dessaturado
        'agent-cat-sourcing':      '#6E9B7E',  // Captação — sage/verde-acinzentado
        'agent-cat-communication': '#C0795E',  // Comunicação — terracota suave
        'agent-cat-analytics':     '#8A6E9E',  // Análise — plum dessaturado (NÃO cyan)
        'agent-cat-jobs':          '#B58A52',  // Vagas — ocre/âmbar-acinzentado
        'agent-cat-automation':    '#6B6F86',  // Automação — ardósia/steel neutro-frio
        // Alias canonical name → wedo-cyan equivalente (backward compat preservado)
        'lia-cyan':       '#60BED1',
        // ──────────────────────────────────────────────
        // BRAND — wedo-cyan EXCLUSIVO para LIA/IA
        // Fonte de verdade: design-tokens.css (--wedo-cyan)
        // Hardcoded aqui para suportar opacity modifiers (bg-wedo-cyan/10)
        // ──────────────────────────────────────────────
        'wedo-cyan': '#60BED1',
        'wedo-cyan-dark': '#4DA8BB',
        // ──────────────────────────────────────────────
        // STATUS SEMÂNTICOS — obrigatórios WCAG 1.4.1
        // Fonte de verdade: design-tokens.css (--status-*)
        // Usar: text-status-success, bg-status-error, etc.
        // ──────────────────────────────────────────────
        'status-success':              '#16A34A',
        'status-error':                '#DC2626',
        'status-warning':              '#D97706',
        'status-success-bg':           'var(--status-success-bg)',
        'status-error-bg':             'var(--status-error-bg)',
        'status-warning-bg':           'var(--status-warning-bg)',
        'status-error-border':         'var(--status-error-border)',
        'status-warning-border':       'var(--status-warning-border)',
        'status-warning-border-light': 'var(--status-warning-border-light)',
        'gray-border':                 'var(--gray-border)',
        'white-token':                 '#FFFFFF',
        // ──────────────────────────────────────────────
        // BRAND EXTERNALS — LinkedIn
        // Tokens: text-brand-linkedin, hover:text-brand-linkedin-hover
        // ──────────────────────────────────────────────
        brand: {
          linkedin:         '#0A66C2',
          'linkedin-hover': '#004182',
        },
        // ──────────────────────────────────────────────
        // CHART — tons monocromáticos para visualização
        // Fonte de verdade: design-tokens.css (--chart-*)
        // Usar apenas em componentes de gráfico
        // ──────────────────────────────────────────────
        'chart-1': 'rgba(3,7,18,1.00)',
        'chart-2': 'rgba(3,7,18,0.60)',
        'chart-3': 'rgba(3,7,18,0.35)',
        'chart-4': 'rgba(3,7,18,0.15)',
        // ──────────────────────────────────────────────
        // LIA DESIGN TOKENS — Fase 5 (inline styles → Tailwind)
        // Fonte de verdade: design-tokens.css (--lia-*)
        // Suportam dark mode automático via CSS variables
        // Uso: bg-lia-bg-primary, text-lia-text-secondary, border-lia-border-default, etc.
        // ──────────────────────────────────────────────
        'lia-bg-primary':           'var(--lia-bg-primary)',
        'lia-bg-secondary':         'var(--lia-bg-secondary)',
        'lia-bg-tertiary':          'var(--lia-bg-tertiary)',
        'lia-bg-elevated':          'var(--lia-bg-elevated)',
        'lia-bg-inverse':           'var(--lia-bg-inverse)',
        'lia-overlay':              'var(--lia-overlay)',
        'lia-overlay-light':        'var(--lia-overlay-light)',
        'lia-text-on-inverse':      'var(--lia-text-on-inverse)',
        'lia-border-subtle':        'var(--lia-border-subtle)',
        'lia-border-default':       'var(--lia-border-default)',
        'lia-border-medium':        'var(--lia-border-medium)',
        'lia-border-strong':        'var(--lia-border-strong)',
        'lia-text-primary':         'var(--lia-text-primary)',
        'lia-text-secondary':       'var(--lia-text-secondary)',
        'lia-text-tertiary':        'var(--lia-text-tertiary)',
        'lia-text-disabled':        'var(--lia-text-disabled)',
        'lia-text-inverse':         'var(--lia-text-inverse)',
        // ──────────────────────────────────────────────
        // LEGACY ALIASES — canonical-fix 2026-05-25
        // 4 tokens não-canonical herdados (Replit Agent / cherry-pick) usados em
        // ~695 sites do codebase. Sintoma mais visível: modal "Nova Política de
        // Remuneração" renderizando transparente porque `bg-lia-surface` não
        // existia. Aliases mapeiam pro token canonical equivalente — fix no
        // produtor resolve todos os consumidores em 1 commit.
        // NÃO USAR em código novo. Preferir o token canonical à direita.
        // ──────────────────────────────────────────────
        'lia-surface':              'var(--lia-bg-elevated)',     // → preferir 'lia-bg-elevated' (modal/card) ou 'lia-bg-primary' (page)
        'lia-border':               'var(--lia-border-default)',  // → preferir 'lia-border-default' ou 'lia-border-subtle'
        'lia-primary':              '#60BED1',                    // → preferir 'wedo-cyan' (acento IA canonical)
        'lia-muted':                'var(--lia-bg-tertiary)',     // → preferir 'lia-bg-tertiary' (hover) ou 'lia-interactive-hover'
        'lia-interactive-hover':    'var(--lia-interactive-hover)',
        'lia-interactive-active':   'var(--lia-interactive-active)',
        'lia-interactive-focus':    'var(--lia-interactive-focus)',
        'lia-brand-primary':        'var(--lia-brand-primary)',
        'lia-brand-primary-hover':  'var(--lia-brand-primary-hover)',
        'lia-brand-primary-light':  'var(--lia-brand-primary-light)',
        'lia-info-color':           'var(--lia-info-color)',
        'lia-info-light':           'var(--lia-info-light)',
        'lia-status-high-bg':       'var(--lia-status-high-bg)',
        'lia-status-high-text':     'var(--lia-status-high-text)',
        'lia-status-high-border':   'var(--lia-status-high-border)',
        'lia-status-medium-bg':     'var(--lia-status-medium-bg)',
        'lia-status-medium-text':   'var(--lia-status-medium-text)',
        'lia-status-medium-border': 'var(--lia-status-medium-border)',
        'lia-status-low-bg':        'var(--lia-status-low-bg)',
        'lia-status-low-text':      'var(--lia-status-low-text)',
        'lia-status-low-border':    'var(--lia-status-low-border)',
        'lia-destructive-bg':       'var(--lia-destructive-bg)',
        'lia-destructive-text':     'var(--lia-destructive-text)',
        'lia-destructive-border':   'var(--lia-destructive-border)',
        'lia-btn-primary-bg':       'var(--lia-btn-primary-bg)',
        'lia-btn-primary-hover':    'var(--lia-btn-primary-hover)',
        'lia-btn-primary-text':     'var(--lia-btn-primary-text)',
        'lia-btn-secondary-bg':     'var(--lia-btn-secondary-bg)',
        'lia-btn-secondary-hover':  'var(--lia-btn-secondary-hover)',
        'lia-btn-secondary-text':   'var(--lia-btn-secondary-text)',
        'lia-btn-secondary-border': 'var(--lia-btn-secondary-border)',
        'lia-btn-ghost-bg':         'var(--lia-btn-ghost-bg)',
        'lia-btn-ghost-hover':      'var(--lia-btn-ghost-hover)',
        'lia-btn-ghost-text':       'var(--lia-btn-ghost-text)',
        'lia-badge-neutral-bg':     'var(--lia-badge-neutral-bg)',
        'lia-badge-neutral-text':   'var(--lia-badge-neutral-text)',
        'lia-badge-neutral-border': 'var(--lia-badge-neutral-border)',
        'lia-input-bg':             'var(--lia-input-bg)',
        'lia-input-border':         'var(--lia-input-border)',
        'lia-input-border-focus':   'var(--lia-input-border-focus)',
        'lia-input-text':           'var(--lia-input-text)',
        'lia-input-placeholder':    'var(--lia-input-placeholder)',
        // ──────────────────────────────────────────────
        // LEGADOS — manter até Fase 3 (consolidação badges)
        // Gradualmente substituir por status-* ou gray-*
        // ──────────────────────────────────────────────
        'wedo-green': '#5DA47A',
        'wedo-green-light': 'var(--wedo-green-light)',
        'wedo-green-pastel': '#A8D5B7',  // [OPT-010] Verde pastel suave — usado em badges de status positivo e indicadores de qualidade (Big Five, screening)
        'wedo-green-bright': '#60D186',
        'wedo-orange': '#D19960',
        'wedo-purple': '#9860D1',
        'wedo-magenta': '#D160AB',
        // TEXT-SAFE DARKER VARIANTS — WCAG AA ≥ 4.5:1 on white (v4.2.4)
        'wedo-cyan-text':    '#0D6E82',
        'wedo-orange-text':  '#7A4E14',
        'wedo-green-text':   '#1E6B42',
        'wedo-purple-text':  '#5E35A8',
        'wedo-magenta-text': '#882B72',

        'wedo-amber':       'var(--wedo-amber)',       // bg-wedo-amber, suporta /opacity
        'wedo-amber-light': 'var(--wedo-amber-light)',  // bg-wedo-amber-light → status amber/warning
        'wedo-coral': '#E87575', /* coral suave — atualizado 2026-03-29, era #E16162 */
        // ──────────────────────────────────────────────
        // TERCEIROS — cores de marca de integrações
        // Usar APENAS em previews/simulações das plataformas
        // ──────────────────────────────────────────────
        'whatsapp-bg': '#E5DDD5',      // Fundo do chat WhatsApp
        'whatsapp-bubble': '#DCF8C6',  // Bolha de mensagem enviada WhatsApp
        'whatsapp-green': '#25D366',   // Verde do ícone WhatsApp
        // 'wedo-blue': '#3B82F6',        // [OPT-058] REMOVIDO -- migrado para text-blue-500/bg-blue-500
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        }
      },
      borderRadius: {
        // WeDo DS canonical (Fundação DS — fonte-da-verdade = código)
        // cards/modais:            rounded-xl  (12px, = default Tailwind 0.75rem)
        // botões/inputs/selects:   rounded-md  (calc(var(--radius) - 2px))
        // chips/badges/pílulas:    rounded-full
        // interfaces imersivas (chat expandido, login): rounded-2xl
        // NUNCA sobrescrever o raio em <Button> (sm/lg já resolvem rounded-md).
        // Paleta: usar SEMPRE tokens status-*/wedo-*/lia-* — NUNCA cores cruas do
        // Tailwind (amber-50, emerald-600, purple-100, blue-50, red-200…).
        // DEFAULT Tailwind values preserved below
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      },
      keyframes: {
        'fade-in-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in-delayed': {
          '0%':   { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-in-up': {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        // Onda 2 F7 (2026-05-27) — pulse exclusivo do pingo cyan no Funil.
        // Cycle 2s ease-in-out. Honra motion-reduce via Tailwind utility.
        'agent-pulse': {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%':      { opacity: '1',   transform: 'scale(1.2)' },
        },
        'pulse-dot': {
          '0%, 80%, 100%': { opacity: '0.2', transform: 'scale(0.8)' },
          '40%':           { opacity: '1',   transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-in-up':       'fade-in-up 0.3s ease-out',
        'scale-in-delayed': 'scale-in-delayed 0.2s ease-out',
        'slide-in-up':      'slide-in-up 0.3s ease-out',
        // Onda 2 F7 — usar com `motion-reduce:animate-none` no consumer.
        'agent-pulse':      'agent-pulse 2s ease-in-out infinite',
      },
      fontFamily: {
        // DS v4.2.1: `font-sans` → Open Sans (fonte primária 85% do produto).
        // Mantido como `font-open-sans` também por compat com componentes
        // legados; ambos resolvem para a mesma stack.
        'sans': ['var(--font-open-sans)', 'sans-serif'],
        'inter': ['var(--font-inter)', 'sans-serif'],
        'open-sans': ['var(--font-open-sans)', 'sans-serif'],
        'crimson': ['var(--font-crimson)', 'serif'],
        'source-serif-4': ['var(--font-source-serif-4)', 'serif'],
        'brand': ['var(--font-open-sans)', 'sans-serif'],
        'data': ['var(--font-inter)', 'sans-serif'],
      },
      container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
        lg: '4rem',
        xl: '5rem',
        '2xl': '6rem',
      },
      screens: {
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',
      },
      },
      // ──────────────────────────────────────────────
      // LIA SHADOW TOKENS — Fase 5 (merged em boxShadow acima)
      // shadow-lia-sm, shadow-lia-default, shadow-lia-md, shadow-lia-lg
      // ──────────────────────────────────────────────
      // ──────────────────────────────────────────────
      // LAYOUT TOKENS — Sprint 5A (Design System v4.2.1)
      // Substituem valores arbitrários w-[Npx] / h-[Npx]
      // ──────────────────────────────────────────────
      width: {
        'panel-sm': '300px',   // w-panel-sm  → 300px
        'panel-md': '350px',   // w-panel-md  → 350px
        'panel-lg': '400px',   // w-panel-lg  → 400px
        'panel-xl': '500px',   // w-panel-xl  → 500px
        'sidebar-content': '200px', // w-sidebar-content → 200px
      },
      height: {
        'chart-sm':    '200px', // h-chart-sm    → 200px  (era 'chart')
        'content-md':  '300px', // h-content-md  → 300px  (era 'panel-md' — renomeado para evitar ambiguidade com w-panel-md=350px)
        'content-lg':  '400px', // h-content-lg  → 400px  (era 'panel-lg')
        'card-lg':     '180px', // h-card-lg     → 180px
      },
      minWidth: {
        'panel-sm': '300px',
        'panel-md': '350px',
      },
      maxWidth: {
        'panel-xl': '500px',
        'panel-lg': '400px',
      },
      maxHeight: {
        'content-lg': '400px', // era 'panel-lg' — renomeado para consistência com height
      },
      // ──────────────────────────────────────────────
      // Z-INDEX SEMÂNTICO — DS v4.2.1
      // Substituem valores arbitrários z-[N]
      // Uso: z-overlay, z-modal, z-toast, etc.
      // ──────────────────────────────────────────────
      zIndex: {
        'base':    '0',
        'raised':  '10',
        'dropdown':'40',
        'sticky':  '50',
        'overlay': '60',    // sub-modais, modais secundários, confirmações
        'toast':   '100',   // notificações, toasts
        'select':  '200',   // SelectContent dentro de modais
        'backdrop':'9998',  // Dialog overlay/backdrop
        'modal':   '9999',  // Dialog content, modais principais
        'max':     '10000', // Sempre acima de tudo (variable-selector)
      },
    }
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
