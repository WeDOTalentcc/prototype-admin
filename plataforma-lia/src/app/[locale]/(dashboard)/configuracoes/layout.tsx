import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Configurações',
  description: 'Configurações da conta e da WeDoTalent',
}

/**
 * IMPORTANTE — NÃO criar `configuracoes/loading.tsx` neste nível.
 *
 * Como existe `configuracoes/ai-credits/loading.tsx` (e podem existir outras
 * sub-rotas com loading próprio no futuro), ter um `loading.tsx` também aqui
 * cria um Suspense parent + child aninhado dentro do route group `(dashboard)`
 * que dispara um deadlock no compile do Turbopack 16.2.4 — a rota
 * `/[locale]/configuracoes` fica eternamente em "Compiling..." sem nunca
 * concluir, causando 0-byte hang infinito no browser.
 *
 * O loading da página principal de configurações é feito INTERNAMENTE pelos
 * 9 hubs lazy-loaded em `SettingsPageEnhanced` via `dynamic({ ssr:false,
 * loading: <I18nLoadingFallback /> })`, então não precisamos de loading.tsx
 * neste nível.
 *
 * Sub-rotas (ai-credits, futuras outras) PODEM e DEVEM ter seu próprio
 * loading.tsx normalmente.
 */
export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
