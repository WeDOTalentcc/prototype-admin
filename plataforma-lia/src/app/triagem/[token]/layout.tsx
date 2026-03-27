import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Triagem | LIA - WeDOTalent",
  description: "Triagem inteligente de candidatos conduzida pela LIA, assistente de recrutamento da WeDOTalent.",
  openGraph: {
    title: "Triagem | LIA - WeDOTalent",
    description: "Realize sua triagem de forma rápida e conversacional com a LIA.",
    type: "website",
    siteName: "WeDOTalent",
  },
  robots: {
    index: false,
    follow: false,
  },
}

export default function TriagemLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 font-['Open_Sans',sans-serif]">
      {children}
    </div>
  )
}
