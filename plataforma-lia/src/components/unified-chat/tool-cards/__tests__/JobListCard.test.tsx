import { render, screen } from '@testing-library/react'
import React from 'react'
import { JobListCard, type JobSummary } from '../JobListCard'
import { ToolSurfaceContext } from '@/contexts/ToolSurfaceContext'

const MOCK_JOBS: JobSummary[] = [
  { id: '1', title: 'Eng. Frontend', department: 'Tech', status: 'ao_vivo' },
  { id: '2', title: 'Product Manager', department: 'Produto', status: 'publicada' },
  { id: '3', title: 'Dev Backend', department: 'Tech', status: 'rascunho' },
  { id: '4', title: 'Designer UX', department: 'Design', status: 'ao_vivo' },
  { id: '5', title: 'Data Analyst', department: 'Analytics', status: 'publicada' },
  { id: '6', title: 'DevOps', department: 'Infra', status: 'rascunho' },
]

describe('JobListCard â inline mode (default)', () => {
  it('mostra contagem total de vagas', () => {
    render(<JobListCard jobs={MOCK_JOBS} totalCount={12} />)
    expect(screen.getByText(/12 vagas/i)).toBeInTheDocument()
  })

  it('mostra apenas 5 vagas no inline', () => {
    render(<JobListCard jobs={MOCK_JOBS} totalCount={12} />)
    expect(screen.getByText('Eng. Frontend')).toBeInTheDocument()
    expect(screen.getByText('Data Analyst')).toBeInTheDocument()
    expect(screen.queryByText('DevOps')).not.toBeInTheDocument()
  })

  it('renderiza botÃ£o "Ver todas" quando onOpenPanel Ã© fornecido', () => {
    render(<JobListCard jobs={MOCK_JOBS} totalCount={12} onOpenPanel={vi.fn()} />)
    expect(screen.getByRole('button', { name: /ver/i })).toBeInTheDocument()
  })
})

describe('JobListCard â panel mode', () => {
  const PanelWrapper = ({ children }: { children: React.ReactNode }) => (
    <ToolSurfaceContext.Provider value="panel">{children}</ToolSurfaceContext.Provider>
  )

  it('mostra todas as vagas no panel mode', () => {
    render(
      <JobListCard jobs={MOCK_JOBS} totalCount={6} />,
      { wrapper: PanelWrapper }
    )
    expect(screen.getByText('Eng. Frontend')).toBeInTheDocument()
    expect(screen.getByText('DevOps')).toBeInTheDocument()
  })
})
