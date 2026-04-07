"use client"

import type { SearchFilters } from './advancedFiltersTypes'

export function convertToPearchFilters(filters: SearchFilters): {
  customFilters: Record<string, unknown>
  apiOptions: Record<string, unknown>
  hideViewedOptions?: {
    enabled: boolean
    scope: string
    period: string
  }
} {
  const customFilters: Record<string, unknown> = {}
  const apiOptions: Record<string, unknown> = {}

  if (filters.ppiOptions) {
    apiOptions.type = filters.ppiOptions.searchType || "fast"
    apiOptions.high_freshness = filters.ppiOptions.highFreshness || false
    apiOptions.strict_filters = filters.ppiOptions.strictFilters || false
    apiOptions.require_emails = filters.ppiOptions.requireEmails || false
    apiOptions.show_emails = filters.ppiOptions.showEmails || false
    apiOptions.require_phone_numbers = filters.ppiOptions.requirePhoneNumbers || false
    apiOptions.show_phone_numbers = filters.ppiOptions.showPhoneNumbers || false
    apiOptions.require_phones_or_emails = filters.ppiOptions.requirePhonesOrEmails || false
  }

  const hideViewedOptions = filters.general?.hideViewedScope && filters.general.hideViewedScope !== "dont_hide" 
    ? {
        enabled: true,
        scope: filters.general.hideViewedScope,
        period: filters.general.hideViewedPeriod || "all_time"
      }
    : undefined

  if (filters.job?.titles?.length) {
    customFilters.titles = filters.job.titles
    customFilters.title_scope = filters.job.titleScope || "current_only"
  }
  if (filters.job?.pastTitles?.length) {
    customFilters.past_titles = filters.job.pastTitles
  }
  if (filters.job?.levels?.length) {
    customFilters.seniority_levels = filters.job.levels
  }
  if (filters.job?.roles?.length) {
    customFilters.job_functions = filters.job.roles
  }
  if (filters.job?.timeInRoleMin || filters.job?.timeInRoleMax) {
    const timeValues: Record<string, number> = {
      "3_months": 3, "6_months": 6, "1_year": 12, "1.5_years": 18,
      "2_years": 24, "3_years": 36, "5_years": 60, "7_years": 84,
      "10_years": 120, "15_years": 180
    }
    const minTime = filters.job.timeInRoleMin !== "no_limit" ? filters.job.timeInRoleMin : undefined
    const maxTime = filters.job.timeInRoleMax !== "no_limit" ? filters.job.timeInRoleMax : undefined
    const minVal = minTime ? timeValues[minTime] || 0 : 0
    const maxVal = maxTime ? timeValues[maxTime] || 999 : 999
    if (minVal <= maxVal) {
      if (minTime) customFilters.time_in_role_min = minTime
      if (maxTime) customFilters.time_in_role_max = maxTime
    }
  }
  if (filters.job?.minAverageTenure && filters.job.minAverageTenure !== "no_limit") {
    customFilters.min_average_tenure = filters.job.minAverageTenure
  }

  if (filters.company?.companyItems?.length) {
    const companyNames = filters.company.companyItems.map(c => c.name)
    const timeFilter = filters.company.companyTimeFilter || 'current_past'
    
    switch (timeFilter) {
      case 'current_only':
        customFilters.current_employer = companyNames
        break
      case 'past_only':
        customFilters.past_employer = companyNames
        break
      case 'current_past':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        break
      case 'specific_years':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        if (filters.company.specificYears) {
          customFilters.company_years_start = filters.company.specificYears.start
          customFilters.company_years_end = filters.company.specificYears.end
        }
        break
      case 'funding_stage':
        customFilters.current_employer = companyNames
        customFilters.past_employer = companyNames
        if (filters.company.fundingStages?.length) {
          customFilters.funding_stages = filters.company.fundingStages
        }
        break
    }
  }

  if (filters.company?.excludedCompanyItems?.length) {
    const excludedNames = filters.company.excludedCompanyItems.map(c => c.name)
    const excludedTimeFilter = filters.company.excludedTimeFilter || 'current_only'
    
    if (excludedTimeFilter === 'current_only') {
      customFilters.exclude_current_employer = excludedNames
    } else {
      customFilters.exclude_companies = excludedNames
    }
  }

  if (filters.company?.excludeDNC) {
    customFilters.exclude_dnc = true
  }

  if (filters.company?.industries?.length) {
    customFilters.industries = filters.company.industries
    if (filters.company.industryTimeFilter) {
      customFilters.industry_time_filter = filters.company.industryTimeFilter
    }
  }
  if (filters.company?.companyTags?.length) {
    customFilters.company_tags = filters.company.companyTags.map(t => t.name)
    if (filters.company.companyTagsTimeFilter) {
      customFilters.company_tags_time_filter = filters.company.companyTagsTimeFilter
    }
  }
  if (filters.company?.companyHQLocations?.length) {
    customFilters.company_hq_locations = filters.company.companyHQLocations
    if (filters.company.companyHQTimeFilter) {
      customFilters.company_hq_time_filter = filters.company.companyHQTimeFilter
    }
  }
  if (filters.company?.companySizes?.length) {
    customFilters.company_sizes = filters.company.companySizes
  }
  if (filters.company?.companyFoundedAfter) {
    customFilters.company_founded_after = filters.company.companyFoundedAfter
  }
  if (filters.company?.fundingStages?.length) {
    customFilters.company_funding_stages = filters.company.fundingStages
  }

  if (filters.skills?.skillItems?.length) {
    const pinnedSkills = filters.skills.skillItems.filter(s => s.isPinned).map(s => s.name)
    const regularSkills = filters.skills.skillItems.filter(s => !s.isPinned).map(s => s.name)
    
    if (pinnedSkills.length > 0) {
      customFilters.must_have_skills = pinnedSkills
    }
    if (regularSkills.length > 0) {
      customFilters.skills = regularSkills
    }
  }

  if (filters.education?.universities?.length) {
    customFilters.universities = filters.education.universities
  }
  if (filters.education?.degrees?.length) {
    customFilters.degrees = filters.education.degrees
  }
  if (filters.education?.fieldsOfStudy?.length) {
    customFilters.fields_of_study = filters.education.fieldsOfStudy
  }

  if (filters.languages?.languages?.length) {
    customFilters.languages = filters.languages.languages
  }

  // Profile indicators (all free)
  if (filters.ppiOptions?.openToWorkOnly) {
    customFilters.is_opentowork = true
  }
  if (filters.profile?.isDecisionMaker) {
    customFilters.is_decision_maker = true
  }
  if (filters.profile?.isTopUniversities) {
    customFilters.is_top_universities = true
  }
  if (filters.profile?.isStartup) {
    customFilters.company_is_startup = true
  }

  // Expertise
  if (filters.skills?.expertise?.length) {
    customFilters.expertise = filters.skills.expertise
  }

  return { customFilters, apiOptions, hideViewedOptions }
}

export function normalizeFiltersFromServer(filters: SearchFilters & Record<string, unknown>): SearchFilters {
  const normalized: SearchFilters & Record<string, unknown> = JSON.parse(JSON.stringify(filters))
  
  if (!normalized.company) {
    normalized.company = {}
  }
  
  if (normalized.company_funding_stages && !normalized.company.fundingStages) {
    normalized.company.fundingStages = normalized.company_funding_stages as string[]
  }
  
  if (normalized.company_tags && !normalized.company.companyTags) {
    const tags = Array.isArray(normalized.company_tags) 
      ? normalized.company_tags.map((t: string | { name: string }) => 
          typeof t === 'string' ? { name: t } : t
        )
      : []
    normalized.company.companyTags = tags
  }
  
  if (normalized.company_hq_locations && !normalized.company.companyHQLocations) {
    normalized.company.companyHQLocations = normalized.company_hq_locations as string[]
  }
  
  if (normalized.company_sizes && !normalized.company.companySizes) {
    normalized.company.companySizes = normalized.company_sizes as string[]
  }
  
  if (normalized.industries && !normalized.company.industries) {
    normalized.company.industries = normalized.industries as string[]
  }
  
  if (normalized.industry_time_filter && !normalized.company.industryTimeFilter) {
    normalized.company!.industryTimeFilter = normalized.industry_time_filter as NonNullable<SearchFilters['company']>['industryTimeFilter']
  }
  
  if (normalized.company_tags_time_filter && !normalized.company.companyTagsTimeFilter) {
    normalized.company!.companyTagsTimeFilter = normalized.company_tags_time_filter as NonNullable<SearchFilters['company']>['companyTagsTimeFilter']
  }
  
  if (normalized.company_hq_time_filter && !normalized.company.companyHQTimeFilter) {
    normalized.company!.companyHQTimeFilter = normalized.company_hq_time_filter as NonNullable<SearchFilters['company']>['companyHQTimeFilter']
  }
  
  const { 
    company_funding_stages, company_tags, company_hq_locations, 
    company_sizes, industries, industry_time_filter,
    company_tags_time_filter, company_hq_time_filter,
    ...cleanedFilters 
  } = normalized
  
  return cleanedFilters as SearchFilters
}
