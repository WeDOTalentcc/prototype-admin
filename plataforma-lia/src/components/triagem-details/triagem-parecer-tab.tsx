"use client"

import { Progress } from "@/components/ui/progress"
import { Brain, AlertCircle, CheckCircle, AlertTriangle, User, Info, Target, Award, Zap, BookOpen, Mic2, MessageSquare, Loader2, Star, Copy } from "lucide-react"
import { cn } from "@/lib/utils"
import type { WSIResultDetails } from "@/services/lia-api"
import type { F11ReportData } from "./useTriagemDetailsState"
import { dreyfusLabel, sevConfig } from "./useTriagemDetailsState"
import { DreyfusRow } from "./dreyfus-row"

interface TechnicalAnalysis {
  pontos_fortes?: string[]
  gaps?: Array<string | { texto?: string; severidade?: string }>
  evidencias?: string[]
}

interface Recommendation {
  decisao?: string
  justificativa?: string
  proximos_passos?: string[]
}

interface BehavioralTraitValue {
  score?: number
  descricao?: string
  is_critical?: boolean
  expected_pct?: number
  dreyfus_esperado?: number
}

function asTechnicalAnalysis(v: Record<string, unknown>): TechnicalAnalysis {
  return v as TechnicalAnalysis
}

function asRecommendation(v: Record<string, unknown>): Recommendation {
  return v as Recommendation
}

interface TriagemParecerTabProps {
  scores: WSIResultDetails["scores"]
  sessionInfo: WSIResultDetails["session"]
  report: WSIResultDetails["report"]
  feedback: WSIResultDetails["feedback"]
  f11Report: F11ReportData | null
  details: WSIResultDetails
  decisionDisplay: { label: string; icon: React.ElementType; color: string; bg: string }
  isPendingDecision: boolean
  canTriggerFeedback: boolean
  feedbackAlreadySent: boolean
  sendingFeedback: boolean
  feedbackSuccess: boolean
  feedbackError: string | null
  handleSendFeedback: () => void
  bigFiveHint: string | null
  setBigFiveHint: (v: string | null) => void
  copiedFeedback: boolean
  setCopiedFeedback: (v: boolean) => void
}

export function TriagemParecerTab({
  scores, sessionInfo, report, feedback, f11Report, details,
  decisionDisplay, isPendingDecision, canTriggerFeedback, feedbackAlreadySent,
  sendingFeedback, feedbackSuccess, feedbackError, handleSendFeedback,
  bigFiveHint, setBigFiveHint, copiedFeedback, setCopiedFeedback,
}: TriagemParecerTabProps) {
  return (
    <div className="space-y-3">
      {/* Faixa "média baixa" (revisão humana recomendada) — escala WSI 0-10. */}
      {(scores.overall_wsi >= 6.0 && scores.overall_wsi < 7.5) && (
        <div className="rounded-xl border border-status-warning/30 bg-status-warning/10 p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-status-warning" />
            <h3 className="text-sm font-semibold text-status-warning">Pontos de Atenção</h3>
            <span className="ml-auto text-micro bg-status-warning/10 text-status-warning px-2 py-0.5 rounded-full font-medium border border-status-warning/30">Revisão humana recomendada</span>
          </div>
          <ul className="space-y-1.5">{((f11Report?.attention_flags as string[] | undefined) || (report as unknown as { flags?: string[] })?.flags || ["Score WSI dentro da zona de revisão — decisão requer análise do recrutador responsável."]).map((a: string, i: number) => (<li key={`flag-${i}`} className="flex items-start gap-2 text-xs text-status-warning/90"><AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" /> {a}</li>))}</ul>
        </div>
      )}
      {report && (
        <>
          <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
            <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              Sumário Executivo
            </h3>
            <p className="text-xs text-lia-text-secondary leading-relaxed">{report.executive_summary}</p>
          </div>
          {report.technical_analysis && Object.keys(report.technical_analysis).length > 0 && (
            <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
              <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                <Target className="w-4 h-4 text-lia-text-secondary" />
                Análise Técnica
              </h3>
              {(() => {
                const ta = asTechnicalAnalysis(report.technical_analysis)
                return (
                  <>
                    {ta.pontos_fortes && (
                      <div className="mb-2">
                        <p className="text-micro font-medium text-status-success mb-1 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Pontos Fortes:</p>
                        {ta.pontos_fortes.map((p: string, i: number) => (
                          <div key={`pf-${i}`} className="flex items-start gap-1.5 mb-1">
                            <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-status-success" />
                            <p className="text-xs text-lia-text-secondary">{p}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    {ta.gaps && ta.gaps.length > 0 && (
                      <div className="mb-2">
                        <p className="text-micro font-medium text-lia-text-secondary mb-1 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5 text-status-warning" /> Gaps Identificados:</p>
                        <ul className="space-y-2">
                          {ta.gaps.map((g, i: number) => {
                            const gs = typeof g === 'string' ? { texto: g, severidade: 'baixa' } : g
                            const sc = sevConfig[(gs.severidade as keyof typeof sevConfig) || 'baixa']
                            return (
                              <li key={`gap-${i}`} className={`flex items-start gap-2.5 text-xs text-lia-text-secondary rounded-lg border px-3 py-2 ${sc.bg} ${sc.border}`}>
                                <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sc.dot}`} />
                                <span className="flex-1">{gs.texto || String(gs)}</span>
                                <span className={`text-micro font-bold tracking-wider shrink-0 ${sc.color}`}>{sc.label}</span>
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                    )}
                    {ta.evidencias && (
                      <div>
                        <p className="text-micro font-medium text-lia-text-secondary mb-1">Evidências:</p>
                        {ta.evidencias.map((e: string, i: number) => (
                          <div key={`ev-${i}`} className="flex items-start gap-1.5 mb-1">
                            <Zap className="w-3 h-3 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                            <p className="text-xs text-lia-text-secondary">{e}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )
              })()}
            </div>
          )}

          {report.behavioral_analysis && Object.keys(report.behavioral_analysis).length > 0 && (() => {
            const BIG_FIVE_MAP: Record<string, string> = {
              openness:          "Abertura a mudanças",
              conscientiousness: "Organização e disciplina",
              extraversion:      "Sociabilidade",
              agreeableness:     "Cooperação",
              neuroticism:       "Estabilidade emocional",
            }
            const BIG_FIVE_HINT: Record<string, string> = {
              openness:          "Adapta-se a novidades, aprende rápido e lida bem com ambiguidade",
              conscientiousness: "Planejamento, atenção a prazos e execução sistemática",
              extraversion:      "Facilidade para interagir, comunicar e construir relacionamentos",
              agreeableness:     "Disposição para colaborar, ceder e trabalhar bem em equipe",
              neuroticism:       "Mantém calma sob pressão e lida bem com críticas e frustrações",
            }
            const behav = report.behavioral_analysis as Record<string, unknown>
            const oceanData = (behav?.ocean_traits && typeof behav.ocean_traits === "object")
              ? behav.ocean_traits as Record<string, unknown>
              : behav
            const entries = Object.entries(oceanData)
            const isBigFive = entries.some(([k]) => Object.keys(BIG_FIVE_MAP).includes(k))
            if (!isBigFive) {
              return (
                <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                    <User className="w-4 h-4 text-lia-text-secondary" />
                    Análise Comportamental
                  </h3>
                  <div className="space-y-2">
                    {entries.map(([key, val]) => {
                      const traitVal = val as BehavioralTraitValue
                      return (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs text-lia-text-primary capitalize">{key}</span>
                          <span className="text-xs font-bold">{traitVal.score?.toFixed(1)}/5.0</span>
                        </div>
                        <Progress value={((traitVal.score || 0) / 5) * 100} className="h-1.5 mb-1" />
                        <p className="text-micro text-lia-text-secondary">{traitVal.descricao}</p>
                      </div>
                    )})}

                  </div>
                </div>
              )
            }
            const seniority = sessionInfo?.seniority_label || "Sênior"
            return (
              <div className="p-3 border border-lia-border-subtle space-y-4 bg-lia-bg-secondary rounded-lg">
                <div>
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
                    <User className="w-4 h-4 text-lia-text-secondary" />
                    Perfil de Personalidade
                  </h3>
                  <p className="text-micro text-lia-text-secondary mt-0.5">
                    Dimensões <span className="text-lia-text-secondary font-medium">críticas</span> determinam fit de performance e cultura.
                  </p>
                </div>
                <div className="flex items-center gap-4 text-micro text-lia-text-secondary">
                  <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-lia-btn-primary-bg rounded-sm inline-block" /> Candidato</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-lia-interactive-active rounded-sm inline-block border border-lia-border-default" /> Esperado</span>
                </div>
                <div className="space-y-5">
                  {entries.map(([key, val]) => {
                    const traitVal = val as BehavioralTraitValue
                    const traitName = BIG_FIVE_MAP[key] || key
                    const hint = BIG_FIVE_HINT[key] || ""
                    const candidato = Math.round((traitVal.score || 0) / 5 * 100)
                    const vagaEsperado = traitVal.expected_pct ?? 70
                    const dreyfusEsperado = traitVal.dreyfus_esperado ?? 4
                    const dreyfusDemonstrado = Math.round((traitVal.score || 0) * 5 / 5)
                    const status = candidato < vagaEsperado - 20 ? "gap" : candidato > vagaEsperado + 10 ? "acima" : "ok"
                    const showHint = bigFiveHint === key
                    return (
                      <div key={key} className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-medium text-lia-text-primary">{traitName}</span>
                          {traitVal.is_critical && (
                            <span className="text-micro font-semibold px-1.5 py-0.5 rounded-full border text-wedo-purple-text bg-wedo-purple/10 border-wedo-purple/30" aria-live="polite" aria-atomic="true">Crítica para esta vaga</span>
                          )}
                          {status === "gap"   && <span className="text-micro font-bold text-status-warning bg-status-warning/10 px-1.5 py-0.5 rounded-full border border-status-warning/30">⚠️ Diferença</span>}
                          {status === "acima" && <span className="text-micro font-bold text-wedo-cyan-text bg-wedo-cyan/10 px-1.5 py-0.5 rounded-full border border-wedo-cyan/30">↑ Acima</span>}
                          {status === "ok"    && <span className="text-micro font-bold text-status-success bg-status-success/10 px-1.5 py-0.5 rounded-full border border-status-success/30">✓ Alinhado</span>}
                          {hint && (
                            <button className="ml-auto" onClick={() => setBigFiveHint(showHint ? null : key)}>
                              <Info className="w-3 h-3 text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none" />
                            </button>
                          )}
                        </div>
                        {showHint && hint && (
                          <p className="text-xs text-lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-md px-2.5 py-1.5">{hint}</p>
                        )}
                        <div className="relative h-3">
                          <div className="absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full bg-lia-interactive-active border border-lia-border-default" style={{width: `${vagaEsperado}%`}} />
                          <div className={`absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full ${status === "gap" ? "bg-status-warning" : status === "acima" ? "bg-wedo-cyan" : "bg-lia-btn-primary-bg"}`} style={{width: `${candidato}%`}} />
                        </div>
                        <div className="flex items-center justify-between text-micro text-lia-text-secondary">
                          <span>Candidato: <span className="font-semibold text-lia-text-secondary" aria-live="polite" aria-atomic="true">{candidato}%</span></span>
                          <span>Vaga espera: <span className="font-semibold text-lia-text-secondary" aria-live="polite" aria-atomic="true">{vagaEsperado}%</span></span>
                        </div>
                        <DreyfusRow dreyfusEsperado={dreyfusEsperado} dreyfusDemonstrado={dreyfusDemonstrado} senioridade={seniority} />
                      </div>
                    )
                  })}
                </div>
                <p className="text-micro text-lia-text-secondary pt-1 border-t border-lia-border-subtle">
                  Clique em <Info className="w-2.5 h-2.5 inline" /> para entender o que cada dimensão mede.
                </p>
              </div>
            )
          })()}

          {report.recommendation && Object.keys(report.recommendation).length > 0 && (
            <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
              <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                <Award className="w-4 h-4 text-lia-text-secondary" />
                Recomendação
              </h3>
              {(() => {
                const rec = asRecommendation(report.recommendation)
                return (
                  <>
                    <div className="p-2.5 rounded-lg mb-2" style={{backgroundColor: decisionDisplay.bg}}>
                      <p className="text-xs font-semibold" style={{color: decisionDisplay.color}}>{rec.decisao}</p>
                      <p className="text-xs mt-1 text-lia-text-secondary">{rec.justificativa}</p>
                    </div>
                    {rec.proximos_passos && (
                      <div>
                        <p className="text-micro font-medium text-lia-text-secondary mb-1">Próximos Passos:</p>
                        {rec.proximos_passos.map((step: string, i: number) => (
                          <div key={`step-${i}`} className="flex items-center gap-1.5 mb-1">
                            <span className="w-4 h-4 rounded-full bg-lia-interactive-active flex items-center justify-center text-micro font-bold text-lia-text-secondary">{i + 1}</span>
                            <p className="text-xs text-lia-text-secondary">{step}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )
              })()}
            </div>
          )}
        </>
      )}

      {f11Report?.cbi_questions && f11Report.cbi_questions.length > 0 && (
        <div className="p-3 border border-lia-border-subtle space-y-3 bg-lia-bg-secondary rounded-lg">
          <div>
            <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
              <Mic2 className="w-4 h-4 text-lia-text-secondary" /> Perguntas sugeridas para a entrevista
            </h3>
            <p className="text-micro text-lia-text-secondary mt-0.5">
              Geradas com base nos gaps identificados — use na entrevista presencial
            </p>
          </div>
          {f11Report.cbi_questions.map((q: { severity?: string; question?: string; texto?: string; focus?: string; foco?: string }, i: number) => {
            const sev = sevConfig[(q.severity as keyof typeof sevConfig) ?? 'baixa']
            return (
              <div key={`cbi-${i}`} className={`border rounded-lg p-4 space-y-2 ${sev.bg} ${sev.border}`}>
                <p className="text-xs text-lia-text-primary leading-relaxed">"{q.question || q.texto}"</p>
                <div className="flex items-center gap-2">
                  <span className="text-micro text-lia-text-secondary">Foco:</span>
                  <span className="text-micro text-lia-text-secondary font-medium bg-lia-bg-primary border border-lia-border-subtle px-2 py-0.5 rounded-full">{q.focus || q.foco || "Competência comportamental"}</span>
                  <span className={`text-micro font-bold ${sev.color}`}>Gap {sev.label}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
      {isPendingDecision && !!details && (
        <div className="p-3 border border-lia-border-subtle space-y-3 bg-lia-bg-secondary rounded-lg">
          <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary"><BookOpen className="w-4 h-4 text-wedo-cyan-text" /> Feedback para o Candidato</h3>
          <p className="text-xs text-lia-text-secondary italic" aria-live="polite" aria-atomic="true">Aguardando decisão do recrutador para liberar feedback ao candidato.</p>
          <div className="bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3"><p className="text-micro text-lia-text-secondary font-medium mb-0.5">Prévia do feedback (rascunho)</p><p className="text-xs text-lia-text-secondary">Agradecemos sua participação na triagem. Suas respostas foram analisadas e entraremos em contato em breve com o próximo passo do processo.</p></div>
        </div>
      )}

      {canTriggerFeedback && (
        <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
          <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
            <MessageSquare className="w-4 h-4 text-wedo-cyan" />
            Envio de Feedback Automático
          </h3>
          <p className="text-xs text-lia-text-secondary mb-3" aria-live="polite" aria-atomic="true">
            O candidato obteve classificação "{scores.classification}" e pode receber feedback construtivo automaticamente.
          </p>
          {feedbackSuccess && (
            <div className="flex items-center gap-2 p-2 mb-3 rounded-lg bg-status-success/[0.08] border border-status-success/20">
              <CheckCircle className="w-4 h-4 text-status-success" />
              <span className="text-xs font-medium text-status-success">Feedback enviado com sucesso</span>
            </div>
          )}
          {feedbackError && (
            <div className="flex items-center gap-2 p-2 mb-3 rounded-lg bg-status-error/[0.08] border border-status-error/20">
              <AlertCircle className="w-4 h-4 text-status-error" />
              <span className="text-xs font-medium text-status-error">{feedbackError}</span>
            </div>
          )}
          <button
            onClick={handleSendFeedback}
            disabled={sendingFeedback || feedbackAlreadySent}
            className={cn("flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-md transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed", feedbackAlreadySent ? "bg-lia-interactive-active text-lia-text-secondary" : "bg-lia-btn-primary-bg text-lia-btn-primary-text")}
          >
            {sendingFeedback ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> Enviando...</>
            ) : feedbackAlreadySent ? (
              <><CheckCircle className="w-3.5 h-3.5" /> Feedback já Enviado</>
            ) : (
              <><MessageSquare className="w-3.5 h-3.5" /> Enviar Feedback ao Candidato</>
            )}
          </button>
        </div>
      )}

      {(feedback || (f11Report?.response_analyses && f11Report.response_analyses.length > 0)) && (
        <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
              <BookOpen className="w-4 h-4 text-wedo-cyan-dark" />
              Feedback para o Candidato
            </h3>
            <button
              onClick={() => {
                const f11Feedback = f11Report?.response_analyses?.map((a: { feedback?: string }) => a.feedback).filter(Boolean) || []
                const text = [
                  ...(feedback ? [
                    feedback.main_message,
                    ...(feedback.technical_strengths || []),
                    ...(feedback.behavioral_strengths || []),
                    ...(feedback.development_opportunities || []),
                    feedback.personalized_tip || '',
                    feedback.next_steps || '',
                  ] : []),
                  ...(f11Feedback.length > 0 ? (feedback ? ['', '--- Avaliação detalhada ---'] : []).concat(f11Feedback.filter((x): x is string => Boolean(x))) : []),
                ].filter(Boolean).join('\n')
                navigator.clipboard.writeText(text)
                setCopiedFeedback(true)
                setTimeout(() => setCopiedFeedback(false), 2000)
              }}
              className="flex items-center gap-1 px-2 py-1 text-micro font-medium text-lia-text-secondary hover:text-lia-text-secondary border border-lia-border-subtle rounded-xl hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            >
              {copiedFeedback ? <CheckCircle className="w-3 h-3 text-status-success" /> : <Copy className="w-3 h-3" />}
              {copiedFeedback ? "Copiado!" : "Copiar feedback"}
            </button>
          </div>
          {feedback?.main_message && (
            <p className="text-xs text-lia-text-secondary leading-relaxed mb-3">{feedback.main_message}</p>
          )}
          {!feedback && f11Report?.response_analyses && (
            <div className="mb-3 space-y-1">
              {f11Report.response_analyses.slice(0, 3).map((a: { feedback?: string }, i: number) => (
                a.feedback && (
                  <p key={i} className="text-xs text-lia-text-secondary leading-relaxed">{a.feedback}</p>
                )
              ))}
            </div>
          )}
          {feedback?.technical_strengths && feedback.technical_strengths.length > 0 && (
            <div className="mb-2">
              <p className="text-micro font-medium text-lia-text-secondary mb-1">Pontos Fortes Técnicos:</p>
              {feedback.technical_strengths.map((s: string, i: number) => (
                <div key={`ts-${i}`} className="flex items-start gap-1.5 mb-0.5">
                  <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-status-success" />
                  <p className="text-xs text-lia-text-secondary">{s}</p>
                </div>
              ))}
            </div>
          )}
          {feedback?.behavioral_strengths && feedback.behavioral_strengths.length > 0 && (
            <div className="mb-2">
              <p className="text-micro font-medium text-lia-text-secondary mb-1">Pontos Fortes Comportamentais:</p>
              {feedback.behavioral_strengths.map((s: string, i: number) => (
                <div key={`bs-${i}`} className="flex items-start gap-1.5 mb-0.5">
                  <Star className="w-3 h-3 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
                  <p className="text-xs text-lia-text-secondary">{s}</p>
                </div>
              ))}
            </div>
          )}
          {feedback?.development_opportunities && feedback.development_opportunities.length > 0 && (
            <div className="mb-2">
              <p className="text-micro font-medium text-lia-text-secondary mb-1">Oportunidades de Desenvolvimento:</p>
              {feedback.development_opportunities.map((d: string, i: number) => (
                <div key={`dev-${i}`} className="flex items-start gap-1.5 mb-0.5">
                  <BookOpen className="w-3 h-3 mt-0.5 flex-shrink-0 text-wedo-cyan-dark" />
                  <p className="text-xs text-lia-text-secondary">{d}</p>
                </div>
              ))}
            </div>
          )}
          {feedback?.personalized_tip && (
            <div className="p-2 rounded-lg mt-2 bg-wedo-cyan/[0.08] border border-wedo-cyan/20">
              <p className="text-micro font-medium mb-0.5 text-lia-text-secondary">Dica Personalizada</p>
              <p className="text-xs text-lia-text-secondary">{feedback.personalized_tip}</p>
            </div>
          )}
          {feedback?.next_steps && (
            <div className="mt-2 p-2 rounded-lg bg-lia-bg-tertiary">
              <p className="text-micro font-medium text-lia-text-secondary mb-0.5">Próximos Passos:</p>
              <p className="text-xs text-lia-text-secondary">{feedback.next_steps}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
