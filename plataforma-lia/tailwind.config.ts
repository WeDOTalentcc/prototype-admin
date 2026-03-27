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
    }
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
