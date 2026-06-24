/**
 * eligibility-utils.ts — helper canônico para extrair resultados de elegibilidade.
 *
 * Consolida a lógica duplicada de CandidatePreviewProfileTab e KanbanPageModalsCore
 * em uma única função exportada. Regra de precedência:
 *
 *   1. candidate.eligibility_results  → já processado pelo backend, usa direto.
 *   2. job.eligibility_questions + candidate.eligibility_answers  → monta na hora.
 *   3. nenhum dos dois → undefined.
 *
 * O parâmetro `job` é opcional; quando ausente, o fallback (2) é ignorado.
 */
import type { EligibilityResultItem } from "@/components/wsi/eligibility-results-section"

export function extractEligibilityResults(
  candidate: Record<string, unknown>,
  job?: Record<string, unknown>,
): EligibilityResultItem[] | undefined {
  // — Caminho 1: resultados já processados no candidato —
  const raw = candidate?.eligibility_results
  if (Array.isArray(raw) && raw.length > 0) {
    return (raw as Record<string, unknown>[]).map((r, i) => ({
      id:              String(r.id ?? r.question_id ?? i),
      question:        String(r.question ?? r.question_text ?? ""),
      answer:          r.answer != null ? String(r.answer) : undefined,
      passed:          Boolean(r.passed ?? r.met ?? true),
      is_eliminatory:  r.is_eliminatory !== false,
      reconsideration: r.reconsideration != null ? String(r.reconsideration) : undefined,
    }))
  }

  // — Caminho 2: perguntas da vaga + respostas avulsas do candidato —
  const jobQuestions = job?.eligibility_questions
  if (Array.isArray(jobQuestions) && jobQuestions.length > 0) {
    const candidateAnswers = (candidate?.eligibility_answers ?? candidate?.answers) as
      | Record<string, unknown>
      | undefined

    return (jobQuestions as Record<string, unknown>[]).map((q, i) => {
      const qId    = String(q.id ?? i)
      const answer = candidateAnswers?.[qId] != null ? String(candidateAnswers[qId]) : undefined
      return {
        id:             qId,
        question:       String(q.question ?? q.question_text ?? ""),
        answer,
        passed:         answer !== undefined
          ? Boolean(candidateAnswers?.[`${qId}_passed`] ?? true)
          : true,
        is_eliminatory: q.is_eliminatory !== false,
      }
    })
  }

  return undefined
}
