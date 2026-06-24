"use client"

import React from "react"
import { User, MapPin, Briefcase, GraduationCap, Mail, Phone, Globe, Brain, MessageSquare, Calendar, UserPlus } from "lucide-react"
import { cn } from "@/lib/utils"

interface ProfileData {
  id?: string | number
  name?: string
  email?: string
  phone?: string
  location?: string
  current_title?: string
  current_company?: string
  experience_years?: number
  education?: string
  linkedin_url?: string
  skills?: string[]
  match_score?: number
  lia_insights?: string[]
  work_history?: Array<{ title: string; company: string; period: string }>
}

interface CandidateProfilePanelProps {
  data: Record<string, unknown>
  onUpdateData?: (data: Record<string, unknown>) => void
}

function sanitizeUrl(url: string | undefined): string | undefined {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (parsed.protocol === "http:" || parsed.protocol === "https:") return url
  } catch {}
  return undefined
}

export function CandidateProfilePanel({ data }: CandidateProfilePanelProps) {
  const profile = (data as unknown) as ProfileData

  const name = profile.name || "Candidato"
  const initials = name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
  const score = profile.match_score != null ? Math.round(profile.match_score * 100) : null
  const scoreColor = score != null
    ? score >= 80 ? "text-status-success bg-status-success/10" : score >= 60 ? "text-status-warning bg-status-warning/10" : "text-status-error bg-status-error/10"
    : ""

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-4 bg-lia-bg-secondary">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center text-lg font-semibold text-lia-text-primary">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-lia-text-primary truncate">{name}</p>
            {profile.current_title && (
              <p className="text-xs text-lia-text-secondary truncate">
                {profile.current_title}{profile.current_company ? ` @ ${profile.current_company}` : ""}
              </p>
            )}
            {score != null && (
              <span className={cn("inline-block text-micro font-semibold px-2 py-0.5 rounded-full mt-1", scoreColor)}>
                Match: {score}%
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="px-4 pt-3 pb-4 space-y-2">
          <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider">Contato</p>
          {profile.email && (
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Mail className="w-3.5 h-3.5 text-lia-text-muted" />
              <span className="truncate">{profile.email}</span>
            </div>
          )}
          {profile.phone && (
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Phone className="w-3.5 h-3.5 text-lia-text-muted" />
              <span>{profile.phone}</span>
            </div>
          )}
          {profile.location && (
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <MapPin className="w-3.5 h-3.5 text-lia-text-muted" />
              <span>{profile.location}</span>
            </div>
          )}
          {sanitizeUrl(profile.linkedin_url) && (
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Globe className="w-3.5 h-3.5 text-lia-text-muted" />
              <a href={sanitizeUrl(profile.linkedin_url)!} target="_blank" rel="noopener noreferrer" className="text-lia-text-secondary hover:underline truncate">
                LinkedIn
              </a>
            </div>
          )}
        </div>

        {profile.experience_years != null && (
          <div className="px-4 pt-3 pb-4">
            <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
              <Briefcase className="w-3.5 h-3.5 text-lia-text-muted" />
              <span>{profile.experience_years} anos de experiência</span>
            </div>
            {profile.education && (
              <div className="flex items-center gap-2 text-xs text-lia-text-secondary mt-1">
                <GraduationCap className="w-3.5 h-3.5 text-lia-text-muted" />
                <span>{profile.education}</span>
              </div>
            )}
          </div>
        )}

        {profile.skills && profile.skills.length > 0 && (
          <div className="px-4 pt-3 pb-4">
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {profile.skills.map((skill, i) => (
                <span key={i} className="px-2 py-0.5 rounded-full text-micro bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {profile.work_history && profile.work_history.length > 0 && (
          <div className="px-4 pt-3 pb-4">
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Histórico</p>
            <div className="space-y-2">
              {profile.work_history.map((job, i) => (
                <div key={i} className="pl-3 border-l-2 border-lia-border-subtle">
                  <p className="text-xs font-medium text-lia-text-primary">{job.title}</p>
                  <p className="text-micro text-lia-text-secondary">{job.company}</p>
                  <p className="text-micro text-lia-text-muted">{job.period}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {profile.lia_insights && profile.lia_insights.length > 0 && (
          <div className="px-4 py-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider">Insights LIA</p>
            </div>
            <div className="space-y-1.5">
              {profile.lia_insights.map((insight, i) => (
                <p key={i} className="text-xs text-lia-text-secondary bg-lia-bg-secondary rounded-lg p-2">
                  {insight}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-t border-lia-border-subtle flex-shrink-0">
        <div className="flex gap-2">
          <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-lia-text-primary bg-lia-bg-tertiary hover:bg-lia-interactive-hover transition-colors border border-lia-border-subtle">
            <MessageSquare className="w-3 h-3" /> Contatar
          </button>
          <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-lia-text-primary bg-lia-bg-tertiary hover:bg-lia-interactive-hover transition-colors border border-lia-border-subtle">
            <Calendar className="w-3 h-3" /> Agendar
          </button>
          <button className="flex items-center justify-center p-2 rounded-lg text-lia-text-secondary bg-lia-bg-tertiary hover:bg-lia-interactive-hover transition-colors border border-lia-border-subtle" title="Adicionar a vaga">
            <UserPlus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}
