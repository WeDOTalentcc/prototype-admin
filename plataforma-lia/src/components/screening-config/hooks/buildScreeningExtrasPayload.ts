import type { CustomQuestion } from '../CustomQuestions'

/**
 * Produtor canonico (canonical-fix) do payload de persistencia dos "extras"
 * da tela de perguntas de triagem: perguntas personalizadas (custom) + perguntas
 * de banco selecionadas + overrides.
 *
 * Resolve P0-1 (ghost feature: extras nunca persistiam) e P0-2 (shape divergente:
 * o campo de UI `character` nunca era traduzido para o canonico `is_eliminatory`).
 *
 * Split semantico (decisao Paulo 2026-06-05):
 *   - eliminatoria  -> eligibility_questions (is_eliminatory=true, gate antes do WSI)
 *   - classificatoria -> screening_questions (entra no scoring, nao desqualifica)
 *
 * Emite o shape canonico de EligibilityQuestionItem (app/schemas/eligibility_question_item.py)
 * e NUNCA o campo legado `character`.
 */

export interface BankCatalogQuestion {
  id: string
  question: string
  is_eliminatory: boolean
  expected_answer?: string
}

export type BankQuestionOverride = {
  character?: 'eliminatoria' | 'classificatoria'
  expectedAnswer?: string
}

/** Shape canonico gravado em JobVacancy.eligibility_questions (JSONB). */
export interface EligibilityQuestionPayload {
  id: string
  question: string
  question_type: string
  options: string[] | null
  is_eliminatory: boolean
  expected_answer: string | null
  category: string
  order: number
}

/** Shape de screening_questions (espelha screening_question_set_service company-injected). */
export interface ScreeningQuestionPayload {
  question: string
  category: string
  block_id: number
  question_type: string
  is_eliminatory: boolean
  weight: number
}

export interface ScreeningExtrasPayload {
  eligibility_questions: EligibilityQuestionPayload[]
  screening_questions: ScreeningQuestionPayload[]
}

export interface BuildScreeningExtrasInput {
  customQuestions: CustomQuestion[]
  selectedBankQuestions: string[]
  bankQuestionOverrides: Record<string, BankQuestionOverride>
  bankCatalog: BankCatalogQuestion[]
}

function toEligibilityItem(
  id: string,
  question: string,
  expectedAnswer: string | undefined,
  order: number,
): EligibilityQuestionPayload {
  return {
    id,
    question,
    question_type: 'yes_no',
    options: null,
    is_eliminatory: true,
    expected_answer: expectedAnswer ?? null,
    category: 'default',
    order,
  }
}

function toScreeningItem(question: string): ScreeningQuestionPayload {
  return {
    question,
    category: 'company',
    block_id: 2,
    question_type: 'open',
    is_eliminatory: false,
    weight: 0.7,
  }
}

export function buildScreeningExtrasPayload(
  input: BuildScreeningExtrasInput,
): ScreeningExtrasPayload {
  const eligibility: EligibilityQuestionPayload[] = []
  const screening: ScreeningQuestionPayload[] = []
  let order = 0

  for (const q of input.customQuestions) {
    if (q.character === 'eliminatoria') {
      eligibility.push(toEligibilityItem(q.id, q.question, q.expectedAnswer, order++))
    } else {
      screening.push(toScreeningItem(q.question))
    }
  }

  const catalogById = new Map(input.bankCatalog.map((c) => [c.id, c]))
  for (const id of input.selectedBankQuestions) {
    const cat = catalogById.get(id)
    if (!cat) continue // id sem correspondencia no catalogo: ignora, nao inventa
    const override = input.bankQuestionOverrides[id] ?? {}
    const character =
      override.character ?? (cat.is_eliminatory ? 'eliminatoria' : 'classificatoria')
    const expectedAnswer = override.expectedAnswer ?? cat.expected_answer
    if (character === 'eliminatoria') {
      eligibility.push(toEligibilityItem(id, cat.question, expectedAnswer, order++))
    } else {
      screening.push(toScreeningItem(cat.question))
    }
  }

  return { eligibility_questions: eligibility, screening_questions: screening }
}

/** Shape que o POST /wsi/questions/save consome (roteiro de screening). */
export interface RoteiroSaveItem {
  text: string
  category: string
  type: string
  weight: number
  block_id: number
}

/**
 * Mapeia os screening_questions extras (classificatorios) para o shape consumido
 * pelo endpoint POST /wsi/questions/save (question->text, question_type->type).
 */
export function screeningExtrasToRoteiroItems(
  extras: ScreeningQuestionPayload[],
): RoteiroSaveItem[] {
  return extras.map((p) => ({
    text: p.question,
    category: p.category,
    type: p.question_type,
    weight: p.weight,
    block_id: p.block_id,
  }))
}
