import { render, screen } from '@testing-library/react'
import React from 'react'
import { CalibrationResultCard, type CalibrationCandidate } from '../CalibrationResultCard'
import { ToolSurfaceContext } from '@/contexts/ToolSurfaceContext'

const MOCK_CANDIDATES: CalibrationCandidate[] = [
  { id: '1', name: 'Ana Lima', score: 92, stage: 'Entrevista Técnica' },
  { id: '2', name: 'Carlos Silva', score: 78, stage: 'Triagem' },
  { id: '3', name: 'Maria Costa', score: 65, stage: 'Triagem' },
  { id: '4', name: 'João Santos', score: 55, stage: 'Entrevista RH' },
]

describe('CalibrationResultCard — inline mode', () => {
  it('mostra score médio', () => {
    render(<CalibrationResultCard candidates={MOCK_CANDIDATES} averageScore={72} />)
    expect(screen.getByText(/72/)).toBeInTheDocument()
  })

  it('mostra apenas 3 candidatos no inline', () => {
    render(<CalibrationResultCard candidates={MOCK_CANDIDATES} averageScore={72} />)
    expect(screen.getByText('Ana Lima')).toBeInTheDocument()
    expect(screen.getByText('Carlos Silva')).toBeInTheDocument()
    expect(screen.getByText('Maria Costa')).toBeInTheDocument()
    expect(screen.queryByText('João Santos')).not.toBeInTheDocument()
  })
})

describe('CalibrationResultCard — panel mode', () => {
  const PanelWrapper = ({ children }: { children: React.ReactNode }) => (
    <ToolSurfaceContext.Provider value="panel">{children}</ToolSurfaceContext.Provider>
  )

  it('mostra todos os candidatos no panel mode', () => {
    render(
      <CalibrationResultCard candidates={MOCK_CANDIDATES} averageScore={72} />,
      { wrapper: PanelWrapper }
    )
    expect(screen.getByText('João Santos')).toBeInTheDocument()
  })
})
