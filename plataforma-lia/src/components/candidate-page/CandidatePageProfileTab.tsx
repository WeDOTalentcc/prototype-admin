"use client"

import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { ProfileExperienceSection } from"@/components/candidate-profile/ProfileExperienceSection"
import { ProfileEducationSection } from"@/components/candidate-profile/ProfileEducationSection"
import {
  MapPin, Building, GraduationCap, Briefcase, Award,
  Brain, CheckCircle, AlertCircle, Clock, Users,
  DollarSign, User, Languages, Home, Cake,
  Code, Linkedin
} from"lucide-react"

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

export interface CandidatePageProfileTabProps {
  candidate: import("@/services/lia-api").CandidateLocal & Record<string, unknown>
  experiences: Record<string, unknown>[]
  education: Record<string, unknown>[]
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
            <h4 className="text-sm font-medium text-lia-text-primary mb-3">Skills Principais</h4>
            <div className="flex flex-wrap gap-1.5">
              {(candidate.technical_skills || candidate.skills || []).map((skill: string) => (
                <Badge key={skill} variant="outline" className="text-xs px-2 py-0.5">
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
                <div className="w-7 h-7 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                  <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-micro font-medium text-lia-text-primary uppercase tracking-wider">Parecer LIA</span>
                    <span className="text-micro font-semibold text-status-success">
                      Score: {opinionsHistory[0]?.score || liaScore}/100
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    {opinionsHistory[0]?.job_vacancy_id ? (
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default dark:border-lia-border-default flex items-center gap-1">
                        <Briefcase className="w-2.5 h-2.5" />
                        #{String(opinionsHistory[0].job_vacancy_id).slice(0, 6)} - {opinionsHistory[0].job_vacancy_title || 'Vaga vinculada'}
                      </Badge>
                    ) : (
                      <Badge className="text-micro px-1.5 py-0 h-4 bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">
                        Sem vaga vinculada
                      </Badge>
                    )}
                    {opinionsHistory[0]?.archetype && (
                      <span className="text-micro text-lia-text-secondary">{opinionsHistory[0].archetype}</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {opinionsHistory[0]?.recommendation === 'approved' && (
                  <Badge className="text-micro px-1.5 py-0 h-4  flex items-center gap-0.5">
                    <CheckCircle className="w-2.5 h-2.5" />
                    APROVADO
                  </Badge>
                )}
                {opinionsHistory[0]?.recommendation === 'pending_review' && (
                  <Badge className="text-micro px-1.5 py-0 h-4  flex items-center gap-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    PENDENTE
                  </Badge>
                )}
              </div>
            </div>
            
            <p className="text-micro text-lia-text-primary leading-relaxed mb-2">
              {opinionsHistory[0]?.summary}
            </p>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <h4 className="text-micro font-medium mb-1 flex items-center gap-1 text-status-success">
                  <CheckCircle className="w-3 h-3" />
                  Pontos Fortes
                </h4>
                <ul className="space-y-0.5">
                  {(opinionsHistory[0]?.strengths || []).slice(0, 3).map((s: string, i: number) => (
                    <li key={`s-${i}`} className="text-micro text-lia-text-secondary flex items-start gap-1">
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
                  {(opinionsHistory[0]?.concerns || []).slice(0, 3).map((c: string, i: number) => (
                    <li key={`c-${i}`} className="text-micro text-lia-text-secondary flex items-start gap-1">
                      <span className="text-status-warning">•</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Card>
        <ProfileExperienceSection experiences={experiences as import("@/components/candidate-profile/ProfileExperienceSection").ExperienceEntry[]} formatDateShort={formatDateShort} />
        <ProfileEducationSection education={education as import("@/components/candidate-profile/ProfileEducationSection").EducationEntry[]} />

        {candidate.certifications && candidate.certifications.length > 0 && (
          <Card>
            <CardHeader className="py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-status-success" />
                <CardTitle className="text-sm font-semibold text-lia-text-primary">
                  Certificações
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-1.5">
                {candidate.certifications.map((cert: string) => (
                  <Badge key={cert} variant="outline" className="text-xs px-2 py-0.5  border-status-success/30">
                    {cert}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-4">

        {(() => {
          const langs = Array.isArray(candidate.languages)
            ? candidate.languages as { language: string; level: string }[]
            : typeof candidate.languages === 'object' && candidate.languages !== null
              ? Object.entries(candidate.languages as Record<string, string>).map(([language, level]) => ({ language, level }))
              : []
          if (langs.length === 0) return null
          return (
            <Card>
              <CardHeader className="py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                <div className="flex items-center gap-2">
                  <Languages className="w-4 h-4 text-wedo-purple" />
                  <CardTitle className="text-sm font-semibold text-lia-text-primary">
                    Idiomas
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                {langs.map(({ language, level }) => (
                  <div key={language} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-lia-text-primary">{language}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle">
                      {level}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )
        })()}

        <Card>
          <CardHeader className="py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <div className="flex items-center gap-2">
              <Home className="w-4 h-4 text-lia-text-secondary" />
              <CardTitle className="text-sm font-semibold text-lia-text-primary">
                Detalhes Adicionais
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div>
              <h5 className="text-xs font-medium text-lia-text-primary mb-1">Localização</h5>
              <p className="text-sm text-lia-text-secondary">
                {[candidate.location_city, candidate.location_state, candidate.location_country]
                  .filter(Boolean).join(', ') || (candidate.location as string) || 'Não informado'}
              </p>
              {(candidate.address_street || candidate.address_district) && (
                <p className="text-xs text-lia-text-tertiary mt-0.5">
                  {[candidate.address_street, candidate.address_number, candidate.address_district, candidate.address_zip, candidate.address_complement]
                    .filter(Boolean).join(', ')}
                </p>
              )}
            </div>

            <div>
              <h5 className="text-xs font-medium text-lia-text-primary mb-1.5">Preferências de Trabalho</h5>
              <div className="flex flex-wrap gap-1.5">
                {candidate.is_remote && (
                  <Badge variant="outline" className="text-xs bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default">Remoto</Badge>
                )}
                {candidate.willing_to_relocate && (
                  <Badge variant="outline" className="text-xs  border-status-success/30">Aceita Relocação</Badge>
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
              <h5 className="text-xs font-medium text-lia-text-primary mb-1">Datas</h5>
              <div className="space-y-0.5 text-xs text-lia-text-secondary">
                {candidate.created_at && <p>Cadastro: {formatDate(candidate.created_at)}</p>}
                {candidate.updated_at && <p>Atualizado: {formatDate(candidate.updated_at)}</p>}
                {candidate.last_contacted_at && <p>Último contato: {formatDate(candidate.last_contacted_at)}</p>}
                {candidate.last_activity_at && <p>Última atividade: {formatDate(candidate.last_activity_at)}</p>}
              </div>
            </div>

            <div>
              <h5 className="text-xs font-medium text-lia-text-primary mb-1.5">Status</h5>
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="outline" className={`text-xs ${candidate.is_active ? ' dark:text-status-success' : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary'}`}>
                  {candidate.is_active ? 'Ativo' : 'Inativo'}
                </Badge>
                {candidate.source && (
                  <Badge variant="outline" className="text-xs">{candidate.source}</Badge>
                )}
              </div>
            </div>

            {candidate.tags && candidate.tags.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-lia-text-primary mb-1.5">Tags</h5>
                <div className="flex flex-wrap gap-1">
                  {candidate.tags.map((tag: string) => (
                    <Badge key={tag} className="text-xs bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default">
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
            <CardHeader className="py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-lia-text-secondary" />
                <CardTitle className="text-sm font-semibold text-lia-text-primary">
                  Dados Pessoais
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-2">
              {(candidate.date_of_birth || (candidate.estimated_age as number | undefined)) && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-lia-text-tertiary flex items-center gap-1">
                    <Cake className="w-3.5 h-3.5" />
                    Idade
                  </span>
                  <span className="text-sm font-medium text-lia-text-primary">
                    {calculateAge(candidate.date_of_birth) || (candidate.estimated_age as number)} anos
                    {candidate.date_of_birth && (
                      <span className="text-xs text-lia-text-secondary ml-1">
                        ({formatDate(candidate.date_of_birth)})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {candidate.gender && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-lia-text-tertiary">Gênero</span>
                  <span className="text-sm font-medium text-lia-text-primary">{candidate.gender}</span>
                </div>
              )}
              {candidate.nationality && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-lia-text-tertiary">Nacionalidade</span>
                  <span className="text-sm font-medium text-lia-text-primary">{candidate.nationality}</span>
                </div>
              )}
              {candidate.marital_status && (
                <div className="flex justify-between items-center">
                  <span className="text-xs text-lia-text-tertiary">Estado Civil</span>
                  <span className="text-sm font-medium text-lia-text-primary">{candidate.marital_status}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {hasPearchData(candidate as unknown as Record<string, unknown>) && (
          <Card className="border-l-4 border-l-lia-border-medium">
            <CardHeader className="py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <div className="flex items-center gap-2">
                <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                <CardTitle className="text-sm font-semibold text-lia-text-primary">
                  LinkedIn Insights
                </CardTitle>
                {candidate.pearch_profile_id && (
                  <Badge className="text-micro px-1.5 py-0 bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary">Pearch</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {(candidate.headline as string | undefined) && (
                <div>
                  <p className="text-sm text-lia-text-primary italic">&quot;{candidate.headline as string}&quot;</p>
                </div>
              )}
              
              <div className="flex flex-wrap gap-1.5">
                {(candidate.is_open_to_work as boolean | undefined) && (
                  <Badge className="text-xs  border-status-success/30">
                    ✓ Open to Work
                  </Badge>
                )}
                {candidate.is_decision_maker && (
                  <Badge className="text-xs  border-wedo-purple/30">
                    👔 Decision Maker
                  </Badge>
                )}
                {candidate.is_top_universities && (
                  <Badge className="text-xs  border-status-warning/30">
                    🎓 Top Universities
                  </Badge>
                )}
                {(candidate.is_hiring as boolean | undefined) && (
                  <Badge className="text-xs bg-lia-bg-tertiary text-lia-text-secondary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default">
                    📢 Hiring
                  </Badge>
                )}
              </div>

              {((candidate.linkedin_connections_count as number | undefined) || (candidate.linkedin_followers_count as number | undefined)) && (
                <div className="flex gap-4 pt-2 border-t border-lia-border-subtle">
                  {(candidate.linkedin_connections_count as number | undefined) && (
                    <div className="text-center">
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(candidate.linkedin_connections_count as number).toLocaleString('pt-BR')}
                      </p>
                      <p className="text-micro text-lia-text-tertiary">Conexões</p>
                    </div>
                  )}
                  {(candidate.linkedin_followers_count as number | undefined) && (
                    <div className="text-center">
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(candidate.linkedin_followers_count as number).toLocaleString('pt-BR')}
                      </p>
                      <p className="text-micro text-lia-text-tertiary">Seguidores</p>
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
