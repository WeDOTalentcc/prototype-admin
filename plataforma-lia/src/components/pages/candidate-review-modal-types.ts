export interface Criterion {
  id: string
  text: string
  isPinned?: boolean
}

interface MatchReason {
  id: string
  criterion: string
  explanation: string
  isGoodMatch: boolean
  scores?: { current: number; total: number }
}

export interface ReviewExperience {
  id: string
  company: string
  companyLogo?: string
  title: string
  period: string
  duration: string
  location?: string
  isPromotion?: boolean
  skills?: string[]
}

export interface ReviewCandidate {
  id: string
  name: string
  linkedinUrl?: string
  location: string
  currentTitle: string
  currentCompany: string
  companyLogo?: string
  education?: string
  summary?: string
  highlights: {
    icon: string
    title: string
    description: string
  }[]
  experienceStats: {
    averageTenure: string
    currentTenure: string
    totalExperience: string
  }
  experiences: ReviewExperience[]
  education_list?: {
    institution: string
    degree: string
    period: string
  }[]
  skills?: string[]
  languages?: string[]
  matchReasons: MatchReason[]
}

export interface CandidateReviewModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: ReviewCandidate[]
  currentIndex: number
  onIndexChange: (index: number) => void
  onApprove: (candidateId: string) => void
  onReject: (candidateId: string) => void
  onEditCriteria?: (criteria: Criterion[]) => void
  criteria: Criterion[]
  jobTitle?: string
}

export interface Preset {
  id: string
  name: string
  criteria: Criterion[]
}

export const DEFAULT_PRESETS: Preset[] = [
  {
    id: 'preset_tech_senior',
    name: 'Tech Senior',
    criteria: [
      { id: 'c1', text: 'Should have 5+ years of experience in software development', isPinned: true },
      { id: 'c2', text: 'Should have experience leading technical teams', isPinned: false },
      { id: 'c3', text: 'Should have experience with cloud technologies (AWS/GCP/Azure)', isPinned: false }
    ]
  },
  {
    id: 'preset_product_manager',
    name: 'Product Manager',
    criteria: [
      { id: 'c1', text: 'Should have experience as Product Manager in tech companies', isPinned: true },
      { id: 'c2', text: 'Should have experience with agile methodologies', isPinned: false },
      { id: 'c3', text: 'Should have data-driven decision making skills', isPinned: false }
    ]
  },
  {
    id: 'preset_marketing',
    name: 'Marketing Digital',
    criteria: [
      { id: 'c1', text: 'Should have experience with digital marketing campaigns', isPinned: true },
      { id: 'c2', text: 'Should have experience with analytics tools (GA, Mixpanel)', isPinned: false },
      { id: 'c3', text: 'Should have experience with content strategy', isPinned: false }
    ]
  }
]
