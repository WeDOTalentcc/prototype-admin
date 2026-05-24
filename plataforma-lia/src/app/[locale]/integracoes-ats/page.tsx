"use client"

/**
 * /[locale]/integracoes-ats/page.tsx
 *
 * Onda 4-P0-Fase7 (2026-05-24): rota canonical pra configuração de
 * integrações ATS.
 *
 * Histórico: IntegrationDetailDrawer.tsx:416 botão "Configurar no Painel
 * ATS" fazia `window.location.href = "/integracoes-ats"` mas a rota nunca
 * foi criada (mesmo padrão Task #712). Usuário clicava e ia pra 404.
 * Descoberto via check_no_broken_window_location.py.
 *
 * Estratégia: esta página é landing canonical interna. Se NEXT_PUBLIC_RAILS_URL
 * estiver configurado, redireciona pro Painel ATS no Rails. Caso contrário,
 * mostra mensagem de "configuração indisponível + voltar pra configurações".
 */

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { ExternalLink, Settings } from "lucide-react"

const RAILS_URL = process.env.NEXT_PUBLIC_RAILS_URL ?? null

export default function IntegracoesAtsPage() {
  const router = useRouter()

  // Se Rails configurado, auto-redirect pro Painel ATS externo
  useEffect(() => {
    if (RAILS_URL) {
      window.location.replace(`${RAILS_URL}/admin/integrations`)
    }
  }, [])

  return (
    <main className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-16 h-16 mx-auto rounded-full bg-wedo-cyan/10 flex items-center justify-center">
          <Settings className="w-8 h-8 text-wedo-cyan" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold text-lia-text-primary">
            Integrações ATS
          </h1>
          {RAILS_URL ? (
            <p className="text-sm text-lia-text-secondary">
              Redirecionando pro Painel ATS...
            </p>
          ) : (
            <p className="text-sm text-lia-text-secondary">
              A configuração de integrações ATS está disponível no Painel
              Administrativo. Entre em contato com o suporte WeDo Talent
              para acesso.
            </p>
          )}
        </div>

        {!RAILS_URL && (
          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <button
              onClick={() => router.push("/configuracoes")}
              className="px-4 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors inline-flex items-center gap-2 justify-center"
            >
              <Settings className="w-4 h-4" />
              Voltar para Configurações
            </button>
            <a
              href="mailto:suporte@wedotalent.cc"
              className="px-4 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-primary hover:bg-lia-bg-secondary transition-colors inline-flex items-center gap-2 justify-center"
            >
              <ExternalLink className="w-4 h-4" />
              Contato suporte
            </a>
          </div>
        )}
      </div>
    </main>
  )
}
