import Link from "next/link"

type PreviewItem = {
  href: string
  title: string
  description: string
}

type PreviewCopy = {
  heading: string
  intro: string
  items: ReadonlyArray<PreviewItem>
}

const COPY: Record<"pt" | "en", PreviewCopy> = {
  pt: {
    heading: "Preview da triagem do candidato",
    intro:
      "Estas paginas sao reproducoes estaticas do que o candidato ve no fluxo real de triagem. Sao destinadas exclusivamente a captura de tela para uso em documentos e materiais de marketing. Nenhum dado real e enviado ou recebido.",
    items: [
      {
        href: "preview/welcome",
        title: "Tela de boas-vindas",
        description:
          "Cartao inicial que o candidato ve ao abrir o link do email, com os 4 canais de resposta.",
      },
      {
        href: "preview/chat",
        title: "Chat em andamento",
        description:
          "Conversa entre IA e candidato com barra de progresso e indicador de digitacao.",
      },
      {
        href: "preview/email",
        title: "Email de convite",
        description:
          "Renderizacao do email de convite para triagem por voz, dentro de uma caixa de email simulada.",
      },
      {
        href: "preview/email-reminder",
        title: "Email de lembrete",
        description:
          "Lembrete enviado quando o candidato ainda nao completou a triagem, na mesma caixa de email simulada.",
      },
      {
        href: "preview/whatsapp",
        title: "Mensagem de WhatsApp",
        description:
          "Aviso de triagem recebida em uma janela de conversa do WhatsApp, com balao verde e cabecalho do contato.",
      },
    ],
  },
  en: {
    heading: "Candidate screening preview",
    intro:
      "These pages are static reproductions of what the candidate sees in the real screening flow. They are intended only for screenshots used in marketing materials and documentation. No real data is sent or received.",
    items: [
      {
        href: "preview/welcome",
        title: "Welcome screen",
        description:
          "Initial card the candidate sees when opening the email link, with the four response channels.",
      },
      {
        href: "preview/chat",
        title: "Chat in progress",
        description:
          "Conversation between IA and the candidate with a progress bar and typing indicator.",
      },
      {
        href: "preview/email",
        title: "Invitation email",
        description:
          "Rendering of the voice screening invitation email inside a simulated inbox.",
      },
      {
        href: "preview/email-reminder",
        title: "Reminder email",
        description:
          "Reminder sent when the candidate hasn't completed the screening yet, in the same simulated inbox.",
      },
      {
        href: "preview/whatsapp",
        title: "WhatsApp message",
        description:
          "Screening confirmation shown inside a WhatsApp chat window, with a green bubble and contact header.",
      },
    ],
  },
}

export default async function TriagemPreviewIndex({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  const copy = locale === "en" ? COPY.en : COPY.pt

  return (
    <main className="min-h-screen bg-lia-bg-secondary dark:bg-lia-bg-primary px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-lia-text-primary">
            {copy.heading}
          </h1>
          <p className="text-sm text-lia-text-secondary leading-relaxed">
            {copy.intro}
          </p>
        </header>

        <ul className="space-y-3">
          {copy.items.map((item) => (
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
