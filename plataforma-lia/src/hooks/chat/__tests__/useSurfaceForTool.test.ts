// src/hooks/chat/__tests__/useSurfaceForTool.test.ts
import { renderHook } from '@testing-library/react'
import { useSurfaceForTool } from '../useSurfaceForTool'

describe('useSurfaceForTool', () => {
  it('tool desconhecida retorna inline (safe default)', () => {
    const { result } = renderHook(() =>
      useSurfaceForTool('unknown_tool', { isFullscreen: true })
    )
    expect(result.current).toBe('inline')
  })

  it('tool com hitl:true retorna inline mesmo em fullscreen', () => {
    const { result } = renderHook(() =>
      useSurfaceForTool('send_email', { isFullscreen: true })
    )
    expect(result.current).toBe('inline')
  })

  it('sem fullscreen retorna sempre inline independente do config', () => {
    const { result } = renderHook(() =>
      useSurfaceForTool('search_candidates', { isFullscreen: false })
    )
    expect(result.current).toBe('inline')
  })

  it('search_candidates em fullscreen com poucos resultados retorna inline (threshold)', () => {
    // search_candidates tem density_threshold: 3
    const { result } = renderHook(() =>
      useSurfaceForTool('search_candidates', { isFullscreen: true, itemCount: 2 })
    )
    expect(result.current).toBe('inline')
  })

  it('search_candidates em fullscreen com muitos resultados retorna panel', () => {
    // itemCount > density_threshold (3)
    const { result } = renderHook(() =>
      useSurfaceForTool('search_candidates', { isFullscreen: true, itemCount: 10 })
    )
    expect(result.current).toBe('panel')
  })

  it('get_candidate_profile em fullscreen retorna panel (sem threshold)', () => {
    const { result } = renderHook(() =>
      useSurfaceForTool('get_candidate_profile', { isFullscreen: true })
    )
    expect(result.current).toBe('panel')
  })
})
