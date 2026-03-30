"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { AISearchToggle } from "@/components/ai-search-toggle"
import { Search, Filter, Plus, MapPin, Calendar, Users, DollarSign, Eye, Edit, Share2, Clock, Layout, Layers3, ChevronDown, ChevronUp, BarChart3, TrendingUp, TrendingDown, FileText, ExternalLink, Briefcase, Building, Target, CheckCircle, Linkedin, Globe, Shield, Hash, UserCheck, Heart } from "lucide-react"
import { JobKanbanPage } from "./job-kanban-page"
import { JobReportModal } from "@/components/job-report-modal"

interface JobFunnel {
  total: number
  screening: number
  interview: number
  final: number
  hired: number
}

interface Job {
  id: number
  jobId: string
  title: string
  department: string
  location: string
  type: string
  level: string
  salary: string
  status: "Ativa" | "Paralisada" | "Concluída" | "Cancelada"
  openDate: string
  deadline?: string
  description: string
  requirements: string[]
  benefits: string[]
  manager: string
  managerEmail: string
  priority: "alta" | "média" | "baixa"
  funnel: JobFunnel
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  isConfidential: boolean
  nps: number
}

const jobs: Job[] = [
  {
    id: 1,
    jobId: "WDT-2025-001",
    title: "UX Designer Sênior",
    department: "Design",
    location: "São Paulo, SP",
    type: "CLT",
    level: "Sênior",
    salary: "R$ 8.000 - R$ 12.000",
    status: "Ativa",
    openDate: "2025-03-01",
    deadline: "2025-04-01",
    description: "Procuramos um UX Designer experiente para liderar projetos de design de produtos digitais...",
    requirements: ["5+ anos de experiência", "Figma", "Prototipagem", "Design System"],
    benefits: ["Vale alimentação", "Plano de saúde", "Home office"],
    manager: "Ana Silva",
    managerEmail: "ana.silva@sodexo.com",
    priority: "alta",
    funnel: { total: 45, screening: 23, interview: 12, final: 6, hired: 0 },
    publishedLinkedIn: true,
    publishedWebsite: true,
    isConfidential: false,
    nps: 82
  },
  {
    id: 2,
    jobId: "WDT-2025-002",
    title: "Desenvolvedor React Sênior",
    department: "Tecnologia",
    location: "Remote",
    type: "PJ",
    level: "Sênior",
    salary: "R$ 10.000 - R$ 15.000",
    status: "Ativa",
    openDate: "2025-02-15",
    deadline: "2025-03-30",
    description: "Buscamos desenvolvedor React experiente para integrar nossa equipe de produtos...",
    requirements: ["React", "TypeScript", "Next.js", "Git"],
    benefits: ["Flexibilidade de horário", "Equipment allowance", "Cursos"],
    manager: "Carlos Santos",
    managerEmail: "carlos.santos@sodexo.com",
    priority: "alta",
    funnel: { total: 68, screening: 34, interview: 18, final: 8, hired: 2 },
    publishedLinkedIn: true,
    publishedWebsite: false,
    isConfidential: false,
    nps: 78
  },
  {
    id: 3,
    jobId: "WDT-2025-003",
    title: "Product Manager",
    department: "Produto",
    location: "São Paulo, SP",
    type: "CLT",
    level: "Sênior",
    salary: "R$ 12.000 - R$ 18.000",
    status: "Paralisada",
    openDate: "2025-03-10",
    deadline: "2025-04-15",
    description: "Product Manager para liderar estratégia e desenvolvimento de produtos digitais...",
    requirements: ["Product Strategy", "Analytics", "Scrum", "Roadmapping"],
    benefits: ["Stock options", "Plano de saúde premium", "Desenvolvimento profissional"],
    manager: "Maria Costa",
    managerEmail: "maria.costa@sodexo.com",
    priority: "média",
    funnel: { total: 28, screening: 15, interview: 8, final: 3, hired: 0 },
    publishedLinkedIn: false,
    publishedWebsite: true,
    isConfidential: true,
    nps: 75
  },
  {
    id: 4,
    jobId: "WDT-2025-004",
    title: "Desenvolvedor Node.js",
    department: "Tecnologia",
    location: "Porto Alegre, RS",
    type: "CLT",
    level: "Pleno",
    salary: "R$ 6.500 - R$ 9.500",
    status: "Concluída",
    openDate: "2025-02-20",
    deadline: "2025-03-25",
    description: "Desenvolvedor backend para APIs e microserviços em Node.js...",
    requirements: ["Node.js", "MongoDB", "Docker", "AWS"],
    benefits: ["Horário flexível", "Plano de saúde", "Vale transporte"],
    manager: "João Lima",
    managerEmail: "joao.lima@sodexo.com",
    priority: "baixa",
    funnel: { total: 52, screening: 28, interview: 15, final: 8, hired: 3 },
    publishedLinkedIn: true,
    publishedWebsite: true,
    isConfidential: false,
    nps: 85
  },
  {
    id: 5,
    jobId: "WDT-2025-005",
    title: "Data Scientist Senior",
    department: "Dados",
    location: "Remote",
    type: "CLT",
    level: "Sênior",
    salary: "R$ 10.000 - R$ 15.000",
    status: "Cancelada",
    openDate: "2025-01-15",
    description: "Cientista de dados para análises avançadas e machine learning...",
    requirements: ["Python", "Machine Learning", "SQL", "TensorFlow"],
    benefits: ["Home office", "Equipment allowance", "Cursos especializados"],
    manager: "Rafael Oliveira",
    managerEmail: "rafael.oliveira@sodexo.com",
    priority: "média",
    funnel: { total: 15, screening: 8, interview: 3, final: 1, hired: 0 },
    publishedLinkedIn: false,
    publishedWebsite: false,
    isConfidential: true,
    nps: 70
  }
]

const statusColors = {
  "Ativa": "bg-ethereal-green-light text-ethereal-green border-ethereal-green/30",
  "Paralisada": "bg-warm-energy-light text-warm-energy border-warm-energy/30",
  "Concluída": "bg-ai-aqua-light text-ai-aqua border-ai-aqua/30",
  "Cancelada": "bg-electric-red-light text-electric-red border-electric-red/30"
}

const priorityColors = {
  "alta": "border-l-red-500",
  "média": "border-l-yellow-500",
  "baixa": "border-l-green-500"
}

export function Jobs2Page() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedStatus, setSelectedStatus] = useState("Todas")
  const [selectedDepartment, setSelectedDepartment] = useState("Todos")
  const [showKanban, setShowKanban] = useState(false)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [showReport, setShowReport] = useState(false)
  const [reportJob, setReportJob] = useState<Job | null>(null)

  const handleSearch = (query: string) => {
    setSearchTerm(query)
  }

  const handleAISearch = (query: string, aiResults: any) => {
    setSearchTerm(query)

    // Aplicar filtros inteligentes baseados nos resultados da IA
    if (aiResults?.filters) {
      if (aiResults.filters.status) {
        setSelectedStatus(aiResults.filters.status)
      }
      if (aiResults.filters.department) {
        setSelectedDepartment(aiResults.filters.department)
      }
    }
  }

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.location.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = selectedStatus === "Todas" || job.status === selectedStatus
    const matchesDepartment = selectedDepartment === "Todos" || job.department === selectedDepartment

    return matchesSearch && matchesStatus && matchesDepartment
  })

  const handleJobClick = (job: Job) => {
    setSelectedJob(job)
    setShowKanban(true)
  }

  const handleBackToJobs = () => {
    setShowKanban(false)
    setSelectedJob(null)
  }

  const handleShowReport = (job: Job) => {
    setReportJob(job)
    setShowReport(true)
  }

  const handleCloseReport = () => {
    setShowReport(false)
    setReportJob(null)
  }

  // Group jobs by status for simple view
  const jobsByStatus = {
    "Ativa": filteredJobs.filter(j => j.status === "Ativa"),
    "Paralisada": filteredJobs.filter(j => j.status === "Paralisada"),
    "Concluída": filteredJobs.filter(j => j.status === "Concluída"),
    "Cancelada": filteredJobs.filter(j => j.status === "Cancelada")
  }

  const uniqueStatuses = Array.from(new Set(jobs.map(j => j.status)))
  const uniqueDepartments = Array.from(new Set(jobs.map(j => j.department)))

  // Job Card Component for Simple View
  const JobCard = ({ job }: { job: Job }) => (
    <Card className={`hover:transition-shadow border-l-4 ${priorityColors[job.priority]} bg-white dark:bg-lia-bg-secondary`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-mono text-gray-600 dark:text-lia-text-tertiary">{job.jobId}</span>
              </div>
              {job.isConfidential && (
                <Badge variant="outline" className="text-xs border-wedo-orange/30 text-wedo-orange">
                  <Shield className="w-3 h-3 mr-1" />
                  Confidencial
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                {job.title}
              </h3>
              <Badge
                variant="outline"
                className={`text-xs ${statusColors[job.status]}`}
              >
                {job.status}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {job.department}
              </Badge>
            </div>

            <div className="flex items-center gap-2 mb-3">
              <UserCheck className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-600 dark:text-lia-text-tertiary">
                Gestor: {job.manager}
              </span>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-lia-text-tertiary mb-3">
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                <span>{job.location}</span>
              </div>
              <div className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                <span>{job.salary}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                <span>Aberta em {new Date(job.openDate).toLocaleDateString("pt-BR")}</span>
              </div>
            </div>

            <p className="text-sm text-gray-600 dark:text-lia-text-tertiary mb-4 line-clamp-2">
              {job.description}
            </p>

            {/* Recruitment Funnel for this job */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-3">Funil de Candidatos</h4>
              <div className="grid grid-cols-5 gap-2">
                <div className="text-center">
                  <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-default">
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-50">{job.funnel.total}</div>
                  </div>
                  <div className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">Total</div>
                </div>
                <div className="text-center">
                  <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-default">
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-50">{job.funnel.screening}</div>
                  </div>
                  <div className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">Triagem</div>
                </div>
                <div className="text-center">
                  <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-default">
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-50">{job.funnel.interview}</div>
                  </div>
                  <div className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">Entrevista</div>
                </div>
                <div className="text-center">
                  <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-default">
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-50">{job.funnel.final}</div>
                  </div>
                  <div className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">Final</div>
                </div>
                <div className="text-center">
                  <div className="bg-gray-50 dark:bg-lia-bg-elevated rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-default">
                    <div className="text-sm font-semibold text-gray-950 dark:text-gray-50">{job.funnel.hired}</div>
                  </div>
                  <div className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">Contratado</div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
              {job.requirements.slice(0, 4).map((req, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {req}
                </Badge>
              ))}
              {job.requirements.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{job.requirements.length - 4} mais
                </Badge>
              )}
            </div>

            {/* Publication Status */}
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600 dark:text-lia-text-tertiary">Publicações:</span>
                <div className="flex items-center gap-1">
                  <Linkedin className={`w-4 h-4 ${job.publishedLinkedIn ? 'text-gray-600' : 'text-gray-600'}`} />
                  <span className="text-xs">{job.publishedLinkedIn ? 'LinkedIn' : ''}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Globe className={`w-4 h-4 ${job.publishedWebsite ? 'text-status-success' : 'text-gray-600'}`} />
                  <span className="text-xs">{job.publishedWebsite ? 'Website' : ''}</span>
                </div>
              </div>
            </div>

            {/* NPS Score */}
            <div className="flex items-center gap-2 mb-3">
              <Heart className="w-4 h-4 text-wedo-magenta" />
              <span className="text-sm text-gray-600 dark:text-lia-text-tertiary">
                NPS: <span className="font-semibold text-gray-950 dark:text-gray-50">{job.nps}</span>
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-2 ml-4">
            <Button size="sm" variant="outline" className="gap-2" onClick={() => handleJobClick(job)}>
              <Eye className="w-4 h-4" />
              Ver Kanban
            </Button>
            <Button size="sm" variant="outline" className="gap-2">
              <Edit className="w-4 h-4" />
              Editar
            </Button>

            <Button
              size="sm"
              variant="default"
              className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              onClick={() => handleShowReport(job)}
            >
              <FileText className="w-4 h-4" />
              Gerar Relatório
            </Button>

            {/* Publication Buttons */}
            <div className="space-y-1">
              <Button
                size="sm"
                variant={job.publishedLinkedIn ? "secondary" : "outline"}
                className="w-full gap-2"
                disabled={job.publishedLinkedIn}
              >
                <Linkedin className="w-4 h-4" />
                {job.publishedLinkedIn ? 'Publicado' : 'Publicar LinkedIn'}
              </Button>
              <Button
                size="sm"
                variant={job.publishedWebsite ? "secondary" : "outline"}
                className="w-full gap-2"
                disabled={job.publishedWebsite}
              >
                <Globe className="w-4 h-4" />
                {job.publishedWebsite ? 'No Site' : 'Publicar Site'}
              </Button>
            </div>

            <Button size="sm" variant="outline" className="gap-2">
              <Share2 className="w-4 h-4" />
              Compartilhar
            </Button>
          </div>
        </div>

        {job.deadline && (
          <div className="bg-gray-50 dark:bg-lia-bg-elevated/50 rounded-md p-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-lia-text-tertiary">
                Prazo para aplicações: {new Date(job.deadline).toLocaleDateString("pt-BR")}
              </span>
              <span className={`font-medium ${
                new Date(job.deadline) < new Date() ? 'text-status-error' : 'text-status-success'
              }`}>
                {Math.ceil((new Date(job.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} dias restantes
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )

  // Show Kanban view if a job is selected
  if (showKanban && selectedJob) {
    return <JobKanbanPage job={selectedJob} onBack={handleBackToJobs} />
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50 mb-2 font-['Open_Sans',sans-serif]">
                Vagas (Layout Básico)
              </h1>
              <p className="text-gray-600 dark:text-lia-text-tertiary">
                Visualização simplificada de todas as posições abertas
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button className="gap-2">
                <Plus className="w-4 h-4" />
                Nova Vaga
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <Card className="bg-white dark:bg-lia-bg-secondary p-4 mb-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <AISearchToggle
                placeholder="Buscar por título, departamento ou localização..."
                onSearch={handleSearch}
                onAISearch={handleAISearch}
                contextType="jobs"
              />
            </div>

            <div className="flex gap-3">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
              >
                <option value="Todas">Todos Status</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>

              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
              >
                <option value="Todos">Todos Departamentos</option>
                {uniqueDepartments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>

              <Button variant="outline" size="sm" className="gap-2">
                <Filter className="w-4 h-4" />
                Filtros
              </Button>
            </div>
          </div>
        </Card>

        {/* Simple Layout - Grouped by Status */}
        <div className="space-y-8">
          {Object.entries(jobsByStatus).map(([status, statusJobs]) => (
            statusJobs.length > 0 && (
              <div key={status}>
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                    {status}
                  </h2>
                  <Badge
                    variant="outline"
                    className={statusColors[status as keyof typeof statusColors]}
                  >
                    {statusJobs.length} {statusJobs.length === 1 ? 'vaga' : 'vagas'}
                  </Badge>
                </div>
                <div className="space-y-4">
                  {statusJobs.map((job) => (
                    <JobCard key={job.id} job={job} />
                  ))}
                </div>
              </div>
            )
          ))}
        </div>

        {filteredJobs.length === 0 && (
          <Card className="bg-white dark:bg-lia-bg-secondary p-8 text-center">
            <div className="text-gray-600 dark:text-lia-text-tertiary">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">Nenhuma vaga encontrada</h3>
              <p className="text-sm">Tente ajustar os filtros ou termos de busca</p>
            </div>
          </Card>
        )}

        {/* Job Report Modal */}
        {showReport && reportJob && (
          <JobReportModal
            isOpen={showReport}
            onClose={handleCloseReport}
            job={reportJob}
          />
        )}
      </div>
    </div>
  )
}
