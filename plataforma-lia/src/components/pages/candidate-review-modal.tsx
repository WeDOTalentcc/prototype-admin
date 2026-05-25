'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Clock, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { EditCriteriaPopup } from './edit-criteria-popup'
import { CandidateProfileColumn } from './candidate-profile-column'
import type { CandidateReviewModalProps } from './candidate-review-modal-types'

export type { Criterion, ReviewExperience, ReviewCandidate, CandidateReviewModalProps } from './candidate-review-modal-types'

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
        <div className="absolute inset-0 bg-lia-overlay" onClick={onClose} />
        
        <div 
          className="relative flex-1 bg-lia-bg-primary dark:bg-lia-bg-primary m-4 rounded-xl overflow-hidden flex flex-col"
         
        >
          <div className="flex items-center justify-between px-6 py-4 dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="flex items-center gap-2 text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
              >
                <ChevronLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Review Profiles</span>
              </button>
            </div>
            {jobTitle && (
              <div className="text-sm text-lia-text-secondary">
                {jobTitle}
              </div>
            )}
          </div>

          <div className="flex-1 flex overflow-hidden">
            <CandidateProfileColumn candidate={currentCandidate} />

            <div className="flex-1 flex flex-col overflow-hidden bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <div className="p-6 dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-lia-text-primary">
                    Why we matched this profile
                  </h3>
                  <button
                    onClick={() => setShowEditCriteria(true)}
                    className="text-sm font-medium text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
                  >
                    Edit Criteria
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {currentCandidate.matchReasons.map((reason) => (
                  <Card key={reason.id} className="bg-lia-bg-primary border-lia-border-subtle">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                          reason.isGoodMatch 
                            ? 'bg-status-success/10 text-status-success' 
                            : 'bg-status-warning/10 text-status-warning'
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
                                key={`dot-${idx}`}
                                className={`w-2 h-2 rounded-full ${
                                  idx < reason.scores!.current
                                    ? 'bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg'
                                    : 'bg-lia-interactive-active'
                                }`}
                              />
                            ))}
                          </div>
                        )}
                      </div>

                      <h4 className="text-sm font-semibold text-lia-text-primary mt-3 mb-2">
                        {reason.criterion}
                      </h4>

                      <p className="text-sm text-lia-text-secondary leading-relaxed">
                        {reason.explanation}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div className="w-[220px] border-l border-lia-border-subtle dark:border-lia-border-subtle flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary">
              <div className="p-4 dark:border-lia-border-subtle">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => onIndexChange(Math.max(0, currentIndex - 1))}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5 text-lia-text-secondary" />
                  </button>
                  <span className="text-sm font-medium text-lia-text-primary">
                    Profile {currentIndex + 1}/{candidates.length}
                  </span>
                  <button
                    onClick={() => onIndexChange(Math.min(candidates.length - 1, currentIndex + 1))}
                    disabled={currentIndex === candidates.length - 1}
                    className="p-2 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5 text-lia-text-secondary" />
                  </button>
                </div>
              </div>

              <div className="p-4 space-y-3">
                <Button
                  onClick={() => {
                    onApprove(currentCandidate.id)
                    if (currentIndex < candidates.length - 1) {
                      onIndexChange(currentIndex + 1)
                    }
                  }}
                  className="w-full justify-center text-sm font-semibold bg-lia-bg-primary text-status-success"
                 
                >
                  Approve
                  <span className="ml-2 text-micro opacity-70 bg-status-success/10 px-1.5 py-0.5 rounded-md">A</span>
                </Button>

                <Button
                  onClick={() => {
                    onReject(currentCandidate.id)
                    if (currentIndex < candidates.length - 1) {
                      onIndexChange(currentIndex + 1)
                    }
                  }}
                  className="w-full justify-center text-sm font-semibold bg-lia-bg-primary text-status-error"
                 
                >
                  Reject
                  <span className="ml-2 text-micro opacity-70 bg-status-error/10 px-1.5 py-0.5 rounded-md">R</span>
                </Button>

                <p className="text-xs text-lia-text-secondary text-center mt-4 leading-relaxed">
                  This only calibrates the agent and does not send emails.
                </p>
              </div>

              <div className="mt-auto p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <p className="text-xs text-lia-text-secondary leading-relaxed">
 You can <button className="hover:underline">pin criteria</button> if it is a mandatory requirement or <button className="text-lia-text-secondary hover:underline">re-order</button> by importance using{' '}
                  <button 
                    className="text-lia-text-secondary hover:underline font-medium"
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
