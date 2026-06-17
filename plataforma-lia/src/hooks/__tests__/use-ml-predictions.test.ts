/**
 * Testes unitários — useMLPredictions (P3-4)
 *
 * Cobre:
 * - Estado inicial: insights/timeToFill/salary=null, loading=false, error=null
 * - fetchInsights: popula insights no sucesso
 * - fetchTimeToFill: popula timeToFill no sucesso
 * - fetchSalary: popula salary no sucesso
 * - Qualquer fetch: seta error em falha HTTP
 * - loading=true durante fetch, false após
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useMLPredictions } from '../use-ml-predictions'

const mockFetch = vi.fn()
global.fetch = mockFetch

const mockInsights = {
  summary: { total_hires: 10, avg_time_to_fill: 30, top_sources: ['LinkedIn'], success_rate: 0.8 },
  recommendations: [{ action: 'Aumentar sourcing', impact: 'high', priority: '1' }],
  top_successful_skills: [{ skill: 'Python', success_rate: 0.9, count: 5 }],
  confidence: 0.85,
}

const mockTimeToFill = {
  predicted_days: 25,
  range_min: 20,
  range_max: 35,
  confidence: 0.78,
  confidence_level: 'medium',
  comparison_to_market: 'abaixo da média setorial',
  explanation: 'Baseado em 15 vagas similares',
  factors: [{ name: 'Seniority', impact: 'alto', value: 'senior' }],
  model_version: '1.0.0',
}

const mockSalary = {
  suggested_min: 8000,
  suggested_max: 12000,
  market_percentile: 60,
  competitive_analysis: 'Competitivo para o mercado',
  confidence: 0.72,
  confidence_level: 'medium',
  explanation: 'Baseado em benchmark setorial',
  factors: [{ name: 'Localidade', impact: 'médio', value: 'São Paulo' }],
}

describe('useMLPredictions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('estado inicial: tudo null, loading=false, error=null', () => {
    const { result } = renderHook(() => useMLPredictions())
    expect(result.current.insights).toBeNull()
    expect(result.current.timeToFill).toBeNull()
    expect(result.current.salary).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchInsights: popula insights e limpa loading', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockInsights })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchInsights('company-1', 'Engenheiro')
    })

    expect(result.current.insights).toEqual(mockInsights)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(mockFetch).toHaveBeenCalledWith('/api/backend-proxy/ml/insights', expect.objectContaining({
      method: 'POST',
    }))
  })

  it('fetchInsights: passa company_id e role no body', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockInsights })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchInsights('cmp-42', 'Product Manager')
    })

    const callBody = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(callBody.company_id).toBe('cmp-42')
    expect(callBody.role).toBe('Product Manager')
  })

  it('fetchTimeToFill: popula timeToFill no sucesso', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockTimeToFill })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchTimeToFill('company-1', { title: 'Dev Senior', seniority: 'senior' })
    })

    expect(result.current.timeToFill).toEqual(mockTimeToFill)
    expect(result.current.loading).toBe(false)
    expect(mockFetch).toHaveBeenCalledWith('/api/backend-proxy/ml/predict/time-to-fill', expect.anything())
  })

  it('fetchSalary: popula salary no sucesso', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockSalary })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchSalary('company-1', { title: 'Dev', location: 'SP' })
    })

    expect(result.current.salary).toEqual(mockSalary)
    expect(result.current.loading).toBe(false)
    expect(mockFetch).toHaveBeenCalledWith('/api/backend-proxy/ml/predict/salary', expect.anything())
  })

  it('fetchInsights: seta error em resposta não-ok', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500 })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchInsights('company-1')
    })

    expect(result.current.insights).toBeNull()
    expect(result.current.error).not.toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('fetchTimeToFill: seta error em exceção de rede', async () => {
    mockFetch.mockRejectedValue(new Error('Timeout'))
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchTimeToFill('company-1', {})
    })

    expect(result.current.timeToFill).toBeNull()
    expect(result.current.error).toBe('Timeout')
  })

  it('estados independentes: fetchInsights não afeta timeToFill e salary', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockInsights })
    const { result } = renderHook(() => useMLPredictions())

    await act(async () => {
      await result.current.fetchInsights('company-1')
    })

    expect(result.current.insights).not.toBeNull()
    expect(result.current.timeToFill).toBeNull()
    expect(result.current.salary).toBeNull()
  })
})
