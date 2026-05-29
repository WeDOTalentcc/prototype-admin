import { redirect } from "next/navigation"

interface PageProps {
  params: Promise<{ locale: string }>
}

export default async function AiCreditsRedirectPage({ params }: PageProps) {
  const { locale } = await params
  redirect(`/${locale}/configuracoes?section=consumo`)
}
