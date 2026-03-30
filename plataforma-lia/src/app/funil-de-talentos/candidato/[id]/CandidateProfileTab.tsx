"use client"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TabsContent } from "@/components/ui/tabs"
import {
  Award, Brain, Briefcase, Building2, Cake, Code, DollarSign, Download,
  ExternalLink, FileText, GraduationCap, Home, Languages, Lightbulb,
  Linkedin, Mail, User, Users
} from "lucide-react"
import type { CandidateLocal } from "@/services/lia-api"

type CandidateWithExtras = CandidateLocal & {
  estimated_age?: number | null
  headline?: string | null
  is_open_to_work?: boolean
  is_hiring?: boolean
  linkedin_connections_count?: number | null
  linkedin_followers_count?: number | null
}

interface EducationEntry {
  institution?: string
  school?: string
  degree?: string
  title?: string
  field_of_study?: string
  fieldOfStudy?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
  description?: string
}

interface ExperienceEntry {
  company?: string
  company_name?: string
  title?: string
  position?: string
  role?: string
  start_date?: string
  startDate?: string
  end_date?: string
  endDate?: string
  description?: string
  location?: string
  is_current?: boolean
  duration_years?: number
  industries?: string[]
  technologies?: string[]
  company_size?: string
  company_size_range?: string
  is_startup?: boolean
}

interface LanguageEntry {
  language: string
  level: string
}

interface SkillCategoryEntry {
  label: string
  skills: string[]
}

interface CandidateProfileTabProps {
  candidate: CandidateWithExtras
  education: EducationEntry[]
  experiences: ExperienceEntry[]
  skillCategories: Array<[string, SkillCategoryEntry]>
  languagesData: LanguageEntry[]
  calculateAge: (date: string) => number | null
  formatCurrency: (value: number | null | undefined, currency?: string) => string | null
  formatDate: (date: string | null | undefined) => string | null
  formatDateShort: (date: string | null | undefined) => string | null
  getLanguageLevel: (level: string) => { label: string; percent: number; color: string }
  hasDocuments: (c: Record<string, unknown>) => boolean
  hasPearchData: (c: Record<string, unknown>) => boolean
  hasPersonalData: (c: Record<string, unknown>) => boolean
}

export function CandidateProfileTab({
  candidate, education, experiences, skillCategories, languagesData,
  calculateAge, formatCurrency, formatDate, formatDateShort, getLanguageLevel,
  hasDocuments, hasPearchData, hasPersonalData
}: CandidateProfileTabProps) {
  return (
    <>
{/* TAB: PROFILE */}
<TabsContent value="profile" className="mt-4">
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
    {/* LEFT COLUMN (2/3) */}
    <div className="lg:col-span-2 space-y-4">
      {/* Technical Skills */}
      {candidate.technical_skills && candidate.technical_skills.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <Code className="w-4 h-4 lia-text-600" />
              Skills Principais
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.technical_skills.map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs px-2 py-0.5">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Skills Map - Categorized */}
      {skillCategories.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <Code className="w-4 h-4 lia-text-600" />
              Mapa de Skills
              <Badge className="text-xs bg-gray-200 lia-text-800 dark:text-lia-text-primary">
                {candidate.technical_skills?.length || 0} itens
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {skillCategories.map(([key, category]) => (
              <div key={key}>
                <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5">{category.label}</h5>
                <div className="flex flex-wrap gap-1.5">
                  {category.skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs px-2 py-0.5 bg-gray-50">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}

            {/* Soft Skills */}
            {candidate.soft_skills && candidate.soft_skills.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-status-warning mb-1.5 flex items-center gap-1">
                  <Users className="w-3 h-3" /> Soft Skills
                </h5>
                <div className="flex flex-wrap gap-1.5">
                  {candidate.soft_skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs px-2 py-0.5 bg-status-warning/10 text-status-warning border-status-warning/30">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Professional Experience */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
            <Briefcase className="w-4 h-4 lia-text-600" />
            Experiência Profissional
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-4">
          {experiences.length > 0 ? (
            experiences.map((exp, index: number) => {
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
                <div key={`${index}-${company}`} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-lia-border-default'} pl-3`}>
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div>
                      <h5 className="text-sm font-medium lia-text-800">{title || 'Cargo não informado'}</h5>
                      <p className="text-sm lia-text-600">
                        {company || 'Empresa não informada'}
                        {location && ` • ${location}`}
                        {exp.duration_years != null && <span className="lia-text-400 ml-1">({exp.duration_years.toFixed(1)} anos)</span>}
                      </p>
                    </div>
                    <span className="text-xs lia-text-500 whitespace-nowrap">
                      {formatDateShort(startDate)}{startDate && endDate ? ' - ' : ''}{endDate === 'Atual' ? 'Atual' : formatDateShort(endDate)}
                    </span>
                  </div>

                  {/* Metadata Row */}
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {industries.slice(0, 2).map((ind: string) => (
                      <span key={ind} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-lia-bg-primary lia-text-900 dark:lia-text-50 border border-lia-border-subtle dark:border-lia-border-subtle">
                        <Building2 className="w-2.5 h-2.5 mr-0.5" />
                        {ind}
                      </span>
                    ))}
                    {isStartup && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30">
                        🚀 Startup
                      </span>
                    )}
                    {companySize && (
                      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 lia-text-600 border border-lia-border-subtle">
                        <Users className="w-2.5 h-2.5" />
                        {companySize}
                      </span>
                    )}
                  </div>

                  {/* Technologies */}
                  {technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      <span className="text-micro lia-text-400 flex items-center gap-0.5">
                        <Code className="w-2.5 h-2.5" />
                        Stack:
                      </span>
                      {technologies.slice(0, 6).map((tech: string) => (
                        <span key={tech} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 lia-text-800 dark:text-lia-text-primary">
                          {tech}
                        </span>
                      ))}
                      {technologies.length > 6 && (
                        <span className="text-micro lia-text-400">+{technologies.length - 6}</span>
                      )}
                    </div>
                  )}

                  {description && (
                    <p className="text-xs lia-text-600 mt-1">{description}</p>
                  )}
                </div>
              )
            })
          ) : (
            <p className="text-sm lia-text-500 italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Education */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
            <GraduationCap className="w-4 h-4 lia-text-600" />
            Formação Acadêmica
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          {education.length > 0 ? (
            education.map((edu, index: number) => (
              <div key={`edu-${index}-${String(edu.institution || edu.school || index)}`} className={`flex items-start justify-between gap-2 ${index < education.length - 1 ? 'pb-3 border-b border-lia-border-subtle' : ''}`}>
                <div>
                  <h5 className="text-sm font-medium lia-text-800">
                    {edu.degree || edu.title || 'Formação'}
                    {(edu.field_of_study || edu.fieldOfStudy) && ` em ${edu.field_of_study || edu.fieldOfStudy}`}
                  </h5>
                  <p className="text-sm lia-text-600">{edu.school || edu.institution || 'Instituição não informada'}</p>
                </div>
                <span className="text-xs lia-text-500 whitespace-nowrap">
                  {edu.start_date || edu.startDate || ''}{(edu.start_date || edu.startDate) && (edu.end_date || edu.endDate) ? ' - ' : ''}{edu.end_date || edu.endDate || ''}
                </span>
              </div>
            ))
          ) : (
            <p className="text-sm lia-text-500 italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Certifications */}
      {candidate.certifications && candidate.certifications.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <Award className="w-4 h-4 lia-text-600" />
              Certificações
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-2">
              {candidate.certifications.map((cert, idx) => {
                const certName = typeof cert === 'string' ? cert : String((cert as { name?: string }).name || 'Certificação')
                return (
                  <Badge key={idx} variant="secondary" className="text-xs px-2 py-1">
                    {certName}
                  </Badge>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>

    {/* RIGHT COLUMN (1/3) */}
    <div className="space-y-4">
      {/* Salary Card */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
            <DollarSign className="w-4 h-4 lia-text-600" />
            Remuneração
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-2">
          {candidate.current_salary && (
            <div className="flex justify-between items-center">
              <span className="text-xs lia-text-500">Salário Atual</span>
              <span className="text-sm font-medium lia-text-800">{formatCurrency(candidate.current_salary, candidate.salary_currency || 'BRL')}</span>
            </div>
          )}
          {candidate.salary_expectation_clt && (
            <div className="flex justify-between items-center">
              <span className="text-xs lia-text-500">Pretensão CLT</span>
              <span className="text-sm font-medium lia-text-800">{formatCurrency(candidate.salary_expectation_clt)}</span>
            </div>
          )}
          {candidate.salary_expectation_pj && (
            <div className="flex justify-between items-center">
              <span className="text-xs lia-text-500">Pretensão PJ</span>
              <span className="text-sm font-medium lia-text-800">{formatCurrency(candidate.salary_expectation_pj)}</span>
            </div>
          )}
          {candidate.salary_expectation_freelance && (
            <div className="flex justify-between items-center">
              <span className="text-xs lia-text-500">Freelance</span>
              <span className="text-sm font-medium lia-text-800">{formatCurrency(candidate.salary_expectation_freelance)}</span>
            </div>
          )}
          {(candidate.desired_salary_min || candidate.desired_salary_max) && (
            <div className="flex justify-between items-center pt-2 border-t border-lia-border-subtle">
              <span className="text-xs lia-text-500">Faixa Desejada</span>
              <span className="text-sm font-medium lia-text-800">
                {formatCurrency(candidate.desired_salary_min)} - {formatCurrency(candidate.desired_salary_max)}
              </span>
            </div>
          )}
          {candidate.salary_expectation_clt && (
            <div className="flex justify-between items-center pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary -mx-4 px-4 py-2">
              <span className="text-xs font-medium lia-text-800 dark:text-lia-text-primary">Total Anual (CLT)</span>
              <span className="text-sm font-semibold lia-text-900 dark:text-lia-text-primary">
                {formatCurrency((candidate.salary_expectation_clt ?? 0) * 13.33)}
              </span>
            </div>
          )}
          {!candidate.current_salary && !candidate.salary_expectation_clt && !candidate.salary_expectation_pj && (
            <p className="text-sm lia-text-500 italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Languages Card */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
            <Languages className="w-4 h-4 lia-text-600" />
            Idiomas
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          {languagesData.length > 0 ? (
            languagesData.map((lang, index) => {
              const levelInfo = getLanguageLevel(lang.level)
              return (
                <div key={`lang-${lang.language || lang.name || index}`} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">{lang.language}</span>
                    <span className="text-xs lia-text-500">{levelInfo.label}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full ${levelInfo.color}`} 
                      style={{width: `${levelInfo.percent}%`}}
                    />
                  </div>
                </div>
              )
            })
          ) : (
            <p className="text-sm lia-text-500 italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Additional Details Card */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
            <Home className="w-4 h-4 lia-text-600" />
            Detalhes Adicionais
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          {/* Location */}
          <div>
            <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1">Localização</h5>
            <p className="text-sm lia-text-600">
              {[candidate.location_city, candidate.location_state, candidate.location_country]
                .filter(Boolean).join(', ') || 'Não informado'}
            </p>
            {(candidate.address_street || candidate.address_district) && (
              <p className="text-xs lia-text-500 mt-0.5">
                {[candidate.address_street, candidate.address_number, candidate.address_district, candidate.address_zip, candidate.address_complement]
                  .filter(Boolean).join(', ')}
              </p>
            )}
          </div>

          {/* Work Preferences */}
          <div>
            <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5">Preferências de Trabalho</h5>
            <div className="flex flex-wrap gap-1.5">
              {candidate.is_remote && (
                <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-lia-bg-primary lia-text-900 dark:lia-text-50 border-lia-border-default dark:border-lia-border-default">Remoto</Badge>
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

          {/* Dates */}
          <div>
            <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1">Datas</h5>
            <div className="space-y-0.5 text-xs lia-text-600">
              {candidate.created_at && <p>Cadastro: {formatDate(candidate.created_at)}</p>}
              {candidate.updated_at && <p>Atualizado: {formatDate(candidate.updated_at)}</p>}
              {candidate.last_contacted_at && <p>Último contato: {formatDate(candidate.last_contacted_at)}</p>}
              {candidate.last_activity_at && <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>}
            </div>
          </div>

          {/* Status */}
          <div>
            <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5">Status</h5>
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="outline" className={`text-xs ${candidate.is_active ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 lia-text-600'}`}>
                {candidate.is_active ? 'Ativo' : 'Inativo'}
              </Badge>
              {candidate.source && (
                <Badge variant="outline" className="text-xs">{candidate.source}</Badge>
              )}
            </div>
          </div>

          {/* Tags */}
          {candidate.tags && candidate.tags.length > 0 && (
            <div>
              <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5">Tags</h5>
              <div className="flex flex-wrap gap-1">
                {candidate.tags.map((tag) => (
                  <Badge key={tag} className="text-xs bg-gray-100 lia-text-700 border-lia-border-subtle dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:border-lia-border-default">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Personal Data Card - Dados Pessoais */}
      {hasPersonalData(candidate as unknown as Record<string, unknown>) && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <User className="w-4 h-4 lia-text-600" />
              Dados Pessoais
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-2">
            {(candidate.date_of_birth || candidate.estimated_age) && (
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500 flex items-center gap-1">
                  <Cake className="w-3.5 h-3.5" />
                  Idade
                </span>
                <span className="text-sm font-medium lia-text-800">
                  {(candidate.date_of_birth ? calculateAge(candidate.date_of_birth) : null) || candidate.estimated_age} anos
                  {candidate.date_of_birth && (
                    <span className="text-xs lia-text-400 ml-1">
                      ({formatDate(candidate.date_of_birth)})
                    </span>
                  )}
                </span>
              </div>
            )}
            {candidate.gender && (
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Gênero</span>
                <span className="text-sm font-medium lia-text-800">{candidate.gender}</span>
              </div>
            )}
            {candidate.nationality && (
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Nacionalidade</span>
                <span className="text-sm font-medium lia-text-800">{candidate.nationality}</span>
              </div>
            )}
            {candidate.marital_status && (
              <div className="flex justify-between items-center">
                <span className="text-xs lia-text-500">Estado Civil</span>
                <span className="text-sm font-medium lia-text-800">{candidate.marital_status}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* LinkedIn/Pearch Insights Card */}
      {hasPearchData(candidate as unknown as Record<string, unknown>) && (
        <Card className="border-lia-border-subtle border-l-4 border-l-brand-linkedin">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <Linkedin className="w-4 h-4 text-brand-linkedin" />
              LinkedIn Insights
              {candidate.pearch_profile_id && (
                <Badge className="text-micro px-1.5 py-0 bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary">Pearch</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {candidate.headline && (
              <div>
                <p className="text-sm lia-text-800 dark:text-lia-text-primary italic">"{candidate.headline}"</p>
              </div>
            )}

            {/* Badges de Status */}
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
                <Badge className="text-xs bg-gray-50 dark:bg-lia-bg-primary lia-text-900 dark:lia-text-50 border-lia-border-default dark:border-lia-border-default">
                  📢 Hiring
                </Badge>
              )}
            </div>

            {/* Connections & Followers */}
            {(candidate.linkedin_connections_count || candidate.linkedin_followers_count) && (
              <div className="flex gap-4 pt-2 border-t border-lia-border-subtle">
                {candidate.linkedin_connections_count && (
                  <div className="text-center">
                    <p className="text-lg font-semibold lia-text-800">
                      {(candidate.linkedin_connections_count ?? 0).toLocaleString('pt-BR')}
                    </p>
                    <p className="text-micro lia-text-500">Conexões</p>
                  </div>
                )}
                {candidate.linkedin_followers_count && (
                  <div className="text-center">
                    <p className="text-lg font-semibold lia-text-800">
                      {(candidate.linkedin_followers_count ?? 0).toLocaleString('pt-BR')}
                    </p>
                    <p className="text-micro lia-text-500">Seguidores</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Documents Card */}
      {hasDocuments(candidate as unknown as Record<string, unknown>) && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <FileText className="w-4 h-4 lia-text-600" />
              Documentos
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {candidate.resume_url && (
              <div>
                <a 
                  href={candidate.resume_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-md text-sm lia-text-800 dark:text-lia-text-primary transition-colors motion-reduce:transition-none"
                >
                  <Download className="w-4 h-4" />
                  Baixar Currículo
                  <ExternalLink className="w-3 h-3 lia-text-400" />
                </a>
              </div>
            )}

            {candidate.self_introduction && (
              <div>
                <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5 flex items-center gap-1">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  Apresentação Profissional
                </h5>
                <p className="text-sm lia-text-600 bg-gray-50 p-3 rounded-md leading-relaxed">
                  {candidate.self_introduction.length > 300 
                    ? `${candidate.self_introduction.slice(0, 300)}...` 
                    : candidate.self_introduction}
                </p>
              </div>
            )}

            {candidate.cover_letter && (
              <div>
                <h5 className="text-xs font-medium lia-text-800 dark:text-lia-text-primary mb-1.5 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  Carta de Apresentação
                </h5>
                <p className="text-sm lia-text-600 bg-gray-50 p-3 rounded-md leading-relaxed">
                  {candidate.cover_letter.length > 300 
                    ? `${candidate.cover_letter.slice(0, 300)}...` 
                    : candidate.cover_letter}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Interests Card */}
      {candidate.interests && candidate.interests.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold lia-text-800 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 lia-text-600" />
              Interesses
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.interests!.map((interest: string) => (
                <Badge key={interest} variant="outline" className="text-xs px-2 py-0.5 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                  {interest}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  </div>
</TabsContent>

    </>
  )
}
