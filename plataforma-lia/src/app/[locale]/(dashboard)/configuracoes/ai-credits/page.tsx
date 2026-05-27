import { redirect } from "next/navigation"

interface PageProps {
  params: { locale: string }
}

export default function AiCreditsRedirectPage({ params }: PageProps) {
  redirect(`/${params.locale}/configuracoes?section=consumo`)
}
