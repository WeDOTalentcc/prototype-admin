import type { Metadata } from "next"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const title = slug.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
  return {
    title: `${title} | WeDoTalent`,
    description: `Detalhes da vaga ${title}`,
    robots: { index: true, follow: true },
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
