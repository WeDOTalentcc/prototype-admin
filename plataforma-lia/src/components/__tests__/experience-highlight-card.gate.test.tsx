import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"

// Pina P2-9: o CTA "Gerar resumo" nao desabilitava quando companyId vazio
// (POST iria com company_id= vazio). Agora disabled={!hasCompany}.
vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: null, company: null, tenantId: null, loading: false, error: null, refetch: async () => {} }),
}))

function renderCard(companyId: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  // 404 -> highlight=null -> branch "ainda nao gerado" (CTA) renderiza
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status: 404, ok: false, json: async () => ({}) }))
  return render(
    <QueryClientProvider client={qc}>
      <ExperienceHighlightCard candidate={{ id: "cand-x", name: "Fulano" }} companyId={companyId} />
    </QueryClientProvider>
  )
}

describe("ExperienceHighlightCard — gate companyId no CTA (P2-9)", () => {
  it("companyId vazio => botao Gerar resumo DESABILITADO", async () => {
    renderCard("")
    expect(await screen.findByRole("button", { name: /Gerar resumo/i })).toBeDisabled()
  })
  it("companyId presente => botao Gerar resumo habilitado", async () => {
    renderCard("co-1")
    expect(await screen.findByRole("button", { name: /Gerar resumo/i })).not.toBeDisabled()
  })
})
