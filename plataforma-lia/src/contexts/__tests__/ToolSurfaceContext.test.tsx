// src/contexts/__tests__/ToolSurfaceContext.test.ts
import { renderHook } from '@testing-library/react'
import React from 'react'
import {
  ToolSurfaceContext,
  ToolActivateContext,
  useToolSurface,
  useToolActivate,
} from '../ToolSurfaceContext'

describe('ToolSurfaceContext', () => {
  it('useToolSurface default é "inline" sem provider', () => {
    const { result } = renderHook(() => useToolSurface())
    expect(result.current).toBe('inline')
  })

  it('useToolSurface retorna "panel" quando provider define "panel"', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ToolSurfaceContext.Provider value="panel">{children}</ToolSurfaceContext.Provider>
    )
    const { result } = renderHook(() => useToolSurface(), { wrapper })
    expect(result.current).toBe('panel')
  })
})

describe('ToolActivateContext', () => {
  it('useToolActivate default é null sem provider', () => {
    const { result } = renderHook(() => useToolActivate())
    expect(result.current).toBeNull()
  })

  it('useToolActivate retorna o callback quando provider o define', () => {
    const cb = vi.fn()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ToolActivateContext.Provider value={cb}>{children}</ToolActivateContext.Provider>
    )
    const { result } = renderHook(() => useToolActivate(), { wrapper })
    result.current?.('tc-123')
    expect(cb).toHaveBeenCalledWith('tc-123')
  })
})
