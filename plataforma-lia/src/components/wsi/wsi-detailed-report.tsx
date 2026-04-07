"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  ChevronDown, ChevronUp, CheckCircle, AlertTriangle, XCircle,
  Target, Clock, Trophy, BarChart3, Star, ShieldAlert, Layers,
  Mic, Mic2, BookOpen, Zap, Info, AlertCircle, Loader2
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import type { WSIResultDetails } from "@/services/lia-api/types/wsi.types"

interface WSIDetailedReportProps {
  resultId: string
  candidateName?: string
  candidateTitle?: string
  onApprove?: (resultId: string) => void
  onReject?: (resultId: string) => void
  onRequestReview?: (resultId: string) => void
}

type TabKey = "respostas" | "parecer" | "ranking"

const TABS: { key: TabKey; label: string }[] = [
  { key: "respostas", label: "Respostas e Avaliação" },
  { key: "parecer", label: "Parecer e Feedback" },
  { key: "ranking", label: "Ranking e Comparativo" },
]

const severidadeConfig = {
  alta: { label: "ALTA", color: "text-status-error", bg: "bg-status-error/10", border: "border-status-error/30", dot: "bg-status-error" },
  media: { label: "MÉDIA", color: "text-status-warning", bg: "bg-status-warning/10", border: "border-status-warning/30", dot: "bg-status-warning" },
  baixa: { label: "BAIXA", color: "text-lia-text-tertiary", bg: "bg-lia-bg-secondary", border: "border-lia-border-subtle", dot: "bg-lia-text-tertiary" },
}

const gapConfig = {
  ok: { label: "Alinhado", icon: CheckCircle, color: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" },
  aligned: { label: "Alinhado", icon: CheckCircle, color: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" },
  acima: { label: "Acima do esperado", icon: Star, color: "text-wedo-cyan-dark", bg: "bg-wedo-cyan/10", border: "border-wedo-cyan/30" },
  above: { label: "Acima do esperado", icon: Star, color: "text-wedo-cyan-dark", bg: "bg-wedo-cyan/10", border: "border-wedo-cyan/30" },
  gap: { label: "Gap identificado", icon: AlertTriangle, color: "text-status-warning", bg: "bg-status-warning/10", border: "border-status-warning/30" },
  below: { label: "Gap identificado", icon: AlertTriangle, color: "text-status-warning", bg: "bg-status-warning/10", border: "border-status-warning/30" },
  critical_gap: { label: "Gap crítico", icon: XCircle, color: "text-status-error", bg: "bg-status-error/10", border: "border-status-error/30" },
}

function getClassificacao(score: number): { label: string; color: string } {
  if (score >= 4.5) return { label: "Excepcional", color: "text-status-success" }
  if (score >= 4.0) return { label: "Excelente", color: "text-status-success" }
  if (score >= 3.5) return { label: "Alto", color: "text-wedo-cyan-dark" }
  if (score >= 3.0) return { label: "Médio", color: "text-status-warning" }
  if (score >= 2.25) return { label: "Abaixo da média", color: "text-wedo-orange" }
  return { label: "Regular / Baixo", color: "text-status-error" }
}

function getDecisionConfig(decision?: string) {
  switch (decision) {
    case "approve":
    case "approved":
      return { label: "Aprovado", badge: "bg-status-success/15 text-status-success", confidence: "Alta confiança" }
    case "reject":
    case "rejected":
      return { label: "Reprovado", badge: "bg-status-error/15 text-status-error", confidence: "" }
    default:
      return { label: "Revisão Necessária", badge: "bg-status-warning/15 text-status-warning", confidence: "Revisão recomendada" }
  }
}

const dreyfusLabel = (n?: number) => {
  if (n == null) return "—"
  return ["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"][n] ?? String(n)
}

const bloomLabel = (n?: number) => {
  if (n == null) return "—"
  return ["", "Recordar", "Compreender", "Aplicar", "Analisar", "Avaliar"][n] ?? String(n)
}

const starComponents = [
  { key: "S", label: "Situação", desc: "Contexto descrito" },
  { key: "T", label: "Tarefa", desc: "Objetivo claro" },
  { key: "A", label: "Ação", desc: "O que foi feito" },
  { key: "R", label: "Resultado", desc: "Impacto mensurável" },
]

function ReportHeader({ data, candidateName, candidateTitle }: { data: WSIResultDetails; candidateName?: string; candidateTitle?: string }) {
  const scores = data.scores
  const session = data.session
  const classificacao = getClassificacao(scores.overall_wsi)
  const decision = getDecisionConfig(scores.decision)

  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-wedo-cyan/15 flex items-center justify-center">
            <Target className="w-5 h-5 text-wedo-cyan" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-lia-text-primary">
              Detalhes da Triagem WSI — {candidateName || "Candidato"}
            </h1>
            {candidateTitle && (
              <p className="text-xs text-lia-text-tertiary">{candidateTitle}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={`${decision.badge} text-xs font-medium px-3 py-1 rounded-full`}>
            {scores.decision === "approve" || scores.decision === "approved" ? (
              <><CheckCircle className="w-3.5 h-3.5 mr-1" />{decision.label}</>
            ) : (
              <><Clock className="w-3.5 h-3.5 mr-1" />{decision.label}</>
            )}
          </Badge>
          {decision.confidence && (
            <span className="text-[10px] font-medium text-lia-text-tertiary bg-lia-bg-secondary border border-lia-border-subtle px-2 py-0.5 rounded-full">
              {decision.confidence}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-6 text-sm flex-wrap">
        <div>
          <p className="text-xs text-lia-text-tertiary">Score WSI</p>
          <p className="font-bold text-lia-text-primary">
            {scores.overall_wsi.toFixed(1)}
            <span className="text-lia-text-tertiary font-normal">/5.0</span>
          </p>
        </div>
        {scores.percentile != null && (
          <div>
            <p className="text-xs text-lia-text-tertiary">Ranking</p>
            <p className="font-semibold text-lia-text-primary flex items-center gap-1">
              <Trophy className="w-3.5 h-3.5 text-status-warning" />
              Top {scores.percentile}%
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-lia-text-tertiary">Classificação</p>
          <p className={`font-semibold ${classificacao.color}`}>{classificacao.label}</p>
        </div>
        {session.duration_minutes != null && (
          <div>
            <p className="text-xs text-lia-text-tertiary">Duração</p>
            <p className="font-semibold text-lia-text-primary flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />{session.duration_minutes} min
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-lia-text-tertiary">Modo de triagem</p>
          <p className="font-semibold text-lia-text-secondary flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-lia-text-tertiary" />
            {session.screening_type === "voice" ? "Voz" : "Texto"} · {session.mode === "compact" ? "Compact" : "Compact+"} · {data.responses.length} perguntas
          </p>
        </div>
      </div>
    </div>
  )
}

function ScoresByDimension({ data }: { data: WSIResultDetails }) {
  const scores = data.scores
  const session = data.session
  const dims = [
    { label: "Geral", value: scores.overall_wsi, pct: Math.round((scores.overall_wsi / 5) * 100) },
    { label: "Comp. Técnicas", value: scores.technical_wsi, pct: Math.round((scores.technical_wsi / 5) * 100) },
    { label: "Comp. Comportamentais", value: scores.behavioral_wsi, pct: Math.round((scores.behavioral_wsi / 5) * 100) },
  ]

  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
      <h2 className="text-sm font-semibold text-lia-text-secondary flex items-center gap-2 mb-4">
        <BarChart3 className="w-4 h-4" /> Scores por Dimensão
      </h2>
      <div className="grid grid-cols-3 gap-4">
        {dims.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-3xl font-bold text-lia-text-primary">{s.value.toFixed(1)}</p>
            <p className="text-xs text-lia-text-tertiary mb-2">{s.label} ({s.pct}%)</p>
            <div className="h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
              <div className="h-full bg-lia-text-primary rounded-full transition-all" style={{ width: `${s.pct}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-lia-border-subtle space-y-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-xs text-lia-text-tertiary bg-lia-bg-secondary px-2 py-1 rounded-full">
            {session.screening_type === "voice" ? <Mic className="w-3 h-3" /> : <Target className="w-3 h-3" />}
            {session.screening_type === "voice" ? "Triagem por Voz" : "Triagem por Texto"}
          </span>
          {scores.percentile != null && (
            <span className="text-xs text-lia-text-tertiary">Top {scores.percentile}%</span>
          )}
          {session.completed_at && (
            <span className="text-xs text-lia-text-tertiary">
              {new Date(session.completed_at).toLocaleDateString("pt-BR")}
            </span>
          )}
        </div>
        {session.seniority_label && (
          <div className="flex items-center gap-1.5 text-[11px] text-lia-text-tertiary bg-lia-bg-secondary border border-lia-border-subtle rounded-lg px-3 py-2">
            <BarChart3 className="w-3 h-3 text-lia-text-tertiary shrink-0" />
            <span>
              Para <span className="font-medium text-lia-text-secondary">{session.seniority_label}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function ResponseCard({ response, index, isOpen, onToggle }: {
  response: WSIResultDetails["responses"][0]
  index: number
  isOpen: boolean
  onToggle: () => void
}) {
  const gapKey = (response.gap_status || "ok") as keyof typeof gapConfig
  const gap = gapConfig[gapKey] || gapConfig.ok
  const GapIcon = gap.icon
  const starData = (response.star || response.scores.star || {}) as Record<string, boolean>
  const scoreColor = response.scores.final_score >= 4.5 ? "text-status-success" : response.scores.final_score >= 3.5 ? "text-status-warning" : "text-status-error"

  return (
    <div>
      <button
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-bg-secondary transition-colors text-left"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-lia-text-primary">{response.competency}</span>
          <span className="text-[10px] bg-lia-bg-secondary text-lia-text-tertiary px-2 py-0.5 rounded-full">
            {response.question.framework}
          </span>
          {response.is_critical && (
            <span className="flex items-center gap-0.5 text-[10px] font-bold text-status-error bg-status-error/10 border border-status-error/30 px-1.5 py-0.5 rounded-full">
              <ShieldAlert className="w-2.5 h-2.5" /> Crítica
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold ${scoreColor}`}>
            {response.scores.final_score.toFixed(1)}/5.0
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" /> : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-4 pb-4 space-y-4 bg-lia-bg-secondary/50">
          <div className="space-y-2">
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-1">Pergunta</p>
              <p className="text-xs text-lia-text-secondary leading-relaxed">{response.question.text}</p>
            </div>
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-1">Resposta do Candidato</p>
              <p className="text-xs text-lia-text-primary leading-relaxed">{response.response_text}</p>
            </div>
          </div>

          {Object.keys(starData).length > 0 && (
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-2">Qualidade da resposta (STAR)</p>
              <div className="flex items-center gap-2 flex-wrap">
                {starComponents.map(({ key, label, desc }) => {
                  const present = !!starData[key]
                  return (
                    <div
                      key={key}
                      title={desc}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                        present
                          ? "bg-status-success/10 border-status-success/30 text-status-success"
                          : "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-tertiary"
                      }`}
                    >
                      {present
                        ? <CheckCircle className="w-3 h-3" />
                        : <span className="w-3 h-3 flex items-center justify-center text-lia-text-tertiary font-bold text-[10px]">–</span>}
                      <span>{label}</span>
                    </div>
                  )
                })}
                {!starData.R && (
                  <span className="text-[10px] text-status-warning bg-status-warning/10 border border-status-warning/30 px-2 py-0.5 rounded-full">
                    Resultado não evidenciado
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-4 gap-2">
            {[
              { label: "Autodeclaração", value: response.scores.autodeclaration?.toFixed(1) ?? "—" },
              { label: "Contexto", value: response.scores.context?.toFixed(1) ?? "—" },
              { label: "Bloom", value: bloomLabel(response.scores.bloom_level), sub: response.scores.bloom_level ? `Nível ${response.scores.bloom_level}` : undefined },
              { label: "Dreyfus", value: dreyfusLabel(response.scores.dreyfus_level), sub: response.scores.dreyfus_level ? `Nível ${response.scores.dreyfus_level}` : undefined },
            ].map((s) => (
              <div key={s.label} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-2 text-center">
                <p className="text-[9px] text-lia-text-tertiary mb-1">{s.label}</p>
                <p className="text-sm font-bold text-lia-text-primary">{s.value}</p>
              </div>
            ))}
          </div>

          <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
            <div className="flex items-center gap-2">
              <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
              <span className={`text-xs font-medium ${gap.color}`}>Esperado pela vaga</span>
            </div>
            <div className="flex items-center gap-4 text-xs">
              {response.bloom_expected != null && (
                <div className="text-right">
                  <p className="text-[9px] text-lia-text-tertiary">Bloom</p>
                  <p className={`font-semibold ${gap.color}`}>{bloomLabel(response.bloom_expected)}</p>
                </div>
              )}
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                {gap.label}
              </span>
            </div>
          </div>

          {response.evidences.length > 0 && (
            <div>
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-2">Evidências</p>
              <div className="flex flex-wrap gap-2">
                {response.evidences.map((e, j) => (
                  <span key={j} className="flex items-center gap-1 text-[11px] bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle text-lia-text-secondary px-2 py-1 rounded-full">
                    <CheckCircle className="w-3 h-3 text-status-success" /> {e}
                  </span>
                ))}
              </div>
              <p className="text-xs text-lia-text-tertiary italic mt-2">{response.justification}</p>
            </div>
          )}

          {response.red_flags.length > 0 && (
            <div>
              <p className="text-[10px] text-status-error uppercase tracking-wide mb-2">Red Flags</p>
              <div className="flex flex-wrap gap-2">
                {response.red_flags.map((rf, j) => (
                  <span key={j} className="flex items-center gap-1 text-[11px] bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1 rounded-full">
                    <AlertTriangle className="w-3 h-3" /> {rf}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TabRespostas({ data }: { data: WSIResultDetails }) {
  const [expanded, setExpanded] = useState<number | null>(0)

  return (
    <div className="space-y-4">
      <ScoresByDimension data={data} />

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl shadow-lia-sm overflow-hidden">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-sm font-semibold text-lia-text-secondary">Respostas por Competência ({data.responses.length})</h2>
          <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
        </div>

        <div className="divide-y divide-lia-border-subtle">
          {data.responses.map((r, i) => (
            <ResponseCard
              key={i}
              response={r}
              index={i}
              isOpen={expanded === i}
              onToggle={() => setExpanded(expanded === i ? null : i)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function TabParecer({ data }: { data: WSIResultDetails }) {
  const report = data.report
  const feedback = data.feedback
  const isApproved = data.scores.decision === "approve" || data.scores.decision === "approved"
  const isPending = !isApproved && data.scores.decision !== "reject" && data.scores.decision !== "rejected"

  const strengths = (report?.technical_analysis as { strengths?: string[] })?.strengths || feedback?.technical_strengths || []
  const gaps = (report?.technical_analysis as { gaps?: { text: string; severity: string }[] })?.gaps || []
  const concerns = (report?.recommendation as { concerns?: string[] })?.concerns || []

  return (
    <div className="space-y-4">
      {report?.executive_summary && (
        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
          <h2 className="text-sm font-semibold text-lia-text-secondary mb-3 flex items-center gap-2">
            <Star className="w-4 h-4 text-status-warning" /> Sumário Executivo
          </h2>
          <p className="text-sm text-lia-text-secondary leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {concerns.length > 0 && isPending && (
        <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl p-4 shadow-lia-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-status-warning" />
            <h2 className="text-sm font-semibold text-status-warning">Pontos de Atenção</h2>
            <span className="ml-auto text-[10px] bg-status-warning/15 text-status-warning px-2 py-0.5 rounded-full font-medium border border-status-warning/30">
              Revisão humana recomendada
            </span>
          </div>
          <ul className="space-y-1.5">
            {concerns.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                <AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" /> {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm space-y-4">
        <h2 className="text-sm font-semibold text-lia-text-secondary">Análise Técnica</h2>

        {strengths.length > 0 && (
          <div>
            <p className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> Pontos Fortes
            </p>
            <ul className="space-y-1.5">
              {strengths.map((s: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success mt-0.5 shrink-0" /> {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {gaps.length > 0 && (
          <div>
            <p className="text-xs font-medium text-lia-text-secondary mb-2 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-status-warning" /> Gaps Identificados
            </p>
            <ul className="space-y-2">
              {gaps.map((g: { text: string; severity: string }, i: number) => {
                const sev = severidadeConfig[(g.severity || "baixa") as keyof typeof severidadeConfig] || severidadeConfig.baixa
                return (
                  <li key={i} className={`flex items-start gap-2.5 text-xs text-lia-text-secondary rounded-lg border px-3 py-2 ${sev.bg} ${sev.border}`}>
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sev.dot}`} />
                    <span className="flex-1">{g.text}</span>
                    <span className={`text-[9px] font-bold tracking-wider shrink-0 ${sev.color}`}>{sev.label}</span>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </div>

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
        <h2 className="text-sm font-semibold text-lia-text-secondary mb-3">Recomendação</h2>
        {isApproved ? (
          <div className="bg-status-success/10 border border-status-success/30 rounded-lg p-4">
            <p className="text-sm font-semibold text-status-success mb-1">Fortemente Recomendado</p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {(report?.recommendation as { text?: string })?.text ||
                "Perfil alinhado com os requisitos da posição. Recomendamos avançar para a próxima etapa."}
            </p>
          </div>
        ) : (
          <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-4">
            <p className="text-sm font-semibold text-status-warning mb-1">Revisão Humana Recomendada</p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {(report?.recommendation as { text?: string })?.text ||
                "O perfil demonstrado precisa de avaliação adicional antes de uma decisão."}
            </p>
          </div>
        )}
      </div>

      {feedback && (
        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm space-y-4">
          <h2 className="text-sm font-semibold text-lia-text-secondary flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-wedo-cyan" /> Feedback para o Candidato
          </h2>
          {feedback.main_message && (
            <p className="text-xs text-lia-text-secondary leading-relaxed">{feedback.main_message}</p>
          )}
          {feedback.technical_strengths.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">Pontos Fortes Técnicos:</p>
              {feedback.technical_strengths.map((s, i) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-lia-text-secondary mb-1">
                  <CheckCircle className="w-3 h-3 text-status-success shrink-0" /> {s}
                </p>
              ))}
            </div>
          )}
          {feedback.development_opportunities.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">Oportunidades de Desenvolvimento:</p>
              {feedback.development_opportunities.map((s, i) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-lia-text-secondary mb-1">
                  <BookOpen className="w-3 h-3 text-wedo-cyan shrink-0" /> {s}
                </p>
              ))}
            </div>
          )}
          {feedback.personalized_tip && (
            <div className="bg-wedo-cyan/10 border border-wedo-cyan/30 rounded-lg p-3">
              <p className="text-[10px] text-wedo-cyan font-medium mb-0.5">Dica Personalizada</p>
              <p className="text-xs text-lia-text-secondary">{feedback.personalized_tip}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TabRanking() {
  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-8 shadow-lia-sm text-center">
      <BarChart3 className="w-10 h-10 text-lia-text-tertiary mx-auto mb-3" />
      <h3 className="text-sm font-semibold text-lia-text-secondary mb-1">Ranking e Comparativo</h3>
      <p className="text-xs text-lia-text-tertiary">
        A visualização de ranking comparativo entre candidatos será exibida aqui quando disponível.
      </p>
    </div>
  )
}

export function WSIDetailedReport({
  resultId,
  candidateName,
  candidateTitle,
  onApprove,
  onReject,
  onRequestReview,
}: WSIDetailedReportProps) {
  const [activeTab, setActiveTab] = useState<TabKey>("respostas")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<WSIResultDetails | null>(null)

  useEffect(() => {
    loadDetails()
  }, [resultId])

  const loadDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await liaApi.wsiGetResultDetails(resultId)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar detalhes")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className="ml-2 text-sm text-lia-text-tertiary">Carregando relatório...</span>
      </div>
    )
  }

  if (error || !data) {
    return (
      <Card className="border-status-error/30">
        <CardContent className="py-6 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-status-error" />
          <span className="ml-2 text-sm text-status-error">{error || "Dados não encontrados"}</span>
        </CardContent>
      </Card>
    )
  }

  const isApproved = data.scores.decision === "approve" || data.scores.decision === "approved"
  const isRejected = data.scores.decision === "reject" || data.scores.decision === "rejected"

  return (
    <div className="max-w-[820px] mx-auto space-y-4">
      <ReportHeader data={data} candidateName={candidateName} candidateTitle={candidateTitle} />

      <div className="flex gap-1 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ? "bg-lia-text-primary text-lia-bg-primary"
                : "text-lia-text-tertiary hover:bg-lia-bg-secondary"
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "respostas" && <TabRespostas data={data} />}
      {activeTab === "parecer" && <TabParecer data={data} />}
      {activeTab === "ranking" && <TabRanking />}

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-4 flex items-center justify-between shadow-lia-sm">
        <span className="text-xs text-lia-text-tertiary">Decisão do Recrutador</span>
        <div className="flex gap-2">
          {onReject && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs border-status-error/30 text-status-error hover:bg-status-error/10"
              onClick={() => onReject(resultId)}
            >
              <XCircle className="w-3.5 h-3.5 mr-1" /> Reprovar
            </Button>
          )}
          {onRequestReview && !isApproved && !isRejected && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs border-status-warning/30 text-status-warning hover:bg-status-warning/10"
              onClick={() => onRequestReview(resultId)}
            >
              <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Solicitar Revisão
            </Button>
          )}
          {onApprove && (
            <Button
              size="sm"
              className="text-xs bg-lia-text-primary text-lia-bg-primary hover:bg-lia-text-secondary"
              onClick={() => onApprove(resultId)}
            >
              <CheckCircle className="w-3.5 h-3.5 mr-1" /> Aprovar para Entrevista
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
