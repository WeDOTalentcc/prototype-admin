"use client"

import type { ParsedEntities } from "./smartSearchConstants"

type SegmentType = 'normal' | 'job_title' | 'location' | 'skills' | 'experience' | 'industry'

interface Segment {
  text: string
  type: SegmentType
}

const getHighlightStyle = (type: string): React.CSSProperties => {
  switch (type) {
    case 'job_title':
      return { borderRadius: '3px', padding: '0 2px' }
    case 'location':
      return { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--wedo-purple)', borderRadius: '3px', padding: '0 2px' }
    case 'skills':
      return { backgroundColor: 'var(--lia-bg-secondary)', color: 'var(--status-success)', borderRadius: '3px', padding: '0 2px' }
    case 'experience':
      return { backgroundColor: 'var(--status-warning-bg)', color: 'var(--status-warning)', borderRadius: '3px', padding: '0 2px' }
    case 'industry':
      return { backgroundColor: 'var(--lia-bg-tertiary)', color: 'var(--lia-text-primary)', borderRadius: '3px', padding: '0 2px' }
    default:
      return {}
  }
}

export function buildHighlightedText(value: string, entities: ParsedEntities, filledCount: number): React.ReactNode | null {
  if (!value || filledCount === 0) {
    return null
  }

  let segments: Segment[] = []
  const usedRanges: { start: number; end: number }[] = []

  const entityMatches: { value: string; type: SegmentType; start: number; end: number }[] = []

  if (entities.job_title) {
    const idx = value.toLowerCase().indexOf(entities.job_title.toLowerCase())
    if (idx !== -1) {
      entityMatches.push({ value: entities.job_title, type: 'job_title', start: idx, end: idx + entities.job_title.length })
    }
  }
  if (entities.location) {
    const idx = value.toLowerCase().indexOf(entities.location.toLowerCase())
    if (idx !== -1) {
      entityMatches.push({ value: entities.location, type: 'location', start: idx, end: idx + entities.location.length })
    }
  }
  if (entities.years_experience) {
    const idx = value.toLowerCase().indexOf(entities.years_experience.toLowerCase())
    if (idx !== -1) {
      entityMatches.push({ value: entities.years_experience, type: 'experience', start: idx, end: idx + entities.years_experience.length })
    }
  }
  if (entities.industry) {
    const idx = value.toLowerCase().indexOf(entities.industry.toLowerCase())
    if (idx !== -1) {
      entityMatches.push({ value: entities.industry, type: 'industry', start: idx, end: idx + entities.industry.length })
    }
  }
  if (entities.skills && entities.skills.length > 0) {
    entities.skills.forEach(skill => {
      const idx = value.toLowerCase().indexOf(skill.toLowerCase())
      if (idx !== -1) {
        entityMatches.push({ value: skill, type: 'skills', start: idx, end: idx + skill.length })
      }
    })
  }

  entityMatches.sort((a, b) => a.start - b.start)

  let lastEnd = 0
  entityMatches.forEach(match => {
    const overlaps = usedRanges.some(r => 
      (match.start >= r.start && match.start < r.end) || 
      (match.end > r.start && match.end <= r.end)
    )
    if (!overlaps) {
      if (match.start > lastEnd) {
        segments.push({ text: value.substring(lastEnd, match.start), type: 'normal' })
      }
      segments.push({ text: value.substring(match.start, match.end), type: match.type })
      usedRanges.push({ start: match.start, end: match.end })
      lastEnd = match.end
    }
  })

  if (lastEnd < value.length) {
    segments.push({ text: value.substring(lastEnd), type: 'normal' })
  }

  if (segments.length === 0) {
    segments = [{ text: value, type: 'normal' }]
  }

  return (
    <span className="whitespace-pre-wrap break-words">
      {segments.map((seg, idx) => (
        <span 
          key={idx} 
          style={seg.type !== 'normal' ? getHighlightStyle(seg.type) : {}}
          className={seg.type !== 'normal' ? 'font-medium' : ''}
        >
          {seg.text}
        </span>
      ))}
    </span>
  )
}
