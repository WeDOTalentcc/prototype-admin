import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Preview da Triagem",
  description: "Visualizacao estatica da triagem para fins de captura de tela",
  robots: { index: false, follow: false },
}

export default function PreviewLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
