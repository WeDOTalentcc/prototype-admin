'use client'

import NextImage from"next/image"
import React, { useState } from 'react'
import { ExternalLink, Linkedin, MapPin, Briefcase, GraduationCap, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Chip } from '@/components/ui/chip'
import { ReviewCandidate } from './candidate-review-modal-types'

interface CandidateProfileColumnProps {
  candidate: ReviewCandidate
}

export const CandidateProfileColumn: React.FC<CandidateProfileColumnProps> = ({ candidate }) => {
  const [activeProfileTab, setActiveProfileTab] = useState('experience')

  return (
    <div className="w-[420px] border-r border-lia-border-subtle dark:border-lia-border-subtle flex flex-col overflow-hidden">
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-semibold text-lia-text-primary">
              {candidate.name}
            </h2>
            {candidate.linkedinUrl && (
              <a 
                href={candidate.linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-lia-text-secondary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            )}
          </div>
          {candidate.linkedinUrl && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={() => window.open(candidate.linkedinUrl, '_blank')}
            >
              Full Profile
              <ExternalLink className="w-3 h-3 ml-1" />
            </Button>
          )}
        </div>

        <div className="flex items-center gap-1 text-sm text-lia-text-secondary mb-2">
          <MapPin className="w-4 h-4" />
          {candidate.location}
        </div>

        <div className="flex items-center gap-2 text-sm text-lia-text-primary mb-2">
          {candidate.companyLogo ? (
            <NextImage src={candidate.companyLogo} alt="" width={20} height={20} className="w-5 h-5 rounded-md" />
          ) : (
            <Briefcase className="w-4 h-4 text-lia-text-secondary" />
          )}
          <span>{candidate.currentTitle} at {candidate.currentCompany}</span>
        </div>

        {candidate.education && (
          <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
            <GraduationCap className="w-4 h-4 text-lia-text-secondary" />
            <span>{candidate.education}</span>
          </div>
        )}
      </div>

      <div >
        <div className="flex px-6">
          {['Experience', 'Education', 'Skill Map'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveProfileTab(tab.toLowerCase().replace(' ', '-'))}
              className={`px-4 py-3 text-sm font-medium transition-colors motion-reduce:transition-none rounded-lg ${
                activeProfileTab === tab.toLowerCase().replace(' ', '-')
                  ? 'text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-medium'
                  : 'text-lia-text-secondary border-transparent hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {activeProfileTab === 'experience' && (
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-lia-text-primary">Highlights</h4>
                <button className="text-xs text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
                  Show more ({candidate.highlights.length})
                </button>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {candidate.highlights.slice(0, 3).map((highlight, idx) => (
                  <div
                    key={`hl-${idx}`}
                    className="p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{highlight.icon}</span>
                      <span className="text-xs font-semibold text-lia-text-primary">{highlight.title}</span>
                    </div>
                    <p className="text-xs text-lia-text-secondary line-clamp-2">
                      {highlight.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 py-4 border-t border-lia-border-subtle">
              <div>
                <p className="text-xs text-lia-text-secondary uppercase tracking-wide mb-1">Average Tenure</p>
                <p className="text-sm font-semibold text-lia-text-primary">{candidate.experienceStats.averageTenure}</p>
              </div>
              <div>
                <p className="text-xs text-lia-text-secondary uppercase tracking-wide mb-1">Current Tenure</p>
                <p className="text-sm font-semibold text-lia-text-primary">{candidate.experienceStats.currentTenure}</p>
              </div>
              <div>
                <p className="text-xs text-lia-text-secondary uppercase tracking-wide mb-1">Total Experience</p>
                <p className="text-sm font-semibold text-lia-text-primary">{candidate.experienceStats.totalExperience}</p>
              </div>
            </div>

            <div className="space-y-4">
              {candidate.experiences.map((exp) => (
                <div key={exp.id} className="relative pl-6 pb-4 border-l-4 border-lia-border-subtle last:border-l-transparent">
                  <div className="absolute left-[-5px] top-0 w-2 h-2 rounded-full bg-lia-border-medium" />
                  
                  <div className="flex items-start gap-3">
                    {exp.companyLogo ? (
                      <NextImage src={exp.companyLogo} alt={exp.company} width={40} height={40} className="w-10 h-10 rounded-md" />
                    ) : (
                      <div className="w-10 h-10 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-lia-text-secondary" />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h5 className="text-sm font-semibold text-lia-text-primary">{exp.company}</h5>
                        <span className="text-xs text-lia-text-secondary">{exp.duration}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-sm text-lia-text-primary">{exp.title}</p>
                        {exp.isPromotion && (
                          <Chip density="relaxed" variant="success" muted className="px-1.5 py-0.5">
                            Promotion
                          </Chip>
                        )}
                      </div>
                      <p className="text-xs text-lia-text-secondary mt-1">{exp.period}</p>
                      {exp.skills && exp.skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {exp.skills.slice(0, 5).map((skill, idx) => (
                            <span key={skill} className="text-xs text-lia-text-secondary">
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

            {candidate.summary && (
              <div className="pt-4 border-t border-lia-border-subtle">
                <p className="text-sm text-lia-text-secondary leading-relaxed">
                  {candidate.summary}
                  <button className="text-lia-text-secondary hover:underline ml-1">Read More</button>
                </p>
              </div>
            )}
          </div>
        )}

        {activeProfileTab === 'education' && (
          <div className="space-y-4">
            {candidate.education_list?.map((edu, idx) => (
              <div key={`edu-${idx}`} className="p-4 bg-lia-bg-secondary rounded-xl">
                <h5 className="text-sm font-semibold text-lia-text-primary">{edu.institution}</h5>
                <p className="text-sm text-lia-text-secondary">{edu.degree}</p>
                <p className="text-xs text-lia-text-secondary mt-1">{edu.period}</p>
              </div>
            )) || (
              <p className="text-sm text-lia-text-secondary">No education data available</p>
            )}
          </div>
        )}

        {activeProfileTab === 'skill-map' && (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold text-lia-text-primary mb-2">Skills</h4>
              <div className="flex flex-wrap gap-2">
                {candidate.skills?.map((skill) => (
                  <Chip density="relaxed" key={skill} variant="neutral" >
                    {skill}
                  </Chip>
                )) || (
                  <p className="text-sm text-lia-text-secondary">No skills data available</p>
                )}
              </div>
            </div>
            {candidate.languages && candidate.languages.length > 0 && (
              <div className="pt-4 border-t border-lia-border-subtle">
                <h4 className="text-sm font-semibold text-lia-text-primary mb-2">Languages</h4>
                <div className="flex flex-wrap gap-2">
                  {candidate.languages.map((lang, idx) => (
                    <Chip density="relaxed" key={`lang-${idx}`} variant="neutral" >
                      {lang}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
