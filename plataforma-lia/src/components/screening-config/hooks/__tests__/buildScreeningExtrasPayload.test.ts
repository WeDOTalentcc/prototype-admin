import { describe, it, expect } from 'vitest'
import { buildScreeningExtrasPayload, screeningExtrasToRoteiroItems } from '../buildScreeningExtrasPayload'
import type { CustomQuestion } from '../../CustomQuestions'

const ELIG_CANONICAL_KEYS = ['id', 'question', 'question_type', 'options', 'is_eliminatory', 'expected_answer', 'category', 'order']

describe('buildScreeningExtrasPayload — split semantico custom + banco (P0-1/P0-2)', () => {
  it('pergunta custom eliminatoria vai para eligibility_questions com is_eliminatory=true e expected_answer', () => {
    const custom: CustomQuestion[] = [
      { id: 'c1', question: 'Possui CNH categoria B?', character: 'eliminatoria', expectedAnswer: 'Sim' },
    ]
    const out = buildScreeningExtrasPayload({ customQuestions: custom, selectedBankQuestions: [], bankQuestionOverrides: {}, bankCatalog: [] })
    expect(out.eligibility_questions).toHaveLength(1)
    expect(out.screening_questions).toHaveLength(0)
    const q = out.eligibility_questions[0]
    expect(q.is_eliminatory).toBe(true)
    expect(q.question).toBe('Possui CNH categoria B?')
    expect(q.expected_answer).toBe('Sim')
  })

  it('pergunta custom classificatoria vai para screening_questions (is_eliminatory=false), NUNCA para eligibility', () => {
    const custom: CustomQuestion[] = [
      { id: 'c2', question: 'Descreva sua experiencia com Python', character: 'classificatoria' },
    ]
    const out = buildScreeningExtrasPayload({ customQuestions: custom, selectedBankQuestions: [], bankQuestionOverrides: {}, bankCatalog: [] })
    expect(out.eligibility_questions).toHaveLength(0)
    expect(out.screening_questions).toHaveLength(1)
    expect(out.screening_questions[0].is_eliminatory).toBe(false)
    expect(out.screening_questions[0].question).toBe('Descreva sua experiencia com Python')
  })

  it('NUNCA emite o campo legado "character" (guarda de regressao do shape divergente P0-2)', () => {
    const custom: CustomQuestion[] = [
      { id: 'c3', question: 'Aceita modelo presencial?', character: 'eliminatoria', expectedAnswer: 'Sim' },
      { id: 'c4', question: 'Nivel de ingles?', character: 'classificatoria' },
    ]
    const out = buildScreeningExtrasPayload({ customQuestions: custom, selectedBankQuestions: [], bankQuestionOverrides: {}, bankCatalog: [] })
    for (const q of [...out.eligibility_questions, ...out.screening_questions]) {
      expect('character' in q).toBe(false)
    }
  })

  it('item de elegibilidade emite apenas chaves canonicas do EligibilityQuestionItem', () => {
    const custom: CustomQuestion[] = [
      { id: 'c5', question: 'Possui disponibilidade imediata?', character: 'eliminatoria', expectedAnswer: 'Sim' },
    ]
    const out = buildScreeningExtrasPayload({ customQuestions: custom, selectedBankQuestions: [], bankQuestionOverrides: {}, bankCatalog: [] })
    for (const key of Object.keys(out.eligibility_questions[0])) {
      expect(ELIG_CANONICAL_KEYS).toContain(key)
    }
  })

  it('bank-selected resolve do catalogo; override.character roteia e override.expectedAnswer vence', () => {
    const bankCatalog = [
      { id: 'b1', question: 'Possui certificacao PMP?', is_eliminatory: true, expected_answer: 'Sim' },
      { id: 'b2', question: 'Anos de lideranca?', is_eliminatory: false },
    ]
    const out = buildScreeningExtrasPayload({
      customQuestions: [],
      selectedBankQuestions: ['b1', 'b2'],
      bankQuestionOverrides: { b2: { character: 'eliminatoria', expectedAnswer: 'Mais de 3' } },
      bankCatalog,
    })
    // b1 segue catalogo (eliminatoria), b2 override -> eliminatoria
    expect(out.eligibility_questions.map(q => q.question).sort()).toEqual(['Anos de lideranca?', 'Possui certificacao PMP?'])
    const b2 = out.eligibility_questions.find(q => q.question === 'Anos de lideranca?')!
    expect(b2.expected_answer).toBe('Mais de 3')
  })

  it('bank-selected sem id no catalogo e ignorado silenciosamente (nao quebra, nao inventa)', () => {
    const out = buildScreeningExtrasPayload({
      customQuestions: [],
      selectedBankQuestions: ['fantasma'],
      bankQuestionOverrides: {},
      bankCatalog: [{ id: 'b1', question: 'X?', is_eliminatory: true }],
    })
    expect(out.eligibility_questions).toHaveLength(0)
    expect(out.screening_questions).toHaveLength(0)
  })
})

describe('screeningExtrasToRoteiroItems — mapeia extras classificatorios para o shape do POST /wsi/questions/save', () => {
  it('mapeia question->text, question_type->type e preserva category/weight/block_id; NUNCA emite question_type nem is_eliminatory', () => {
    const items = screeningExtrasToRoteiroItems([
      { question: 'Descreva um projeto', category: 'company', block_id: 2, question_type: 'open', is_eliminatory: false, weight: 0.7 },
    ])
    expect(items).toHaveLength(1)
    expect(items[0].text).toBe('Descreva um projeto')
    expect(items[0].type).toBe('open')
    expect(items[0].category).toBe('company')
    expect(items[0].block_id).toBe(2)
    expect(items[0].weight).toBe(0.7)
    expect('question_type' in items[0]).toBe(false)
    expect('is_eliminatory' in items[0]).toBe(false)
  })
})
