"use client"

import { textStyles } from '@/lib/design-tokens'
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Brain, Code, Linkedin, Heart, Tag } from"lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"

interface ProfileSkillsMapCardProps {
  candidate: Record<string, unknown>
}

const backendKeywords = ['java', 'spring', 'node', 'python', 'django', 'flask', 'fastapi', 'ruby', 'rails', 'php', 'laravel', '.net', 'c#', 'go', 'golang', 'rust', 'express', 'nestjs', 'graphql', 'rest', 'api', 'microservices', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'kafka', 'rabbitmq']
const frontendKeywords = ['react', 'angular', 'vue', 'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind', 'next', 'nuxt', 'svelte', 'redux', 'webpack', 'vite', 'jquery', 'bootstrap']
const dataKeywords = ['python', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'machine learning', 'ml', 'ai', 'data science', 'sql', 'etl', 'spark', 'hadoop', 'tableau', 'power bi', 'analytics', 'bigquery', 'databricks', 'airflow', 'dbt']
const devopsKeywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions', 'ci/cd', 'linux', 'devops', 'sre', 'monitoring', 'grafana', 'prometheus', 'elastic']
const designKeywords = ['figma', 'sketch', 'adobe', 'photoshop', 'illustrator', 'xd', 'ui', 'ux', 'design', 'prototyping', 'wireframe', 'invision', 'zeplin']
const mobileKeywords = ['ios', 'android', 'swift', 'kotlin', 'react native', 'flutter', 'xamarin', 'mobile', 'objective-c']

function categorizeSkills(allSkills: string[]) {
  const skillCategories: Record<string, { label: string, bgColor: string, skills: string[] }> = {
    backend: { label: 'Backend', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    frontend: { label: 'Frontend', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    data: { label: 'Dados & Analytics', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    devops: { label: 'DevOps & Cloud', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    design: { label: 'Design', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    mobile: { label: 'Mobile', bgColor: 'bg-lia-bg-tertiary', skills: [] },
    other: { label: 'Outras', bgColor: 'bg-lia-bg-tertiary', skills: [] }
  }

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

  return Object.entries(skillCategories).filter(([, cat]) => cat.skills.length > 0)
}

function parseExpertise(candidate: Record<string, unknown>): string[] {
  const expertise = candidate.expertise ?? candidate.areas_expertise ?? candidate.areasOfExpertise
  if (Array.isArray(expertise)) {
    return expertise as string[]
  } else if (typeof expertise === 'string') {
    try {
      const parsed = JSON.parse(expertise)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return expertise.includes(',') ? expertise.split(',').map((s: string) => s.trim()) : []
    }
  }
  return []
}

export function ProfileSkillsMapCard({ candidate }: ProfileSkillsMapCardProps) {
  const allSkills = [...(candidate.skills as string[] || []), ...((candidate.technical_skills as string[]) || [])]
  const softSkillsList = (candidate.soft_skills as string[]) || []
  const expertiseList = parseExpertise(candidate)
  const interests = Array.isArray(candidate.interests) ? (candidate.interests as string[]) : []
  const tags = Array.isArray(candidate.tags) ? (candidate.tags as string[]) : []

  const totalItems = allSkills.length + softSkillsList.length + expertiseList.length + interests.length + tags.length
  if (totalItems === 0) return null

  const categoriesWithSkills = categorizeSkills(allSkills)

  return (
    <Card className="border-lia-border-subtle">
      <CardHeader className="py-1.5 px-2.5 bg-lia-bg-primary">
        <div className="flex items-center gap-1.5">
          <Code className="w-3.5 h-3.5 text-lia-text-primary" />
          <CardTitle className="text-xs font-semibold text-lia-text-primary">
            Mapa de Skills
          </CardTitle>
          <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-interactive-active text-lia-text-primary">
            {totalItems} itens
          </Chip>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="lia-text-secondary cursor-help text-micro">ⓘ</span>
            </TooltipTrigger>
            <TooltipContent side="right" className="text-xs max-w-xs">
              <div className="space-y-1">
                <p><span className="inline-block w-2 h-2 rounded-full bg-lia-border-medium mr-1"></span> Skills do CV</p>
                <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-lia-btn-primary-bg"></span> Expertise do LinkedIn</p>
                <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-lia-btn-primary-bg"></span> Soft Skills (IA)</p>
                <p><span className="inline-block w-2 h-2 rounded-full bg-wedo-magenta mr-1"></span> Interesses</p>
                <p><span className="inline-block w-2 h-2 rounded-full mr-1 bg-lia-btn-primary-bg"></span> Tags</p>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
      </CardHeader>
      <CardContent className="p-2.5 space-y-2">
        {categoriesWithSkills.map(([key, category]) => (
          <div key={key}>
            <div className="flex items-center gap-1.5 mb-1">
              <div className="w-2 h-2 rounded-full bg-lia-border-medium" />
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
              {category.skills.map((skill: string, skillIdx: number) => (
                <Chip variant="neutral" muted
                  key={`${key}-${skill}-${skillIdx}`}
                  className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-primary border-0"
                >
                  {skill}
                </Chip>
              ))}
            </div>
          </div>
        ))}
        
        {softSkillsList.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <Brain className="w-3 h-3 text-wedo-cyan" />
              <span className={`${textStyles.label} text-lia-text-secondary`}>Soft Skills</span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-help text-micro text-lia-text-secondary">ⓘ</span>
                </TooltipTrigger>
                <TooltipContent side="right" className="text-xs">
                  Competências comportamentais inferidas pela IA
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="flex flex-wrap gap-1 ml-3.5">
              {softSkillsList.map((skill: string) => (
                <Chip variant="neutral" muted 
                  key={skill} 
                  className="text-micro px-1.5 py-0 h-4 flex items-center border-0 bg-wedo-cyan/15 text-lia-text-primary"
                >
                  {skill}
                </Chip>
              ))}
            </div>
          </div>
        )}
        
        {expertiseList.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <Linkedin className="w-3 h-3 text-lia-text-secondary" />
              <span className={`${textStyles.label} text-lia-text-secondary`}>Expertise LinkedIn</span>
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
                <Chip variant="neutral" muted
                  key={item}
                  className="text-micro px-1.5 py-0 h-4 flex items-center border-0 bg-lia-interactive-active/30 text-lia-text-primary"
                >
                  {item}
                </Chip>
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
                <Chip variant="neutral" muted 
                  key={interest} 
                  className="text-micro px-1.5 py-0 h-4 flex items-center bg-wedo-magenta/10 text-wedo-magenta border-0"
                >
                  {interest}
                </Chip>
              ))}
            </div>
          </div>
        )}
        
        {tags.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <Tag className="w-3 h-3 text-lia-text-secondary" />
              <span className={`${textStyles.label} text-lia-text-secondary`}>Tags</span>
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
                <Chip variant="neutral" muted
                  key={tag}
                  className="text-micro px-1.5 py-0 h-4 flex items-center border-0 bg-lia-interactive-active/30 text-lia-text-primary"
                >
                  {tag}
                </Chip>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
