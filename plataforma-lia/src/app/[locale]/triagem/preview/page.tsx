import Link from "next/link"

const PREVIEWS = [
  {
    href: "preview/welcome",
    title: "Tela de boas-vindas",
    description: "Cartao inicial que o candidato ve ao abrir o link do email, com os 4 canais de resposta.",
  },
  {
    href: "preview/chat",
    title: "Chat em andamento",
    description: "Conversa entre LIA e candidato com barra de progresso e indicador de digitacao.",
  },
  {
    href: "preview/email",
    title: "Email de convite",
    description: "Renderizacao do email de convite para triagem por voz, dentro de uma caixa de email simulada.",
  },
] as const

export default async function TriagemPreviewIndex({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  return (
    <main className="min-h-screen bg-lia-bg-secondary dark:bg-lia-bg-primary px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-lia-text-primary">
            Preview da triagem do candidato
          </h1>
          <p className="text-sm text-lia-text-secondary leading-relaxed">
            Estas paginas sao reproducoes estaticas do que o candidato ve no fluxo real de triagem.
            Sao destinadas exclusivamente a captura de tela para uso em documentos e materiais de marketing.
            Nenhum dado real e enviado ou recebido.
          </p>
        </header>

        <ul className="space-y-3">
          {PREVIEWS.map((item) => (
            <li key={item.href}>
              <Link
                href={`/${locale}/triagem/${item.href}`}
                className="block rounded-xl border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-5 hover:border-wedo-cyan/60 transition-colors motion-reduce:transition-none focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              >
                <h2 className="text-base font-semibold text-lia-text-primary mb-1">
                  {item.title}
                </h2>
                <p className="text-sm text-lia-text-secondary leading-relaxed">
                  {item.description}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </main>
  )
}
