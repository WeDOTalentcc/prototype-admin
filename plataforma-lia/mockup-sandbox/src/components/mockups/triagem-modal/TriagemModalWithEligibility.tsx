import { useState } from "react"

type EligibilityState = "approved" | "eliminated"

interface EligibilityQA {
  question: string
  answer: string
  met: boolean
  eliminating?: boolean
  reconsideration?: string
}

const MOCK_CANDIDATE = {
  name: "Ana Carolina Ferreira",
  role: "Engenheira de Software Sênior",
  location: "São Paulo, SP",
}

const APPROVED_QAS: EligibilityQA[] = [
  {
    question: "Você possui CNH categoria B válida e disponibilidade para viagens mensais?",
    answer: "Sim, tenho CNH B e posso viajar com frequência.",
    met: true,
  },
  {
    question: "Você tem disponibilidade para início imediato (até 15 dias)?",
    answer: "Sim, posso iniciar em até 10 dias.",
    met: true,
  },
  {
    question: "Você possui inglês fluente para reuniões diárias com o time internacional?",
    answer: "Sim, trabalho em inglês diariamente há 4 anos em reuniões com times distribuídos.",
    met: true,
  },
]

const ELIMINATED_QAS: EligibilityQA[] = [
  {
    question: "Você possui CNH categoria B válida e disponibilidade para viagens mensais?",
    answer: "Sim, tenho CNH B e posso viajar com frequência.",
    met: true,
  },
  {
    question: "Você tem disponibilidade para início imediato (até 15 dias)?",
    answer: "Sim, posso iniciar em até 10 dias.",
    met: true,
  },
  {
    question: "Você possui inglês fluente para reuniões diárias com o time internacional?",
    answer: "Tenho inglês intermediário, consigo me comunicar mas não me considero fluente.",
    met: false,
    eliminating: true,
    reconsideration: "1ª tentativa: \"Tenho inglês básico\" → Candidata reconsiderou antes da resposta final.",
  },
]

const MOCK_WSI_SCORES = [
  { label: "Liderança Técnica", score: 8.4, color: "var(--status-success)" },
  { label: "Resolução de Problemas", score: 7.9, color: "var(--status-success)" },
  { label: "Comunicação", score: 6.2, color: "var(--status-warning)" },
  { label: "Trabalho em Equipe", score: 8.1, color: "var(--status-success)" },
  { label: "Adaptabilidade", score: 7.5, color: "var(--status-success)" },
]

const MOCK_RESPONSES_PREVIEW = [
  {
    competency: "Liderança Técnica",
    score: 8.4,
    question: "Descreva uma situação em que você liderou uma decisão técnica complexa sob pressão.",
    answer: "Lideramos a migração de um monolito para microsserviços em 6 meses sem downtime, coordenando um time de 8 devs.",
  },
  {
    competency: "Resolução de Problemas",
    score: 7.9,
    question: "Como você aborda um bug crítico em produção?",
    answer: "Primeiro isolo o problema com logs e métricas, comunico o status ao time e usuários, aplico hotfix com rollback pronto.",
  },
]

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 7.5
    ? "var(--status-success)"
    : score >= 6.0
      ? "var(--status-warning)"
      : "var(--status-error)"
  return (
    <span style={{ color }} className="text-sm font-bold tabular-nums">
      {score.toFixed(1)}<span style={{ color: "var(--lia-text-disabled)" }} className="text-xs font-normal">/10.0</span>
    </span>
  )
}

function EligibilitySection({ state, qas }: { state: EligibilityState; qas: EligibilityQA[] }) {
  const allMet = state === "approved"
  const [expanded, setExpanded] = useState(!allMet)

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        border: `1px solid ${allMet ? "var(--status-success-border)" : "var(--status-error-border)"}`,
        background: allMet ? "var(--status-success-bg)" : "var(--status-error-bg)",
      }}
    >
      <button
        className="w-full flex items-center justify-between px-4 py-3 transition-colors text-left"
        style={{ background: "transparent" }}
        onMouseEnter={e => (e.currentTarget.style.background = "rgba(0,0,0,0.04)")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
            style={{ background: allMet ? "var(--status-success-bg-15)" : "var(--status-error-bg-15)" }}
          >
            <svg
              className="w-4 h-4"
              style={{ color: allMet ? "var(--status-success)" : "var(--status-error)" }}
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d={allMet
                  ? "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  : "M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                }
              />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold" style={{ color: "var(--lia-text-primary)" }}>
              Pré-triagem — Elegibilidade
            </p>
            <p className="text-xs mt-0.5" style={{ color: allMet ? "var(--status-success)" : "var(--status-error)" }}>
              {allMet
                ? "✅ Todas as perguntas atendidas"
                : "❌ Candidato(a) eliminado(a) nesta fase"}
            </p>
          </div>
        </div>
        <svg
          className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          style={{ color: "var(--lia-text-disabled)" }}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div
          className="divide-y"
          style={{
            borderTop: `1px solid ${allMet ? "var(--status-success-border)" : "var(--status-error-border)"}`,
            borderColor: allMet ? "var(--status-success-border)" : "var(--status-error-border)",
          }}
        >
          {qas.map((qa, i) => (
            <div
              key={i}
              className="px-4 py-3"
              style={{
                background: qa.eliminating ? "var(--status-error-bg-15)" : "transparent",
                borderColor: allMet ? "var(--status-success-border)" : "var(--status-error-border)",
              }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-xs mb-1 leading-relaxed" style={{ color: "var(--lia-text-tertiary)" }}>
                    <span className="font-medium" style={{ color: "var(--lia-text-secondary)" }}>Pergunta:</span>{" "}
                    {qa.question}
                  </p>
                  <p className="text-xs leading-relaxed" style={{ color: "var(--lia-text-secondary)" }}>
                    <span className="font-medium">Resposta:</span> {qa.answer}
                  </p>
                  {qa.reconsideration && (
                    <p
                      className="text-xs italic mt-1.5 pl-2"
                      style={{
                        color: "var(--lia-text-disabled)",
                        borderLeft: `2px solid var(--status-error-border)`,
                      }}
                    >
                      {qa.reconsideration}
                    </p>
                  )}
                </div>
                <div className="flex-shrink-0 mt-0.5">
                  {qa.met ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                      style={{
                        background: "var(--status-success-bg)",
                        color: "var(--status-success)",
                        border: "1px solid var(--status-success-border)",
                      }}
                    >
                      ✅ Atendido
                    </span>
                  ) : (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                      style={{
                        background: "var(--status-error-bg)",
                        color: "var(--status-error)",
                        border: "1px solid var(--status-error-border)",
                      }}
                    >
                      ❌ Não atendido
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function WSIScoresPanel({ dimmed }: { dimmed?: boolean }) {
  return (
    <div
      className={`rounded-xl overflow-hidden transition-opacity ${dimmed ? "opacity-40" : ""}`}
      style={{
        border: "1px solid var(--lia-border-subtle)",
        background: "var(--lia-bg-primary)",
      }}
    >
      <div
        className="px-4 py-3 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--lia-border-subtle)" }}
      >
        <h3 className="text-xs font-semibold flex items-center gap-2" style={{ color: "var(--lia-text-primary)" }}>
          <svg className="w-4 h-4" style={{ color: "var(--wedo-cyan)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Scores WSI por Dimensão
        </h3>
        {dimmed && (
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full"
            style={{
              color: "var(--lia-text-disabled)",
              background: "var(--lia-bg-tertiary)",
              border: "1px solid var(--lia-border-subtle)",
            }}
          >
            N/A
          </span>
        )}
      </div>
      <div className="p-3 space-y-2.5">
        {MOCK_WSI_SCORES.map((s) => (
          <div key={s.label}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs" style={{ color: "var(--lia-text-tertiary)" }}>{s.label}</span>
              <span
                className="text-xs font-bold tabular-nums"
                style={{ color: dimmed ? "var(--lia-text-disabled)" : s.color }}
              >
                {s.score.toFixed(1)}
              </span>
            </div>
            <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "var(--lia-bg-tertiary)" }}>
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${(s.score / 10) * 100}%`,
                  backgroundColor: dimmed ? "var(--lia-border-subtle)" : s.color,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ResponsesSection({ dimmed }: { dimmed?: boolean }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div
      className={`rounded-xl overflow-hidden transition-opacity ${dimmed ? "opacity-40" : ""}`}
      style={{
        border: "1px solid var(--lia-border-subtle)",
        background: "var(--lia-bg-primary)",
      }}
    >
      <button
        className="w-full flex items-center justify-between px-4 py-3 transition-colors text-left"
        style={{ background: "transparent" }}
        onMouseEnter={e => !dimmed && (e.currentTarget.style.background = "var(--lia-interactive-hover)")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
        onClick={() => !dimmed && setExpanded(v => !v)}
      >
        <h3 className="text-xs font-semibold flex items-center gap-2" style={{ color: "var(--lia-text-primary)" }}>
          <svg className="w-4 h-4" style={{ color: "var(--lia-text-disabled)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          Respostas por Competência ({MOCK_RESPONSES_PREVIEW.length})
        </h3>
        <div className="flex items-center gap-2">
          {dimmed && (
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{
                color: "var(--lia-text-disabled)",
                background: "var(--lia-bg-tertiary)",
                border: "1px solid var(--lia-border-subtle)",
              }}
            >
              N/A
            </span>
          )}
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
            style={{ color: "var(--lia-text-disabled)" }}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      {expanded && !dimmed && (
        <div className="divide-y" style={{ borderTop: "1px solid var(--lia-border-subtle)", borderColor: "var(--lia-border-subtle)" }}>
          {MOCK_RESPONSES_PREVIEW.map((r, i) => (
            <div key={i} className="px-4 py-3" style={{ borderColor: "var(--lia-border-subtle)" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium" style={{ color: "var(--lia-text-primary)" }}>{r.competency}</span>
                <ScoreBadge score={r.score} />
              </div>
              <div className="space-y-1">
                <div className="rounded-lg p-2" style={{ background: "var(--lia-bg-secondary)", border: "1px solid var(--lia-border-subtle)" }}>
                  <p className="text-xs uppercase tracking-wide mb-0.5" style={{ color: "var(--lia-text-disabled)" }}>Pergunta</p>
                  <p className="text-xs" style={{ color: "var(--lia-text-tertiary)" }}>{r.question}</p>
                </div>
                <div className="rounded-lg p-2" style={{ background: "var(--lia-bg-primary)", border: "1px solid var(--lia-border-subtle)" }}>
                  <p className="text-xs uppercase tracking-wide mb-0.5" style={{ color: "var(--lia-text-disabled)" }}>Resposta do Candidato</p>
                  <p className="text-xs" style={{ color: "var(--lia-text-secondary)" }}>{r.answer}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function TriagemModalWithEligibility() {
  const [eligibilityState, setEligibilityState] = useState<EligibilityState>("approved")
  const [activeTab, setActiveTab] = useState<"triagem" | "parecer" | "comparativo">("triagem")

  const isEliminated = eligibilityState === "eliminated"
  const overallScore = isEliminated ? null : 7.8
  const currentQAs = isEliminated ? ELIMINATED_QAS : APPROVED_QAS

  const tabs = [
    { key: "triagem" as const, label: "Respostas e Avaliação" },
    { key: "parecer" as const, label: "Parecer e Feedback" },
    { key: "comparativo" as const, label: "Ranking e Comparativo" },
  ]

  return (
    <div
      className="min-h-screen flex items-start justify-center py-8 px-4"
      style={{ background: "var(--lia-bg-tertiary)" }}
    >
      <div className="w-full max-w-2xl">
        {/* ── State toggle ── */}
        <div
          className="mb-4 flex items-center gap-3 rounded-xl p-3"
          style={{
            background: "var(--lia-bg-primary)",
            border: "1px solid var(--lia-border-subtle)",
            boxShadow: "var(--lia-shadow-md)",
          }}
        >
          <span className="text-xs font-medium" style={{ color: "var(--lia-text-tertiary)" }}>Visualizar estado:</span>
          <div className="flex gap-2">
            <button
              onClick={() => setEligibilityState("approved")}
              className="px-3 py-1.5 text-xs font-medium rounded-full transition-colors"
              style={eligibilityState === "approved"
                ? { background: "var(--status-success)", color: "#fff", border: "1px solid var(--status-success)" }
                : { background: "var(--lia-bg-primary)", color: "var(--lia-text-tertiary)", border: "1px solid var(--lia-border-subtle)" }
              }
            >
              ✅ Estado A — Aprovado
            </button>
            <button
              onClick={() => setEligibilityState("eliminated")}
              className="px-3 py-1.5 text-xs font-medium rounded-full transition-colors"
              style={eligibilityState === "eliminated"
                ? { background: "var(--status-error)", color: "#fff", border: "1px solid var(--status-error)" }
                : { background: "var(--lia-bg-primary)", color: "var(--lia-text-tertiary)", border: "1px solid var(--lia-border-subtle)" }
              }
            >
              ❌ Estado B — Eliminado
            </button>
          </div>
        </div>

        {/* ── Modal container ── */}
        <div
          className="w-full max-h-[calc(100vh-120px)] overflow-hidden flex flex-col rounded-xl"
          style={{
            border: "1px solid var(--lia-border-subtle)",
            background: "var(--lia-bg-secondary)",
            boxShadow: "0 20px 40px -8px rgb(0 0 0 / 0.15), 0 8px 16px -4px rgb(0 0 0 / 0.08)",
          }}
        >

          {/* LGPD banner (Estado B only) */}
          {isEliminated && (
            <div
              className="mx-4 mt-3 flex items-start gap-2 rounded-lg px-3 py-2"
              style={{
                border: "1px solid var(--status-warning-border)",
                background: "var(--status-warning-bg)",
              }}
            >
              <svg className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "var(--status-warning)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
              <p className="text-xs leading-relaxed" style={{ color: "var(--lia-text-secondary)" }}>
                <span className="font-semibold">LGPD / EU AI Act:</span> Triagem encerrada na fase de pré-elegibilidade. O candidato pode solicitar revisão da decisão via Central de Privacidade.
              </p>
            </div>
          )}

          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3" style={{ background: "var(--lia-bg-secondary)" }}>
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0"
                style={{ background: "rgba(96,190,209,0.12)" }}
              >
                <svg className="w-4 h-4" style={{ color: "var(--wedo-cyan)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-semibold" style={{ color: "var(--lia-text-primary)" }}>
                  Detalhes da Triagem WSI — {MOCK_CANDIDATE.name}
                </h2>
                <p className="text-xs" style={{ color: "var(--lia-text-tertiary)" }}>
                  {MOCK_CANDIDATE.role} • {MOCK_CANDIDATE.location}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-xl transition-colors"
                style={{
                  color: "var(--lia-text-secondary)",
                  border: "1px solid var(--lia-border-subtle)",
                  background: "var(--lia-bg-secondary)",
                }}
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Exportar
              </button>
              <button
                className="h-7 w-7 flex items-center justify-center rounded-full transition-colors"
                style={{ color: "var(--lia-text-disabled)" }}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Summary bar */}
          <div
            className="px-4 py-2.5"
            style={{ borderBottom: "1px solid var(--lia-border-subtle)", background: "var(--lia-bg-secondary)" }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-5">
                {/* Score WSI */}
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" style={{ color: "var(--wedo-cyan)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <div>
                    <p className="text-xs" style={{ color: "var(--lia-text-disabled)" }}>Score WSI</p>
                    {overallScore != null ? (
                      <p className="text-sm font-bold tabular-nums" style={{ color: "var(--status-success)" }}>
                        {overallScore.toFixed(1)}<span style={{ color: "var(--lia-text-disabled)" }} className="font-normal">/10.0</span>
                      </p>
                    ) : (
                      <p className="text-sm font-bold" style={{ color: "var(--lia-text-disabled)" }}>—</p>
                    )}
                  </div>
                </div>
                {/* Ranking */}
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" style={{ color: "var(--lia-text-disabled)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  <div>
                    <p className="text-xs" style={{ color: "var(--lia-text-disabled)" }}>Ranking</p>
                    <p className="text-sm font-bold" style={{ color: "var(--lia-text-primary)" }}>
                      {isEliminated ? "—" : "#3 de 18"}
                    </p>
                  </div>
                </div>
                {/* Classificação */}
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" style={{ color: "var(--lia-text-disabled)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                  <div>
                    <p className="text-xs" style={{ color: "var(--lia-text-disabled)" }}>Classificação</p>
                    <span
                      className="inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded-full"
                      style={isEliminated
                        ? { background: "var(--status-error-bg)", color: "var(--status-error)", border: "1px solid var(--status-error-border)" }
                        : { background: "var(--status-success-bg)", color: "var(--status-success)", border: "1px solid var(--status-success-border)" }
                      }
                    >
                      {isEliminated ? "Não Elegível" : "Alto"}
                    </span>
                  </div>
                </div>
                {/* Duração */}
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" style={{ color: "var(--lia-text-disabled)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-xs" style={{ color: "var(--lia-text-disabled)" }}>Duração</p>
                    <p className="text-xs font-medium" style={{ color: "var(--lia-text-primary)" }}>
                      {isEliminated ? "4 min" : "28 min"}
                    </p>
                  </div>
                </div>
              </div>
              {/* Decisão badge */}
              <span
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full"
                style={isEliminated
                  ? { background: "var(--status-error-bg)", color: "var(--status-error)", border: "1px solid var(--status-error-border)" }
                  : { background: "var(--status-success-bg)", color: "var(--status-success)", border: "1px solid var(--status-success-border)" }
                }
              >
                {isEliminated ? "Não Aprovado" : "Em Avaliação"}
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div
            className="px-4 py-2"
            style={{ borderBottom: "1px solid var(--lia-border-subtle)" }}
          >
            <div className="flex gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className="px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 rounded-full"
                  style={activeTab === tab.key
                    ? { background: "var(--lia-btn-primary-bg)", color: "var(--lia-btn-primary-text)" }
                    : { color: "var(--lia-text-tertiary)", background: "transparent" }
                  }
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4" style={{ background: "var(--lia-bg-secondary)" }}>
            {activeTab === "triagem" && (
              <div className="space-y-3">
                {/* Banner alerta Estado B */}
                {isEliminated && (
                  <div
                    className="flex items-start gap-2.5 rounded-xl px-4 py-3"
                    style={{
                      border: "1px solid var(--status-error-border)",
                      background: "var(--status-error-bg)",
                    }}
                  >
                    <svg className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "var(--status-error)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                    </svg>
                    <div>
                      <p className="text-xs font-semibold" style={{ color: "var(--status-error)" }}>
                        Triagem encerrada na fase de elegibilidade
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--lia-text-secondary)" }}>
                        O candidato não atendeu ao critério de inglês fluente. As seções de Score WSI e Respostas não foram aplicadas.
                      </p>
                    </div>
                  </div>
                )}

                {/* Seção de elegibilidade — PRIMEIRO elemento; key força remount ao trocar estado */}
                <EligibilitySection
                  key={eligibilityState}
                  state={eligibilityState}
                  qas={currentQAs}
                />

                {/* Scores WSI (dimmed se eliminado) */}
                <WSIScoresPanel dimmed={isEliminated} />

                {/* Respostas (dimmed se eliminado) */}
                <ResponsesSection dimmed={isEliminated} />
              </div>
            )}

            {activeTab === "parecer" && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <svg className="w-10 h-10 mb-3" style={{ color: "var(--lia-border-subtle)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-sm font-medium" style={{ color: "var(--lia-text-tertiary)" }}>Parecer e Feedback</p>
                <p className="text-xs mt-1" style={{ color: "var(--lia-text-disabled)" }}>Conteúdo desta tab não faz parte do escopo deste mockup.</p>
              </div>
            )}

            {activeTab === "comparativo" && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <svg className="w-10 h-10 mb-3" style={{ color: "var(--lia-border-subtle)" }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm font-medium" style={{ color: "var(--lia-text-tertiary)" }}>Ranking e Comparativo</p>
                <p className="text-xs mt-1" style={{ color: "var(--lia-text-disabled)" }}>Conteúdo desta tab não faz parte do escopo deste mockup.</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div
            className="px-4 py-3 flex items-center justify-between"
            style={{
              borderTop: "1px solid var(--lia-border-subtle)",
              background: "var(--lia-bg-secondary)",
            }}
          >
            <p className="text-xs" style={{ color: "var(--lia-text-disabled)" }}>WSI Session · ID: wsi_mock_001</p>
            <div className="flex items-center gap-2">
              <button
                className="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                style={{
                  border: "1px solid var(--status-error-border)",
                  color: "var(--status-error)",
                  background: "transparent",
                }}
              >
                Rejeitar
              </button>
              <button
                className="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                disabled={isEliminated}
                style={isEliminated
                  ? { background: "var(--lia-bg-tertiary)", color: "var(--lia-text-disabled)", cursor: "not-allowed", border: "none" }
                  : { background: "var(--lia-btn-primary-bg)", color: "var(--lia-btn-primary-text)", border: "none" }
                }
              >
                Aprovar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
