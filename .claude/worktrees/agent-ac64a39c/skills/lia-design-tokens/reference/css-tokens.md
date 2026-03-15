# CSS Design Tokens - Design System LIA v4.1

```css
:root {
  /* ============ CORES - BACKGROUNDS ============ */
  --lia-bg-primary: #FFFFFF;
  --lia-bg-secondary: #F9FAFB;
  --lia-bg-tertiary: #F3F4F6;
  --lia-bg-elevated: #FFFFFF;
  
  /* ============ CORES - TEXTOS ============ */
  --lia-text-primary: #111827;
  --lia-text-body: #1F2937;
  --lia-text-secondary: #4B5563;
  --lia-text-muted: #6B7280;
  --lia-text-disabled: #9CA3AF;
  
  /* ============ CORES - BORDAS ============ */
  --lia-border-subtle: #E5E7EB;
  --lia-border-default: #D1D5DB;
  --lia-border-medium: #9CA3AF;
  
  /* ============ CORES WEDO - ACCENT (10%) ============ */
  --wedo-cyan: #60BED1;
  --wedo-cyan-dark: #4DA8BB;
  --wedo-cyan-light: rgba(96, 190, 209, 0.1);
  --wedo-green: #5DA47A;
  --wedo-green-light: rgba(93, 164, 122, 0.1);
  --wedo-orange: #D19960;
  --wedo-orange-light: rgba(209, 153, 96, 0.1);
  --wedo-purple: #9860D1;
  --wedo-purple-light: rgba(152, 96, 209, 0.1);
  --wedo-magenta: #D160AB;
  --wedo-magenta-light: rgba(209, 96, 171, 0.1);
  --wedo-amber: #F59E0B;
  
  /* ============ TIPOGRAFIA ============ */
  --font-brand: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-data: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  
  /* ============ ESPAÇAMENTO (8px system) ============ */
  --space-0: 0px;
  --space-0-5: 4px;
  --space-1: 8px;
  --space-1-5: 12px;
  --space-2: 16px;
  --space-2-5: 20px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;
  --space-8: 64px;
  
  /* ============ BORDER RADIUS ============ */
  --radius-sm: 4px;
  --radius-default: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* ============ SHADOWS ============ */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-default: 0 2px 4px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.10), 0 4px 8px rgba(0, 0, 0, 0.08);
  --shadow-xl: 0 16px 32px rgba(0, 0, 0, 0.12), 0 8px 16px rgba(0, 0, 0, 0.10);
  
  /* ============ FOCUS RING ============ */
  --focus-ring: 0 0 0 3px rgba(17, 24, 39, 0.2);
  
  /* ============ TRANSITIONS ============ */
  --transition-fast: 100ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-default: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============ DARK MODE ============ */
@media (prefers-color-scheme: dark) {
  :root[data-theme="dark"] {
    --lia-bg-primary: #0F1113;
    --lia-bg-secondary: #1A1D1F;
    --lia-bg-tertiary: #26292B;
    --lia-bg-elevated: #1A1D1F;
    --lia-text-primary: #F9FAFB;
    --lia-text-body: #E5E7EB;
    --lia-text-secondary: #9CA3AF;
    --lia-text-muted: #6B7280;
    --lia-text-disabled: #4B5563;
    --lia-border-subtle: #374151;
    --lia-border-default: #4B5563;
    --lia-border-medium: #6B7280;
  }
}

/* ============ UTILITY CLASSES ============ */
.focus-ring:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.glass-card { background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(0,0,0,0.05); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border-width: 0; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```
