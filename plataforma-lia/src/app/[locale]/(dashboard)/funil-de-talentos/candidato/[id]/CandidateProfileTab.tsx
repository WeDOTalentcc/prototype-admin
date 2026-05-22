"use client"

import { cn } from "@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { TabsContent } from"@/components/ui/tabs"
import {
  Award, Brain, Briefcase, Building2, Cake, Code, DollarSign, Download,
  ExternalLink, FileText, GraduationCap, Home, Languages, Lightbulb,
  Linkedin, Mail, User, Users
} from"lucide-react"
import type { CandidateLocal } from"@/services/lia-api"
import { ProfileExperienceSection } from"@/components/candidate-profile/ProfileExperienceSection"
import { ProfileEducationSection } from"@/components/candidate-profile/ProfileEducationSection"

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
  [key: string]: unknown
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
  [key: string]: unknown
}

interface LanguageEntry {
  language: string
  level: string
  [key: string]: unknown
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
  formatDate: (date: string | null | undefined) => string
  formatDateShort: (date: string | null | undefined) => string
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
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Code className="w-4 h-4 text-lia-text-secondary" />
              Skills Principais
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.technical_skills.map((skill) => (
                <Chip density="relaxed" key={skill} variant="neutral" muted className="px-2 py-0.5 border-wedo-cyan/20">
                  {skill}
                </Chip>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Skills Map - Categorized */}
      {skillCategories.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Code className="w-4 h-4 text-lia-text-secondary" />
              Mapa de Skills
              <Chip density="relaxed" variant="neutral" muted className="bg-lia-interactive-active text-lia-text-primary dark:text-lia-text-primary">
                {candidate.technical_skills?.length || 0} itens
              </Chip>
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {skillCategories.map(([key, category]) => (
              <div key={key}>
                <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5">{category.label}</h5>
                <div className="flex flex-wrap gap-1.5">
                  {category.skills.map((skill) => (
                    <Chip density="relaxed" key={skill} variant="neutral" className="px-2 py-0.5 bg-lia-bg-secondary">
                      {skill}
                    </Chip>
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
                    <Chip density="relaxed" key={skill} variant="warning" className="px-2 py-0.5">
                      {skill}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      <ProfileExperienceSection experiences={experiences} formatDateShort={formatDateShort} />
      <ProfileEducationSection education={education} />

      {/* Certifications */}
      {candidate.certifications && candidate.certifications.length > 0 && (
        <Card className="border-lia-border-subtle">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Award className="w-4 h-4 text-lia-text-secondary" />
              Certificações
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-2">
              {candidate.certifications.map((cert, idx) => {
                const certName = typeof cert === 'string' ? cert : String((cert as { name?: string }).name || 'Certificação')
                return (
                  <Chip density="relaxed" key={`cert-${idx}`} variant="neutral" muted className="px-2 py-1">
                    {certName}
                  </Chip>
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
          <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-lia-text-secondary" />
            Remuneração
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-2">
          {candidate.current_salary && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-lia-text-secondary">Salário Atual</span>
              <span className="text-sm font-medium text-lia-text-primary">{formatCurrency(candidate.current_salary, candidate.salary_currency || 'BRL')}</span>
            </div>
          )}
          {candidate.salary_expectation_clt && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-lia-text-secondary">Pretensão CLT</span>
              <span className="text-sm font-medium text-lia-text-primary">{formatCurrency(candidate.salary_expectation_clt)}</span>
            </div>
          )}
          {candidate.salary_expectation_pj && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-lia-text-secondary">Pretensão PJ</span>
              <span className="text-sm font-medium text-lia-text-primary">{formatCurrency(candidate.salary_expectation_pj)}</span>
            </div>
          )}
          {candidate.salary_expectation_freelance && (
            <div className="flex justify-between items-center">
              <span className="text-xs text-lia-text-secondary">Freelance</span>
              <span className="text-sm font-medium text-lia-text-primary">{formatCurrency(candidate.salary_expectation_freelance)}</span>
            </div>
          )}
          {(candidate.desired_salary_min || candidate.desired_salary_max) && (
            <div className="flex justify-between items-center pt-2">
              <span className="text-xs text-lia-text-secondary">Faixa Desejada</span>
              <span className="text-sm font-medium text-lia-text-primary">
                {formatCurrency(candidate.desired_salary_min)} - {formatCurrency(candidate.desired_salary_max)}
              </span>
            </div>
          )}
          {candidate.salary_expectation_clt && (
            <div className="flex justify-between items-center pt-2 mt-1 bg-lia-bg-secondary rounded-lg dark:bg-lia-bg-secondary -mx-4 px-4 py-2">
              <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Total Anual (CLT)</span>
              <span className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">
                {formatCurrency((candidate.salary_expectation_clt ?? 0) * 13.33)}
              </span>
            </div>
          )}
          {!candidate.current_salary && !candidate.salary_expectation_clt && !candidate.salary_expectation_pj && (
            <p className="text-sm text-lia-text-secondary italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Languages Card */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Languages className="w-4 h-4 text-lia-text-secondary" />
            Idiomas
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          {languagesData.length > 0 ? (
            languagesData.map((lang, index) => {
              const levelInfo = getLanguageLevel(lang.level)
              return (
                <div key={`lang-${lang.language || (lang as Record<string, unknown>).name || index}`} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{lang.language}</span>
                    <span className="text-xs text-lia-text-secondary">{levelInfo.label}</span>
                  </div>
                  <div className="w-full bg-lia-interactive-active rounded-full h-1.5">
                    <div 
                      className={`h-1.5 rounded-full ${levelInfo.color}`} 
                      style={{width: `${levelInfo.percent}%`}}
                    />
                  </div>
                </div>
              )
            })
          ) : (
            <p className="text-sm text-lia-text-secondary italic">Não informado</p>
          )}
        </CardContent>
      </Card>

      {/* Additional Details Card */}
      <Card className="border-lia-border-subtle">
        <CardHeader className="py-2.5 px-4">
          <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Home className="w-4 h-4 text-lia-text-secondary" />
            Detalhes Adicionais
          </CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 space-y-3">
          {/* Location */}
          <div>
            <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">Localização</h5>
            <p className="text-sm text-lia-text-secondary">
              {[candidate.location_city, candidate.location_state, candidate.location_country]
                .filter(Boolean).join(', ') || 'Não informado'}
            </p>
            {(candidate.address_street || candidate.address_district) && (
              <p className="text-xs text-lia-text-secondary mt-0.5">
                {[candidate.address_street, candidate.address_number, candidate.address_district, candidate.address_zip, candidate.address_complement]
                  .filter(Boolean).join(', ')}
              </p>
            )}
          </div>

          {/* Work Preferences */}
          <div>
            <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5">Preferências de Trabalho</h5>
            <div className="flex flex-wrap gap-1.5">
              {candidate.is_remote && (
                <Chip density="relaxed" variant="neutral" className="bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default">Remoto</Chip>
              )}
              {candidate.willing_to_relocate && (
                <Chip density="relaxed" variant="success" >Aceita Relocação</Chip>
              )}
              {candidate.work_model_preference && (
                <Chip density="relaxed" variant="neutral" >{candidate.work_model_preference}</Chip>
              )}
              {candidate.contract_type_preference && (
                <Chip density="relaxed" variant="neutral" >{candidate.contract_type_preference}</Chip>
              )}
            </div>
          </div>

          {/* Dates */}
          <div>
            <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">Datas</h5>
            <div className="space-y-0.5 text-xs text-lia-text-secondary">
              {candidate.created_at && <p>Cadastro: {formatDate(candidate.created_at)}</p>}
              {candidate.updated_at && <p>Atualizado: {formatDate(candidate.updated_at)}</p>}
              {candidate.last_contacted_at && <p>Último contato: {formatDate(candidate.last_contacted_at)}</p>}
              {candidate.last_activity_at && <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>}
            </div>
          </div>

          {/* Status */}
          <div>
            <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5">Status</h5>
            <div className="flex flex-wrap gap-1.5">
              <Chip density="relaxed" variant="neutral" className={cn(!candidate.is_active && 'bg-lia-bg-tertiary text-lia-text-secondary')}>
                {candidate.is_active ? 'Ativo' : 'Inativo'}
              </Chip>
              {candidate.source && (
                <Chip density="relaxed" variant="neutral" >{candidate.source}</Chip>
              )}
            </div>
          </div>

          {/* Tags */}
          {candidate.tags && candidate.tags.length > 0 && (
            <div>
              <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5">Tags</h5>
              <div className="flex flex-wrap gap-1">
                {candidate.tags.map((tag) => (
                  <Chip density="relaxed" variant="neutral" muted key={tag} className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:border-lia-border-default">
                    {tag}
                  </Chip>
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
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <User className="w-4 h-4 text-lia-text-secondary" />
              Dados Pessoais
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-2">
            {(candidate.date_of_birth || candidate.estimated_age) && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-lia-text-secondary flex items-center gap-1">
                  <Cake className="w-3.5 h-3.5" />
                  Idade
                </span>
                <span className="text-sm font-medium text-lia-text-primary">
                  {(candidate.date_of_birth ? calculateAge(candidate.date_of_birth) : null) || candidate.estimated_age} anos
                  {candidate.date_of_birth && (
                    <span className="text-xs text-lia-text-tertiary ml-1">
                      ({formatDate(candidate.date_of_birth)})
                    </span>
                  )}
                </span>
              </div>
            )}
            {candidate.gender && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-lia-text-secondary">Gênero</span>
                <span className="text-sm font-medium text-lia-text-primary">{candidate.gender}</span>
              </div>
            )}
            {candidate.nationality && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-lia-text-secondary">Nacionalidade</span>
                <span className="text-sm font-medium text-lia-text-primary">{candidate.nationality}</span>
              </div>
            )}
            {candidate.marital_status && (
              <div className="flex justify-between items-center">
                <span className="text-xs text-lia-text-secondary">Estado Civil</span>
                <span className="text-sm font-medium text-lia-text-primary">{candidate.marital_status}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* LinkedIn/Pearch Insights Card */}
      {hasPearchData(candidate as unknown as Record<string, unknown>) && (
        <Card className="border-lia-border-subtle border-l-4 border-l-brand-linkedin">
          <CardHeader className="py-2.5 px-4">
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Linkedin className="w-4 h-4 text-brand-linkedin" />
              LinkedIn Insights
              {candidate.pearch_profile_id && (
                <Chip variant="neutral" muted className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-secondary">Pearch</Chip>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-3">
            {candidate.headline && (
              <div>
                <p className="text-sm text-lia-text-primary dark:text-lia-text-primary italic">"{candidate.headline}"</p>
              </div>
            )}

            {/* Badges de Status */}
            <div className="flex flex-wrap gap-1.5">
              {candidate.is_open_to_work && (
                <Chip density="relaxed" variant="success" muted >
                  ✓ Open to Work
                </Chip>
              )}
              {candidate.is_decision_maker && (
                <Chip density="relaxed" variant="neutral" muted className="border-wedo-purple/30">
                  👔 Decision Maker
                </Chip>
              )}
              {candidate.is_top_universities && (
                <Chip density="relaxed" variant="warning" muted >
                  🎓 Top Universities
                </Chip>
              )}
              {candidate.is_hiring && (
                <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default">
                  📢 Hiring
                </Chip>
              )}
            </div>

            {/* Connections & Followers */}
            {(candidate.linkedin_connections_count || candidate.linkedin_followers_count) && (
              <div className="flex gap-4 pt-2">
                {candidate.linkedin_connections_count && (
                  <div className="text-center">
                    <p className="text-lg font-semibold text-lia-text-primary">
                      {(candidate.linkedin_connections_count ?? 0).toLocaleString('pt-BR')}
                    </p>
                    <p className="text-micro text-lia-text-secondary">Conexões</p>
                  </div>
                )}
                {candidate.linkedin_followers_count && (
                  <div className="text-center">
                    <p className="text-lg font-semibold text-lia-text-primary">
                      {(candidate.linkedin_followers_count ?? 0).toLocaleString('pt-BR')}
                    </p>
                    <p className="text-micro text-lia-text-secondary">Seguidores</p>
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
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <FileText className="w-4 h-4 text-lia-text-secondary" />
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
                  className="inline-flex items-center gap-2 px-3 py-2 bg-lia-bg-secondary hover:bg-lia-bg-tertiary rounded-md text-sm text-lia-text-primary dark:text-lia-text-primary transition-colors motion-reduce:transition-none"
                >
                  <Download className="w-4 h-4" />
                  Baixar Currículo
                  <ExternalLink className="w-3 h-3 text-lia-text-tertiary" />
                </a>
              </div>
            )}

            {candidate.self_introduction && (
              <div>
                <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5 flex items-center gap-1">
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  Apresentação Profissional
                </h5>
                <p className="text-sm text-lia-text-secondary bg-lia-bg-secondary p-3 rounded-xl leading-relaxed">
                  {candidate.self_introduction.length > 300 
                    ? `${candidate.self_introduction.slice(0, 300)}...` 
                    : candidate.self_introduction}
                </p>
              </div>
            )}

            {candidate.cover_letter && (
              <div>
                <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary mb-1.5 flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  Carta de Apresentação
                </h5>
                <p className="text-sm text-lia-text-secondary bg-lia-bg-secondary p-3 rounded-xl leading-relaxed">
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
            <CardTitle className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-lia-text-secondary" />
              Interesses
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-wrap gap-1.5">
              {candidate.interests!.map((interest: string) => (
                <Chip density="relaxed" key={interest} variant="neutral" className="px-2 py-0.5 border-wedo-purple/30">
                  {interest}
                </Chip>
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
