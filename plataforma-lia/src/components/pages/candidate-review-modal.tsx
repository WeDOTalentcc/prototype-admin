'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { X, ChevronLeft, ChevronRight, ExternalLink, Check, XIcon, GripVertical, Plus, Linkedin, MapPin, Briefcase, GraduationCap, Award, TrendingUp, Building2, Clock, Star, Bookmark, Edit2, Trash2, Save, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

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

interface Preset {
  id: string
  name: string
  criteria: Criterion[]
}

const DEFAULT_PRESETS: Preset[] = [
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

const EditCriteriaPopup: React.FC<{
  isOpen: boolean
  onClose: () => void
  criteria: Criterion[]
  onUpdate: (criteria: Criterion[]) => void
}> = ({ isOpen, onClose, criteria, onUpdate }) => {
  const [localCriteria, setLocalCriteria] = useState<Criterion[]>(criteria)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [showPresets, setShowPresets] = useState(false)
  const [presetName, setPresetName] = useState('')
  const [showSavePreset, setShowSavePreset] = useState(false)
  const [savedPresets, setSavedPresets] = useState<Preset[]>([])

  useEffect(() => {
    setLocalCriteria(criteria)
  }, [criteria])

  useEffect(() => {
    try {
      const stored = localStorage.getItem('lia_criteria_presets')
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          setSavedPresets(parsed)
        }
      }
    } catch (error) {
      console.error('Error loading presets from localStorage:', error)
      setSavedPresets([])
    }
  }, [])

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return

    const newCriteria = [...localCriteria]
    const draggedItem = newCriteria[draggedIndex]
    newCriteria.splice(draggedIndex, 1)
    newCriteria.splice(index, 0, draggedItem)
    setLocalCriteria(newCriteria)
    setDraggedIndex(index)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
  }

  const handleRemove = (id: string) => {
    setLocalCriteria(localCriteria.filter(c => c.id !== id))
  }

  const handleAdd = () => {
    const newCriterion: Criterion = {
      id: `criterion_${Date.now()}`,
      text: 'New criterion...',
      isPinned: false
    }
    setLocalCriteria([...localCriteria, newCriterion])
  }

  const handleUpdate = () => {
    onUpdate(localCriteria)
    onClose()
  }

  const handleSelectPreset = (preset: Preset) => {
    const newCriteria = preset.criteria.map((c, idx) => ({
      ...c,
      id: `preset_${Date.now()}_${idx}`
    }))
    setLocalCriteria(newCriteria)
    setShowPresets(false)
  }

  const handleSavePreset = () => {
    if (!presetName.trim()) return
    
    const newPreset: Preset = {
      id: `user_preset_${Date.now()}`,
      name: presetName,
      criteria: localCriteria
    }
    
    const updatedPresets = [...savedPresets, newPreset]
    setSavedPresets(updatedPresets)
    localStorage.setItem('lia_criteria_presets', JSON.stringify(updatedPresets))
    setPresetName('')
    setShowSavePreset(false)
  }

  const allPresets = [...DEFAULT_PRESETS, ...savedPresets]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div 
        className="relative bg-white dark:bg-gray-900 rounded-md w-full max-w-lg p-6 z-10"
        style={{ fontFamily: 'Open Sans, sans-serif' }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Edit Criteria
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="space-y-2 mb-6 max-h-[300px] overflow-y-auto">
          {localCriteria.map((criterion, index) => (
            <div
              key={criterion.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={`flex items-center gap-3 p-3 bg-gray-50 rounded-md border transition-all ${
                draggedIndex === index ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-800/50' : 'border-gray-200'
              }`}
            >
              <span className="text-sm font-medium text-gray-600 w-6">{index + 1}</span>
              <GripVertical className="w-4 h-4 text-gray-600 cursor-grab" />
              <input
                type="text"
                value={criterion.text}
                onChange={(e) => {
                  const newCriteria = [...localCriteria]
                  newCriteria[index].text = e.target.value
                  setLocalCriteria(newCriteria)
                }}
                className="flex-1 bg-transparent border-none outline-none text-sm text-gray-800 dark:text-gray-200"
              />
              <button
                onClick={() => handleRemove(criterion.id)}
                className="p-1 rounded hover:bg-red-50 transition-colors"
              >
                <XIcon className="w-4 h-4 text-red-400" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center gap-4 relative">
            <button 
              onClick={() => setShowPresets(!showPresets)}
              className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:underline hover:text-gray-900 dark:hover:text-gray-50"
            >
              Select Preset
            </button>
            <button 
              onClick={() => setShowSavePreset(!showSavePreset)}
              className="text-sm font-medium text-gray-600 hover:text-gray-900 flex items-center gap-1"
            >
              <Bookmark className="w-4 h-4" />
              Save Preset
            </button>

            {showPresets && (
              <div className="absolute left-0 bottom-full mb-2 bg-white rounded-md border border-gray-200 py-2 min-w-[200px] z-20">
                <p className="px-3 py-1 text-xs text-gray-600 uppercase tracking-wide">Select a preset</p>
                {allPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset)}
                    className="w-full px-3 py-2 text-left text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-50 flex items-center justify-between"
                  >
                    <span>{preset.name}</span>
                    <span className="text-xs text-gray-600">{preset.criteria.length} criteria</span>
                  </button>
                ))}
              </div>
            )}

            {showSavePreset && (
              <div className="absolute left-0 bottom-full mb-2 bg-white rounded-md border border-gray-200 p-3 min-w-[250px] z-20">
                <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Save as preset</p>
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="Preset name..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-md focus:outline-none focus:border-gray-400 dark:focus:border-gray-500 mb-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-50"
                />
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowSavePreset(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSavePreset}
                    disabled={!presetName.trim()}
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                  >
                    Save
                  </Button>
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleAdd}
              className="text-sm"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Criterion
            </Button>
            <Button
              onClick={handleUpdate}
              className="text-sm bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              Update
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export const CandidateReviewModal: React.FC<CandidateReviewModalProps> = ({
  isOpen,
  onClose,
  candidates,
  currentIndex,
  onIndexChange,
  onApprove,
  onReject,
  onEditCriteria,
  criteria,
  jobTitle
}) => {
  const [showEditCriteria, setShowEditCriteria] = useState(false)
  const [activeProfileTab, setActiveProfileTab] = useState('experience')

  const currentCandidate = candidates[currentIndex]

  const handleKeyPress = useCallback((e: KeyboardEvent) => {
    if (!isOpen || showEditCriteria) return

    if (e.key === 'a' || e.key === 'A') {
      if (currentCandidate) {
        onApprove(currentCandidate.id)
        if (currentIndex < candidates.length - 1) {
          onIndexChange(currentIndex + 1)
        }
      }
    } else if (e.key === 'r' || e.key === 'R') {
      if (currentCandidate) {
        onReject(currentCandidate.id)
        if (currentIndex < candidates.length - 1) {
          onIndexChange(currentIndex + 1)
        }
      }
    } else if (e.key === 'ArrowLeft') {
      if (currentIndex > 0) {
        onIndexChange(currentIndex - 1)
      }
    } else if (e.key === 'ArrowRight') {
      if (currentIndex < candidates.length - 1) {
        onIndexChange(currentIndex + 1)
      }
    }
  }, [isOpen, showEditCriteria, currentCandidate, currentIndex, candidates.length, onApprove, onReject, onIndexChange])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [handleKeyPress])

  if (!isOpen || !currentCandidate) return null

  return (
    <>
      <div className="fixed inset-0 z-50 flex">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        
        <div 
          className="relative flex-1 bg-white dark:bg-gray-900 m-4 rounded-md overflow-hidden flex flex-col"
          style={{ fontFamily: 'Open Sans, sans-serif' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Review Profiles</span>
              </button>
            </div>
            {jobTitle && (
              <div className="text-sm text-gray-600">
                {jobTitle}
              </div>
            )}
          </div>

          {/* Main Content - 3 Column Layout */}
          <div className="flex-1 flex overflow-hidden">
            {/* LEFT COLUMN - Candidate Profile */}
            <div className="w-[420px] border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
              {/* Candidate Header */}
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                      {currentCandidate.name}
                    </h2>
                    {currentCandidate.linkedinUrl && (
                      <a 
                        href={currentCandidate.linkedinUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-600 hover:text-gray-700 transition-colors"
                      >
                        <Linkedin className="w-5 h-5" />
                      </a>
                    )}
                  </div>
                  {currentCandidate.linkedinUrl && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs"
                      onClick={() => window.open(currentCandidate.linkedinUrl, '_blank')}
                    >
                      Full Profile
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </Button>
                  )}
                </div>

                <div className="flex items-center gap-1 text-sm text-gray-600 mb-2">
                  <MapPin className="w-4 h-4" />
                  {currentCandidate.location}
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200 mb-2">
                  {currentCandidate.companyLogo ? (
                    <img src={currentCandidate.companyLogo} alt="" className="w-5 h-5 rounded" />
                  ) : (
                    <Briefcase className="w-4 h-4 text-gray-600" />
                  )}
                  <span>{currentCandidate.currentTitle} at {currentCandidate.currentCompany}</span>
                </div>

                {currentCandidate.education && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <GraduationCap className="w-4 h-4 text-gray-600" />
                    <span>{currentCandidate.education}</span>
                  </div>
                )}
              </div>

              {/* Profile Tabs */}
              <div className="border-b border-gray-100">
                <div className="flex px-6">
                  {['Experience', 'Education', 'Skill Map'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveProfileTab(tab.toLowerCase().replace(' ', '-'))}
                      className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                        activeProfileTab === tab.toLowerCase().replace(' ', '-')
                          ? 'text-gray-950 dark:text-gray-50 border-gray-950 dark:border-gray-50'
                          : 'text-gray-600 border-transparent hover:text-gray-800 dark:hover:text-gray-200'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeProfileTab === 'experience' && (
                  <div className="space-y-6">
                    {/* Highlights */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50">Highlights</h4>
                        <button className="text-xs text-gray-600 hover:text-gray-800 dark:hover:text-gray-200">
                          Show more ({currentCandidate.highlights.length})
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        {currentCandidate.highlights.slice(0, 3).map((highlight, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-gray-50 rounded-md border border-gray-100"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-lg">{highlight.icon}</span>
                              <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">{highlight.title}</span>
                            </div>
                            <p className="text-xs text-gray-600 line-clamp-2">
                              {highlight.description}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Experience Stats */}
                    <div className="grid grid-cols-3 gap-4 py-4 border-t border-gray-100">
                      <div>
                        <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Average Tenure</p>
                        <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">{currentCandidate.experienceStats.averageTenure}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Current Tenure</p>
                        <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">{currentCandidate.experienceStats.currentTenure}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Total Experience</p>
                        <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">{currentCandidate.experienceStats.totalExperience}</p>
                      </div>
                    </div>

                    {/* Experiences */}
                    <div className="space-y-4">
                      {currentCandidate.experiences.map((exp) => (
                        <div key={exp.id} className="relative pl-6 pb-4 border-l-2 border-gray-200 last:border-l-transparent">
                          <div className="absolute left-[-5px] top-0 w-2 h-2 rounded-full bg-gray-400" />
                          
                          <div className="flex items-start gap-3">
                            {exp.companyLogo ? (
                              <img src={exp.companyLogo} alt={exp.company} className="w-10 h-10 rounded-md" />
                            ) : (
                              <div className="w-10 h-10 rounded-md bg-gray-100 flex items-center justify-center">
                                <Building2 className="w-5 h-5 text-gray-600" />
                              </div>
                            )}
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h5 className="text-sm font-semibold text-gray-950 dark:text-gray-50">{exp.company}</h5>
                                <span className="text-xs text-gray-600">{exp.duration}</span>
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <p className="text-sm text-gray-800 dark:text-gray-200">{exp.title}</p>
                                {exp.isPromotion && (
                                  <Badge className="text-xs px-1.5 py-0.5 bg-green-50 text-green-700 border-green-200">
                                    Promotion
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-gray-600 mt-1">{exp.period}</p>
                              {exp.skills && exp.skills.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {exp.skills.slice(0, 5).map((skill, idx) => (
                                    <span key={idx} className="text-xs text-gray-600">
                                      {skill}{idx < Math.min(exp.skills!.length - 1, 4) ? ' · ' : ''}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {currentCandidate.summary && (
                      <div className="pt-4 border-t border-gray-100">
                        <p className="text-sm text-gray-600 leading-relaxed">
                          {currentCandidate.summary}
                          <button className="text-gray-600 dark:text-gray-400 hover:underline ml-1">Read More</button>
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {activeProfileTab === 'education' && (
                  <div className="space-y-4">
                    {currentCandidate.education_list?.map((edu, idx) => (
                      <div key={idx} className="p-4 bg-gray-50 rounded-md">
                        <h5 className="text-sm font-semibold text-gray-950 dark:text-gray-50">{edu.institution}</h5>
                        <p className="text-sm text-gray-600">{edu.degree}</p>
                        <p className="text-xs text-gray-600 mt-1">{edu.period}</p>
                      </div>
                    )) || (
                      <p className="text-sm text-gray-600">No education data available</p>
                    )}
                  </div>
                )}

                {activeProfileTab === 'skill-map' && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-2">Skills</h4>
                      <div className="flex flex-wrap gap-2">
                        {currentCandidate.skills?.map((skill, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        )) || (
                          <p className="text-sm text-gray-600">No skills data available</p>
                        )}
                      </div>
                    </div>
                    {currentCandidate.languages && currentCandidate.languages.length > 0 && (
                      <div className="pt-4 border-t border-gray-100">
                        <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-2">Languages</h4>
                        <div className="flex flex-wrap gap-2">
                          {currentCandidate.languages.map((lang, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {lang}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* CENTER COLUMN - Why We Matched */}
            <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-800">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    Why we matched this profile
                  </h3>
                  <button
                    onClick={() => setShowEditCriteria(true)}
                    className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 transition-colors"
                  >
                    Edit Criteria
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {currentCandidate.matchReasons.map((reason) => (
                  <Card key={reason.id} className="bg-white border-gray-200">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                          reason.isGoodMatch 
                            ? 'bg-green-50 text-green-700' 
                            : 'bg-yellow-50 text-yellow-700'
                        }`}>
                          {reason.isGoodMatch ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : (
                            <Clock className="w-3 h-3" />
                          )}
                          {reason.isGoodMatch ? 'Good Match' : 'Partial Match'}
                        </div>
                        {reason.scores && (
                          <div className="flex items-center gap-1">
                            {[...Array(reason.scores.total)].map((_, idx) => (
                              <div
                                key={idx}
                                className={`w-2 h-2 rounded-full ${
                                  idx < reason.scores!.current
                                    ? 'bg-gray-900 dark:bg-gray-50'
                                    : 'bg-gray-200'
                                }`}
                              />
                            ))}
                          </div>
                        )}
                      </div>

                      <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mt-3 mb-2">
                        {reason.criterion}
                      </h4>

                      <p className="text-sm text-gray-600 leading-relaxed">
                        {reason.explanation}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* RIGHT COLUMN - Navigation & Actions */}
            <div className="w-[220px] border-l border-gray-200 dark:border-gray-700 flex flex-col bg-white dark:bg-gray-900">
              {/* Profile Navigation */}
              <div className="p-4 border-b border-gray-100 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => onIndexChange(Math.max(0, currentIndex - 1))}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5 text-gray-600" />
                  </button>
                  <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                    Profile {currentIndex + 1}/{candidates.length}
                  </span>
                  <button
                    onClick={() => onIndexChange(Math.min(candidates.length - 1, currentIndex + 1))}
                    disabled={currentIndex === candidates.length - 1}
                    className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-4 space-y-3">
                <Button
                  onClick={() => {
                    onApprove(currentCandidate.id)
                    if (currentIndex < candidates.length - 1) {
                      onIndexChange(currentIndex + 1)
                    }
                  }}
                  className="w-full justify-center text-sm font-semibold"
                  style={{
                    backgroundColor: 'white',
                    color: 'var(--status-success)',
                    border: '2px solid var(--status-success)'
                  }}
                >
                  Approve
                  <span className="ml-2 text-xs opacity-70 bg-green-50 px-1.5 py-0.5 rounded">A</span>
                </Button>

                <Button
                  onClick={() => {
                    onReject(currentCandidate.id)
                    if (currentIndex < candidates.length - 1) {
                      onIndexChange(currentIndex + 1)
                    }
                  }}
                  className="w-full justify-center text-sm font-semibold"
                  style={{
                    backgroundColor: 'white',
                    color: 'var(--status-error)',
                    border: '2px solid var(--status-error)'
                  }}
                >
                  Reject
                  <span className="ml-2 text-xs opacity-70 bg-red-50 px-1.5 py-0.5 rounded">R</span>
                </Button>

                <p className="text-xs text-gray-600 text-center mt-4 leading-relaxed">
                  This only calibrates the agent and does not send emails.
                </p>
              </div>

              {/* Tips Section */}
              <div className="mt-auto p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs text-gray-600 leading-relaxed">
 You can <button className="hover:underline">pin criteria</button> if it is a mandatory requirement or <button className="text-gray-600 hover:underline">re-order</button> by importance using{' '}
                  <button 
                    className="text-gray-600 dark:text-gray-400 hover:underline font-medium"
                    onClick={() => setShowEditCriteria(true)}
                  >
                    Edit Criteria
                  </button>.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Criteria Popup */}
      <EditCriteriaPopup
        isOpen={showEditCriteria}
        onClose={() => setShowEditCriteria(false)}
        criteria={criteria}
        onUpdate={(newCriteria) => {
          if (onEditCriteria) {
            onEditCriteria(newCriteria)
          }
        }}
      />
    </>
  )
}

export default CandidateReviewModal
