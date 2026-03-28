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
      fontSize: {
        'xs':       ['var(--font-size-xs)',      { lineHeight: 'var(--line-height-normal)' }],
        'micro':    ['var(--font-size-micro)',    { lineHeight: 'var(--line-height-tight)' }],
        'sm-ui':    ['var(--font-size-sm-ui)',    { lineHeight: 'var(--line-height-normal)' }],
        'base-ui':  ['var(--font-size-base-ui)',  { lineHeight: 'var(--line-height-relaxed)' }],
      },
      colors: {
        // ──────────────────────────────────────────────
        // BRAND — wedo-cyan EXCLUSIVO para LIA/IA
        // Fonte de verdade: design-tokens.css (--wedo-cyan)
        // Hardcoded aqui para suportar opacity modifiers (bg-wedo-cyan/10)
        // ──────────────────────────────────────────────
        'wedo-cyan': '#60BED1',
        'wedo-cyan-dark': '#4DA8BB',
        'chat-cyan': '#00B8B8',
        // ──────────────────────────────────────────────
        // STATUS SEMÂNTICOS — obrigatórios WCAG 1.4.1
        // Fonte de verdade: design-tokens.css (--status-*)
        // Usar: text-status-success, bg-status-error, etc.
        // ──────────────────────────────────────────────
        'status-success': '#16A34A',
        'status-error':   '#DC2626',
        'status-warning': '#D97706',
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
        // LEGADOS — manter até Fase 3 (consolidação badges)
        // Gradualmente substituir por status-* ou gray-*
        // ──────────────────────────────────────────────
        'wedo-green': '#5DA47A',
        'wedo-green-light': '#7BC29A',
        'wedo-green-pastel': '#A8D5B7',
        'wedo-green-bright': '#60D186',
        'wedo-orange': '#D19960',
        'wedo-purple': '#9860D1',
        'wedo-magenta': '#D160AB',
        'wedo-coral': '#E16162',
        // ──────────────────────────────────────────────
        // TERCEIROS — cores de marca de integrações
        // Usar APENAS em previews/simulações das plataformas
        // ──────────────────────────────────────────────
        'whatsapp-bg': '#E5DDD5',      // Fundo do chat WhatsApp
        'whatsapp-bubble': '#DCF8C6',  // Bolha de mensagem enviada WhatsApp
        'whatsapp-green': '#25D366',   // Verde do ícone WhatsApp
        'wedo-blue': '#3B82F6',        // Azul informativo (legado)
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
      },
      animation: {
        'fade-in-up':       'fade-in-up 0.3s ease-out',
        'scale-in-delayed': 'scale-in-delayed 0.2s ease-out',
        'slide-in-up':      'slide-in-up 0.3s ease-out',
      },
      fontFamily: {
        'inter': ['var(--font-inter)', 'sans-serif'],
        'open-sans': ['var(--font-open-sans)', 'sans-serif'],
        'crimson': ['var(--font-crimson)', 'serif'],
        'source-serif-4': ['var(--font-source-serif-4)', 'serif'],
        'brand': ['var(--font-open-sans)', 'sans-serif'],
        'data': ['var(--font-inter)', 'sans-serif'],
        'sidebar': ['var(--font-source-serif-4)', 'serif'],
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
