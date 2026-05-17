"use client"

/**
 * JDScoresComparison — Task #1158
 *
 * Mockup com baseline + 3 variantes do painel de scores do JD.
 *
 * IMPORTANTE: este arquivo é uma EXTRAÇÃO ADAPTADA dos componentes reais de
 * produção (`plataforma-lia/src/components/wsi/jd-evaluation/`), NÃO uma
 * reimplementação visual. O JSX dos blocos `HeaderReal` e `CriteriaReal`
 * abaixo é cópia literal de `JDEvaluationHeader.tsx` e `JDEvalCriteriaList.tsx`
 * — a única transformação é a substituição dos tokens CSS proprietários
 * (`lia-*`, `wedo-*`, `status-*`, `text-base-ui`, `text-micro`) por classes
 * equivalentes do tema padrão do sandbox (slate/emerald/amber/red/indigo).
 *
 * Tabela de substituição usada (preserva semântica de cor/hierarquia):
 *   lia-bg-primary       → white                lia-bg-secondary    → slate-50
 *   lia-bg-tertiary      → slate-100            lia-text-primary    → slate-900
 *   lia-text-secondary   → slate-600            lia-text-tertiary   → slate-500
 *   lia-text-disabled    → slate-400            lia-border-subtle   → slate-200
 *   lia-border-default   → slate-300            lia-interactive-hover→slate-100
 *   lia-btn-primary-bg   → indigo-600           status-success      → emerald-600
 *   status-warning       → amber-600            status-error        → red-600
 *   wedo-orange          → orange-500           wedo-cyan           → cyan-500
 *   text-base-ui         → text-sm              text-micro          → text-[11px]
 *
 * As variantes A/B/C envolvem (não substituem) `HeaderReal` + `CriteriaReal`,
 * adicionando apenas as mudanças cirúrgicas propostas. Quando o usuário
 * escolher uma variante, basta replicar essas mudanças nos componentes reais.
 */

import React, { useMemo, useState } from "react"
import {
  FileText, ChevronUp, Pencil, XCircle,
  Brain, CheckCircle, Info, ArrowRight, Sparkles,
} from "lucide-react"

// ---------------------------------------------------------------------------
// cn — réplica de plataforma-lia/src/lib/utils.ts (sem dependências externas)
// ---------------------------------------------------------------------------
function cn(...inputs: Array<string | false | null | undefined>): string {
  return inputs.filter(Boolean).join(" ")
}

// ---------------------------------------------------------------------------
// Tipos — espelham `JDEvaluationData` de useJDEvaluation.ts
// ---------------------------------------------------------------------------
type Status = "sufficient" | "partial" | "insufficient"
interface JDIndicator {
  dimension?: string
  label: string
  weight?: number
  earned?: number
  status: Status
  detail?: string
  count?: number
}
interface JDEvaluationData {
  score: number
  band?: string
  band_label?: string
  lia_suggestion?: string
  can_generate?: boolean
  indicators: JDIndicator[]
}

// ---------------------------------------------------------------------------
// SEED — cenário do screenshot: score 90, D5 "Consistência de senioridade"
// partial; demais sufficient. Mesmas weights/earned do contrato /wsi/jd-evaluate.
// ---------------------------------------------------------------------------
const SEED: JDEvaluationData = {
  score: 90,
  band: "excelente",
  band_label: "Excelente",
  can_generate: true,
  lia_suggestion:
    "Vaga bem estruturada. Para subir de 90 para 100, reforce a consistência de senioridade entre título, anos de experiência e escopo das responsabilidades.",
  indicators: [
    { dimension: "D1", label: "Título objetivo",            weight: 10, earned: 10, status: "sufficient" },
    { dimension: "D2", label: "Sumário/Propósito",          weight: 10, earned: 10, status: "sufficient" },
    { dimension: "D3", label: "Responsabilidades claras",   weight: 15, earned: 15, status: "sufficient" },
    { dimension: "D4", label: "Comp. técnicas alinhadas",   weight: 15, earned: 15, status: "sufficient" },
    { dimension: "D5", label: "Consistência de senioridade",weight: 15, earned: 7,  status: "partial",
      detail: "Título 'Pleno' mas escopo de responsabilidades sugere Sênior. Anos de experiência não declarados." },
    { dimension: "D6", label: "Comp. comportamentais",      weight: 10, earned: 10, status: "sufficient" },
    { dimension: "D7", label: "Contexto da empresa",        weight: 10, earned: 10, status: "sufficient" },
    { dimension: "D8", label: "Linguagem inclusiva",        weight: 10, earned: 10, status: "sufficient" },
    { dimension: "D9", label: "Benefícios/Modelo trabalho", weight: 5,  earned: 3,  status: "sufficient" },
  ],
}

// ---------------------------------------------------------------------------
// Dicionário estático D1–D9 (proposto para virar campo `definition` no backend
// — ver report `docs/research/jd-scores-redesign.md` §3). Hoje não existe.
// ---------------------------------------------------------------------------
const DIM_DEFS: Record<string, { what: string; how: string }> = {
  D1: { what: "O título da vaga é específico, comum no mercado e sem jargão interno.",
        how:  "Use formato '<Cargo> <Senioridade>'. Evite siglas internas ou inventadas." },
  D2: { what: "Existe um sumário curto explicando propósito da vaga e impacto no negócio.",
        how:  "Adicione 2–3 frases sobre por que a vaga existe e o que essa pessoa vai destravar." },
  D3: { what: "Responsabilidades são entregáveis observáveis, não tarefas vagas.",
        how:  "Reescreva começando por verbo no infinitivo + objeto + critério de sucesso." },
  D4: { what: "Competências técnicas estão amarradas às responsabilidades.",
        how:  "Para cada responsabilidade, liste 1–2 skills técnicas obrigatórias." },
  D5: { what: "Título, anos de experiência e escopo das responsabilidades batem entre si.",
        how:  "Se título é 'Pleno', escopo não deve incluir liderança técnica de outros sêniores. Declare anos de experiência esperados." },
  D6: { what: "Competências comportamentais estão presentes e alinhadas ao contexto.",
        how:  "Inclua 3–5 comportamentais com exemplos de situação esperada." },
  D7: { what: "Há contexto da empresa: setor, estágio, time, cultura.",
        how:  "1 parágrafo sobre setor + tamanho + diferencial do time." },
  D8: { what: "Linguagem evita viés de gênero, idade ou grupo subrepresentado.",
        how:  "Substitua termos enviesados (ex.: 'jovem dinâmico') por linguagem neutra. FairnessGuard já bloqueia os piores casos." },
  D9: { what: "Benefícios e modelo de trabalho (remoto/híbrido/presencial) declarados.",
        how:  "Liste benefícios materiais + modelo + faixa salarial quando possível." },
}

// ===========================================================================
// HeaderReal — EXTRAÇÃO de JDEvaluationHeader.tsx (linhas 22-152, ramo expanded)
// ===========================================================================
const BAND_COLORS: Record<string, string> = {
  excelente:    "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
  bom:          "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
  adequado:     "bg-amber-500/10 text-amber-700 border-amber-500/30",
  insuficiente: "bg-orange-500/10 text-orange-700 border-orange-500/30",
  critico:      "bg-red-500/10 text-red-700 border-red-500/30",
}
function deriveBand(e: JDEvaluationData) {
  const band = e.band ||
    (e.score >= 90 ? "excelente" : e.score >= 70 ? "bom" :
     e.score >= 50 ? "adequado" : e.score >= 30 ? "insuficiente" : "critico")
  const bandLabel = e.band_label ||
    (band === "excelente" ? "Excelente" : band === "bom" ? "Bom" :
     band === "adequado" ? "Adequado" : band === "insuficiente" ? "Insuficiente" : "Crítico")
  return { band, bandLabel }
}

interface HeaderRealProps {
  jobTitle: string
  evaluation: JDEvaluationData
  /** Quando true, o card cinza com `lia_suggestion` NÃO é renderizado (usado
   * pelas variantes que substituem esse bloco por algo próprio). */
  hideSuggestionCard?: boolean
  /** Override do conteúdo do card cinza (Variante A). */
  suggestionOverride?: React.ReactNode
}
function HeaderReal({ jobTitle, evaluation, hideSuggestionCard, suggestionOverride }: HeaderRealProps) {
  const { band, bandLabel } = deriveBand(evaluation)
  return (
    <>
      {/* Title bar — JDEvaluationHeader.tsx:92-118 */}
      <div className="flex items-center justify-between px-4 py-3 bg-white hover:bg-slate-100 transition-colors">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-slate-600" />
          <span className="text-sm font-semibold text-slate-900">Descrição do Cargo</span>
          <span className="text-xs text-slate-500">— {jobTitle}</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="h-7 text-xs px-3 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-100 inline-flex items-center">
            <Pencil className="h-3 w-3 mr-1.5" /> Editar Descrição
          </button>
          <ChevronUp className="h-4 w-4 text-slate-600" />
        </div>
      </div>

      {/* Summary row — JDEvaluationHeader.tsx:121-152 */}
      <div className="px-3 pt-3 pb-2 space-y-2 border-b border-slate-200">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-900">{evaluation.score}</span>
            <span className="text-[11px] text-slate-600">/100</span>
          </div>
          <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full border", BAND_COLORS[band])}>
            {bandLabel}
          </span>
          {band === "critico" && (
            <span className="text-[11px] text-red-600 font-medium flex items-center gap-1">
              <XCircle className="w-3 h-3" /> JD bloqueado — geração de perguntas desabilitada
            </span>
          )}
        </div>
        {!hideSuggestionCard && (suggestionOverride !== undefined ? suggestionOverride : (
          evaluation.lia_suggestion && (
            <div className={cn(
              "text-[11px] px-2.5 py-2 rounded-md border leading-relaxed",
              evaluation.can_generate
                ? "bg-slate-50 border-slate-200 text-slate-600/80"
                : "bg-red-500/10 border-red-500/30 text-red-700"
            )}>
              {evaluation.lia_suggestion}
            </div>
          )
        ))}
      </div>
    </>
  )
}

// ===========================================================================
// CriteriaReal — EXTRAÇÃO de JDEvalCriteriaList.tsx (linhas 26-57)
// ===========================================================================
interface CriteriaRealProps {
  evaluation: JDEvaluationData
  /** Variante A: ativa tooltip com definição+recomendação ao hover. */
  withTooltip?: boolean
  /** Variante B: torna cada card clicável e devolve a dimensão selecionada. */
  onCardClick?: (dim: string) => void
  selectedDim?: string | null
  /** Variante C: highlight cruzado quando hover acontece no painel lateral. */
  highlightedDim?: string | null
}
function CriteriaReal({ evaluation, withTooltip, onCardClick, selectedDim, highlightedDim }: CriteriaRealProps) {
  if (!evaluation.indicators?.length) return null
  return (
    <div className="grid grid-cols-3 gap-1.5 pb-2">
      {evaluation.indicators.map((ind) => {
        const def = ind.dimension ? DIM_DEFS[ind.dimension] : undefined
        const isSelected = selectedDim === ind.dimension
        const isHighlighted = highlightedDim === ind.dimension
        const interactive = !!onCardClick
        return (
          <div
            key={ind.label}
            onClick={interactive ? () => onCardClick!(ind.dimension!) : undefined}
            className={cn(
              "group relative flex items-center gap-1.5 px-2 py-1.5 rounded-md border text-[11px] transition-all",
              ind.status === "sufficient" ? "bg-emerald-500/10 border-emerald-500/30" :
              ind.status === "partial"    ? "bg-amber-500/10 border-amber-500/30" :
                                            "bg-red-500/10 border-red-500/30",
              interactive && "cursor-pointer hover:shadow-sm",
              isSelected && "ring-2 ring-indigo-500 ring-offset-1",
              isHighlighted && "ring-2 ring-indigo-400 scale-[1.02]",
            )}
          >
            {ind.status === "sufficient" ? <CheckCircle className="w-3 h-3 text-emerald-600 shrink-0" />
              : ind.status === "partial" ? <Brain className="w-3 h-3 text-amber-600 shrink-0" />
              : <XCircle className="w-3 h-3 text-red-600 shrink-0" />}
            <div className="flex-1 min-w-0">
              <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide block">{ind.dimension}</span>
              <span className={cn(
                "truncate block font-medium",
                ind.status === "sufficient" ? "text-emerald-700" :
                ind.status === "partial"    ? "text-amber-700" : "text-red-700",
              )}>{ind.label}</span>
            </div>
            <span className="text-[11px] font-semibold text-slate-600 shrink-0">
              {ind.earned ?? 0}/{ind.weight ?? 0}
            </span>
            {withTooltip && def && (
              <div className="invisible group-hover:visible absolute z-20 left-0 top-full mt-1 w-72 p-3 rounded-md border border-slate-200 bg-white shadow-lg text-left">
                <p className="text-[11px] font-semibold text-slate-900 mb-1">{ind.dimension} — {ind.label}</p>
                <p className="text-[11px] text-slate-600 mb-2">{def.what}</p>
                {ind.status !== "sufficient" && (
                  <div className="border-t border-slate-200 pt-2">
                    <p className="text-[11px] font-semibold text-indigo-700 mb-0.5 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Como subir o score
                    </p>
                    <p className="text-[11px] text-slate-700">{def.how}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ===========================================================================
// Bloco LLM-gerado — simula o conteúdo de `enrichedJd.generated_jd_text` que
// hoje é renderizado em JDEvalResultsPanel.tsx:100-102 como
// `<p className="whitespace-pre-wrap">…</p>` e que, quando o LLM inclui uma
// seção tipo "Qualidade da descrição (WSI) 90.0" no markdown, aparece como o
// 3º bloco visualmente redundante do screenshot do usuário.
// ===========================================================================
const LLM_GENERATED_TEXT = `Qualidade da descrição (WSI) 90.0

D1 Título objetivo                       ██████████ 10/10
D2 Sumário/Propósito                     ██████████ 10/10
D3 Responsabilidades claras              ██████████ 15/15
D4 Comp. técnicas alinhadas              ██████████ 15/15
D5 Consistência de senioridade           ████░░░░░░  7/15
D6 Comp. comportamentais                 ██████████ 10/10
D7 Contexto da empresa                   ██████████ 10/10
D8 Linguagem inclusiva                   ██████████ 10/10
D9 Benefícios/Modelo trabalho            ██████░░░░  3/5

(JD enriquecido — texto gerado pela LIA)`

// ===========================================================================
// BASELINE — composição idêntica à de JDEvaluationPanel.tsx hoje
// ===========================================================================
function BaselineReal() {
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <HeaderReal jobTitle="Engenheiro(a) de Software Pleno" evaluation={SEED} />
      <div className="p-3 space-y-3">
        <CriteriaReal evaluation={SEED} />
        <div className="border border-cyan-500/20 bg-cyan-500/[.02] rounded-xl p-3">
          <span className="text-xs font-semibold uppercase tracking-wide block mb-2 text-slate-900">
            Descrição Enriquecida (LIA)
          </span>
          <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap">{LLM_GENERATED_TEXT}</p>
        </div>
      </div>
    </div>
  )
}

// ===========================================================================
// VARIANTE A — Tooltip nos cards + resumo acionável
// Mudanças cirúrgicas:
//   1. CriteriaReal recebe prop `withTooltip` (definição + ação).
//   2. HeaderReal recebe `suggestionOverride` com um resumo "Para subir de
//      90 para 100" derivado dos indicadores `partial`/`insufficient`.
//   3. O bloco de markdown LLM com barras é REMOVIDO (pedir ao backend que
//      pare de incluir essa seção em `generated_jd_text`).
// ===========================================================================
function VariantA() {
  const lagging = SEED.indicators.filter(i => i.status !== "sufficient" && DIM_DEFS[i.dimension!])
  const override = (
    <div className="text-[11px] px-2.5 py-2 rounded-md border border-indigo-200 bg-indigo-50 leading-relaxed">
      <p className="font-semibold text-indigo-900 mb-1 flex items-center gap-1">
        <Sparkles className="w-3 h-3" /> Para subir de {SEED.score} para 100
      </p>
      <ul className="space-y-1 text-slate-700">
        {lagging.map(i => (
          <li key={i.dimension} className="flex items-start gap-1.5">
            <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-indigo-600" />
            <span><strong>{i.dimension}</strong> · {DIM_DEFS[i.dimension!].how}</span>
          </li>
        ))}
      </ul>
    </div>
  )
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <HeaderReal jobTitle="Engenheiro(a) de Software Pleno" evaluation={SEED} suggestionOverride={override} />
      <div className="p-3 space-y-3">
        <CriteriaReal evaluation={SEED} withTooltip />
        <p className="text-[10px] text-slate-400 italic">
          (Bloco de markdown LLM removido — depende de ajuste no prompt `jd_generator_service`.)
        </p>
      </div>
    </div>
  )
}

// ===========================================================================
// VARIANTE B — Acordeão drill-down
// Mudanças cirúrgicas:
//   1. CriteriaReal recebe `onCardClick` — clicar abre painel inferior.
//   2. HeaderReal mantém o card cinza original (sem mudança).
//   3. Bloco LLM removido.
// ===========================================================================
function VariantB() {
  const [sel, setSel] = useState<string | null>("D5")
  const selectedInd = useMemo(() => SEED.indicators.find(i => i.dimension === sel), [sel])
  const def = sel ? DIM_DEFS[sel] : undefined
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <HeaderReal jobTitle="Engenheiro(a) de Software Pleno" evaluation={SEED} />
      <div className="p-3 space-y-3">
        <CriteriaReal evaluation={SEED} onCardClick={(d) => setSel(d === sel ? null : d)} selectedDim={sel} />
        {selectedInd && def && (
          <div className="border border-indigo-200 bg-indigo-50/40 rounded-md p-3 space-y-2 animate-in fade-in slide-in-from-top-1">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-slate-900">
                {selectedInd.dimension} · {selectedInd.label}
                <span className="ml-2 text-[11px] font-normal text-slate-500">
                  {selectedInd.earned}/{selectedInd.weight} pts
                </span>
              </p>
              <button onClick={() => setSel(null)} className="text-[11px] text-slate-500 hover:text-slate-700">fechar</button>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide font-semibold text-slate-500 mb-0.5">O que isso mede</p>
              <p className="text-xs text-slate-700">{def.what}</p>
            </div>
            {selectedInd.detail && (
              <div>
                <p className="text-[11px] uppercase tracking-wide font-semibold text-slate-500 mb-0.5">O que a LIA observou nesta vaga</p>
                <p className="text-xs text-slate-700">{selectedInd.detail}</p>
              </div>
            )}
            {selectedInd.status !== "sufficient" && (
              <div>
                <p className="text-[11px] uppercase tracking-wide font-semibold text-indigo-700 mb-0.5 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> Como subir
                </p>
                <p className="text-xs text-slate-700">{def.how}</p>
              </div>
            )}
          </div>
        )}
        <p className="text-[10px] text-slate-400 italic">(Bloco de markdown LLM removido — mesmo ajuste de prompt da Variante A.)</p>
      </div>
    </div>
  )
}

// ===========================================================================
// VARIANTE C — Painel "Recomendações da LIA" top-3 com cross-highlight
// Mudanças cirúrgicas:
//   1. CriteriaReal recebe `highlightedDim` controlado pelo painel.
//   2. HeaderReal renderiza com `hideSuggestionCard` — card cinza some.
//   3. Painel "Recomendações" prioriza por (weight - earned) e cruza hover.
//   4. Bloco LLM removido.
// ===========================================================================
function VariantC() {
  const [hov, setHov] = useState<string | null>(null)
  const recs = useMemo(() => {
    return [...SEED.indicators]
      .filter(i => i.status !== "sufficient" || (i.weight ?? 0) - (i.earned ?? 0) > 0)
      .sort((a, b) => ((b.weight ?? 0) - (b.earned ?? 0)) - ((a.weight ?? 0) - (a.earned ?? 0)))
      .slice(0, 3)
  }, [])
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <HeaderReal jobTitle="Engenheiro(a) de Software Pleno" evaluation={SEED} hideSuggestionCard />
      <div className="p-3 space-y-3">
        <CriteriaReal evaluation={SEED} highlightedDim={hov} />
        <div className="border border-indigo-200 bg-indigo-50/40 rounded-md p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-700 mb-2 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> Recomendações da LIA · ações priorizadas ({recs.length})
          </p>
          <ol className="space-y-2">
            {recs.map((r, idx) => {
              const def = DIM_DEFS[r.dimension!]
              const gap = (r.weight ?? 0) - (r.earned ?? 0)
              return (
                <li
                  key={r.dimension}
                  onMouseEnter={() => setHov(r.dimension!)}
                  onMouseLeave={() => setHov(null)}
                  className="flex items-start gap-2 p-1.5 rounded-md hover:bg-white cursor-default"
                >
                  <span className="flex items-center justify-center w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] font-bold shrink-0 mt-0.5">{idx + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-900">
                      <strong>{r.dimension} · {r.label}</strong>
                      <span className="ml-1.5 text-[11px] text-indigo-600 font-semibold">+{gap} pts possíveis</span>
                    </p>
                    <p className="text-[11px] text-slate-600 leading-snug">{def?.how}</p>
                  </div>
                </li>
              )
            })}
          </ol>
        </div>
        <p className="text-[10px] text-slate-400 italic">(Bloco de markdown LLM removido — mesmo ajuste de prompt da Variante A.)</p>
      </div>
    </div>
  )
}

// ===========================================================================
// Layout — 2×2 grid com legendas
// ===========================================================================
function Caption({ title, changes, effort, beDeps }: { title: string; changes: string; effort: string; beDeps: string }) {
  return (
    <div className="mt-2 text-[11px] text-slate-600 space-y-0.5 px-1">
      <p className="font-semibold text-slate-900">{title}</p>
      <p><strong>Mudanças:</strong> {changes}</p>
      <p><strong>Esforço FE:</strong> {effort}</p>
      <p><strong>Dep. backend:</strong> {beDeps}</p>
    </div>
  )
}

export default function JDScoresComparison() {
  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="bg-white border border-slate-200 rounded-xl p-4">
          <h1 className="text-xl font-bold text-slate-900 mb-1">Painel de scores do JD — Baseline + 3 variantes (Task #1158)</h1>
          <p className="text-sm text-slate-600">
            Cenário: score <strong>90</strong>, "Consistência de senioridade" (D5) <strong>parcial</strong>, demais sufficient.
            Cards <code>HeaderReal</code> e <code>CriteriaReal</code> são <strong>extração literal</strong> dos componentes de produção
            <code> JDEvaluationHeader.tsx</code> e <code>JDEvalCriteriaList.tsx</code> — apenas tokens CSS foram substituídos (ver topo do arquivo).
            Variantes envolvem (não substituem) esses componentes.
          </p>
          <div className="mt-3 p-2.5 rounded-md border border-amber-300 bg-amber-50 text-[11px] text-amber-900 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <span>
              <strong>Origem do 3º bloco de barras (confirmado, ver report §1.2):</strong> NÃO existe componente terceiro.
              As barras "Qualidade da descrição (WSI) 90.0" vêm do texto LLM <code>enrichedJd.generated_jd_text</code> renderizado como
              <code> whitespace-pre-wrap</code> em <code>JDEvalResultsPanel.tsx:100-102</code>. Para remover é preciso ajustar o prompt em
              <code> lia-agent-system/app/domains/job_management/services/jd_generator_service.py</code> (a remoção é uma das tarefas filhas).
            </span>
          </div>
        </header>

        <section>
          <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-2">Baseline (estado atual em produção)</h2>
          <BaselineReal />
          <Caption
            title="Baseline"
            changes="Nenhuma — réplica fiel do que o usuário vê hoje."
            effort="—"
            beDeps="—"
          />
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-2">Variante A · Tooltip + resumo acionável</h2>
            <VariantA />
            <Caption
              title="A — explica no hover, resume no card cinza"
              changes="Cards D1–D9 ganham tooltip (definição + como subir). Card cinza vira 'Para subir de 90 para 100'. Bloco LLM removido."
              effort="Baixo (FE only). Dicionário D1–D9 hardcoded no FE."
              beDeps="Nenhuma para liberar. Backend pode opcionalmente expor `definition`/`recommendation` (Task filha #1159) para internacionalizar."
            />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-2">Variante B · Acordeão drill-down</h2>
            <VariantB />
            <Caption
              title="B — clicar no card revela o porquê"
              changes="Cards D1–D9 ficam clicáveis. Painel inferior mostra 'O que mede / O que a LIA viu / Como subir'. Card cinza inalterado. Bloco LLM removido."
              effort="Baixo–médio (FE only). Reaproveita `indicator.detail` já existente."
              beDeps="Nenhuma para liberar. Mesmo benefício opcional da #1159."
            />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide mb-2">Variante C · Recomendações priorizadas + cross-highlight</h2>
            <VariantC />
            <Caption
              title="C — top-3 ações priorizadas por impacto"
              changes="Card cinza some. Painel 'Recomendações da LIA' lista top-3 dimensões ordenadas por (weight−earned). Hover destaca o card D# correspondente. Bloco LLM removido."
              effort="Médio (FE only). Lógica de priorização + cross-highlight."
              beDeps="Nenhuma para liberar."
            />
          </div>
        </section>

        <footer className="text-[11px] text-slate-500 pt-2">
          Relatório completo (auditoria + 5 refs de mercado): <code>docs/research/jd-scores-redesign.md</code>.
          Componentes reais inalterados em produção.
        </footer>
      </div>
    </div>
  )
}
