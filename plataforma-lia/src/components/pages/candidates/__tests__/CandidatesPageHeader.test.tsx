/**
 * Tests — CandidatesPageHeader component
 *
 * Covers:
 * - Renders title "Funil de Talentos"
 * - Renders "Novo Candidato" button always
 * - onAddCandidate fires on Novo Candidato click
 * - "Nova Busca" button visible when activeTab=search & showSearchResults=true
 * - "Nova Busca" button calls onNewSearch
 * - "Salvar Busca" button visible when searchTerm not empty
 * - "Salvar Busca" calls onSaveCurrentSearch
 * - "Nova Busca" shows for favorites tab
 * - Tab list is rendered via CandidateTabs
 * - onTabChange fires when tab clicked
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CandidatesPageHeader } from '../CandidatesPageHeader'

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => {
    const MAP: Record<string, string> = {
      "header.title": "Funil de Talentos",
      "header.newCandidate": "Novo Candidato",
      "header.newSearch": "Nova Busca",
      "header.saveSearch": "Salvar Busca",
      "header.saveSearchTitle": "Salvar esta busca para reutilizar",
    }
    return MAP[key] ?? key
  },
}))


const defaultTabs = [
  { id: 'search', label: 'Busca' },
  { id: 'favorites', label: 'Favoritos' },
]

const defaultProps = {
  tabs: defaultTabs,
  activeTab: 'search',
  showSearchResults: false,
  searchTerm: '',
  quickFilters: new Set<string>(),
  getActiveAdvancedFiltersCount: () => 0,
  onTabChange: vi.fn(),
  onAddCandidate: vi.fn(),
  onNewSearch: vi.fn(),
  onSaveCurrentSearch: vi.fn(),
}

describe('CandidatesPageHeader', () => {
  it('renders title "Funil de Talentos"', () => {
    render(<CandidatesPageHeader {...defaultProps} />)
    expect(screen.getByText('Funil de Talentos')).toBeInTheDocument()
  })

  it('renders Novo Candidato button always', () => {
    render(<CandidatesPageHeader {...defaultProps} />)
    expect(screen.getByRole('button', { name: /Novo Candidato/i })).toBeInTheDocument()
  })

  it('calls onAddCandidate when Novo Candidato is clicked', () => {
    const onAddCandidate = vi.fn()
    render(<CandidatesPageHeader {...defaultProps} onAddCandidate={onAddCandidate} />)
    fireEvent.click(screen.getByRole('button', { name: /Novo Candidato/i }))
    expect(onAddCandidate).toHaveBeenCalledOnce()
  })

  it('does not show Nova Busca button when search tab but no results', () => {
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={false} />)
    expect(screen.queryByRole('button', { name: /Nova Busca/i })).not.toBeInTheDocument()
  })

  it('shows Nova Busca button when search tab and showSearchResults=true', () => {
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={true} />)
    expect(screen.getByRole('button', { name: /Nova Busca/i })).toBeInTheDocument()
  })

  it('calls onNewSearch when Nova Busca is clicked', () => {
    const onNewSearch = vi.fn()
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={true} onNewSearch={onNewSearch} />)
    fireEvent.click(screen.getByRole('button', { name: /Nova Busca/i }))
    expect(onNewSearch).toHaveBeenCalledOnce()
  })

  it('shows Salvar Busca button when searchTerm is not empty and results visible', () => {
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={true} searchTerm="engineer" />)
    expect(screen.getByRole('button', { name: /Salvar Busca/i })).toBeInTheDocument()
  })

  it('calls onSaveCurrentSearch when Salvar Busca is clicked', () => {
    const onSaveCurrentSearch = vi.fn()
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={true} searchTerm="engineer" onSaveCurrentSearch={onSaveCurrentSearch} />)
    fireEvent.click(screen.getByRole('button', { name: /Salvar Busca/i }))
    expect(onSaveCurrentSearch).toHaveBeenCalledOnce()
  })

  it('does not show Salvar Busca button when searchTerm is empty', () => {
    render(<CandidatesPageHeader {...defaultProps} activeTab="search" showSearchResults={true} searchTerm="" />)
    expect(screen.queryByRole('button', { name: /Salvar Busca/i })).not.toBeInTheDocument()
  })

  it('shows Nova Busca button for favorites tab', () => {
    render(<CandidatesPageHeader {...defaultProps} activeTab="favorites" showSearchResults={false} />)
    expect(screen.getByRole('button', { name: /Nova Busca/i })).toBeInTheDocument()
  })

  it('renders tabs from CandidateTabs', () => {
    render(<CandidatesPageHeader {...defaultProps} />)
    expect(screen.getByText('Busca')).toBeInTheDocument()
    expect(screen.getByText('Favoritos')).toBeInTheDocument()
  })

  it('calls onTabChange when a tab is clicked', () => {
    const onTabChange = vi.fn()
    render(<CandidatesPageHeader {...defaultProps} onTabChange={onTabChange} />)
    fireEvent.click(screen.getByText('Favoritos'))
    expect(onTabChange).toHaveBeenCalledWith('favorites')
  })
})
