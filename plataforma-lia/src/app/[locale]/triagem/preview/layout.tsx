import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Preview da Triagem",
  description: "Visualizacao estatica da triagem para fins de captura de tela",
  robots: { index: false, follow: false },
}

/**
 * Onda 4-N5 (2026-05-24): banner canonical "Preview de Design" envolvendo
 * todas as 6 sub-pages (welcome, chat, email, email-reminder, whatsapp + index).
 *
 * Antes: páginas mockup com dados estáticos PT-BR/EN podiam ser confundidas
 * com produção se URL fosse compartilhada (apesar do robots:noindex já em
 * place). Banner sticky no topo deixa explícito que tudo abaixo é mockup.
 *
 * Layout group canonical — não afeta semântica HTML, só wrapping visual.
 */
export default function PreviewLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div
        role="status"
        className="sticky top-0 z-50 bg-amber-500/95 text-white text-xs font-medium py-1.5 px-4 text-center shadow-sm backdrop-blur-sm"
      >
        🎨 Preview de Design — páginas estáticas para captura de tela. Nenhum dado real é processado.
      </div>
      {children}
    </>
  )
}
