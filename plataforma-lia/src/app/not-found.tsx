import Link from 'next/link'
import { FileQuestion, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary">
      <div className="text-center space-y-6 max-w-md px-6">
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-xl bg-lia-bg-secondary flex items-center justify-center">
            <FileQuestion className="w-10 h-10 text-lia-text-tertiary" />
          </div>
        </div>
        <div className="space-y-2">
          <h1 className="text-4xl font-semibold text-lia-text-primary">404</h1>
          <h2 className="text-xl font-semibold text-lia-text-primary">Página não encontrada</h2>
          <p className="text-lia-text-secondary text-sm">
            A página que você está procurando não existe ou foi movida.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan-dark transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao painel
        </Link>
      </div>
    </div>
  )
}
