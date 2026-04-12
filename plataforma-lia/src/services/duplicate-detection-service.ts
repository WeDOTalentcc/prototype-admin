export interface CandidateBasicInfo {
  id: string
  name: string
  email?: string
  phone?: string
  linkedin_url?: string
  current_title?: string
  current_company?: string
  location_city?: string
}

export interface DuplicateCheckResult {
  found: boolean
  candidate: CandidateBasicInfo | null
  matchType: 'email' | 'phone' | 'linkedin' | 'name_similarity' | null
  confidence: number
  message: string
}

export interface DuplicateCheckParams {
  email?: string
  phone?: string
  linkedinUrl?: string
  name?: string
}

function normalizePhone(phone: string): string {
  return phone.replace(/\D/g, '')
}

function normalizeEmail(email: string): string {
  return email.toLowerCase().trim()
}

function extractLinkedInUsername(url: string): string | null {
  const match = url.match(/linkedin\.com\/in\/([^/?]+)/i)
  return match ? match[1].toLowerCase() : null
}

function calculateNameSimilarity(name1: string, name2: string): number {
  const n1 = name1.toLowerCase().trim()
  const n2 = name2.toLowerCase().trim()
  
  if (n1 === n2) return 1.0
  
  const words1 = n1.split(/\s+/)
  const words2 = n2.split(/\s+/)
  
  let matchingWords = 0
  for (const w1 of words1) {
    if (words2.some(w2 => w2 === w1 || w2.includes(w1) || w1.includes(w2))) {
      matchingWords++
    }
  }
  
  const maxWords = Math.max(words1.length, words2.length)
  return matchingWords / maxWords
}

export class DuplicateDetectionService {
  private candidates: CandidateBasicInfo[] = []
  private lastFetchTime: number = 0
  private cacheTimeout: number = 60000

  async refreshCandidates(): Promise<void> {
    try {
      const response = await fetch('/api/backend-proxy/candidates/?skip=0&limit=1000', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      if (response.ok) {
        const data = await response.json()
        const candidatesList = Array.isArray(data) ? data : (data.candidates || data.items || [])
        this.candidates = candidatesList.map((c: Record<string, unknown>) => ({
          id: String(c.id || ''),
          name: String(c.name || c.full_name || ''),
          email: c.email != null ? String(c.email) : undefined,
          phone: c.phone != null ? String(c.phone) : undefined,
          linkedin_url: c.linkedin_url != null ? String(c.linkedin_url) : undefined,
          current_title: c.current_title != null ? String(c.current_title) : undefined,
          current_company: c.current_company != null ? String(c.current_company) : undefined,
          location_city: c.location_city != null ? String(c.location_city) : undefined
        }))
        this.lastFetchTime = Date.now()
      }
    } catch (error) {
      this.candidates = []
    }
  }

  private async ensureFreshData(): Promise<void> {
    if (Date.now() - this.lastFetchTime > this.cacheTimeout) {
      await this.refreshCandidates()
    }
  }

  async checkDuplicate(params: DuplicateCheckParams): Promise<DuplicateCheckResult> {
    await this.ensureFreshData()

    const { email, phone, linkedinUrl, name } = params

    if (email) {
      const normalizedEmail = normalizeEmail(email)
      const match = this.candidates.find(c => 
        c.email && normalizeEmail(c.email) === normalizedEmail
      )
      if (match) {
        return {
          found: true,
          candidate: match,
          matchType: 'email',
          confidence: 1.0,
          message: `Candidato "${match.name}" já existe com este email.`
        }
      }
    }

    if (phone) {
      const normalizedPhone = normalizePhone(phone)
      if (normalizedPhone.length >= 8) {
        const match = this.candidates.find(c => 
          c.phone && normalizePhone(c.phone) === normalizedPhone
        )
        if (match) {
          return {
            found: true,
            candidate: match,
            matchType: 'phone',
            confidence: 1.0,
            message: `Candidato "${match.name}" já existe com este telefone.`
          }
        }
      }
    }

    if (linkedinUrl) {
      const username = extractLinkedInUsername(linkedinUrl)
      if (username) {
        const match = this.candidates.find(c => {
          if (!c.linkedin_url) return false
          const existingUsername = extractLinkedInUsername(c.linkedin_url)
          return existingUsername === username
        })
        if (match) {
          return {
            found: true,
            candidate: match,
            matchType: 'linkedin',
            confidence: 1.0,
            message: `Candidato "${match.name}" já existe com este perfil LinkedIn.`
          }
        }
      }
    }

    if (name && name.trim().length >= 3) {
      let bestMatch: CandidateBasicInfo | null = null
      let bestSimilarity = 0

      for (const candidate of this.candidates) {
        const similarity = calculateNameSimilarity(name, candidate.name)
        if (similarity > 0.8 && similarity > bestSimilarity) {
          bestSimilarity = similarity
          bestMatch = candidate
        }
      }

      if (bestMatch && bestSimilarity > 0.85) {
        return {
          found: true,
          candidate: bestMatch,
          matchType: 'name_similarity',
          confidence: bestSimilarity,
          message: `Possível duplicata: "${bestMatch.name}" (${Math.round(bestSimilarity * 100)}% similar).`
        }
      }
    }

    return {
      found: false,
      candidate: null,
      matchType: null,
      confidence: 0,
      message: 'Nenhum candidato duplicado encontrado.'
    }
  }

  async checkByParsedCV(parsedData: { 
    full_name?: string
    email?: string
    phone?: string
    linkedin?: string 
  }): Promise<DuplicateCheckResult> {
    return this.checkDuplicate({
      email: parsedData.email,
      phone: parsedData.phone,
      linkedinUrl: parsedData.linkedin,
      name: parsedData.full_name
    })
  }
}

export const duplicateDetectionService = new DuplicateDetectionService()
