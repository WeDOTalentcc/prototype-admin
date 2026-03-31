
import { type ApiCandidate, type ApiExperience, type ApiEducation } from "./lia-sidebar-types"

export function mapApiCandidates(candidates: ApiCandidate[], sourceId: string) {
  return candidates.map((c) => ({
    id: c.id || `${sourceId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    candidateId: c.id?.substring(0, 8).toUpperCase() || sourceId.toUpperCase(),
    name: c.name || 'Nome não disponível',
    email: c.email || '',
    phone: c.phone || '',
    current_title: c.headline || c.current_title || '',
    current_company: c.current_company || '',
    location: c.location || '',
    linkedin_url: c.linkedin_url,
    avatar_url: c.avatar_url || c.picture_url,
    avatar: c.avatar_url,
    technical_skills: c.skills || [],
    skills: c.skills || [],
    seniority_level: c.seniority_level,
    years_of_experience: c.years_experience || c.total_experience_years,
    experience: c.years_experience || c.total_experience_years || 0,
    score: c.match_score ? Math.round(c.match_score * 25) : 75,
    source: c.source || 'pearch',
    has_email: c.has_email ?? true,
    has_phone: c.has_phone ?? true,
    is_opentowork: c.is_opentowork,
    is_decision_maker: c.is_decision_maker,
    is_top_universities: c.is_top_universities,
    is_startup: c.is_startup || c.company_info?.is_startup,
    expertise: c.expertise,
    outreach_message: c.outreach_message,
    experiences: c.experiences || [],
    workHistory: (c.experiences || []).map((exp: ApiExperience) => ({
      company: exp.company_info?.name || exp.company || '',
      title: exp.company_roles?.[0]?.title || exp.title || '',
      startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
      endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
      duration: exp.duration || '',
      location: exp.company_info?.location || exp.location || '',
      description: exp.company_roles?.[0]?.description || exp.description || ''
    })),
    education: (c.education || []).map((edu: ApiEducation) => ({
      school: edu.school || '',
      degree: edu.degree || '',
      field_of_study: edu.field_of_study || '',
      fieldOfStudy: edu.field_of_study || '',
      startDate: edu.start_date || '',
      endDate: edu.end_date || ''
    }))
  }))
}
