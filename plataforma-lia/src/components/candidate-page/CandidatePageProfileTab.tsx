"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  MapPin, Building, GraduationCap, Briefcase, Award,
  Brain, CheckCircle, AlertCircle, Clock, Users,
  DollarSign, User, Languages, Home, Cake,
  Code, Linkedin
} from "lucide-react"

interface OpinionRecord {
  id?: string
  score?: number
  wsi_score?: number
  job_vacancy_id?: string
  job_vacancy_title?: string
  archetype?: string
  recommendation?: string
  summary?: string
  content?: string
  strengths?: string[]
  concerns?: string[]
  created_at?: string
}

interface ExperienceRecord {
  title?: string
  position?: string
  role?: string
  company?: string
  company_name?: string
  location?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
  is_current?: boolean
  description?: string
  industries?: string[]
  technologies?: string[]
  company_size?: string
  company_size_range?: string
  is_startup?: boolean
  duration_years?: number
}

interface EducationRecord {
  degree?: string
  title?: string
  field_of_study?: string
  fieldOfStudy?: string
  school?: string
  institution?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
}

interface CandidateRecord {
  name: string
  position?: string
  location?: string
  skills?: string[]
  certifications?: string[]
  location_city?: string
  location_state?: string
  location_country?: string
  address_street?: string
  address_number?: string
  address_district?: string
  address_zip?: string
  address_complement?: string
  is_remote?: boolean
  willing_to_relocate?: boolean
  work_model_preference?: string
  contract_type_preference?: string
  created_at?: string
  updated_at?: string
  last_contacted_at?: string
  last_activity_at?: string
  is_active?: boolean
  source?: string
  tags?: string[]
  date_of_birth?: string
  gender?: string
  nationality?: string
  marital_status?: string
  estimated_age?: number
  headline?: string
  is_open_to_work?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_hiring?: boolean
  linkedin_connections_count?: number
  linkedin_followers_count?: number
  pearch_profile_id?: string
  liaAnalysis?: { score?: number; fitScore?: number }
  workHistory?: ExperienceRecord[]
  work_history?: ExperienceRecord[]
  experiences?: ExperienceRecord[]
  education?: EducationRecord[]
  additional_data?: {
    work_history?: ExperienceRecord[]
    experiences?: ExperienceRecord[]
    education?: EducationRecord[]
  }
}

export interface CandidatePageProfileTabProps {
  candidate: CandidateRecord
  experiences: ExperienceRecord[]
  education: EducationRecord[]
  liaScore: number
  opinionsHistory: OpinionRecord[]
  formatDateShort: (dateStr: string | null | undefined) => string
  formatDate: (dateStr: string | null | undefined) => string | null
  calculateAge: (dateOfBirth: string | null | undefined) => number | null
  hasPersonalData: (c: Record<string, unknown>) => boolean
  hasPearchData: (c: Record<string, unknown>) => boolean
}

export function CandidatePageProfileTab({
  candidate,
  experiences,
  education,
  liaScore,
  opinionsHistory,
  formatDateShort,
  formatDate,
  calculateAge,
  hasPersonalData,
  hasPearchData,
}: CandidatePageProfileTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <Card>
          <CardContent className="p-4">
            <h4 className="text-sm font-medium text-gray-950 mb-3">Skills Principais</h4>
            <div className="flex flex-wrap gap-1.5">
              {(candidate.skills || ['Figma', 'Sketch', 'Design Systems', 'Prototipagem', 'User Research', 'Wireframing', 'Adobe XD', 'Prototyping', 'UI Design', 'UX Strategy']).map((skill: string, index: number) => (
                <Badge key={index} variant="outline" className="text-xs px-2 py-0.5">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border border-lia-border-subtle dark:border-lia-border-subtle overflow-hidden">
          <div className="p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                  <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-micro font-medium text-gray-800 dark:text-lia-text-primary uppercase tracking-wider">Parecer LIA</span>
                    <span className="text-micro font-semibold text-status-success">
                      Score: {opinionsHistory[0]?.score || liaScore}/100
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    {opinionsHistory[0]?.job_vacancy_id ? (
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default flex items-center gap-1">
                        <Briefcase className="w-2.5 h-2.5" />
                        #{String(opinionsHistory[0].job_vacancy_id).slice(0, 6)} - {opinionsHistory[0].job_vacancy_title || 'Vaga vinculada'}
                      </Badge>
                    ) : (
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary">
                        Sem vaga vinculada
                      </Badge>
                    )}
                    {opinionsHistory[0]?.archetype && (
                      <span className="text-micro lia-text-secondary">{opinionsHistory[0].archetype}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {opinionsHistory[0]?.recommendation === 'approved' && (
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-status-success/10 text-status-success flex items-center gap-0.5">
                    <CheckCircle className="w-2.5 h-2.5" />
                    APROVADO
                  </Badge>
                )}
                {opinionsHistory[0]?.recommendation === 'pending_review' && (
                  <Badge className="text-micro px-1.5 py-0 h-4 bg-status-warning/10 text-status-warning flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    PENDENTE
                  </Badge>
                )}
              </div>
            </div>
            
            <p className="text-micro text-gray-800 dark:text-lia-text-primary leading-relaxed mb-2">
              {opinionsHistory[0]?.summary || 'UX Designer sênior com 5+ anos de experiência em produtos digitais. Excelente liderança técnica e visão estratégica.'}
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <h4 className="text-micro font-medium mb-1 flex items-center gap-1 text-status-success">
                  <CheckCircle className="w-3 h-3" />
                  Pontos Fortes
                </h4>
                <ul className="space-y-0.5">
                  {(opinionsHistory[0]?.strengths || ['Ferramentas de design', 'Design systems', 'Liderança de equipes']).slice(0, 3).map((s: string, i: number) => (
                    <li key={i} className="text-micro text-gray-600 dark:text-lia-text-tertiary flex items-start gap-1">
                      <span className="text-status-success">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-micro font-medium mb-1 flex items-center gap-1 text-status-warning">
                  <AlertCircle className="w-3 h-3" />
                  A Desenvolver
                </h4>
                <ul className="space-y-0.5">
                  {(opinionsHistory[0]?.concerns || ['Acessibilidade avançada', 'Analytics de UX', 'Motion design']).slice(0, 3).map((c: string, i: number) => (
                    <li key={i} className="text-micro text-gray-600 dark:text-lia-text-tertiary flex items-start gap-1">
                      <span className="text-status-warning">•</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
            <div className="flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-gray-700 dark:text-lia-text-secondary" />
              <CardTitle className="text-sm font-semibold text-gray-950">
                Experiência Profissional
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            {experiences.length > 0 ? (
              experiences.map((exp: ExperienceRecord, index: number) => {
                const title = exp.title || exp.position || exp.role || ''
                const company = exp.company || exp.company_name || ''
                const location = exp.location || ''
                const startDate = exp.start_date || exp.startDate || ''
                const endDate = exp.is_current ? 'Atual' : (exp.end_date || exp.endDate || '')
                const description = exp.description || ''
                const industries = Array.isArray(exp.industries) ? exp.industries : []
                const technologies = Array.isArray(exp.technologies) ? exp.technologies : []
                const companySize = exp.company_size || exp.company_size_range || null
                const isStartup = exp.is_startup
                
                return (
<div key={index} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-lia-border-default dark:border-lia-border-default'} pl-3`}>
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <div>
                        <h5 className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">{title || 'Cargo não informado'}</h5>
                        <p className="text-xs text-gray-600 dark:text-lia-text-tertiary">
                          {company || 'Empresa não informada'}
                          {location && ` • ${location}`}
                          {exp.duration_years && <span className="lia-text-secondary ml-1">({exp.duration_years.toFixed(1)} anos)</span>}
                        </p>
                      </div>
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {formatDateShort(startDate)}{startDate && endDate ? ' - ' : ''}{endDate === 'Atual' ? 'Atual' : formatDateShort(endDate)}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {industries.slice(0, 2).map((ind: string, idx: number) => (
                        <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-default">
                          <Building className="w-2.5 h-2.5 mr-0.5" />
                          {ind}
                        </span>
                      ))}
                      {isStartup && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30">
                          🚀 Startup
                        </span>
                      )}
                      {companySize && (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary border border-lia-border-subtle dark:border-lia-border-subtle">
                          <Users className="w-2.5 h-2.5" />
                          {companySize}
                        </span>
                      )}
                    </div>

                    {technologies.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        <span className="text-micro lia-text-secondary flex items-center gap-0.5">
                          <Code className="w-2.5 h-2.5" />
                          Stack:
                        </span>
                        {technologies.slice(0, 6).map((tech: string, idx: number) => (
                          <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 dark:bg-lia-bg-secondary text-gray-800 dark:text-lia-text-primary">
                            {tech}
                          </span>
                        ))}
                        {technologies.length > 6 && (
                          <span className="text-micro lia-text-secondary">+{technologies.length - 6}</span>
                        )}
                      </div>
                    )}
                    
                    {description && (
                      <p className="text-xs text-gray-600 dark:text-lia-text-tertiary mt-1">{description}</p>
                    )}
                  </div>
                )
              })
            ) : (
              <p className="text-sm text-gray-500 italic">Não informado</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-wedo-purple" />
              <CardTitle className="text-sm font-semibold text-gray-950">
                Formação Acadêmica
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {education.length > 0 ? (
              education.map((edu: EducationRecord, index: number) => (
                <div key={index} className={`flex items-start justify-between gap-2 ${index < education.length - 1 ? 'pb-3 border-b border-lia-border-subtle' : ''}`}>
                  <div>
                    <h5 className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">
                      {edu.degree || edu.title || 'Formação'}
                      {(edu.field_of_study || edu.fieldOfStudy) && ` em ${edu.field_of_study || edu.fieldOfStudy}`}
                    </h5>
                    <p className="text-xs text-gray-600 dark:text-lia-text-tertiary">{edu.school || edu.institution || 'Instituição não informada'}</p>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap">
                    {edu.start_date || edu.startDate || ''}{(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? ' - ' : ''}{edu.end_date || edu.endDate || ''}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">Não informado</p>
            )}
          </CardContent>
        </Card>

        {candidate.certifications && candidate.certifications.length > 0 && (
          <Card>
            <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-status-success" />
                <CardTitle className="text-sm font-semibold text-gray-950">
                  Certificações
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-1.5">
                {candidate.certifications.map((cert: string, idx: number) => (
                  <Badge key={idx} variant="outline" className="text-xs px-2 py-0.5 bg-status-success/10 text-status-success border-status-success/30">
                    {cert}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <Card className="">
          <CardHeader className="py-3 bg-wedo-green/10 dark:bg-wedo-green/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-status-success" />
                <CardTitle className="text-sm font-bold text-gray-950">
                  Pacote de Remuneração Total
                </CardTitle>
              </div>
              <Badge className="text-xs px-2 py-0.5 bg-status-success text-white">
                Total Compensation
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-3">
              <div className="bg-gray-50 dark:bg-lia-bg-secondary p-3 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">Salário Mensal</span>
                  <span className="text-sm font-bold text-gray-950">
                    R$ 15.000,00
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">Anualizado (13,33x)</span>
                  <span className="text-sm font-semibold text-status-success">
                    R$ 199.950,00
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">Bônus Anual</span>
                  <span className="text-xs font-semibold text-gray-950">
                    R$ 45.000,00
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600 dark:text-lia-text-tertiary">Stock Options</span>
                  <span className="text-xs font-semibold text-gray-950">
                    R$ 25.000,00
                  </span>
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-2">Benefícios Inclusos:</p>
                <div className="flex flex-wrap gap-1">
                  <Badge className="bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary text-xs">VR R$1.500</Badge>
                  <Badge className="bg-status-success/10 text-status-success text-xs">Saúde Premium</Badge>
                  <Badge className="bg-wedo-purple/10 text-wedo-purple text-xs">Gympass</Badge>
                  <Badge className="bg-wedo-orange/10 text-wedo-orange text-xs">Home Office</Badge>
                </div>
              </div>

              <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-gray-950">
                    TOTAL ANUAL
                  </span>
                  <span className="text-lg font-bold text-status-success">
                    R$ 349.190,00
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
            <div className="flex items-center gap-2">
              <Languages className="w-4 h-4 text-wedo-purple" />
              <CardTitle className="text-sm font-semibold text-gray-950">
                Idiomas
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-950">
                Português
              </span>
              <Badge className="text-xs px-2 py-0.5 bg-gray-100 text-status-success">
                Nativo
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-950">
                Inglês
              </span>
              <Badge className="text-xs px-2 py-0.5 bg-gray-400 text-white">
                Fluente
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-950">
                Espanhol
              </span>
              <Badge className="text-xs px-2 py-0.5 bg-gray-200 lia-text-base">
                Intermediário
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
            <div className="flex items-center gap-2">
              <Home className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
              <CardTitle className="text-sm font-semibold text-gray-950">
                Detalhes Adicionais
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div>
              <h5 className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1">Localização</h5>
              <p className="text-sm text-gray-600 dark:text-lia-text-tertiary">
                {[candidate.location_city, candidate.location_state, candidate.location_country]
                  .filter(Boolean).join(', ') || candidate.location || 'Não informado'}
              </p>
              {(candidate.address_street || candidate.address_district) && (
                <p className="text-xs text-gray-500 mt-0.5">
                  {[candidate.address_street, candidate.address_number, candidate.address_district, candidate.address_zip, candidate.address_complement]
                    .filter(Boolean).join(', ')}
                </p>
              )}
            </div>

            <div>
              <h5 className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1.5">Preferências de Trabalho</h5>
              <div className="flex flex-wrap gap-1.5">
                {candidate.is_remote && (
                  <Badge variant="outline" className="text-xs bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-default">Remoto</Badge>
                )}
                {candidate.willing_to_relocate && (
                  <Badge variant="outline" className="text-xs bg-status-success/10 text-status-success border-status-success/30">Aceita Relocação</Badge>
                )}
                {candidate.work_model_preference && (
                  <Badge variant="outline" className="text-xs">{candidate.work_model_preference}</Badge>
                )}
                {candidate.contract_type_preference && (
                  <Badge variant="outline" className="text-xs">{candidate.contract_type_preference}</Badge>
                )}
              </div>
            </div>

            <div>
              <h5 className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1">Datas</h5>
              <div className="space-y-0.5 text-xs text-gray-600 dark:text-lia-text-tertiary">
                {candidate.created_at && <p>Cadastro: {formatDate(candidate.created_at)}</p>}
                {candidate.updated_at && <p>Atualizado: {formatDate(candidate.updated_at)}</p>}
                {candidate.last_contacted_at && <p>Último contato: {formatDate(candidate.last_contacted_at)}</p>}
                {candidate.last_activity_at && <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>}
              </div>
            </div>

            <div>
              <h5 className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1.5">Status</h5>
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="outline" className={`text-xs ${candidate.is_active ? 'bg-status-success/10 text-status-success dark:text-status-success' : 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-600 dark:text-lia-text-tertiary'}`}>
                  {candidate.is_active ? 'Ativo' : 'Inativo'}
                </Badge>
                {candidate.source && (
                  <Badge variant="outline" className="text-xs">{candidate.source}</Badge>
                )}
              </div>
            </div>

            {candidate.tags && candidate.tags.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1.5">Tags</h5>
                <div className="flex flex-wrap gap-1">
                  {candidate.tags.map((tag: string, idx: number) => (
                    <Badge key={idx} className="text-xs bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-default">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {hasPersonalData(candidate as unknown as Record<string, unknown>) && (
          <Card>
            <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-gray-600 dark:text-lia-text-tertiary" />
                <CardTitle className="text-sm font-semibold text-gray-950">
                  Dados Pessoais
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-2">
              {(candidate.date_of_birth || candidate.estimated_age) && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <Cake className="w-3.5 h-3.5" />
                    Idade
                  </span>
                  <span className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">
                    {calculateAge(candidate.date_of_birth) || candidate.estimated_age} anos
                    {candidate.date_of_birth && (
                      <span className="text-xs lia-text-secondary ml-1">
                        ({formatDate(candidate.date_of_birth)})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {candidate.gender && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Gênero</span>
                  <span className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">{candidate.gender}</span>
                </div>
              )}
              {candidate.nationality && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Nacionalidade</span>
                  <span className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">{candidate.nationality}</span>
                </div>
              )}
              {candidate.marital_status && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Estado Civil</span>
                  <span className="text-sm font-medium text-gray-800 dark:text-lia-text-primary">{candidate.marital_status}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {hasPearchData(candidate as unknown as Record<string, unknown>) && (
          <Card className="border-l-4 border-l-gray-400">
            <CardHeader className="py-3 bg-gray-50 dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <Linkedin className="w-4 h-4 lia-text-base" />
                <CardTitle className="text-sm font-semibold text-gray-950">
                  LinkedIn Insights
                </CardTitle>
                {candidate.pearch_profile_id && (
                  <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary">Pearch</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {candidate.headline && (
                <div>
                  <p className="text-sm text-gray-800 dark:text-lia-text-primary italic">&quot;{candidate.headline}&quot;</p>
                </div>
              )}
              
              <div className="flex flex-wrap gap-1.5">
                {candidate.is_open_to_work && (
                  <Badge className="text-xs bg-status-success/10 text-status-success border-status-success/30">
                    ✓ Open to Work
                  </Badge>
                )}
                {candidate.is_decision_maker && (
                  <Badge className="text-xs bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                    👔 Decision Maker
                  </Badge>
                )}
                {candidate.is_top_universities && (
                  <Badge className="text-xs bg-status-warning/10 text-status-warning border-status-warning/30">
                    🎓 Top Universities
                  </Badge>
                )}
                {candidate.is_hiring && (
                  <Badge className="text-xs bg-gray-100 text-gray-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-default">
                    📢 Hiring
                  </Badge>
                )}
              </div>

              {(candidate.linkedin_connections_count || candidate.linkedin_followers_count) && (
                <div className="flex gap-4 pt-2 border-t border-lia-border-subtle">
                  {candidate.linkedin_connections_count && (
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-800 dark:text-lia-text-primary">
                        {candidate.linkedin_connections_count.toLocaleString('pt-BR')}
                      </p>
                      <p className="text-micro text-gray-500">Conexões</p>
                    </div>
                  )}
                  {candidate.linkedin_followers_count && (
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-800 dark:text-lia-text-primary">
                        {candidate.linkedin_followers_count.toLocaleString('pt-BR')}
                      </p>
                      <p className="text-micro text-gray-500">Seguidores</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
