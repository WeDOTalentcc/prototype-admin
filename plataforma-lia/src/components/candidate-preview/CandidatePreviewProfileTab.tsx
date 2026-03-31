// @ts-nocheck
"use client"

import { textStyles, badgeStyles } from '@/lib/design-tokens'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Brain, Clock, CheckCircle, AlertCircle, Code, Linkedin,
  Heart, Tag, Building, Users, GraduationCap, Award,
  Languages, DollarSign, User, Home, MapPin, Globe,
  Briefcase, UserPlus
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { ExperienceHighlightCard } from "@/components/experience-highlight-card"

interface LanguageEntry {
  language: string
  proficiency: string
}

interface OpinionEntry {
  opinion_type?: string
  wsi_score?: number | null
  score?: number | null
  archetype?: string
  summary?: string
  created_at?: string
}

interface OpinionsData {
  current_general_opinion?: OpinionEntry | null
  vacancy_opinions?: OpinionEntry[]
  total_opinions?: number
}

export interface CandidatePreviewProfileTabProps {
  candidate: Record<string, unknown>
  jobId?: string
  opinionsData: OpinionsData | null
  isLoadingOpinions: boolean
  isAnalyzingWithLia: boolean
  lastAnalysisDate: Date | null
  formatAnalysisDate: (date: Date | null) => string
  handleAnalyzeWithLia: () => void
  formatCurrency: (value: number | string | null | undefined, currency?: string) => string
  languagesData: LanguageEntry[]
  hasSalaryData: () => boolean
  hasAddressData: () => boolean
  getAddressString: () => string
}

export function CandidatePreviewProfileTab({
  candidate,
  jobId,
  opinionsData,
  isLoadingOpinions,
  isAnalyzingWithLia,
  lastAnalysisDate,
  formatAnalysisDate,
  handleAnalyzeWithLia,
  formatCurrency,
  languagesData,
  hasSalaryData,
  hasAddressData,
  getAddressString,
}: CandidatePreviewProfileTabProps) {
  return (
          <div className="p-3 space-y-3">
            <ExperienceHighlightCard candidate={candidate as { id: string; name: string }} companyId="demo_company" />
            
            {jobId && (opinionsData?.current_general_opinion || (opinionsData?.vacancy_opinions && opinionsData.vacancy_opinions.length > 0)) && (
              <Card className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle">
                <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary border-b border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="p-0.5 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      </div>
                      <CardTitle className={`${textStyles.label} text-lia-text-secondary dark:text-lia-text-tertiary`}>Parecer LIA</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`flex items-center gap-1 ${textStyles.caption}`}>
                        <Clock className="w-3 h-3" />
                        <span>{formatAnalysisDate(
                          opinionsData?.current_general_opinion?.created_at 
                            ? new Date(opinionsData.current_general_opinion.created_at)
                            : opinionsData?.vacancy_opinions?.[0]?.created_at
                              ? new Date(opinionsData.vacancy_opinions[0].created_at)
                              : lastAnalysisDate
                        )}</span>
                      </div>
                      <Button
                        onClick={handleAnalyzeWithLia}
                        disabled={isAnalyzingWithLia}
                        size="sm"
                        variant="ghost"
                        className={`gap-1 px-2 py-1 ${textStyles.caption} h-6 hover:bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary transition-colors motion-reduce:transition-none disabled:opacity-50`}
                      >
                        {isAnalyzingWithLia ? (
                          <>
                            <div className="w-3 h-3 border-2 border-gray-900 border-t-transparent rounded-full animate-spin motion-reduce:animate-none" />
                            <span>Analisando...</span>
                          </>
                        ) : (
                          <>
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            <span>Atualizar</span>
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-2.5 pb-2.5 px-2.5">
                  {(() => {
                    const opinion = opinionsData?.current_general_opinion || opinionsData?.vacancy_opinions?.[0]
                    if (!opinion) return null
                    
                    const isWsiOpinion = opinion.opinion_type === 'wsi' || opinion.wsi_score !== null
                    const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
                    
                    const getScoreColor = (score: number | null, isWsi: boolean = false) => {
                      if (score === null || score === undefined) return 'lia-text-base'
                      if (isWsi) {
                        return score >= 4.0 ? 'text-status-success' : score >= 3.0 ? 'text-status-warning' : 'text-status-error'
                      }
                      return score >= 80 ? 'text-status-success' : score >= 60 ? 'text-status-warning' : 'text-status-error'
                    }
                    
                    return (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          {displayScore !== null && displayScore !== undefined && (
                            <span className={`${textStyles.label} ${getScoreColor(displayScore, isWsiOpinion)}`}>
                              {isWsiOpinion ? `WSI: ${displayScore.toFixed(1)}/5` : `Score: ${Math.round(displayScore)}/100`}
                            </span>
                          )}
                          {opinion.archetype && (
                            <>
                              <span className="lia-text-muted">•</span>
                              <Badge className={badgeStyles.default}>{opinion.archetype}</Badge>
                            </>
                          )}
                        </div>
                        {opinion.summary && (
                          <p className={`${textStyles.caption} text-lia-text-secondary dark:text-lia-text-tertiary leading-relaxed`}>
                            {opinion.summary}
                          </p>
                        )}
                      </div>
                    )
                  })()}
                </CardContent>
              </Card>
            )}
            
            {jobId && isLoadingOpinions && !opinionsData && (
              <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3 animate-pulse motion-reduce:animate-none">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-4 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                  <div className="w-24 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                </div>
                <div className="space-y-1.5">
                  <div className="w-32 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                  <div className="w-full h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                </div>
              </div>
            )}
            
            {(() => {
              const allSkills = [...(candidate.skills as string[] || []), ...((candidate.technical_skills as string[]) || [])]
              const softSkillsList = (candidate.soft_skills as string[]) || []
              
              const expertise = candidate.expertise ?? candidate.areas_expertise ?? candidate.areasOfExpertise
              let expertiseList: string[] = []
              if (Array.isArray(expertise)) {
                expertiseList = expertise as string[]
              } else if (typeof expertise === 'string') {
                try {
                  const parsed = JSON.parse(expertise)
                  expertiseList = Array.isArray(parsed) ? parsed : []
                } catch {
                  expertiseList = expertise.includes(',') ? expertise.split(',').map((s: string) => s.trim()) : []
                }
              }
              
              const interests = Array.isArray(candidate.interests) ? (candidate.interests as string[]) : []
              const tags = Array.isArray(candidate.tags) ? (candidate.tags as string[]) : []
              
              const totalItems = allSkills.length + softSkillsList.length + expertiseList.length + interests.length + tags.length
              if (totalItems === 0) return null
              
              const skillCategories: Record<string, { label: string, bgColor: string, skills: string[] }> = {
                backend: { label: 'Backend', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                frontend: { label: 'Frontend', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                data: { label: 'Dados & Analytics', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                devops: { label: 'DevOps & Cloud', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                design: { label: 'Design', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                mobile: { label: 'Mobile', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] },
                other: { label: 'Outras', bgColor: 'bg-gray-100 dark:bg-lia-bg-secondary', skills: [] }
              }
              
              const backendKeywords = ['java', 'spring', 'node', 'python', 'django', 'flask', 'fastapi', 'ruby', 'rails', 'php', 'laravel', '.net', 'c#', 'go', 'golang', 'rust', 'express', 'nestjs', 'graphql', 'rest', 'api', 'microservices', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'kafka', 'rabbitmq']
              const frontendKeywords = ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind', 'next', 'nuxt', 'svelte', 'redux', 'webpack', 'vite', 'jquery', 'bootstrap']
              const dataKeywords = ['python', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'ml', 'ai', 'data science', 'sql', 'etl', 'spark', 'hadoop', 'tableau', 'power bi', 'analytics', 'bigquery', 'databricks', 'airflow', 'dbt']
              const devopsKeywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd', 'linux', 'devops', 'sre', 'monitoring', 'grafana', 'prometheus', 'elastic']
              const designKeywords = ['figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'xd', 'ui', 'ux', 'design', 'prototyping', 'wireframe', 'invision', 'zeplin']
              const mobileKeywords = ['ios', 'android', 'swift', 'kotlin', 'react native', 'flutter', 'xamarin', 'mobile', 'objective-c']
              
              allSkills.forEach((skill: string) => {
                const skillLower = skill.toLowerCase()
                if (backendKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.backend.skills.push(skill)
                } else if (frontendKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.frontend.skills.push(skill)
                } else if (dataKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.data.skills.push(skill)
                } else if (devopsKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.devops.skills.push(skill)
                } else if (designKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.design.skills.push(skill)
                } else if (mobileKeywords.some(k => skillLower.includes(k))) {
                  skillCategories.mobile.skills.push(skill)
                } else {
                  skillCategories.other.skills.push(skill)
                }
              })
              
              const categoriesWithSkills = Object.entries(skillCategories).filter(([, cat]) => cat.skills.length > 0)
              
              return (
                <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                    <div className="flex items-center gap-1.5">
                      <Code className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                      <CardTitle className="text-xs font-semibold text-lia-text-primary">
                        Mapa de Skills
                      </CardTitle>
                      <Badge className="text-micro px-1 py-0 h-4 bg-gray-200 text-lia-text-primary dark:text-lia-text-primary">
                        {totalItems} itens
                      </Badge>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="lia-text-secondary cursor-help text-micro">ⓘ</span>
                        </TooltipTrigger>
                        <TooltipContent side="right" className="text-xs max-w-xs">
                          <div className="space-y-1">
                            <p><span className="inline-block w-2 h-2 rounded-full bg-gray-400 mr-1"></span> Skills do CV</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Expertise do LinkedIn</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Soft Skills (LIA)</p>
                            <p><span className="inline-block w-2 h-2 rounded-full bg-wedo-magenta mr-1"></span> Interesses</p>
                            <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-gray-900"></span> Tags</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardHeader>
                  <CardContent className="p-2.5 space-y-2">
                    {categoriesWithSkills.map(([key, category]) => (
                      <div key={key}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <div className="w-2 h-2 rounded-full bg-gray-400" />
                          <span className={textStyles.label}>{category.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="lia-text-muted cursor-help text-micro">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Extraído do currículo (CV)
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {category.skills.map((skill: string) => (
                            <Badge 
                              key={skill} 
                              className="text-micro px-1.5 py-0 bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary border-0"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                    
                    {softSkillsList.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Brain className="w-3 h-3 text-wedo-cyan" />
                          <span className={`${textStyles.label} lia-text-base`}>Soft Skills</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro lia-text-base">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Competências comportamentais inferidas pela LIA
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {softSkillsList.map((skill: string) => (
                            <Badge 
                              key={skill} 
                              className="text-micro px-1.5 py-0 border-0 bg-wedo-cyan/15 lia-text-strong"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {expertiseList.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Linkedin className="w-3 h-3 lia-text-base" />
                          <span className={`${textStyles.label} text-lia-text-secondary dark:text-lia-text-secondary`}>Expertise LinkedIn</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro text-lia-text-disabled">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Áreas de expertise extraídas do perfil LinkedIn
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {expertiseList.map((item: string) => (
                            <Badge
                              key={item}
                              className="text-micro px-1.5 py-0 border-0 bg-gray-200/30 lia-text-strong"
                            >
                              {item}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {interests.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Heart className="w-3 h-3 text-wedo-magenta" />
                          <span className={`${textStyles.label} text-wedo-magenta`}>Interesses</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="text-wedo-magenta cursor-help text-micro">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Áreas de interesse declaradas pelo candidato
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {interests.map((interest: string) => (
                            <Badge 
                              key={skill} 
                              className="text-micro px-1.5 py-0 bg-wedo-magenta/10 text-wedo-magenta border-0"
                            >
                              {interest}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {tags.length > 0 && (
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <Tag className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                          <span className={`${textStyles.label} text-lia-text-secondary dark:text-lia-text-secondary`}>Tags</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help text-micro text-lia-text-disabled">ⓘ</span>
                            </TooltipTrigger>
                            <TooltipContent side="right" className="text-xs">
                              Tags adicionadas pelo recrutador ou sistema
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <div className="flex flex-wrap gap-1 ml-3.5">
                          {tags.map((tag: string) => (
                            <Badge
                              key={tag}
                              className="text-micro px-1.5 py-0 border-0 bg-gray-200/30 lia-text-strong"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })()}

            {(() => {
              const isOpenToWork = candidate.is_opentowork ?? candidate.is_open_to_work ?? candidate.isOpenToWork
              const isTopUniversity = candidate.is_top_universities ?? candidate.top_universities ?? candidate.isTopUniversities
              const isDecisionMaker = candidate.is_decision_maker ?? candidate.isDecisionMaker
              const isBlacklisted = candidate.is_blacklisted ?? candidate.blacklist_status ?? candidate.isBlacklisted
              const blacklistReason = candidate.blacklist_reason ?? candidate.motivo_lista_negra ?? candidate.blacklistReason
              
              const hasAnyIndicator = isOpenToWork === true || isTopUniversity === true || isDecisionMaker === true || isBlacklisted === true
              
              if (!hasAnyIndicator) return null
              
              return (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {isOpenToWork === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20 dark:text-status-success dark:border-status-success/30 flex items-center gap-1">
                      <Globe className="w-3 h-3 text-status-success dark:text-status-success" />
                      Open to Work
                    </Badge>
                  )}
                  {isTopUniversity === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30 flex items-center gap-1">
                      🎓 Top University
                    </Badge>
                  )}
                  {isDecisionMaker === true && (
                    <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-gray-100 lia-text-base dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle flex items-center gap-1">
                      👔 Decision Maker
                    </Badge>
                  )}
                  {isBlacklisted === true && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge variant="outline" className="text-micro px-2 py-0.5 h-5 bg-status-error/10 text-status-error border-status-error/30 flex items-center gap-1 cursor-help">
                          ⚠️ LCNU
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent side="bottom" className="text-xs max-w-xs">
                        <p className="font-medium mb-1">Lista de Candidatos Não Utilizáveis</p>
                        {!!blacklistReason && <p>{String(blacklistReason)}</p>}
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              )
            })()}

            {(() => {
              const headline = candidate.headline ?? candidate.linkedinHeadline
              const estimatedAge = candidate.estimated_age ?? candidate.estimatedAge ?? candidate.age
              const followersCount = candidate.linkedin_followers_count ?? candidate.followers_count ?? candidate.linkedinFollowersCount
              const connectionsCount = candidate.linkedin_connections_count ?? candidate.connections_count ?? candidate.linkedinConnectionsCount
              
              const hasLinkedInData = headline || estimatedAge || followersCount || connectionsCount
              
              if (!hasLinkedInData) return null
              
              return (
                <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                    <div className="flex items-center gap-1.5">
                      <Linkedin className="w-3.5 h-3.5 lia-text-base" />
                      <CardTitle className="text-xs font-semibold text-lia-text-primary">
                        Perfil LinkedIn
                      </CardTitle>
                      <Globe className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    </div>
                  </CardHeader>
                  <CardContent className="p-2.5 space-y-2">
                    {!!headline && (
                      <p className="text-xs text-lia-text-primary dark:text-lia-text-primary leading-relaxed">
                        {String(headline)}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-3 flex-wrap">
                      {!!estimatedAge && (
                        <div className="flex items-center gap-1">
                          <span className={textStyles.caption}>Idade estimada:</span>
                          <span className={`${textStyles.bodySmall} font-medium`}>{String(estimatedAge)} anos</span>
                        </div>
                      )}
                      {followersCount !== undefined && followersCount !== null && (
                        <div className="flex items-center gap-1">
                          <Users className="w-3 h-3 text-lia-text-disabled" />
                          <span className={`${textStyles.bodySmall} font-medium`}>{(followersCount as number).toLocaleString('pt-BR')}</span>
                          <span className={textStyles.caption}>seguidores</span>
                        </div>
                      )}
                      {connectionsCount !== undefined && connectionsCount !== null && (
                        <div className="flex items-center gap-1">
                          <UserPlus className="w-3 h-3 text-lia-text-disabled" />
                          <span className={`${textStyles.bodySmall} font-medium`}>{(connectionsCount as number) >= 500 ? '500+' : String(connectionsCount)}</span>
                          <span className={textStyles.caption}>conexões</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })()}

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Experiência Profissional
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2.5">
                {(((candidate.workHistory as Record<string, unknown>[])?.length > 0) || ((candidate.work_history as Record<string, unknown>[])?.length > 0) || ((candidate.experiences as Record<string, unknown>[])?.length > 0) || ((candidate.additional_data as Record<string, unknown>)?.work_history as Record<string, unknown>[])?.length > 0 || ((candidate.additional_data as Record<string, unknown>)?.experiences as Record<string, unknown>[])?.length > 0) ? (
                  <div className="space-y-2.5">
                    {((candidate.workHistory || candidate.work_history || candidate.experiences || (candidate.additional_data as Record<string, unknown>)?.work_history || (candidate.additional_data as Record<string, unknown>)?.experiences || []) as Record<string, unknown>[]).map((exp: Record<string, unknown>, index: number) => { /* key below uses company+title combo */
                      const title = (exp.title || exp.position || exp.role || '') as string
                      const company = (exp.company || exp.company_name || exp.organization || '') as string
                      const location = (exp.location || exp.city || '') as string
                      const startDate = (exp.start_date || exp.startDate || '') as string
                      const endDate = (exp.end_date || exp.endDate || (exp.current ? 'Atual' : '')) as string
                      const description = exp.description || exp.responsibilities || ''
                      const descriptionList = Array.isArray(description) ? description as string[] : (description ? [description as string] : [])
                      
                      const industries = exp.industries || exp.industry || exp.segment || exp.segmento || []
                      const industriesList = Array.isArray(industries) ? industries as string[] : (industries ? [industries as string] : [])
                      const technologies = exp.technologies || exp.tech_stack || exp.skills || []
                      const technologiesList = Array.isArray(technologies) ? technologies as string[] : []
                      const companySize = (exp.company_size || exp.company_size_range || exp.porte || null) as string | null
                      const isStartup = exp.is_startup || exp.startup
                      
                      let durationYears = (exp.duration_years as number | null) || null
                      if (!durationYears && startDate) {
                        try {
                          const start = new Date(startDate)
                          const end = endDate && endDate !== 'Atual' ? new Date(endDate) : new Date()
                          const diffMs = end.getTime() - start.getTime()
                          durationYears = Math.round((diffMs / (1000 * 60 * 60 * 24 * 365)) * 10) / 10
                        } catch { /* ignore */ }
                      }
                      
                      const formatDate = (dateStr: string) => {
                        if (!dateStr || dateStr === 'Atual') return dateStr
                        try {
                          return new Date(dateStr).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
                        } catch {
                          return dateStr
                        }
                      }
                      
                      return (
                        <div key={`${index}-${company}`} className={`border-l-2 ${index === 0 ? 'border-gray-700' : 'border-lia-border-default dark:border-lia-border-default'} pl-3`}>
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <div>
                              <h5 className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">{title || 'Cargo não informado'}</h5>
                              <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                                {company || 'Empresa não informada'}
                                {location && ` • ${location}`}
                                {durationYears && durationYears > 0 && <span className="lia-text-secondary ml-1">({durationYears.toFixed(1)} anos)</span>}
                              </p>
                            </div>
                            {(startDate || endDate) && (
                              <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary whitespace-nowrap">
                                {formatDate(startDate)}{startDate && endDate ? ' - ' : ''}{formatDate(endDate)}
                              </span>
                            )}
                          </div>
                          
                          <div className="flex flex-wrap gap-1.5 mb-2">
                            {industriesList.slice(0, 2).map((ind: string) => (
 <span key={ind} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro bg-gray-100 lia-text-base dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
                                <Building className="w-2.5 h-2.5 mr-0.5" />
                                {ind}
                              </span>
                            ))}
                            {!!isStartup && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30">
                                🚀 Startup
                              </span>
                            )}
                            {!!companySize && (
                              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-micro bg-gray-50 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border border-lia-border-subtle dark:border-lia-border-subtle">
                                <Users className="w-2.5 h-2.5" />
                                {companySize}
                              </span>
                            )}
                          </div>

                          {technologiesList.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-2">
                              <span className="text-micro lia-text-secondary flex items-center gap-0.5">
                                <Code className="w-2.5 h-2.5" />
                                Stack:
                              </span>
                              {technologiesList.slice(0, 6).map((tech: string) => (
                                <span key={tech} className="inline-flex items-center px-1.5 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-lia-text-primary dark:text-lia-text-primary">
                                  {tech}
                                </span>
                              ))}
                              {technologiesList.length > 6 && (
                                <span className="text-micro text-lia-text-disabled">+{technologiesList.length - 6}</span>
                              )}
                            </div>
                          )}
                          
                          {descriptionList.length > 0 && (
                            <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-1">{descriptionList[0]}</p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Formação Acadêmica
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {candidate.education && (candidate.education as Record<string, unknown>[]).length > 0 ? (
                  (candidate.education as Record<string, unknown>[]).map((edu: Record<string, unknown>, index: number) => (
                    <div key={`edu-${index}-${String(edu.institution || edu.school || index)}`} className={`flex items-start justify-between gap-2 ${index < (candidate.education as Record<string, unknown>[]).length - 1 ? 'pb-2 border-b border-lia-border-subtle' : ''}`}>
                      <div className="min-w-0 flex-1">
                        <h5 className={textStyles.label}>
                          {(edu.degree || edu.title || 'Formação') as string}{(edu.field_of_study || edu.fieldOfStudy) ? ` em ${(edu.field_of_study || edu.fieldOfStudy) as string}` : ''}
                        </h5>
                        <p className={textStyles.bodySmall}>
                          {(edu.school || edu.institution || 'Instituição não informada') as string}
                        </p>
                      </div>
                      <span className="text-xs text-lia-text-primary dark:text-lia-text-primary flex-shrink-0">
                        {(edu.start_date || edu.startDate || '') as string}{((edu.start_date || edu.startDate) && (edu.end_date || edu.endDate)) ? ' - ' : ''}{(edu.end_date || edu.endDate || '') as string}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Cursos e Certificações
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {candidate.certifications && (candidate.certifications as Record<string, unknown>[]).length > 0 ? (
                  (candidate.certifications as (string | Record<string, unknown>)[]).map((cert: string | Record<string, unknown>, index: number) => {
                    const certName = typeof cert === 'string' ? cert : ((cert.name || cert.title || 'Certificação') as string)
                    const certIssuer = typeof cert === 'object' ? ((cert.issuer || cert.organization || '') as string) : ''
                    const certDate = typeof cert === 'object' ? ((cert.date || cert.year || '') as string) : ''
                    return (
                      <div key={`cert-${index}-${certName || certIssuer}`} className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <h5 className={`${textStyles.label} truncate`}>
                            {certName}
                          </h5>
                          {certIssuer && <p className={textStyles.bodySmall}>{certIssuer}</p>}
                        </div>
                        {certDate && <span className="text-xs text-lia-text-primary dark:text-lia-text-primary flex-shrink-0">{certDate}</span>}
                      </div>
                    )
                  })
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <Languages className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Idiomas
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-1.5">
                {languagesData.length > 0 ? (
                  languagesData.map((lang, index) => (
                    <div key={`lang-${lang.language || lang.name || index}`} className="flex items-center justify-between">
                      <span className={`${textStyles.bodySmall} font-medium`}>
                        {lang.language}
                      </span>
                      {lang.proficiency && (
                        <Badge className="text-xs px-1.5 py-0 h-4 bg-gray-200 text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default font-semibold">
                          {lang.proficiency}
                        </Badge>
                      )}
                    </div>
                  ))
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle col-span-2">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Remuneração
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5">
                {hasSalaryData() ? (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Salário Atual</span>
                      <span className={textStyles.label}>
                        {formatCurrency((candidate.current_salary || candidate.currentSalary) as number | string | null, (candidate.salary_currency || candidate.salaryCurrency || 'BRL') as string)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Pretensão Salarial</span>
                      <span className={textStyles.label}>
                        {((candidate.desired_salary_min || candidate.desiredSalaryMin) && (candidate.desired_salary_max || candidate.desiredSalaryMax))
                          ? `${formatCurrency((candidate.desired_salary_min || candidate.desiredSalaryMin) as number | string | null)} - ${formatCurrency((candidate.desired_salary_max || candidate.desiredSalaryMax) as number | string | null)}`
                          : formatCurrency((candidate.desired_salary_min || candidate.desiredSalaryMin || candidate.desired_salary_max || candidate.desiredSalaryMax) as number | string | null)
                        }
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Expectativa CLT</span>
                      <span className={textStyles.label}>
                        {formatCurrency((candidate.salary_expectation_clt || candidate.salaryExpectationClt) as number | string | null)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className={textStyles.bodySmall}>Expectativa PJ</span>
                      <span className={textStyles.label}>
                        {formatCurrency((candidate.salary_expectation_pj || candidate.salaryExpectationPj) as number | string | null)}
                      </span>
                    </div>
                    {!!(candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance) && (
                      <div className="flex items-center justify-between">
                        <span className={textStyles.bodySmall}>Expectativa Freelance</span>
                        <span className={textStyles.label}>
                          {formatCurrency((candidate.salary_expectation_freelance || candidate.salaryExpectationFreelance) as number | string | null)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Preferências e Dados Pessoais
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5 space-y-2">
                {!!candidate.gender && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Gênero</span>
                    <Badge className={badgeStyles.default}>
                      {candidate.gender as string}
                    </Badge>
                  </div>
                )}
                {!!(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Modelo de Trabalho</span>
                    <Badge className={badgeStyles.default}>
                      {(candidate.work_model_preference || candidate.workModelPreference || candidate.workModel) as string}
                    </Badge>
                  </div>
                )}
                {!!(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Tipo de Contrato</span>
                    <Badge className={badgeStyles.default}>
                      {(candidate.contract_type_preference || candidate.contractTypePreference || candidate.contractType) as string}
                    </Badge>
                  </div>
                )}
                {candidate.is_remote !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Aceita Remoto</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.is_remote ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary'}`}>
                      {candidate.is_remote ? 'Sim' : 'Não'}
                    </Badge>
                  </div>
                )}
                {(candidate.willing_to_relocate !== undefined || candidate.willingToRelocate !== undefined) && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Aceita Mudança</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${(candidate.willing_to_relocate ?? candidate.willingToRelocate) ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary'}`}>
                      {(candidate.willing_to_relocate ?? candidate.willingToRelocate) === true ? 'Sim' : 
                       (candidate.willing_to_relocate ?? candidate.willingToRelocate) === false ? 'Não' : 
                       String(candidate.willing_to_relocate ?? candidate.willingToRelocate)}
                    </Badge>
                  </div>
                )}
                {candidate.mobility !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Disponibilidade Viagens</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.mobility ? 'bg-status-success/15 text-status-success' : 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary'}`}>
                      {candidate.mobility === true ? 'Sim' : candidate.mobility === false ? 'Não' : String(candidate.mobility)}
                    </Badge>
                  </div>
                )}
                {candidate.communication_consent !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className={textStyles.bodySmall}>Consentimento LGPD</span>
                    <Badge className={`text-xs px-1.5 py-0 h-4 ${candidate.communication_consent ? 'bg-status-success/15 text-status-success' : 'bg-status-error/15 text-status-error'}`}>
                      {candidate.communication_consent ? '✓ Consentido' : '✗ Não consentido'}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="border-lia-border-subtle dark:border-lia-border-subtle">
              <CardHeader className="py-1.5 px-2.5 bg-white dark:bg-lia-bg-primary">
                <div className="flex items-center gap-1.5">
                  <Home className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                  <CardTitle className="text-xs font-semibold text-lia-text-primary">
                    Endereço
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-2.5">
                {hasAddressData() ? (
                  <div className="space-y-1">
                    <div className="flex items-start gap-2">
                      <MapPin className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5 flex-shrink-0" />
                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary whitespace-pre-line">
                        {getAddressString()}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className={`${textStyles.description} italic`}>Não informado</p>
                )}
              </CardContent>
            </Card>
          </div>
  )
}