import { useState, useEffect } from "react"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

export interface TableColumnConfig {
  id: string
  label: string
  visible: boolean
  order: number
  width?: number
  minWidth?: number
  category: string
  sortable?: boolean
  isGlobalSearch?: boolean
}

export interface SavedColumnView {
  id: string
  name: string
  columns: Array<{ id: string; label: string; visible: boolean; order: number }>
  createdAt: string
}

export function useCandidatesTableConfig() {
  const [showColumnConfig, setShowColumnConfig] = useState(false)
  const [tableColumns, setTableColumns] = useState<TableColumnConfig[]>([
    { id: 'feedback', label: '', visible: true, order: -2, width: 70, minWidth: 70, category: 'basico', sortable: false },
    { id: 'source', label: 'Fonte', visible: true, order: -1, category: 'basico' },
    { id: 'match_score', label: 'Match', visible: true, order: -0.5, category: 'ia' },
    { id: 'name', label: 'Candidato', visible: true, order: 0, category: 'basico' },
    { id: 'current_title', label: 'Cargo atual', visible: true, order: 1, category: 'profissional' },
    { id: 'current_company', label: 'Empresa atual', visible: true, order: 2, category: 'profissional' },
    { id: 'current_salary', label: 'Salário atual', visible: true, order: 3, category: 'salario' },
    { id: 'desired_salary_max', label: 'Expectativa salarial', visible: true, order: 4, category: 'salario' },
    { id: 'mobile_phone', label: 'Celular', visible: true, order: 5, category: 'contato' },
    { id: 'email', label: 'E-mail', visible: true, order: 6, category: 'contato' },
    { id: 'location_city', label: 'Cidade', visible: false, order: 7, category: 'localizacao' },
    { id: 'linkedin_url', label: 'LinkedIn', visible: true, order: 8, category: 'contato' },
    { id: 'id', label: 'ID do candidato', visible: false, order: 9, category: 'basico' },
    { id: 'secondary_email', label: 'E-mail secundário', visible: false, order: 10, category: 'contato' },
    { id: 'phone', label: 'Telefone fixo', visible: false, order: 11, category: 'contato' },
    { id: 'secondary_phone', label: 'Telefone adicional', visible: false, order: 12, category: 'contato' },
    { id: 'github_url', label: 'GitHub', visible: false, order: 13, category: 'contato' },
    { id: 'portfolio_url', label: 'Portfólio', visible: false, order: 14, category: 'contato' },
    { id: 'date_of_birth', label: 'Data de nascimento', visible: false, order: 15, category: 'pessoal' },
    { id: 'gender', label: 'Gênero', visible: false, order: 17, category: 'pessoal' },
    { id: 'nationality', label: 'Nacionalidade', visible: false, order: 18, category: 'pessoal' },
    { id: 'marital_status', label: 'Estado civil', visible: false, order: 19, category: 'pessoal' },
    { id: 'cpf', label: 'CPF', visible: false, order: 20, category: 'pessoal' },
    { id: 'seniority_level', label: 'Nível de senioridade', visible: false, order: 21, category: 'profissional' },
    { id: 'years_of_experience', label: 'Anos de experiência', visible: false, order: 22, category: 'profissional' },
    { id: 'self_introduction', label: 'Autoapresentação', visible: false, order: 23, category: 'profissional' },
    { id: 'technical_skills', label: 'Habilidades técnicas', visible: false, order: 24, category: 'competencias' },
    { id: 'soft_skills', label: 'Comp. Comportamentais', visible: false, order: 25, category: 'competencias' },
    { id: 'languages', label: 'Idiomas', visible: false, order: 26, category: 'competencias' },
    { id: 'certifications', label: 'Certificações', visible: false, order: 27, category: 'competencias' },
    { id: 'interests', label: 'Interesses', visible: false, order: 28, category: 'competencias' },
    { id: 'education', label: 'Formação acadêmica', visible: false, order: 28.5, category: 'competencias' },
    { id: 'location_state', label: 'Estado', visible: false, order: 29, category: 'localizacao' },
    { id: 'location_country', label: 'País', visible: false, order: 30, category: 'localizacao' },
    { id: 'address_street', label: 'Endereço – Rua', visible: false, order: 31, category: 'endereco' },
    { id: 'address_number', label: 'Endereço – Número', visible: false, order: 32, category: 'endereco' },
    { id: 'address_district', label: 'Endereço – Bairro', visible: false, order: 33, category: 'endereco' },
    { id: 'address_zip', label: 'Endereço – CEP', visible: false, order: 34, category: 'endereco' },
    { id: 'address_complement', label: 'Endereço – Complemento', visible: false, order: 35, category: 'endereco' },
    { id: 'is_remote', label: 'Aceita remoto', visible: false, order: 36, category: 'preferencias' },
    { id: 'willing_to_relocate', label: 'Aceita mudança', visible: false, order: 37, category: 'preferencias' },
    { id: 'mobility', label: 'Disponibilidade para viagens', visible: false, order: 38, category: 'preferencias' },
    { id: 'work_model_preference', label: 'Modelo de trabalho preferido', visible: false, order: 39, category: 'preferencias' },
    { id: 'contract_type_preference', label: 'Tipo de contrato preferido', visible: false, order: 40, category: 'preferencias' },
    { id: 'salary_currency', label: 'Moeda do salário', visible: false, order: 41, category: 'salario' },
    { id: 'desired_salary_min', label: 'Salário mínimo desejado', visible: false, order: 42, category: 'salario' },
    { id: 'salary_expectation_clt', label: 'Expectativa salarial CLT', visible: false, order: 43, category: 'salario' },
    { id: 'salary_expectation_pj', label: 'Expectativa salarial PJ', visible: false, order: 45, category: 'salario' },
    { id: 'salary_expectation_freelance', label: 'Expectativa salarial Freelance', visible: false, order: 46, category: 'salario' },
    { id: 'resume_url', label: 'Currículo (URL)', visible: false, order: 47, category: 'documentos' },
    { id: 'resume_text', label: 'Currículo (texto)', visible: false, order: 48, category: 'documentos' },
    { id: 'cover_letter', label: 'Carta de apresentação', visible: false, order: 49, category: 'documentos' },
    { id: 'source', label: 'Fonte de cadastro', visible: false, order: 50, category: 'origem' },
    { id: 'ats_source_name', label: 'Nome do ATS', visible: false, order: 51, category: 'origem' },
    { id: 'ats_candidate_id', label: 'ID no ATS', visible: false, order: 52, category: 'origem' },
    { id: 'pearch_profile_id', label: 'ID na Base Global', visible: false, order: 53, category: 'origem' },
    { id: 'is_open_to_work', label: 'Open to Work', visible: false, order: 54, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_decision_maker', label: 'Decision Maker', visible: false, order: 55, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_top_universities', label: 'Top Universities', visible: false, order: 56, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_hiring', label: 'Está contratando', visible: false, order: 57, category: 'busca_global', isGlobalSearch: true },
    { id: 'headline', label: 'Headline LinkedIn', visible: false, order: 58, category: 'busca_global', isGlobalSearch: true },
    { id: 'expertise', label: 'Expertise', visible: false, order: 59, category: 'busca_global', isGlobalSearch: true },
    { id: 'linkedin_followers_count', label: 'Seguidores LinkedIn', visible: false, order: 60, category: 'busca_global', isGlobalSearch: true },
    { id: 'linkedin_connections_count', label: 'Conexões LinkedIn', visible: false, order: 61, category: 'busca_global', isGlobalSearch: true },
    { id: 'outreach_message', label: 'Mensagem de Abordagem', visible: false, order: 62, category: 'busca_global', isGlobalSearch: true },
    { id: 'best_personal_email', label: 'Melhor Email Pessoal', visible: false, order: 63, category: 'busca_global', isGlobalSearch: true },
    { id: 'phone_types', label: 'Tipos de Telefone', visible: false, order: 64, category: 'busca_global', isGlobalSearch: true },
    { id: 'estimated_age', label: 'Idade Estimada', visible: false, order: 65, category: 'busca_global', isGlobalSearch: true },
    { id: 'match_reasoning', label: 'Justificativa do Match', visible: false, order: 66, category: 'busca_global', isGlobalSearch: true },
    { id: 'overall_summary', label: 'Resumo Geral', visible: false, order: 67, category: 'busca_global', isGlobalSearch: true },
    { id: 'query_insights', label: 'Insights por Requisito', visible: false, order: 68, category: 'busca_global', isGlobalSearch: true },
    { id: 'pearch_insights', label: 'Insights Pearch', visible: false, order: 69, category: 'busca_global', isGlobalSearch: true },
    { id: 'middle_name', label: 'Nome do Meio', visible: false, order: 70, category: 'busca_global', isGlobalSearch: true },
    { id: 'best_business_email', label: 'Email Corporativo', visible: false, order: 71, category: 'busca_global', isGlobalSearch: true },
    { id: 'personal_emails', label: 'Emails Pessoais', visible: false, order: 72, category: 'busca_global', isGlobalSearch: true },
    { id: 'business_emails', label: 'Emails Corporativos', visible: false, order: 73, category: 'busca_global', isGlobalSearch: true },
    { id: 'company_followers_count', label: 'Seguidores da Empresa', visible: false, order: 74, category: 'busca_global', isGlobalSearch: true },
    { id: 'company_keywords', label: 'Palavras-chave da Empresa', visible: false, order: 75, category: 'busca_global', isGlobalSearch: true },
    { id: 'lia_score', label: 'Score LIA', visible: true, order: 64, category: 'ia' },
    { id: 'lia_insights', label: 'Insights LIA', visible: false, order: 65, category: 'ia' },
    { id: 'skills_match_percentage', label: '% Match de habilidades', visible: false, order: 66, category: 'ia' },
    { id: 'status', label: 'Status no funil', visible: false, order: 56, category: 'status' },
    { id: 'is_active', label: 'Ativo no sistema', visible: false, order: 57, category: 'status' },
    { id: 'is_blacklisted', label: 'LCNU', visible: false, order: 58, category: 'status' },
    { id: 'blacklist_reason', label: 'Motivo LCNU', visible: false, order: 59, category: 'status' },
    { id: 'preferred_contact_method', label: 'Método de contato preferido', visible: false, order: 60, category: 'comunicacao' },
    { id: 'best_time_to_contact', label: 'Melhor horário para contato', visible: false, order: 61, category: 'comunicacao' },
    { id: 'communication_consent', label: 'Consentimento LGPD', visible: false, order: 62, category: 'comunicacao' },
    { id: 'completed_register', label: 'Cadastro completo', visible: false, order: 63, category: 'cadastro' },
    { id: 'accept_terms', label: 'Aceite dos termos', visible: false, order: 64, category: 'cadastro' },
    { id: 'tags', label: 'Tags', visible: false, order: 65, category: 'adicional' },
    { id: 'notes', label: 'Notas internas', visible: false, order: 66, category: 'adicional' },
    { id: 'additional_data', label: 'Dados adicionais', visible: false, order: 67, category: 'adicional' },
    { id: 'created_at', label: 'Data de cadastro', visible: false, order: 68, category: 'datas' },
    { id: 'updated_at', label: 'Última atualização', visible: false, order: 69, category: 'datas' },
    { id: 'last_contacted_at', label: 'Último contato', visible: false, order: 70, category: 'datas' },
    { id: 'last_activity_at', label: 'Última atividade', visible: false, order: 71, category: 'datas' },
    { id: 'acoes', label: 'Ações', visible: true, order: 0.5, category: 'basico' }
  ])
  const [savedColumnViews, setSavedColumnViews] = useState<SavedColumnView[]>([
    {
      id: '1',
      name: 'Visualização Padrão',
      columns: [
        { id: 'name', label: 'Nome completo', visible: true, order: 0 },
        { id: 'score_lia', label: 'Score LIA', visible: true, order: 1 },
        { id: 'role_name', label: 'Cargo atual', visible: true, order: 2 },
        { id: 'current_company', label: 'Empresa atual', visible: true, order: 3 },
        { id: 'city', label: 'Cidade', visible: true, order: 4 },
      ],
      createdAt: '2025-01-01T00:00:00.000Z'
    }
  ])

  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({
    checkbox: 50, acoes: 120,
    source: 60, name: 220, id: 100,
    email: 200, secondary_email: 200, phone: 130, mobile_phone: 130,
    secondary_phone: 130, linkedin_url: 60, github_url: 150, portfolio_url: 150,
    date_of_birth: 120, gender: 100, nationality: 130, marital_status: 120, cpf: 130,
    match_score: 50,
    current_title: 250, current_company: 150, seniority_level: 130,
    years_of_experience: 100, self_introduction: 200,
    lia_score: 100, lia_insights: 200, skills_match_percentage: 100,
    technical_skills: 200, soft_skills: 180, languages: 150,
    certifications: 180, interests: 150, education: 200,
    location_city: 120, location_state: 100, location_country: 100,
    address_street: 180, address_number: 80, address_district: 120,
    address_zip: 100, address_complement: 150,
    is_remote: 100, willing_to_relocate: 100, mobility: 100,
    work_model_preference: 130, contract_type_preference: 130,
    current_salary: 130, salary_currency: 80, desired_salary_min: 130,
    desired_salary_max: 130, salary_expectation_clt: 130,
    salary_expectation_pj: 130, salary_expectation_freelance: 130,
    resume_url: 150, resume_text: 200, cover_letter: 200,
    ats_source_name: 120, ats_candidate_id: 120, pearch_profile_id: 120,
    is_open_to_work: 100, is_decision_maker: 120, is_top_universities: 130,
    is_hiring: 100, headline: 250, expertise: 200,
    linkedin_followers_count: 120, linkedin_connections_count: 120,
    outreach_message: 300, best_personal_email: 180, phone_types: 150,
    estimated_age: 100, match_reasoning: 300, overall_summary: 300,
    query_insights: 350, pearch_insights: 200, middle_name: 120,
    best_business_email: 200, personal_emails: 180, business_emails: 180,
    company_followers_count: 130, company_keywords: 200,
    status: 120, is_active: 80, is_blacklisted: 100, blacklist_reason: 150,
    preferred_contact_method: 130, best_time_to_contact: 130, communication_consent: 100,
    completed_register: 100, accept_terms: 100,
    tags: 150, notes: 200, additional_data: 150,
    created_at: 130, updated_at: 130, last_contacted_at: 130, last_activity_at: 130
  })

  const [draggedColumnId, setDraggedColumnId] = useState<string | null>(null)
  const [dragOverColumnId, setDragOverColumnId] = useState<string | null>(null)
  const [columnOrder, setColumnOrder] = useState<string[]>([
    'checkbox', 'id', 'candidato', 'cargo', 'empresa', 'salario_mensal', 'localizacao', 'modelo_trabalho', 'acoes'
  ])

  const isColumnVisible = (columnId: string) => {
    const column = tableColumns.find(col => col.id === columnId)
    return column ? column.visible : false
  }

  const visibleTableColumns = tableColumns
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order)

  const handleToggleColumnConfig = () => {
    setShowColumnConfig(!showColumnConfig)
  }

  const setCandidateTableColumns = useUIPreferencesStore(s => s.setCandidateTableColumns)
  const setCandidateColumnViews = useUIPreferencesStore(s => s.setCandidateColumnViews)
  const setCandidateTableColumnOrder = useUIPreferencesStore(s => s.setCandidateTableColumnOrder)

  const handleSaveColumns = () => {
    setCandidateTableColumns(tableColumns as unknown as Parameters<typeof setCandidateTableColumns>[0])
    setShowColumnConfig(false)
  }

  const handleSaveColumnView = (view: Record<string, unknown>) => {
    const newView = {
      ...view,
      id: Date.now().toString(),
      createdAt: new Date().toISOString()
    }
    const updatedViews = [...savedColumnViews, newView] as typeof savedColumnViews
    setSavedColumnViews(updatedViews)
    setCandidateColumnViews(updatedViews as Parameters<typeof setCandidateColumnViews>[0])
  }

  const handleLoadColumnView = (view: Record<string, unknown>) => {
    setTableColumns(view.columns as typeof tableColumns)
  }

  const handleDeleteColumnView = (viewId: string) => {
    const updatedViews = savedColumnViews.filter(view => view.id !== viewId)
    setSavedColumnViews(updatedViews)
    setCandidateColumnViews(updatedViews as Parameters<typeof setCandidateColumnViews>[0])
  }

  const startResize = (column: string, event: React.MouseEvent) => {
    event.preventDefault()
    const startX = event.clientX
    const startWidth = columnWidths[column as keyof typeof columnWidths]

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(80, startWidth + (e.clientX - startX))
      setColumnWidths(prev => ({ ...prev, [column]: newWidth }))
    }
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  const handleColumnDragStart = (columnId: string, e: React.DragEvent) => {
    setDraggedColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', columnId)
    const dragImage = document.createElement('div')
    dragImage.style.opacity = '0'
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 0, 0)
    setTimeout(() => document.body.removeChild(dragImage), 0)
  }

  const handleColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedColumnId && draggedColumnId !== columnId && columnId !== 'checkbox' && columnId !== 'acoes') {
      setDragOverColumnId(columnId)
    }
  }

  const handleColumnDragLeave = () => {
    setDragOverColumnId(null)
  }

  const handleColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedColumnId || draggedColumnId === targetColumnId) {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }
    if (targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }
    setColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      if (draggedIndex === -1 || targetIndex === -1) return prev
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedColumnId)
      setCandidateTableColumnOrder(newOrder)
      return newOrder
    })
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }

  const handleColumnDragEnd = () => {
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }

  const storedColumnOrder = useUIPreferencesStore(s => s.candidateTableColumnOrder)

  // intentional: run once on mount to restore persisted column order; adding storedColumnOrder would cause re-runs on every store write
   
  useEffect(() => {
    const defaultOrder = ['checkbox', 'id', 'candidato', 'cargo', 'empresa', 'salario_mensal', 'localizacao', 'modelo_trabalho', 'acoes']
    const savedOrder = storedColumnOrder
    if (savedOrder) {
      try {
        const parsed = savedOrder
        const validOrder = defaultOrder.filter(id => parsed.includes(id))
        if (validOrder.length === defaultOrder.length) {
          const orderedCols = parsed.filter((id: string) => defaultOrder.includes(id))
          const finalOrder = ['checkbox', ...orderedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes'), 'acoes']
          setColumnOrder(finalOrder)
        } else {
          setColumnOrder(defaultOrder)
        }
      } catch (e) {
        setColumnOrder(defaultOrder)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentional: mount-only init from persisted store; adding deps would re-run on every store write

  return {
    state: {
      showColumnConfig, tableColumns, savedColumnViews, columnWidths,
      draggedColumnId, dragOverColumnId, columnOrder,
      visibleTableColumns,
    },
    actions: {
      setShowColumnConfig, setTableColumns, setSavedColumnViews, setColumnWidths,
      setDraggedColumnId, setDragOverColumnId, setColumnOrder,
      isColumnVisible,
      handleToggleColumnConfig, handleSaveColumns,
      handleSaveColumnView, handleLoadColumnView, handleDeleteColumnView,
      startResize,
      handleColumnDragStart, handleColumnDragOver, handleColumnDragLeave,
      handleColumnDrop, handleColumnDragEnd,
    },
  }
}
