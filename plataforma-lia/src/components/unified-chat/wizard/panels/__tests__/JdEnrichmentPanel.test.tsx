import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { JdEnrichmentPanel } from "../JdEnrichmentPanel"

/**
 * Canonical idle state contract — REGRA "Wizard panels canonical pattern".
 *
 * O backend  (lia-agent-system/app/domains/job_creation/
 * nodes/jd_enrichment.py:269-285) emite  quando o
 * raw_input do recrutador e magro demais para enriquecer (e.g., usuario disse
 * apenas "vamos abrir uma vaga" sem cole de JD). O painel DEVE renderizar
 * idle state — sem badge "Critico 0/100", sem JdLoadingState (timer 30s).
 *
 * Bug historico (2026-05-29): o painel ignorava  e
 * renderizava "Critico - Score: 0/100 - O enriquecimento esta demorando..."
 * mesmo quando nenhum enriquecimento havia sido disparado. Defeito de
 * canal: produtor emite sinal correto, consumidor nao le.
 */
describe("JdEnrichmentPanel — canonical idle state (awaiting_jd_input)", () => {
  it("renderiza idle state sem badge nem timer quando awaiting_jd_input=true", () => {
    render(
      <JdEnrichmentPanel
        data={{
          awaiting_jd_input: true,
          message: "Cole a descricao da vaga (JD) no chat para enriquecermos juntos.",
        }}
        requiresApproval={false}
      />,
    )
    // Defeito historico: badge "Critico" e score 0/100 renderizados em idle.
    expect(screen.queryByText(/Critico/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/0\/100/)).not.toBeInTheDocument()
    // Defeito historico: JdLoadingState timer 30s mostra "demorando".
    expect(screen.queryByText(/demorando/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Aguardar mais/i)).not.toBeInTheDocument()
    // Idle state mostra mensagem do produtor + CTA neutro.
    expect(screen.getByTestId("jd-awaiting-input")).toBeInTheDocument()
    expect(screen.getByText(/Cole a descricao da vaga/i)).toBeInTheDocument()
  })

  it("nao renderiza badge quando enriched ausente (mesmo sem flag idle)", () => {
    // Estado intermediario: agente comecou a chamar LLM mas ainda nao terminou.
    // Score=0 default NAO deve virar badge "Critico" — badge so existe quando
    // enriquecimento realmente terminou (score real, nao default).
    render(
      <JdEnrichmentPanel
        data={{
          jd_raw: "long enough JD content to be enriched here ...",
          message: "Enriquecendo...",
        }}
        requiresApproval={false}
      />,
    )
    expect(screen.queryByText(/Critico/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/0\/100/)).not.toBeInTheDocument()
    // Loading state legitimo aqui (LLM realmente rodando).
    expect(screen.getByText(/Enriquecendo JD/i)).toBeInTheDocument()
  })

  it("renderiza badge + score + content quando enriched presente", () => {
    render(
      <JdEnrichmentPanel
        data={{
          jd_raw: "Senior Backend Engineer Python Django",
          jd_enriched: {
            titulo_padronizado: "Senior Backend Engineer",
            senioridade_confirmada: "Senior",
            about_role: "Build backend services",
            responsabilidades: [],
            skills_obrigatorias: [],
            skills_desejaveis: [],
            competencias_comportamentais: [],
            context_signals: {
              nivel_autonomia: "alto",
              nivel_inovacao: "medio",
              nivel_pressao: "medio",
              nivel_colaboracao: "medio",
            },
            alteracoes_realizadas: [],
            fairness_corrections: [],
            wsi_quality_score: 85,
            wsi_quality_warnings: [],
          },
          quality_score: 85,
          quality_warnings: [],
          message: "JD enriquecida.",
        }}
        requiresApproval={true}
      />,
    )
    expect(screen.getByText("Bom")).toBeInTheDocument()
    expect(screen.getByText(/85\/100/)).toBeInTheDocument()
    expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument()
  })
})
